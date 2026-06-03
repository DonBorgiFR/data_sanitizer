"""
Módulo de Costeo de Producto (Product Costing) para validación pre-migración SAP S/4HANA.

Simula el cálculo de coste estándar a partir de la lista de materiales (BOM),
las hojas de ruta (Routing) y los datos maestros de materiales (MM).

Limitaciones conocidas:
- La explosión de BOM es de un solo nivel (single-level). No se realiza
  explosión recursiva de sub-ensamblajes. Los componentes que a su vez
  tengan su propia BOM no serán desglosados en sus materias primas.

Principios de diseño:
- Lógica pura, sin dependencias de UI (no importa streamlit).
- Degradación elegante: si faltan tablas o columnas, se devuelven
  resultados parciales con mensajes claros en lugar de bloquear la ejecución.
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple, Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_numeric(val) -> Optional[float]:
    """
    Convierte un valor a float de forma segura.

    Maneja formatos con comas como separador decimal, espacios y valores NaN.

    Args:
        val: Valor a convertir (puede ser str, int, float, None, NaN).

    Returns:
        float si la conversión es exitosa, None en caso contrario.
    """
    if pd.isna(val):
        return None
    val_str = str(val).strip().replace(' ', '').replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# 1. Cálculo de coste estándar
# ---------------------------------------------------------------------------

def calculate_standard_cost(
    bom_df: Optional[pd.DataFrame],
    routing_df: Optional[pd.DataFrame],
    mm_df: Optional[pd.DataFrame],
    default_rate: float = 35.0,
) -> Tuple[pd.DataFrame, List[Dict[str, str]], str]:
    """
    Calcula el coste estándar simulado de cada material.

    Fórmula: Coste_Total = Σ(BOM_Cantidad × Precio_Componente) + Σ(Tiempo_Ruta × Tarifa)

    La explosión de BOM es de un solo nivel (no recursiva).

    Args:
        bom_df: DataFrame con columnas [MATERIAL_PARENT, COMPONENT, QUANTITY, UOM].
                 Si es None, se omite el coste de BOM.
        routing_df: DataFrame con columnas [MATERIAL, WORK_CENTER, SETUP_TIME,
                    MACHINE_TIME, LABOR_TIME] y opcionalmente RATE.
                    Si es None, se omite el coste de ruta.
        mm_df: DataFrame con columnas [MATERIAL, PRICE].
               Si es None, se retorna DataFrame vacío con advertencia.
        default_rate: Tarifa por defecto (€/hora) cuando no existe columna RATE
                      en routing_df.

    Returns:
        Tupla (cost_df, logs, method_info):
        - cost_df: DataFrame con columnas [MATERIAL, COST_BOM, COST_ROUTING,
          COST_TOTAL_CALC, COST_LOADED, DEVIATION_ABS, DEVIATION_PCT].
        - logs: Lista de dicts con claves 'level' y 'message'.
        - method_info: 'column_rate' si se usó la columna RATE del routing,
          'default_rate' si se usó la tarifa por defecto.
    """
    logs: List[Dict[str, str]] = []
    method_info: str = "default_rate"

    result_columns = [
        "MATERIAL", "COST_BOM", "COST_ROUTING",
        "COST_TOTAL_CALC", "COST_LOADED", "DEVIATION_ABS", "DEVIATION_PCT",
    ]

    # --- Validación de mm_df (imprescindible) ---
    if mm_df is None or mm_df.empty:
        logs.append({
            "level": "WARNING",
            "message": "Datos maestros de materiales (mm_df) no disponibles. "
                       "No es posible calcular costes.",
        })
        return pd.DataFrame(columns=result_columns), logs, method_info

    # Asegurar columnas mínimas en mm_df
    mm_required = {"MATERIAL", "PRICE"}
    mm_missing = mm_required - set(mm_df.columns)
    if mm_missing:
        logs.append({
            "level": "WARNING",
            "message": f"mm_df carece de columna(s): {mm_missing}. "
                       "No es posible calcular costes.",
        })
        return pd.DataFrame(columns=result_columns), logs, method_info

    # Preparar mm_df: limpiar PRICE
    mm_clean = mm_df[["MATERIAL", "PRICE"]].copy()
    mm_clean["PRICE"] = mm_clean["PRICE"].apply(clean_numeric).fillna(0.0)

    # ---------------------------------------------------------------
    # Coste BOM
    # ---------------------------------------------------------------
    if bom_df is not None and not bom_df.empty:
        bom_required = {"MATERIAL_PARENT", "COMPONENT", "QUANTITY"}
        bom_missing = bom_required - set(bom_df.columns)
        if bom_missing:
            logs.append({
                "level": "WARNING",
                "message": f"bom_df carece de columna(s): {bom_missing}. "
                           "Se omite el coste de BOM.",
            })
            bom_cost = pd.DataFrame(columns=["MATERIAL", "COST_BOM"])
        else:
            bom_work = bom_df[["MATERIAL_PARENT", "COMPONENT", "QUANTITY"]].copy()
            bom_work["QUANTITY"] = bom_work["QUANTITY"].apply(clean_numeric).fillna(0.0)

            # Unir con precios de componentes
            bom_merged = bom_work.merge(
                mm_clean.rename(columns={"MATERIAL": "COMPONENT", "PRICE": "COMP_PRICE"}),
                on="COMPONENT",
                how="left",
            )
            bom_merged["COMP_PRICE"] = bom_merged["COMP_PRICE"].fillna(0.0)

            # Componentes sin precio
            sin_precio = bom_merged.loc[
                bom_merged["COMP_PRICE"] == 0.0, "COMPONENT"
            ].unique()
            if len(sin_precio) > 0:
                logs.append({
                    "level": "INFO",
                    "message": f"{len(sin_precio)} componente(s) de BOM sin precio en "
                               f"datos maestros: {list(sin_precio[:10])}"
                               + (" ..." if len(sin_precio) > 10 else ""),
                })

            bom_merged["LINE_COST"] = bom_merged["QUANTITY"] * bom_merged["COMP_PRICE"]
            bom_cost = (
                bom_merged.groupby("MATERIAL_PARENT", as_index=False)["LINE_COST"]
                .sum()
                .rename(columns={"MATERIAL_PARENT": "MATERIAL", "LINE_COST": "COST_BOM"})
            )
            logs.append({
                "level": "INFO",
                "message": f"Coste BOM calculado para {len(bom_cost)} material(es).",
            })
    else:
        logs.append({
            "level": "WARNING",
            "message": "bom_df no proporcionado o vacío. COST_BOM se establece a 0.",
        })
        bom_cost = pd.DataFrame(columns=["MATERIAL", "COST_BOM"])

    # ---------------------------------------------------------------
    # Coste Routing
    # ---------------------------------------------------------------
    if routing_df is not None and not routing_df.empty:
        routing_required = {"MATERIAL", "SETUP_TIME", "MACHINE_TIME", "LABOR_TIME"}
        routing_missing = routing_required - set(routing_df.columns)
        if routing_missing:
            logs.append({
                "level": "WARNING",
                "message": f"routing_df carece de columna(s): {routing_missing}. "
                           "Se omite el coste de ruta.",
            })
            routing_cost = pd.DataFrame(columns=["MATERIAL", "COST_ROUTING"])
        else:
            rt_work = routing_df.copy()

            # Limpiar tiempos
            for col in ["SETUP_TIME", "MACHINE_TIME", "LABOR_TIME"]:
                rt_work[col] = rt_work[col].apply(clean_numeric).fillna(0.0)

            rt_work["TOTAL_TIME"] = (
                rt_work["SETUP_TIME"] + rt_work["MACHINE_TIME"] + rt_work["LABOR_TIME"]
            )

            # Determinar tarifa
            if "RATE" in rt_work.columns:
                rt_work["RATE_CLEAN"] = rt_work["RATE"].apply(clean_numeric).fillna(default_rate)
                method_info = "column_rate"
                logs.append({
                    "level": "INFO",
                    "message": "Se usa la columna RATE del routing para la tarifa.",
                })
            else:
                rt_work["RATE_CLEAN"] = default_rate
                method_info = "default_rate"
                logs.append({
                    "level": "INFO",
                    "message": f"Columna RATE no encontrada en routing. "
                               f"Se aplica tarifa por defecto: {default_rate} €/h.",
                })

            rt_work["LINE_COST"] = rt_work["TOTAL_TIME"] * rt_work["RATE_CLEAN"]
            routing_cost = (
                rt_work.groupby("MATERIAL", as_index=False)["LINE_COST"]
                .sum()
                .rename(columns={"LINE_COST": "COST_ROUTING"})
            )
            logs.append({
                "level": "INFO",
                "message": f"Coste de ruta calculado para {len(routing_cost)} material(es).",
            })
    else:
        logs.append({
            "level": "WARNING",
            "message": "routing_df no proporcionado o vacío. COST_ROUTING se establece a 0.",
        })
        routing_cost = pd.DataFrame(columns=["MATERIAL", "COST_ROUTING"])

    # ---------------------------------------------------------------
    # Consolidar
    # ---------------------------------------------------------------
    # Reunir todos los materiales conocidos (de BOM, routing y mm)
    all_materials = set()
    if not bom_cost.empty:
        all_materials.update(bom_cost["MATERIAL"].unique())
    if not routing_cost.empty:
        all_materials.update(routing_cost["MATERIAL"].unique())
    all_materials.update(mm_clean["MATERIAL"].unique())

    cost_df = pd.DataFrame({"MATERIAL": list(all_materials)})

    # Unir costes BOM
    if not bom_cost.empty:
        cost_df = cost_df.merge(bom_cost, on="MATERIAL", how="left")
    else:
        cost_df["COST_BOM"] = 0.0

    # Unir costes Routing
    if not routing_cost.empty:
        cost_df = cost_df.merge(routing_cost, on="MATERIAL", how="left")
    else:
        cost_df["COST_ROUTING"] = 0.0

    cost_df["COST_BOM"] = cost_df["COST_BOM"].fillna(0.0)
    cost_df["COST_ROUTING"] = cost_df["COST_ROUTING"].fillna(0.0)
    cost_df["COST_TOTAL_CALC"] = cost_df["COST_BOM"] + cost_df["COST_ROUTING"]

    # Unir coste cargado desde datos maestros
    cost_df = cost_df.merge(
        mm_clean.rename(columns={"PRICE": "COST_LOADED"}),
        on="MATERIAL",
        how="left",
    )
    cost_df["COST_LOADED"] = cost_df["COST_LOADED"].fillna(0.0)

    # Desviaciones
    cost_df["DEVIATION_ABS"] = (cost_df["COST_LOADED"] - cost_df["COST_TOTAL_CALC"]).abs()
    cost_df["DEVIATION_PCT"] = cost_df.apply(
        lambda r: (
            (r["DEVIATION_ABS"] / r["COST_TOTAL_CALC"] * 100.0)
            if r["COST_TOTAL_CALC"] != 0
            else (100.0 if r["COST_LOADED"] != 0 else 0.0)
        ),
        axis=1,
    )

    # Reordenar columnas
    cost_df = cost_df[result_columns]

    logs.append({
        "level": "INFO",
        "message": f"Cálculo de coste estándar completado: {len(cost_df)} material(es).",
    })

    return cost_df, logs, method_info


# ---------------------------------------------------------------------------
# 2. Detección de desviaciones
# ---------------------------------------------------------------------------

def detect_cost_deviations(
    cost_df: pd.DataFrame,
    tolerance_pct: float = 5.0,
) -> Tuple[pd.DataFrame, List[Dict[str, str]], Dict[str, int]]:
    """
    Clasifica las desviaciones de coste en niveles de severidad.

    Umbrales:
    - OK: |DEVIATION_PCT| <= tolerance_pct
    - WARNING: tolerance_pct < |DEVIATION_PCT| <= tolerance_pct × 3
    - ERROR: |DEVIATION_PCT| > tolerance_pct × 3

    También indica la dirección: 'overvalued' si el coste cargado es superior
    al calculado, 'undervalued' si es inferior, 'ok' si coinciden.

    Args:
        cost_df: DataFrame resultado de calculate_standard_cost con columnas
                 DEVIATION_PCT, COST_LOADED, COST_TOTAL_CALC.
        tolerance_pct: Umbral base de tolerancia en porcentaje (por defecto 5%).

    Returns:
        Tupla (cost_df_con_estado, logs, kpis):
        - cost_df_con_estado: DataFrame original con columnas adicionales
          DEV_STATUS y DEV_DIRECTION.
        - logs: Lista de dicts con 'level' y 'message'.
        - kpis: Dict con claves 'cost_deviations_ok', 'cost_deviations_warning',
          'cost_deviations_error'.
    """
    logs: List[Dict[str, str]] = []

    if cost_df is None or cost_df.empty:
        logs.append({
            "level": "WARNING",
            "message": "cost_df vacío o None. No se pueden detectar desviaciones.",
        })
        kpis = {
            "cost_deviations_ok": 0,
            "cost_deviations_warning": 0,
            "cost_deviations_error": 0,
        }
        return cost_df if cost_df is not None else pd.DataFrame(), logs, kpis

    df = cost_df.copy()
    warn_limit = tolerance_pct * 3

    # Estado de desviación (vectorizado con np-style conditions)
    conditions_status = [
        df["DEVIATION_PCT"].abs() <= tolerance_pct,
        df["DEVIATION_PCT"].abs() <= warn_limit,
    ]
    choices_status = ["OK", "WARNING"]
    df["DEV_STATUS"] = "ERROR"  # default
    # Aplicar de más específico a menos (OK primero, luego WARNING; el resto ERROR)
    mask_ok = df["DEVIATION_PCT"].abs() <= tolerance_pct
    mask_warning = (df["DEVIATION_PCT"].abs() > tolerance_pct) & (
        df["DEVIATION_PCT"].abs() <= warn_limit
    )
    df.loc[mask_ok, "DEV_STATUS"] = "OK"
    df.loc[mask_warning, "DEV_STATUS"] = "WARNING"

    # Dirección
    df["DEV_DIRECTION"] = "ok"
    df.loc[df["COST_LOADED"] > df["COST_TOTAL_CALC"], "DEV_DIRECTION"] = "overvalued"
    df.loc[df["COST_LOADED"] < df["COST_TOTAL_CALC"], "DEV_DIRECTION"] = "undervalued"

    # KPIs
    kpis = {
        "cost_deviations_ok": int((df["DEV_STATUS"] == "OK").sum()),
        "cost_deviations_warning": int((df["DEV_STATUS"] == "WARNING").sum()),
        "cost_deviations_error": int((df["DEV_STATUS"] == "ERROR").sum()),
    }

    logs.append({
        "level": "INFO",
        "message": (
            f"Desviaciones detectadas (tolerancia {tolerance_pct}%): "
            f"OK={kpis['cost_deviations_ok']}, "
            f"WARNING={kpis['cost_deviations_warning']}, "
            f"ERROR={kpis['cost_deviations_error']}."
        ),
    })

    return df, logs, kpis


# ---------------------------------------------------------------------------
# 3. Estimación de impacto en márgenes
# ---------------------------------------------------------------------------

def estimate_margin_impact(cost_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Estima el impacto en márgenes a partir de las desviaciones de coste.

    Calcula la sobrevaloración y subvaloración totales, así como el porcentaje
    de materiales que presentan alguna desviación.

    Args:
        cost_df: DataFrame con columnas DEVIATION_ABS, DEVIATION_PCT,
                 COST_LOADED y COST_TOTAL_CALC (resultado de detect_cost_deviations
                 o calculate_standard_cost).

    Returns:
        Dict con claves:
        - total_overvaluation: Suma de DEVIATION_ABS donde COST_LOADED > COST_TOTAL_CALC.
        - total_undervaluation: Suma de DEVIATION_ABS donde COST_LOADED < COST_TOTAL_CALC.
        - materials_with_deviation: Cantidad de materiales con |DEVIATION_PCT| > 0.
        - materials_total: Total de materiales.
        - pct_with_deviation: Porcentaje de materiales con desviación.
    """
    if cost_df is None or cost_df.empty:
        return {
            "total_overvaluation": 0.0,
            "total_undervaluation": 0.0,
            "materials_with_deviation": 0,
            "materials_total": 0,
            "pct_with_deviation": 0.0,
        }

    df = cost_df.copy()

    mask_over = df["COST_LOADED"] > df["COST_TOTAL_CALC"]
    mask_under = df["COST_LOADED"] < df["COST_TOTAL_CALC"]
    mask_dev = df["DEVIATION_PCT"].abs() > 0

    materials_total = len(df)
    materials_with_deviation = int(mask_dev.sum())

    return {
        "total_overvaluation": float(df.loc[mask_over, "DEVIATION_ABS"].sum()),
        "total_undervaluation": float(df.loc[mask_under, "DEVIATION_ABS"].sum()),
        "materials_with_deviation": materials_with_deviation,
        "materials_total": materials_total,
        "pct_with_deviation": (
            round(materials_with_deviation / materials_total * 100.0, 2)
            if materials_total > 0
            else 0.0
        ),
    }
