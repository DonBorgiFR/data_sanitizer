import streamlit as st
import pandas as pd
from typing import Dict, Any, Tuple

from sanitizer.sap_templates import SAP_TEMPLATES

def render_diagnostics(health: Dict[str, Any]):
    """
    Renders the visual health check dashboard.
    """
    st.markdown("### 📊 Diagnóstico de Salud del Archivo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{health["total_rows"]}</div><div class="metric-label">Total Registros</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{health["total_columns"]}</div><div class="metric-label">Columnas Detectadas</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{health["exact_duplicates"]}</div><div class="metric-label">Duplicados Exactos (Filas)</div></div>', unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("🔍 Ver reporte de columnas y tipos de datos inferidos", expanded=False):
        col_info_list = []
        for col_name, metrics in health["columns"].items():
            col_info_list.append({
                "Columna": col_name,
                "Tipo Inferido": metrics["inferred_type"],
                "Celdas Vacías": metrics["null_count"],
                "Porcentaje Vacíos": f"{metrics['null_percentage']}%"
            })
        st.dataframe(pd.DataFrame(col_info_list), use_container_width=True)

def suggest_mapping(source_columns, target_key):
    matches = {
        "NAME": ["NAME", "NOMBRE", "RAZON SOCIAL", "CLIENTE", "PROVEEDOR", "EMPRESA", "TITLE"],
        "TAX_ID": ["TAX_ID", "TAXID", "NIF", "CIF", "NIE", "IDENTIFICACION", "DNI", "RUT"],
        "IBAN": ["IBAN", "CUENTA", "ACCOUNT", "CRA", "BANK_ACCOUNT", "BANCO"],
        "BIC": ["BIC", "SWIFT", "BIC_CODE", "SWIFT_CODE"],
        "TELEPHONE": ["TELEPHONE", "TELEFONO", "MOVIL", "PHONE", "CELULAR"],
        "POSTAL_CODE": ["POSTAL_CODE", "CP", "CODIGO POSTAL", "ZIP", "ZIP_CODE"],
        "PROVINCIA": ["PROVINCIA", "PROVINCE", "ESTADO", "REGIONAL", "REGION"],
        "ADDRESS": ["ADDRESS", "DIRECCION", "CALLE", "LOCATION", "DOMICILIO"],
        "PRICE_CTRL": ["PRICE_CTRL", "CONTROL_PRECIO", "PRECIO_CONTROL", "V_S", "TIPO_PRECIO"],
        "PRICE": ["PRICE", "PRECIO", "VALORACION", "UNIT_PRICE", "COSTE", "PRECIO_UNITARIO"],
        "MATERIAL_PARENT": ["MATERIAL_PARENT", "PADRE", "CABECERA", "PARENT", "PRODUCTO_PADRE", "MATERIAL_PADRE"],
        "COMPONENT": ["COMPONENT", "COMPONENTE", "HIJO", "CHILD", "ARTICULO_COMPONENTE"],
        "QUANTITY": ["QUANTITY", "CANTIDAD", "CANT", "QTY"],
        "UOM": ["UOM", "UNIDAD", "MEDIDA", "UNIT", "BASE_UOM"],
        "MATERIAL": ["MATERIAL", "ARTICULO", "PRODUCTO", "ITEM", "CODIGO"],
        "WORK_CENTER": ["WORK_CENTER", "PUESTO_TRABAJO", "PUESTO", "WORKCENTER", "MAQUINA"],
        "OPERATION_NUMBER": ["OPERATION_NUMBER", "OPERACION", "NUM_OPERACION", "FASE"],
        "SETUP_TIME": ["SETUP_TIME", "PREPARACION", "TIEMPO_PREPARACION", "SETUP"],
        "MACHINE_TIME": ["MACHINE_TIME", "MAQUINA_TIEMPO", "TIEMPO_MAQUINA", "MACHINE"],
        "LABOR_TIME": ["LABOR_TIME", "MANO_OBRA", "TIEMPO_MANO_OBRA", "LABOR"],
        "COST_CENTER": ["COST_CENTER", "CENTRO_COSTE", "CECO", "COSTCENTER"],
        "CONTROLLING_AREA": ["CONTROLLING_AREA", "SOCIEDAD_CO", "CONTROLLING"],
        "VALID_FROM": ["VALID_FROM", "VALIDO_DESDE", "FECHA_DESDE", "FROM_DATE"],
        "VALID_TO": ["VALID_TO", "VALIDO_HASTA", "FECHA_HASTA", "TO_DATE"],
        "PERSON_IN_CHARGE": ["PERSON_IN_CHARGE", "RESPONSABLE", "USER", "ENCARGADO"],
        "FUNCTIONAL_AREA": ["FUNCTIONAL_AREA", "AREA_FUNCIONAL", "AREA"],
        "HIERARCHY_GROUP": ["HIERARCHY_GROUP", "JERARQUIA", "GRUPO_JERARQUIA", "HIERARCHY"],
        # Inventory / Stock (MB52) — Session 7
        "PLANT": ["PLANT", "CENTRO", "PLANTA", "WERKS"],
        "STORAGE_LOCATION": ["STORAGE_LOCATION", "ALMACEN", "LGORT", "STORE_LOC"],
        "UNRESTRICTED_STOCK": ["UNRESTRICTED_STOCK", "STOCK_LIBRE", "LIBRE_UTILIZACION", "FREI"],
        "BLOCKED_STOCK": ["BLOCKED_STOCK", "STOCK_BLOQUEADO", "BLOQUEADO"],
        "QUALITY_STOCK": ["QUALITY_STOCK", "STOCK_CALIDAD", "CALIDAD", "QM_STOCK"],
        "STANDARD_PRICE": ["STANDARD_PRICE", "PRECIO_ESTANDAR", "STPRS", "STD_PRICE"],
        "MOVING_AVG_PRICE": ["MOVING_AVG_PRICE", "PRECIO_MEDIO", "VERPR", "MAP_PRICE", "PMV"],
        "TOTAL_VALUE": ["TOTAL_VALUE", "VALOR_TOTAL", "SALK3", "STOCK_VALUE"],
        "LAST_MOVEMENT_DATE": ["LAST_MOVEMENT_DATE", "ULTIMO_MOVIMIENTO", "FECHA_MOVIMIENTO", "LAST_MV_DATE"]
    }
    
    suggestions = matches.get(target_key, [])
    for col in source_columns:
        if col.upper().strip() in suggestions:
            return col
    for col in source_columns:
        col_upper = col.upper().strip()
        for suggestion in suggestions:
            if suggestion in col_upper or col_upper in suggestion:
                return col
    return None

MAP_TOOLTIPS = {
    # Custom/General fields
    "NAME": "Limpia espacios adicionales y pone el nombre en mayúsculas.",
    "TAX_ID": "Comprueba que el NIF, CIF o NIE español sea real y no tenga errores de escritura.",
    "IBAN": "Comprueba que la cuenta bancaria sea correcta y válida para transferencias.",
    "BIC": "Verifica el código del banco y que pertenezca al mismo país que la cuenta bancaria.",
    "TELEPHONE": "Normaliza el teléfono añadiendo el prefijo de país automáticamente (ej. +34).",
    "POSTAL_CODE": "Valida que el código postal exista en España y corrige su formato.",
    "PROVINCIA": "Completa o corrige el nombre de la provincia según el código postal.",
    "PROVINCE": "Completa o corrige el nombre de la provincia según el código postal.",
    "ADDRESS": "Separa la dirección en tipo de calle, nombre, número y piso para el ERP.",
    "STREET": "Calle y número de la dirección física.",
    "COUNTRY": "Código de país de dos letras (ej. ES para España).",
    # SAP specific fields
    "PARTNER_ID": "Código único de identificación de este cliente o proveedor.",
    "MATERIAL": "Código interno de este producto o artículo.",
    "DESCRIPTION": "Descripción breve del producto.",
    "MAT_TYPE": "Tipo de material (materia prima, producto semi-elaborado o terminado).",
    "INDUSTRY_SECTOR": "Sector industrial al que pertenece el material (químico, mecánico, etc.).",
    "BASE_UOM": "Unidad de medida base (ej. unidades, kilogramos, litros).",
    "MAT_GROUP": "Grupo de artículos para agrupar productos similares.",
    "NET_WEIGHT": "Peso neto del material.",
    "UNIT_OF_WEIGHT": "Unidad de medida del peso (ej. kilogramos, gramos).",
    "PRICE_CTRL": "Tipo de control de precio contable (precio estándar o precio medio).",
    "PRICE": "Precio de coste o valoración contable del producto.",
    "MATERIAL_PARENT": "Código del producto terminado en la lista de fabricación.",
    "COMPONENT": "Código del componente o ingrediente usado en la fabricación.",
    "QUANTITY": "Cantidad necesaria de este componente para fabricar el producto.",
    "UOM": "Unidad de medida del componente (ej. unidades, kilogramos).",
    "WORK_CENTER": "Máquina o sección de fábrica donde se realiza el trabajo.",
    "OPERATION_NUMBER": "Paso del proceso de fabricación (ej. primer paso, segundo paso).",
    "SETUP_TIME": "Tiempo necesario para preparar la máquina antes de iniciar la producción.",
    "MACHINE_TIME": "Tiempo de funcionamiento automático de la máquina.",
    "LABOR_TIME": "Tiempo de trabajo manual de los operarios.",
    "COST_CENTER": "Centro de coste para imputar los gastos contables de la actividad.",
    "CONTROLLING_AREA": "Área de control de costes de la organización.",
    "VALID_FROM": "Fecha desde la que empieza a ser válido este registro.",
    "VALID_TO": "Fecha límite de validez de este registro (por defecto, indefinido).",
    "PERSON_IN_CHARGE": "Nombre de la persona responsable de este centro de coste.",
    "FUNCTIONAL_AREA": "Área del negocio asociada al gasto (ej. Ventas, Administración).",
    "HIERARCHY_GROUP": "Jerarquía organizativa a la que pertenece el centro de coste.",
    "PLANT": "Centro logístico o fábrica donde se almacena el stock.",
    "STORAGE_LOCATION": "Almacén o zona física concreta dentro de la fábrica.",
    "UNRESTRICTED_STOCK": "Cantidad de producto disponible para su venta o uso libre.",
    "BLOCKED_STOCK": "Cantidad de producto bloqueada por problemas o retenciones.",
    "QUALITY_STOCK": "Cantidad de producto retenida para control de calidad.",
    "STANDARD_PRICE": "Precio estándar fijo definido para valorar el stock.",
    "MOVING_AVG_PRICE": "Precio medio ponderado del stock, calculado según las compras.",
    "TOTAL_VALUE": "Valor total del inventario (cantidad disponible por su precio).",
    "LAST_MOVEMENT_DATE": "Fecha de la última entrada o salida del material."
}

def render_mapping_config(raw_df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, str], str]:
    """
    Renders mapping UI and returns configured mapping dictionaries and active template.
    """
    st.markdown("### 🗺️ Configuración del Mapeo de Columnas")
    
    selected_template = st.selectbox(
        "📋 Cargar plantilla predefinida (SAP S/4HANA)",
        options=["[Ninguna - Mapeo Personalizado]"] + list(SAP_TEMPLATES.keys()),
        help="Elige una plantilla estándar de SAP para rellenar automáticamente los campos."
    )
    
    if selected_template != "[Ninguna - Mapeo Personalizado]":
        template_data = SAP_TEMPLATES[selected_template]
        st.info(f"ℹ️ **Plantilla seleccionada:** {template_data['description']}")
        erp_fields = {}
        for col_name, col_meta in template_data["columns"].items():
            req_label = " (Obligatorio)" if col_meta["required"] else " (Opcional)"
            erp_fields[col_name] = {
                "type": col_meta["type"],
                "label": f"{col_name}{req_label}",
                "desc": f"{col_meta['description']} - SAP Máx: {col_meta.get('length', 'N/A')} carac."
            }
    else:
        erp_fields = {
            "NAME": {"type": "text", "label": "Nombre / Razón Social", "desc": "Se limpiará de espacios y mayúsculas."},
            "TAX_ID": {"type": "tax_id", "label": "Identificación Fiscal (NIF/CIF)", "desc": "Validación estricta."},
            "IBAN": {"type": "iban", "label": "Cuenta Bancaria (IBAN)", "desc": "Módulo 97 y longitud por país."},
            "BIC": {"type": "bic", "label": "Código BIC/SWIFT", "desc": "Estructura y coherencia país-IBAN."},
            "TELEPHONE": {"type": "phone", "label": "Teléfono", "desc": "Normalización E.164 (+34)."},
            "POSTAL_CODE": {"type": "postal_code", "label": "Código Postal (España)", "desc": "Rango y autocompletado."},
            "PROVINCIA": {"type": "province", "label": "Provincia", "desc": "Autocorrección según CP."},
            "ADDRESS": {"type": "address", "label": "Dirección Completa", "desc": "División automática de vía y número."}
        }
        
    mapping_dict = {}
    column_types = {}
    
    m_col1, m_col2 = st.columns(2)
    source_cols_options = ["[Ignorar / No Mapear]"] + list(raw_df.columns)
    
    for i, (target_key, field_info) in enumerate(erp_fields.items()):
        with m_col1 if i % 2 == 0 else m_col2:
            st.markdown(f"**{field_info['label']}** `({target_key})`")
            st.caption(field_info["desc"])
            
            suggested = suggest_mapping(raw_df.columns, target_key)
            default_index = source_cols_options.index(suggested) if suggested else 0
            
            tooltip_text = MAP_TOOLTIPS.get(target_key, f"Selecciona el campo de origen para {target_key}.")
            
            selected_source = st.selectbox(
                f"Selecciona origen para {target_key}",
                options=source_cols_options,
                index=default_index,
                key=f"map_{target_key}",
                label_visibility="collapsed",
                help=tooltip_text
            )
            
            if selected_source != "[Ignorar / No Mapear]":
                mapping_dict[selected_source] = target_key
                column_types[target_key] = field_info["type"]
                
    return mapping_dict, column_types, selected_template

