"""
Módulo de Inventory Health Check para validación pre-migración SAP S/4HANA.

Implementa lógica pura de análisis de inventario sin dependencias de UI.
Diseñado para degradación elegante: si faltan columnas, se omite la
verificación correspondiente y se devuelven resultados parciales con
mensajes de log claros.

Funciones principales:
    - detect_negative_stocks: Detecta stocks negativos en columnas de inventario.
    - detect_obsolete_materials: Identifica materiales obsoletos por inactividad.
    - detect_price_discrepancies: Compara precios estándar vs. media móvil.
    - classify_abc: Clasificación ABC por valor acumulado.
    - standardize_stock_units: Estandariza unidades de medida SAP.
    - run_inventory_health_check: Orquestador maestro de todas las verificaciones.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def clean_numeric(val):
    """
    Convierte un valor a float de forma segura.

    Maneja valores nulos, cadenas con comas decimales europeas y espacios.
    Devuelve None si la conversión no es posible.

    Args:
        val: Valor a convertir (cualquier tipo).

    Returns:
        float o None si la conversión falla.
    """
    if pd.isna(val):
        return None
    val_str = str(val).strip().replace(' ', '').replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None


def parse_date_flexible(val):
    """
    Intenta parsear una fecha probando múltiples formatos comunes en SAP.

    Formatos soportados (en orden de intento):
        - ISO 8601:    YYYY-MM-DD / YYYY-MM-DDTHH:MM:SS
        - SAP alemán:  DD.MM.YYYY
        - SAP compacto: YYYYMMDD
        - Barra:       DD/MM/YYYY

    Args:
        val: Valor a parsear (str, datetime, pd.Timestamp, etc.).

    Returns:
        datetime o None si no se puede parsear.
    """
    if pd.isna(val):
        return None
    if isinstance(val, (datetime, pd.Timestamp)):
        return pd.Timestamp(val).to_pydatetime()

    val_str = str(val).strip()
    if not val_str:
        return None

    formats = [
        "%Y-%m-%d",       # ISO 8601
        "%Y-%m-%dT%H:%M:%S",  # ISO 8601 con hora
        "%d.%m.%Y",       # DD.MM.YYYY (formato SAP alemán)
        "%Y%m%d",          # YYYYMMDD (formato SAP compacto)
        "%d/%m/%Y",        # DD/MM/YYYY
    ]
    for fmt in formats:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            continue

    # Último intento: dejar que pandas lo parsee
    try:
        return pd.to_datetime(val_str).to_pydatetime()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1. Detección de stocks negativos
# ---------------------------------------------------------------------------

def detect_negative_stocks(df):
    """
    Detecta valores negativos en columnas de stock del inventario.

    Verifica obligatoriamente la columna UNRESTRICTED_STOCK y, si existen,
    también BLOCKED_STOCK y QUALITY_STOCK. Los valores se parsean con
    clean_numeric para tolerar formatos europeos y cadenas malformadas.

    Args:
        df (pd.DataFrame): DataFrame con datos de inventario.

    Returns:
        tuple: (negative_df, logs)
            - negative_df: DataFrame con las filas que contienen al menos un
              stock negativo. Vacío si no hay negativos o falta la columna
              principal.
            - logs: Lista de dicts con claves 'level' y 'message'.
    """
    logs = []

    if "UNRESTRICTED_STOCK" not in df.columns:
        logs.append({
            "level": "WARNING",
            "message": "Columna 'UNRESTRICTED_STOCK' no encontrada. "
                       "Se omite la verificación de stocks negativos."
        })
        return pd.DataFrame(), logs

    stock_columns = ["UNRESTRICTED_STOCK"]
    for col in ["BLOCKED_STOCK", "QUALITY_STOCK"]:
        if col in df.columns:
            stock_columns.append(col)
        else:
            logs.append({
                "level": "INFO",
                "message": f"Columna opcional '{col}' no encontrada; se omite."
            })

    # Parsear columnas numéricas de forma segura
    work_df = df.copy()
    for col in stock_columns:
        work_df[f"_num_{col}"] = work_df[col].apply(clean_numeric)

    num_cols = [f"_num_{col}" for col in stock_columns]

    # Detectar filas con al menos un valor negativo
    mask = pd.Series(False, index=work_df.index)
    for num_col in num_cols:
        col_mask = work_df[num_col].apply(
            lambda x: x is not None and x < 0
        )
        mask = mask | col_mask

    negative_df = df.loc[mask].copy()

    total_negatives = int(mask.sum())
    logs.append({
        "level": "WARNING" if total_negatives > 0 else "INFO",
        "message": f"Stocks negativos detectados: {total_negatives} filas "
                   f"en columnas {stock_columns}."
    })

    return negative_df, logs


# ---------------------------------------------------------------------------
# 2. Detección de materiales obsoletos
# ---------------------------------------------------------------------------

def detect_obsolete_materials(df, months=24):
    """
    Identifica materiales cuyo último movimiento fue hace más de N meses.

    Parsea la columna LAST_MOVEMENT_DATE con múltiples formatos de fecha.
    Añade la columna MONTHS_INACTIVE al DataFrame de resultados.

    Args:
        df (pd.DataFrame): DataFrame con datos de inventario.
        months (int): Umbral de meses de inactividad (por defecto 24).

    Returns:
        tuple: (obsolete_df, logs)
            - obsolete_df: DataFrame con materiales obsoletos y columna
              MONTHS_INACTIVE añadida. Vacío si no hay obsoletos o falta
              la columna.
            - logs: Lista de dicts con claves 'level' y 'message'.
    """
    logs = []

    if "LAST_MOVEMENT_DATE" not in df.columns:
        logs.append({
            "level": "WARNING",
            "message": "Columna 'LAST_MOVEMENT_DATE' no encontrada. "
                       "Se omite la verificación de materiales obsoletos."
        })
        return pd.DataFrame(), logs

    now = datetime.now()
    cutoff_date = now - relativedelta(months=months)

    parsed_dates = df["LAST_MOVEMENT_DATE"].apply(parse_date_flexible)

    unparseable_count = int(parsed_dates.isna().sum() & df["LAST_MOVEMENT_DATE"].notna().sum())
    # Contar correctamente los que no se pudieron parsear (tenían valor pero no se parseó)
    has_value = df["LAST_MOVEMENT_DATE"].notna() & (df["LAST_MOVEMENT_DATE"].astype(str).str.strip() != "")
    failed_parse = has_value & parsed_dates.isna()
    unparseable_count = int(failed_parse.sum())

    if unparseable_count > 0:
        logs.append({
            "level": "WARNING",
            "message": f"{unparseable_count} fechas no se pudieron parsear en "
                       "'LAST_MOVEMENT_DATE'."
        })

    # Calcular meses de inactividad
    months_inactive = parsed_dates.apply(
        lambda d: (relativedelta(now, d).years * 12 + relativedelta(now, d).months)
        if d is not None else None
    )

    # Filtrar obsoletos: fecha parseada válida y anterior al corte
    obsolete_mask = parsed_dates.apply(
        lambda d: d is not None and d < cutoff_date
    )

    obsolete_df = df.loc[obsolete_mask].copy()
    obsolete_df["MONTHS_INACTIVE"] = months_inactive.loc[obsolete_mask].values

    total_obsolete = int(obsolete_mask.sum())
    logs.append({
        "level": "WARNING" if total_obsolete > 0 else "INFO",
        "message": f"Materiales obsoletos (>{months} meses sin movimiento): "
                   f"{total_obsolete} de {len(df)} registros."
    })

    return obsolete_df, logs


# ---------------------------------------------------------------------------
# 3. Detección de discrepancias de precio
# ---------------------------------------------------------------------------

def detect_price_discrepancies(df, threshold_pct=10.0):
    """
    Compara STANDARD_PRICE vs MOVING_AVG_PRICE y detecta discrepancias.

    Calcula diferencias absolutas y porcentuales, clasificando cada fila como
    'OK', 'WARNING' o 'ERROR' según umbrales configurables.

    Criterios de clasificación:
        - OK:      diferencia porcentual <= threshold_pct
        - WARNING: threshold_pct < diferencia <= threshold_pct × 2
        - ERROR:   diferencia > threshold_pct × 2

    Args:
        df (pd.DataFrame): DataFrame con columnas de precios.
        threshold_pct (float): Umbral porcentual base (por defecto 10.0).

    Returns:
        tuple: (discrepancy_df, logs, kpis)
            - discrepancy_df: DataFrame solo con filas con discrepancias
              (WARNING o ERROR), enriquecido con PRICE_DIFF_ABS,
              PRICE_DIFF_PCT y PRICE_DISC_STATUS.
            - logs: Lista de dicts con claves 'level' y 'message'.
            - kpis: Dict con conteos {'ok': N, 'warning': N, 'error': N,
              'total_with_discrepancy': N}.
    """
    logs = []
    kpis = {"ok": 0, "warning": 0, "error": 0, "total_with_discrepancy": 0}

    required_cols = ["STANDARD_PRICE", "MOVING_AVG_PRICE"]
    missing = [c for c in required_cols if c not in df.columns]

    if missing:
        logs.append({
            "level": "WARNING",
            "message": f"Columnas de precio faltantes: {missing}. "
                       "Se omite la verificación de discrepancias de precio."
        })
        return pd.DataFrame(), logs, kpis

    work_df = df.copy()
    work_df["_std_price"] = work_df["STANDARD_PRICE"].apply(clean_numeric)
    work_df["_avg_price"] = work_df["MOVING_AVG_PRICE"].apply(clean_numeric)

    # Solo considerar filas donde ambos precios son válidos y el estándar > 0
    valid_mask = (
        work_df["_std_price"].notna() &
        work_df["_avg_price"].notna() &
        (work_df["_std_price"] > 0)
    )

    work_df["PRICE_DIFF_ABS"] = np.nan
    work_df["PRICE_DIFF_PCT"] = np.nan
    work_df["PRICE_DISC_STATUS"] = "OK"

    if valid_mask.any():
        work_df.loc[valid_mask, "PRICE_DIFF_ABS"] = (
            (work_df.loc[valid_mask, "_std_price"] -
             work_df.loc[valid_mask, "_avg_price"]).abs()
        )
        work_df.loc[valid_mask, "PRICE_DIFF_PCT"] = (
            work_df.loc[valid_mask, "PRICE_DIFF_ABS"] /
            work_df.loc[valid_mask, "_std_price"] * 100.0
        )

        # Clasificar
        pct = work_df["PRICE_DIFF_PCT"]
        work_df.loc[valid_mask & (pct > threshold_pct) & (pct <= threshold_pct * 2),
                    "PRICE_DISC_STATUS"] = "WARNING"
        work_df.loc[valid_mask & (pct > threshold_pct * 2),
                    "PRICE_DISC_STATUS"] = "ERROR"

    # Conteos
    status_counts = work_df.loc[valid_mask, "PRICE_DISC_STATUS"].value_counts()
    kpis["ok"] = int(status_counts.get("OK", 0))
    kpis["warning"] = int(status_counts.get("WARNING", 0))
    kpis["error"] = int(status_counts.get("ERROR", 0))
    kpis["total_with_discrepancy"] = kpis["warning"] + kpis["error"]

    # Filtrar solo discrepancias
    disc_mask = work_df["PRICE_DISC_STATUS"].isin(["WARNING", "ERROR"])
    result_cols = [c for c in df.columns] + [
        "PRICE_DIFF_ABS", "PRICE_DIFF_PCT", "PRICE_DISC_STATUS"
    ]
    discrepancy_df = work_df.loc[disc_mask, result_cols].copy()

    logs.append({
        "level": "WARNING" if kpis["total_with_discrepancy"] > 0 else "INFO",
        "message": f"Discrepancias de precio: {kpis['warning']} advertencias, "
                   f"{kpis['error']} errores de {int(valid_mask.sum())} "
                   f"registros evaluados."
    })

    return discrepancy_df, logs, kpis


# ---------------------------------------------------------------------------
# 4. Clasificación ABC
# ---------------------------------------------------------------------------

def classify_abc(df, value_column="TOTAL_VALUE"):
    """
    Realiza la clasificación ABC estándar por valor acumulado.

    Criterios de clasificación:
        - Clase A: Artículos que representan el 80% del valor total acumulado.
        - Clase B: Siguientes artículos que representan el 15% del valor total.
        - Clase C: Artículos restantes que representan el 5% del valor total.

    Añade la columna ABC_CLASS al DataFrame devuelto.

    Args:
        df (pd.DataFrame): DataFrame con datos de inventario.
        value_column (str): Nombre de la columna de valor (por defecto
            'TOTAL_VALUE').

    Returns:
        tuple: (df_with_abc, summary)
            - df_with_abc: DataFrame con columna ABC_CLASS añadida.
            - summary: Dict con estructura por clase:
              {'A': {'count': N, 'pct_items': X, 'pct_value': Y},
               'B': {...}, 'C': {...}}
              Si falta la columna de valor, summary es un dict vacío con
              un log de advertencia.
    """
    logs_or_summary = {}

    if value_column not in df.columns:
        logs_or_summary = {
            "warning": f"Columna '{value_column}' no encontrada. "
                       "Se omite la clasificación ABC."
        }
        return df.copy(), logs_or_summary

    work_df = df.copy()
    work_df["_value_num"] = work_df[value_column].apply(clean_numeric)

    # Reemplazar None/NaN con 0 para la clasificación
    work_df["_value_num"] = work_df["_value_num"].fillna(0.0)

    total_value = work_df["_value_num"].sum()

    if total_value == 0:
        work_df["ABC_CLASS"] = "C"
        summary = {
            "A": {"count": 0, "pct_items": 0.0, "pct_value": 0.0},
            "B": {"count": 0, "pct_items": 0.0, "pct_value": 0.0},
            "C": {"count": len(work_df), "pct_items": 100.0, "pct_value": 0.0},
        }
        result_df = work_df.drop(columns=["_value_num"])
        return result_df, summary

    # Ordenar por valor descendente
    work_df = work_df.sort_values("_value_num", ascending=False).reset_index(drop=True)

    # Calcular valor acumulado porcentual
    work_df["_cum_value"] = work_df["_value_num"].cumsum()
    work_df["_cum_pct"] = work_df["_cum_value"] / total_value * 100.0

    # Asignar clases
    work_df["ABC_CLASS"] = "C"  # Por defecto
    work_df.loc[work_df["_cum_pct"] <= 80.0, "ABC_CLASS"] = "A"

    # Para B: > 80% y <= 95%
    b_mask = (work_df["_cum_pct"] > 80.0) & (work_df["_cum_pct"] <= 95.0)
    work_df.loc[b_mask, "ABC_CLASS"] = "B"

    # Ajuste: asegurar que el primer ítem que cruza el 80% es A
    a_count = (work_df["ABC_CLASS"] == "A").sum()
    if a_count == 0 and len(work_df) > 0:
        work_df.iloc[0, work_df.columns.get_loc("ABC_CLASS")] = "A"

    # Generar resumen
    n_total = len(work_df)
    summary = {}
    for cls in ["A", "B", "C"]:
        cls_mask = work_df["ABC_CLASS"] == cls
        cls_count = int(cls_mask.sum())
        cls_value = float(work_df.loc[cls_mask, "_value_num"].sum())
        summary[cls] = {
            "count": cls_count,
            "pct_items": round(cls_count / n_total * 100.0, 2) if n_total > 0 else 0.0,
            "pct_value": round(cls_value / total_value * 100.0, 2) if total_value > 0 else 0.0,
        }

    # Limpiar columnas temporales
    result_df = work_df.drop(columns=["_value_num", "_cum_value", "_cum_pct"])

    return result_df, summary


# ---------------------------------------------------------------------------
# 5. Estandarización de unidades de stock
# ---------------------------------------------------------------------------

# Tabla de conversiones SAP: unidad_origen -> (factor, unidad_destino)
_UNIT_CONVERSION_TABLE = {
    # Peso → KG
    "G":   (1 / 1000, "KG"),
    "TON": (1000,     "KG"),
    "LB":  (0.4536,   "KG"),
    # Longitud → M
    "CM":  (1 / 100,  "M"),
    "MM":  (1 / 1000, "M"),
    "DM":  (1 / 10,   "M"),
    # Volumen → L
    "ML":  (1 / 1000, "L"),
}


def standardize_stock_units(df, base_uom_column="BASE_UOM", stock_columns=None):
    """
    Estandariza unidades de medida de stock según tabla de conversión SAP.

    Convierte valores de stock de unidades de origen a unidades de referencia
    dentro de cada dimensión (peso→KG, longitud→M, volumen→L).

    Conversiones soportadas:
        - Peso:    G→KG (÷1000), TON→KG (×1000), LB→KG (×0.4536)
        - Longitud: CM→M (÷100), MM→M (÷1000), DM→M (÷10)
        - Volumen:  ML→L (÷1000)

    Si la unidad de medida base no está en la tabla de conversiones, se
    mantiene el valor original sin cambios.

    Args:
        df (pd.DataFrame): DataFrame con datos de inventario.
        base_uom_column (str): Columna con la unidad de medida base
            (por defecto 'BASE_UOM').
        stock_columns (list[str] | None): Lista de columnas de stock a
            estandarizar. Si es None, se usa ['UNRESTRICTED_STOCK'].

    Returns:
        tuple: (df_with_std, logs, conversions_count)
            - df_with_std: DataFrame con columnas STOCK_STANDARDIZED y
              STOCK_UNIT_STANDARDIZED añadidas.
            - logs: Lista de dicts con claves 'level' y 'message'.
            - conversions_count: Entero con el número de conversiones
              realizadas.
    """
    logs = []
    conversions_count = 0

    if base_uom_column not in df.columns:
        logs.append({
            "level": "WARNING",
            "message": f"Columna '{base_uom_column}' no encontrada. "
                       "Se omite la estandarización de unidades."
        })
        return df.copy(), logs, conversions_count

    if stock_columns is None:
        stock_columns = ["UNRESTRICTED_STOCK"]

    # Verificar que al menos una columna de stock exista
    available_stock_cols = [c for c in stock_columns if c in df.columns]
    if not available_stock_cols:
        logs.append({
            "level": "WARNING",
            "message": f"Ninguna columna de stock encontrada entre {stock_columns}. "
                       "Se omite la estandarización."
        })
        return df.copy(), logs, conversions_count

    primary_stock_col = available_stock_cols[0]
    if len(available_stock_cols) < len(stock_columns):
        missing_cols = set(stock_columns) - set(available_stock_cols)
        logs.append({
            "level": "INFO",
            "message": f"Columnas de stock no encontradas: {sorted(missing_cols)}. "
                       f"Se usa '{primary_stock_col}' como columna principal."
        })

    work_df = df.copy()

    # Inicializar columnas de resultado
    work_df["STOCK_STANDARDIZED"] = np.nan
    work_df["STOCK_UNIT_STANDARDIZED"] = ""

    stock_numeric = work_df[primary_stock_col].apply(clean_numeric)

    for idx in work_df.index:
        uom_raw = work_df.loc[idx, base_uom_column]
        stock_val = stock_numeric.loc[idx]

        if pd.isna(uom_raw) or stock_val is None:
            # Mantener valor original si existe
            work_df.loc[idx, "STOCK_STANDARDIZED"] = stock_val if stock_val is not None else np.nan
            uom_str = str(uom_raw).strip().upper() if pd.notna(uom_raw) else ""
            work_df.loc[idx, "STOCK_UNIT_STANDARDIZED"] = uom_str
            continue

        uom = str(uom_raw).strip().upper()

        if uom in _UNIT_CONVERSION_TABLE:
            factor, target_unit = _UNIT_CONVERSION_TABLE[uom]
            work_df.loc[idx, "STOCK_STANDARDIZED"] = round(stock_val * factor, 6)
            work_df.loc[idx, "STOCK_UNIT_STANDARDIZED"] = target_unit
            conversions_count += 1
        else:
            # Unidad no convertible: mantener original
            work_df.loc[idx, "STOCK_STANDARDIZED"] = stock_val
            work_df.loc[idx, "STOCK_UNIT_STANDARDIZED"] = uom

    logs.append({
        "level": "INFO",
        "message": f"Estandarización de unidades completada: {conversions_count} "
                   f"conversiones realizadas de {len(df)} registros."
    })

    return work_df, logs, conversions_count


# ---------------------------------------------------------------------------
# 6. Orquestador maestro: run_inventory_health_check
# ---------------------------------------------------------------------------

def run_inventory_health_check(df, obsolescence_months=24, price_threshold_pct=10.0):
    """
    Ejecuta todas las verificaciones de salud del inventario.

    Orquesta las siguientes verificaciones en secuencia:
        1. Detección de stocks negativos
        2. Detección de materiales obsoletos
        3. Detección de discrepancias de precios
        4. Clasificación ABC
        5. Estandarización de unidades de stock

    Agrega todos los logs y KPIs en un resultado unificado.

    Args:
        df (pd.DataFrame): DataFrame con datos de inventario.
        obsolescence_months (int): Meses de inactividad para considerar
            un material como obsoleto (por defecto 24).
        price_threshold_pct (float): Umbral porcentual para discrepancias
            de precio (por defecto 10.0).

    Returns:
        dict: Diccionario con las siguientes claves:
            - 'negative_stocks': DataFrame con stocks negativos.
            - 'obsolete_materials': DataFrame con materiales obsoletos.
            - 'price_discrepancies': DataFrame con discrepancias de precio.
            - 'abc_classification': Dict resumen de clasificación ABC.
            - 'unit_standardization': DataFrame con unidades estandarizadas.
            - 'logs': Lista consolidada de todos los logs.
            - 'kpis': Dict con conteos clave del análisis.
            - 'df': DataFrame enriquecido con ABC_CLASS y columnas de
              estandarización.
    """
    all_logs = []
    kpis = {
        "negative_stocks": 0,
        "obsolete_materials": 0,
        "price_discrepancies": 0,
        "abc_a_count": 0,
        "abc_b_count": 0,
        "abc_c_count": 0,
        "unit_conversions": 0,
    }

    all_logs.append({
        "level": "INFO",
        "message": f"Iniciando Inventory Health Check: {len(df)} registros, "
                   f"umbral obsolescencia={obsolescence_months} meses, "
                   f"umbral precio={price_threshold_pct}%."
    })

    # --- 1. Stocks negativos ---
    negative_df, neg_logs = detect_negative_stocks(df)
    all_logs.extend(neg_logs)
    kpis["negative_stocks"] = len(negative_df)

    # --- 2. Materiales obsoletos ---
    obsolete_df, obs_logs = detect_obsolete_materials(df, months=obsolescence_months)
    all_logs.extend(obs_logs)
    kpis["obsolete_materials"] = len(obsolete_df)

    # --- 3. Discrepancias de precio ---
    disc_df, disc_logs, disc_kpis = detect_price_discrepancies(
        df, threshold_pct=price_threshold_pct
    )
    all_logs.extend(disc_logs)
    kpis["price_discrepancies"] = disc_kpis.get("total_with_discrepancy", 0)

    # --- 4. Clasificación ABC ---
    df_abc, abc_summary = classify_abc(df)
    if isinstance(abc_summary, dict) and "warning" not in abc_summary:
        kpis["abc_a_count"] = abc_summary.get("A", {}).get("count", 0)
        kpis["abc_b_count"] = abc_summary.get("B", {}).get("count", 0)
        kpis["abc_c_count"] = abc_summary.get("C", {}).get("count", 0)
        all_logs.append({
            "level": "INFO",
            "message": f"Clasificación ABC: A={kpis['abc_a_count']}, "
                       f"B={kpis['abc_b_count']}, C={kpis['abc_c_count']}."
        })
    else:
        all_logs.append({
            "level": "WARNING",
            "message": abc_summary.get("warning", "Clasificación ABC no disponible.")
        })

    # --- 5. Estandarización de unidades ---
    # Aplicar sobre el DataFrame ya enriquecido con ABC
    df_std, std_logs, conv_count = standardize_stock_units(df_abc)
    all_logs.extend(std_logs)
    kpis["unit_conversions"] = conv_count

    all_logs.append({
        "level": "INFO",
        "message": "Inventory Health Check completado."
    })

    return {
        "negative_stocks": negative_df,
        "obsolete_materials": obsolete_df,
        "price_discrepancies": disc_df,
        "abc_classification": abc_summary,
        "unit_standardization": df_std,
        "logs": all_logs,
        "kpis": kpis,
        "df": df_std,
    }