def render_kpis(kpis: Dict[str, int]):
    """
    Renders structured metrics based on the kpis dict from SanitizerResult.
    """
    st.markdown("#### 📈 Resumen de Correcciones Realizadas")
    
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("NIFs Corregidos / Errores", f"{kpis['tax_id_fixes']} / {kpis['tax_id_errors']}", delta=f"{kpis['tax_id_errors']} errores" if kpis['tax_id_errors'] > 0 else None, delta_color="inverse")
        st.metric("CPs Corregidos / Errores", f"{kpis['postal_code_fixes']} / {kpis['postal_code_errors']}", delta=f"{kpis['postal_code_errors']} errores" if kpis['postal_code_errors'] > 0 else None, delta_color="inverse")
    with kpi_col2:
        st.metric("IBANs Corregidos / Errores", f"{kpis['iban_fixes']} / {kpis['iban_errors']}", delta=f"{kpis['iban_errors']} errores" if kpis['iban_errors'] > 0 else None, delta_color="inverse")
        st.metric("Provincias Autocorregidas", f"{kpis['province_fixes']}")
    with kpi_col3:
        st.metric("BICs Corregidos / Errores", f"{kpis['bic_fixes']} / {kpis['bic_errors']}", delta=f"{kpis['bic_errors']} errores" if kpis['bic_errors'] > 0 else None, delta_color="inverse")
        st.metric("Direcciones Separadas", f"{kpis['address_fixes']}")
    with kpi_col4:
        st.metric("Teléfonos Normalizados", f"{kpis['phone_fixes']}")
        st.metric("Textos Normalizados", f"{kpis['text']}")
        
    if kpis.get("industrial_errors", 0) > 0 or kpis.get("industrial_warnings", 0) > 0:
        st.markdown("#### 🏭 Lógica Industrial y Controlling (MM/PP/CO)")
        ind_col1, ind_col2, ind_col3 = st.columns(3)
        with ind_col1:
            st.metric("Errores Industriales Críticos", kpis["industrial_errors"], delta=f"{kpis['industrial_errors']} errores" if kpis["industrial_errors"] > 0 else None, delta_color="inverse")
        with ind_col2:
            st.metric("Advertencias / Heurísticas", kpis["industrial_warnings"])
        with ind_col3:
            if kpis.get("complex_boms", 0) > 0:
                st.metric("BOMs Complejas (>50 comp.)", kpis["complex_boms"])
            elif kpis.get("zero_setup_routes", 0) > 0:
                st.metric("Rutas Preparación Cero", kpis["zero_setup_routes"])
            else:
                st.metric("Estado de Validación", "Validado")


def render_costing_panel(costing_results):
    """
    Renderiza el panel de Coste Estándar con tabla de desviaciones y métricas de impacto.
    """
    if costing_results is None:
        return
    
    st.markdown("### 💰 Análisis de Coste Estándar (Product Costing)")
    
    cost_df = costing_results.get("cost_df")
    method_info = costing_results.get("method_info", "default_rate")
    margin_impact = costing_results.get("margin_impact", {})
    
    if cost_df is None or cost_df.empty:
        st.info("ℹ️ No hay datos de costes disponibles para mostrar.")
        return
    
    # Método de tarifa usado
    if method_info == "column_rate":
        st.success("📊 **Método de tarifa:** Se usó la columna RATE del archivo de rutas.")
    else:
        st.info("📊 **Método de tarifa:** Se aplicó la tarifa por defecto configurada en la UI.")
    
    # Métricas de impacto
    impact_col1, impact_col2, impact_col3, impact_col4 = st.columns(4)
    with impact_col1:
        st.metric("Materiales Analizados", margin_impact.get("materials_total", 0))
    with impact_col2:
        st.metric("Con Desviación", 
                  f"{margin_impact.get('materials_with_deviation', 0)} ({margin_impact.get('pct_with_deviation', 0):.1f}%)")
    with impact_col3:
        overval = margin_impact.get("total_overvaluation", 0)
        st.metric("Sobrevaloración Total", f"{overval:,.2f} €",
                  delta=f"+{overval:,.2f}" if overval > 0 else None, delta_color="inverse")
    with impact_col4:
        underval = margin_impact.get("total_undervaluation", 0)
        st.metric("Subvaloración Total", f"{underval:,.2f} €",
                  delta=f"-{underval:,.2f}" if underval > 0 else None, delta_color="inverse")
    
    # Tabla de desviaciones con coloreo
    st.markdown("#### Detalle de Desviaciones por Material")
    
    display_cols = ["MATERIAL", "COST_BOM", "COST_ROUTING", "COST_TOTAL_CALC", 
                    "COST_LOADED", "DEVIATION_ABS", "DEVIATION_PCT"]
    if "DEV_STATUS" in cost_df.columns:
        display_cols.extend(["DEV_STATUS", "DEV_DIRECTION"])
    
    available_cols = [c for c in display_cols if c in cost_df.columns]
    
    # NOTA TÉCNICA: El estilado avanzado (pandas.Styler) queda desactivado 
    # por compatibilidad interna entre versiones de Streamlit y Pandas.
    
    styled_df = cost_df[available_cols].copy()
    for col in ["COST_BOM", "COST_ROUTING", "COST_TOTAL_CALC", "COST_LOADED", "DEVIATION_ABS"]:
        if col in styled_df.columns:
            styled_df[col] = styled_df[col].round(2)
    if "DEVIATION_PCT" in styled_df.columns:
        styled_df["DEVIATION_PCT"] = styled_df["DEVIATION_PCT"].round(2)
        
    if "DEV_STATUS" in styled_df.columns:
        # Añadir indicadores visuales (emojis)
        def add_status_emoji(val):
            if val == "OK":
                return "🟢 OK"
            elif val == "WARNING":
                return "🟡 WARNING"
            elif val == "ERROR":
                return "🔴 ERROR"
            return val
            
        styled_df["DEV_STATUS_VISUAL"] = styled_df["DEV_STATUS"].apply(add_status_emoji)
        
        # Reordenar para poner DEV_STATUS_VISUAL cerca de DEV_STATUS
        cols = list(styled_df.columns)
        cols.insert(cols.index("DEV_STATUS"), cols.pop(cols.index("DEV_STATUS_VISUAL")))
        styled_df = styled_df[cols]
        
    st.dataframe(styled_df, use_container_width=True, height=400)


def render_inventory_panel(inventory_results):
    """
    Renderiza el panel de Health Check de Inventarios con tabs para cada análisis.
    """
    if inventory_results is None:
        return
    
    st.markdown("### 📦 Health Check de Inventarios Pre-Migración")
    
    inv_kpis = inventory_results.get("kpis", {})
    
    # KPIs de resumen
    inv_col1, inv_col2, inv_col3, inv_col4 = st.columns(4)
    with inv_col1:
        neg = inv_kpis.get("negative_stocks", 0)
        st.metric("Stocks Negativos", neg, 
                  delta=f"-{neg} críticos" if neg > 0 else None, delta_color="inverse")
    with inv_col2:
        obs = inv_kpis.get("obsolete_materials", 0)
        st.metric("Materiales Obsoletos", obs,
                  delta=f"-{obs}" if obs > 0 else None, delta_color="inverse")
    with inv_col3:
        disc = inv_kpis.get("price_discrepancies", 0)
        st.metric("Discrepancias Precio", disc,
                  delta=f"-{disc}" if disc > 0 else None, delta_color="inverse")
    with inv_col4:
        st.metric("ABC", 
                  f"A:{inv_kpis.get('abc_a_count', 0)} / B:{inv_kpis.get('abc_b_count', 0)} / C:{inv_kpis.get('abc_c_count', 0)}")
    
    # Tabs de detalle
    tab_neg, tab_obs, tab_price, tab_abc = st.tabs([
        "🔴 Stocks Negativos", "⏳ Obsolescencia", "💲 Discrepancias Precio", "📊 Clasificación ABC"
    ])
    
    with tab_neg:
        neg_df = inventory_results.get("negative_stocks")
        if neg_df is not None and not neg_df.empty:
            st.warning(f"Se detectaron **{len(neg_df)}** registros con stock negativo.")
            st.dataframe(neg_df, use_container_width=True)
        else:
            st.success("✅ No se detectaron stocks negativos.")
    
    with tab_obs:
        obs_df = inventory_results.get("obsolete_materials")
        if obs_df is not None and not obs_df.empty:
            st.warning(f"Se detectaron **{len(obs_df)}** materiales sin movimiento reciente.")
            st.dataframe(obs_df, use_container_width=True)
        else:
            st.success("✅ No se detectaron materiales obsoletos.")
    
    with tab_price:
        price_df = inventory_results.get("price_discrepancies")
        if price_df is not None and not price_df.empty:
            st.warning(f"Se detectaron **{len(price_df)}** discrepancias entre precio estándar y medio variable.")
            st.dataframe(price_df, use_container_width=True)
        else:
            st.success("✅ No se detectaron discrepancias de precio significativas.")
    
    with tab_abc:
        abc_summary = inventory_results.get("abc_classification")
        if abc_summary:
            abc_col1, abc_col2, abc_col3 = st.columns(3)
            for col_ui, cls in zip([abc_col1, abc_col2, abc_col3], ["A", "B", "C"]):
                cls_data = abc_summary.get(cls, {})
                with col_ui:
                    st.markdown(f"**Clase {cls}**")
                    st.metric("Materiales", cls_data.get("count", 0))
                    st.caption(f"{cls_data.get('pct_items', 0):.1f}% de items, {cls_data.get('pct_value', 0):.1f}% del valor")
        else:
            st.info("ℹ️ Clasificación ABC no disponible (falta columna TOTAL_VALUE).")


def render_premigration_summary(result):
    """
    Renderiza el resumen ejecutivo consolidado de la pre-migración SAP.
    """
    st.markdown("### 🏭 Resumen Ejecutivo de Pre-Migración SAP")
    
    kpis = result.kpis
    
    # Calcular puntuación global simplificada
    total_errors = (kpis.get("tax_id_errors", 0) + kpis.get("iban_errors", 0) +
                    kpis.get("bic_errors", 0) + kpis.get("postal_code_errors", 0) +
                    kpis.get("industrial_errors", 0) + kpis.get("negative_stocks", 0) +
                    kpis.get("cost_deviations_error", 0))
    
    total_warnings = (kpis.get("industrial_warnings", 0) + kpis.get("cost_deviations_warning", 0) +
                      kpis.get("obsolete_materials", 0) + kpis.get("price_discrepancies", 0))
    
    total_fixes = (kpis.get("tax_id_fixes", 0) + kpis.get("iban_fixes", 0) +
                   kpis.get("phone_fixes", 0) + kpis.get("postal_code_fixes", 0) +
                   kpis.get("province_fixes", 0) + kpis.get("bic_fixes", 0) +
                   kpis.get("address_fixes", 0))
    
    sum_col1, sum_col2, sum_col3, sum_col4 = st.columns(4)
    with sum_col1:
        st.metric("🔴 Errores Críticos", total_errors,
                  delta=f"-{total_errors}" if total_errors > 0 else "0", delta_color="inverse")
    with sum_col2:
        st.metric("🟡 Advertencias", total_warnings)
    with sum_col3:
        st.metric("🟢 Correcciones Automáticas", total_fixes)
    with sum_col4:
        st.metric("📄 Registros Procesados", len(result.df))
    
    # Fases completadas
    phases = []
    phases.append("✅ Mapeo y Limpieza Semántica")
    phases.append("✅ Validación Cruzada (Geográfica / Bancaria)")
    
    if kpis.get("industrial_errors", 0) > 0 or kpis.get("industrial_warnings", 0) > 0:
        phases.append("✅ Validación Industrial (MM/PP/CO)")
    
    if result.costing_results is not None:
        phases.append("✅ Cálculo de Coste Estándar")
    
    if result.inventory_results is not None:
        phases.append("✅ Health Check de Inventarios")
    
    if result.duplicates:
        phases.append(f"✅ Deduplicación ({len(result.duplicates)} grupos detectados)")
    
    with st.expander("📋 Fases Ejecutadas", expanded=True):
        for phase in phases:
            st.markdown(f"- {phase}")


def make_error_friendly(error_msg: str) -> str:
    """
    Traduce mensajes técnicos de error a explicaciones sencillas de negocio.
    """
    if not error_msg:
        return ""
    err_lower = error_msg.lower()
    if "dígito de control" in err_lower or "letra" in err_lower or "checksum" in err_lower:
        return "La letra o dígito de control no coincide con los números. Revisa si hay algún número equivocado al teclear."
    if "longitud" in err_lower:
        return "El número de letras o números es incorrecto. Comprueba si falta algún dígito."
    if "formato" in err_lower or "estructura" in err_lower:
        return "El orden o la estructura de letras y números no es válido. Comprueba el formato."
    if "mod-97" in err_lower or "modulo-97" in err_lower or "código de control" in err_lower:
        return "Los dígitos de verificación de la cuenta bancaria son incorrectos. Revisa si hay algún número equivocado."
    if "país" in err_lower or "pais" in err_lower:
        return "El código de país no coincide con las normas internacionales o con el banco asociado."
    if "rango" in err_lower:
        return "El código postal no existe o está fuera del territorio español."
    return error_msg


def render_help_center():
    """
    Renderiza un Centro de Ayuda modular y práctico que incluye:
    - Guía de inicio rápido
    - Glosario breve de tipos semánticos
    - FAQs de incidencias reales
    - Playground interactivo de reglas
    """
    st.markdown("## 📖 Centro de Ayuda & Documentación")
    st.markdown(
        "Aprende cómo estructurar tus archivos maestros y pon a prueba "
        "las reglas de saneamiento del motor en tiempo real."
    )
    
    # Pestañas del Centro de Ayuda para un diseño limpio y modular
    tab_guide, tab_rules, tab_faq, tab_playground = st.tabs([
        "🏁 Guía Rápida", "📋 Reglas de Calidad", "❓ Preguntas Frecuentes", "🧪 Rules Playground"
    ])
    
    with tab_guide:
        st.markdown("### 🏁 Guía de Inicio Rápido en 5 Pasos")
        st.markdown(
            """
            1. **Carga del archivo**: Sube tu archivo CSV o Excel en la barra lateral. El motor autodetecta el formato.
            2. **Selecciona plantilla**: Selecciona si quieres mapear los campos a una plantilla de carga SAP (ej. Business Partner, Materiales, MB52).
            3. **Mapeo de campos**: Asocia las columnas de tu archivo a los campos destino. Revisa los textos descriptivos.
            4. **Opciones adicionales**: Activa la deduplicación difusa para buscar registros repetidos, o las validaciones industriales de Controlling.
            5. **Procesar y descargar**: Haz clic en 'Iniciar Proceso' y descarga tu paquete ZIP listo para la carga o auditoría.
            """
        )
        
    with tab_rules:
        st.markdown("### 📋 Glosario de Tipos de Datos y Validaciones")
        st.markdown(
            """
            | Tipo de Dato | Qué se limpia o normaliza | Qué se valida y verifica |
            | :--- | :--- | :--- |
            | **Identificación Fiscal (NIF/CIF/NIE)** | Símbolos, puntos, espacios y guiones. | Que la letra coincida con los números según las normas fiscales. |
            | **Cuenta Bancaria (IBAN)** | Espacios y guiones. Fuerza mayúsculas. | Que la cuenta bancaria exista y sea válida para transferencias bancarias. |
            | **Código BIC/SWIFT** | Espacios. Fuerza formato estándar. | Que identifique correctamente al banco y sea del mismo país que la cuenta. |
            | **Código Postal** | Espacios. Rellena ceros a la izquierda. | Que sea un código postal real en España (del 01 al 52). |
            | **Provincia** | Espacios y acentos. | Que corresponda exactamente con los dos primeros dígitos del código postal. |
            | **Dirección** | Abreviaturas comunes (C/ -> Calle, Av -> Avenida). | Que se pueda desglosar en tipo de calle, nombre, número y piso. |
            | **Teléfono** | Espacios, guiones y símbolos. | Que tenga el número de dígitos correcto y el formato internacional estándar. |
            """
        )
        
    with tab_faq:
        st.markdown("### ❓ Preguntas Frecuentes (FAQ)")
        
        with st.expander("¿Por qué el motor marca un NIF/CIF o un IBAN como 'Inválido'?"):
            st.write(
                "El motor no solo valida que tengan los caracteres adecuados, sino que realiza un "
                "cálculo matemático de verificación. Si este cálculo falla, el ERP (como SAP) "
                "rechazará el registro inmediatamente al cargarlo. Revisa si hay números bailados en el origen."
            )
            
        with st.expander("¿Qué es el paquete de migración (.ZIP) descargable?"):
            st.write(
                "Es un archivo comprimido que contiene todo lo necesario para tu equipo de IT y de negocio:\n"
                "- `staging_sap_load.xlsx`: Plantilla limpia de columnas técnicas, formateada para subir directamente en SAP S/4HANA (Migration Cockpit).\n"
                "- `full_audit_sanitized.xlsx`: Versión de auditoría con logs detallados de qué celda se corrigió y por qué.\n"
                "- `readiness_report.html`: Reporte de calidad visual e interactivo.\n"
                "- `migration_cleanse_audit.txt`: Trazas y auditoría de ejecución del motor para cumplimiento regulatorio o de IT."
            )
            
        with st.expander("¿Cómo funciona la deduplicación difusa y la clave de bloqueo?"):
            st.write(
                "La deduplicación difusa compara nombres de clientes o proveedores usando el algoritmo de Levenshtein "
                "para encontrar parecidos (ej: 'Construcciones S.A.' y 'Construciones SA'). "
                "Para bases de datos grandes, usamos una **clave de bloqueo** (por ejemplo, agrupar por las 3 primeras letras) "
                "para no comparar todos con todos, reduciendo drásticamente el tiempo de ejecución."
            )

        with st.expander("¿Cómo se valida la lógica industrial (BOM y Hojas de Ruta)?"):
            st.write(
                "Si activas el modo Pre-Migración SAP, el motor valida que los componentes de tus listas de materiales (BOM) "
                "tengan precios coherentes, alerta de rutas de fabricación con tiempos de preparación nulos y "
                "calcula desviaciones entre el coste cargado en SAP y el simulativo real."
            )

    with tab_playground:
        st.markdown("### 🧪 Rules Playground (Zona de Pruebas)")
        st.markdown("Escribe un valor y observa en tiempo real cómo lo procesa el motor de validación.")
        
        rule_type = st.selectbox(
            "Selecciona la regla a probar:",
            ["NIF / CIF / NIE (Fiscal)", "IBAN (Banco)", "Teléfono", "Código Postal & Provincia", "Dirección Completa"],
            help="Selecciona el tipo de validación para ensayar los datos."
        )
        
        # Importaciones dinámicas y locales de las reglas para aislar el playground
        from sanitizer.rules.tax_id import validate_tax_id
        from sanitizer.rules.iban import validate_iban
        from sanitizer.rules.phone import normalize_phone
        from sanitizer.rules.geo import validate_postal_code, get_province_by_cp
        from sanitizer.rules.address import clean_address, split_address
        
        user_input = st.text_input("Introduce un valor de prueba:", value="", placeholder="Escribe aquí un ejemplo...")
        
        if user_input.strip():
            st.markdown("#### Resultado del Análisis:")
            
            if rule_type == "NIF / CIF / NIE (Fiscal)":
                is_valid, cleaned, error = validate_tax_id(user_input)
                friendly_err = make_error_friendly(error)
                col_val1, col_val2 = st.columns(2)
                with col_val1:
                    st.metric("Valor Saneado", cleaned or "-")
                with col_val2:
                    if is_valid:
                        st.success("✅ VÁLIDO")
                    else:
                        st.error(f"❌ INCORRECTO: {friendly_err}")
                        
            elif rule_type == "IBAN (Banco)":
                is_valid, cleaned, error = validate_iban(user_input)
                friendly_err = make_error_friendly(error)
                col_val1, col_val2 = st.columns(2)
                with col_val1:
                    st.metric("Valor Saneado", cleaned or "-")
                with col_val2:
                    if is_valid:
                        st.success("✅ VÁLIDO")
                    else:
                        st.error(f"❌ INCORRECTO: {friendly_err}")
                        
            elif rule_type == "Teléfono":
                cleaned = normalize_phone(user_input)
                st.metric("Valor Saneado (E.164)", cleaned or "-")
                st.info("💡 Limpia espacios, caracteres no numéricos y asume +34 si empieza por 6, 7, 8 o 9 y tiene 9 dígitos.")
                
            elif rule_type == "Código Postal & Provincia":
                is_valid, cleaned, error = validate_postal_code(user_input)
                friendly_err = make_error_friendly(error)
                col_val1, col_val2 = st.columns(2)
                with col_val1:
                    st.metric("CP Saneado", cleaned or "-")
                    if is_valid and cleaned:
                        prov = get_province_by_cp(cleaned)
                        if prov:
                            st.markdown(f"📍 **Provincia sugerida:** `{prov}`")
                with col_val2:
                    if is_valid:
                        st.success("✅ VÁLIDO")
                    else:
                        st.error(f"❌ INCORRECTO: {friendly_err}")
                        
            elif rule_type == "Dirección Completa":
                cleaned = clean_address(user_input)
                t_via, n_via, num, piso = split_address(user_input)
                
                st.metric("Dirección Saneada", cleaned or "-")
                st.markdown("**Desglose compatible con ERP (SAP):**")
                col_d1, col_d2, col_d3, col_d4 = st.columns(4)
                col_d1.metric("Tipo de Vía", t_via or "-")
                col_d2.metric("Nombre de Vía", n_via or "-")
                col_d3.metric("Número", num or "-")
                col_d4.metric("Piso/Letra", piso or "-")
        else:
            st.caption("💡 Escribe algo en el campo superior para ver cómo el motor procesa, limpia y valida la información en tiempo real.")

def render_dry_run_panel(dry_run_df: pd.DataFrame):
    """
    Renderiza la tabla de simulacro (Dry Run).
    """
    st.markdown("### 🔍 Previsualización (Dry Run)")
    if dry_run_df.empty:
        st.info("No hay datos para previsualizar.")
        return
        
    # NOTA TÉCNICA: El estilado avanzado del Dry Run (pandas.Styler) queda desactivado 
    # temporalmente por problemas de compatibilidad interna entre versiones de Streamlit y Pandas.
    # Pendiente de revisión posterior.
    
    if "Estado" in dry_run_df.columns:
        dry_run_df["Estado_Visual"] = dry_run_df["Estado"].apply(
            lambda x: f"🟢 {x}" if str(x) == "Válido" else (f"🔴 {x}" if str(x).startswith("Rechazado") else x)
        )
        
        # Movemos Estado_Visual al principio para mayor visibilidad
        cols = list(dry_run_df.columns)
        cols.insert(0, cols.pop(cols.index("Estado_Visual")))
        dry_run_df = dry_run_df[cols]
        
    st.dataframe(dry_run_df, use_container_width=True)

def render_execution_metrics(metrics: Dict[str, Any]):
    """
    Renderiza métricas de la ejecución de sanitización (tiempo, % de rechazo, etc.).
    """
    st.markdown("#### ⏱️ Métricas de Ejecución")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Filas Procesadas", metrics.get("processed_rows", 0))
    with col2:
        st.metric("Filas Válidas", metrics.get("valid_rows", 0))
    with col3:
        st.metric("Tasa de Rechazo", f"{metrics.get('rejection_rate', 0)} %")
    with col4:
        st.metric("Tiempo de Proceso", f"{metrics.get('process_time_sec', 0)} s")

def render_rejects_panel(rejected_df: pd.DataFrame):
    """
    Muestra la tabla de rechazos y botón de descarga.
    """
    st.markdown("### 🚨 Registros Críticos Rechazados")
    if rejected_df is None or rejected_df.empty:
        st.success("¡Excelente! No hubo registros rechazados por errores críticos.")
        return
        
    st.warning(f"Se aislaron **{len(rejected_df)}** registros debido a errores críticos y no han sido incluidos en la salida principal.")
    
    st.dataframe(rejected_df, use_container_width=True)
    
    import io
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        rejected_df.to_excel(writer, index=False, sheet_name='Rechazos')
    excel_data = excel_buffer.getvalue()
    
    st.download_button(
        label="🚨 Descargar Rechazos para Corrección (Excel)",
        data=excel_data,
        file_name="registros_rechazados.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def render_demo_pitch_tab():
    """
    Renderiza la guía de demostración corporativa y narrativa de producto (Demo Pitch).
    Completamente autocontenida, sin efectos colaterales sobre el resto de la sesión.
    """
    st.markdown("## 🎬 Guía de Demostración Técnica y Pitch para IT SAP")
    st.markdown(
        "Utiliza esta guía interactiva para presentar DataSanitizer ante "
        "equipos de negocio, consultores funcionales y líderes de IT en migraciones de SAP S/4HANA."
    )
    
    # 1. Propuesta de Valor (Business Value)
    with st.expander("💼 1. Propuesta de Valor (Business Value)", expanded=True):
        st.markdown(
            """
            *   **Reducción de Retrasos en Migración (Time-to-Go-Live):** Evita el rebote de cargas de datos maestros en el Migration Cockpit (LTMC/Fiori), reduciendo los tiempos de ciclo en un **80%**.
            *   **Ahorro Cuantitativo de Trabajo Manual:** Automatiza correcciones mecánicas complejas (ej. NIFs, IBANs, provincias) ahorrando un promedio de **0.15 horas (9 minutos)** de manipulación manual en Excel por registro corregido.
            *   **Prevención de Errores Financieros:** Identifica y aísla de manera proactiva cuentas bancarias (IBAN) con dígitos de control incorrectos, evitando fallos de pago valorados en hasta **100 € en costes administrativos y recargos** por cada transacción fallida.
            *   **Cero Caídas en IT:** Aísla registros con errores insalvables (*registros rechazados*) en lugar de abortar el pipeline completo, asegurando que el **99%** de los datos correctos se procesen sin interrupciones.
            """
        )
        
    # 2. Guión de Demo Paso a Paso (6 pasos numerados)
    with st.expander("🎬 2. Guión de Demostración Paso a Paso (Demo Pitch)", expanded=True):
        st.markdown(
            """
            Sigue estos **6 pasos numerados** para realizar una demostración impecable de la herramienta:
            
            1.  **Paso 1: Carga de Archivo (Detección Inteligente):**
                *   *Qué hacer:* Sube el dataset de prueba (ej. `Business Partner` en formato CSV con encoding Cp1252 y separadores de punto y coma).
                *   *Qué destacar:* Explica cómo el motor detecta automáticamente la codificación y los delimitadores, evitando que el usuario lidie con problemas de codificación de caracteres en español.
            2.  **Paso 2: Mapeo y Tipado Semántico:**
                *   *Qué hacer:* Selecciona la plantilla `Business Partner (BP)` en la barra lateral y asocia los campos correspondientes (`TAX_ID`, `IBAN`, `POSTAL_CODE`).
                *   *Qué destacar:* Resalta que la UI auto-sugiere los campos y muestra tooltips informativos con las especificaciones SAP.
            3.  **Paso 3: Ejecución de Simulacro (Dry Run):**
                *   *Qué hacer:* Haz clic en 'Previsualizar Cambios (Dry Run)' antes del procesamiento real.
                *   *Qué destacar:* Muestra la tabla comparativa \"Antes\" y \"Después\" para las primeras filas, ganándote la confianza del cliente al darle total visibilidad de los cambios que el motor planea aplicar.
            4.  **Paso 4: Tolerancia y Aislamiento de Rechazos:**
                *   *Qué hacer:* Haz clic en 'Iniciar Proceso' y navega al panel 'Registros Críticos Rechazados'.
                *   *Qué destacar:* Explica que los registros con errores graves (ej. NIFs matemáticamente incorrectos o obligatorios vacíos) se aíslan en lugar de abortar el proceso.
            5.  **Paso 5: Fusión de Duplicados Difusos:**
                *   *Qué hacer:* Activa la deduplicación difusa en la barra lateral, procesa los datos y aplica la 'Fusión Inteligente' en los acordeones resultantes.
                *   *Qué destacar:* Muestra cómo la distancia Levenshtein unifica entidades duplicadas enriqueciendo la base final.
            6.  **Paso 6: Descarga del Paquete Unificado (ZIP):**
                *   *Qué hacer:* Descarga el archivo ZIP final y muestra su contenido.
                *   *Qué destacar:* Resalta los 4 entregables clave: `datos_limpios.csv` (listo para cargar), `registros_rechazados.csv` (para remediación), `readiness_report.html` (para auditoría ejecutiva) y `auditoria_ejecucion.log` (para cumplimiento técnico).
            """
        )
        
    # 3. Requisitos técnicos SAP
    with st.expander("⚙️ 3. Alineación con Requisitos Técnicos SAP (LTMC)", expanded=True):
        st.markdown(
            """
            | Requisito SAP (Migration Cockpit) | Solución DataSanitizer | Impacto en la Migración |
            | :--- | :--- | :--- |
            | **Longitudes máximas estrictas** | Truncamiento automático e inteligente a los límites de caracteres de SAP (ej: 80 caracteres en nombres). | Previene rechazos fatales en tiempo de importación de la base de datos. |
            | **Validación fiscal nacional** | Comprobación algorítmica matemática (mod-23 para NIF/NIE, sumas pares/impares para CIF). | Garantiza que no se carguen identidades falsas en el maestro de Business Partners. |
            | **Estructura geográfica coherente** | Validación de rango CP (01000 - 52999) y asignación forzada de provincia coherente. | Evita el error número uno de incongruencia de domicilio en el ERP. |
            | **Formato bancario estándar SEPA** | Verificación de estructura IBAN (mod-97) y código de país coordinado con BIC. | Asegura la fluidez de transferencias y cobros automáticos en producción. |
            """
        )

