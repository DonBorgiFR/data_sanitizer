import streamlit as st
import pandas as pd
from sanitizer.diagnostics import DataDiagnostics
from sanitizer.reports import generate_readiness_report

# New UI components and actions
from sanitizer.ui_components import (
    render_diagnostics, 
    render_mapping_config, 
    render_kpis,
    render_costing_panel,
    render_inventory_panel,
    render_premigration_summary,
    render_help_center,
    render_dry_run_panel,
    render_execution_metrics,
    render_rejects_panel,
    render_demo_pitch_tab,
    render_creator_tab
)
from sanitizer.ui_actions import (
    load_raw_dataframe, 
    execute_sanitization_pipeline, 
    execute_premigration_pipeline,
    apply_merge_policies,
    create_migration_zip
)

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="DataSanitizer ERP Engine",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        color: #1e3c72;
    }
    
    .metric-label {
        font-size: 14px;
        color: #6c757d;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2) !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# App Header
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 25px; border-radius: 12px; margin-bottom: 25px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <h1 style="margin: 0; font-size: 34px; font-weight: 700; letter-spacing: -0.5px;">DataSanitizer ERP Migration Engine</h1>
        <p style="margin: 8px 0 0 0; font-size: 16px; opacity: 0.9; font-weight: 300;">Plataforma interactiva para limpieza, validación y normalización de datos maestros (SAP, Sage, Odoo)</p>
    </div>
    """,
    unsafe_allow_html=True
)

def main():
    # Initialize session state keys
    if "processing_done" not in st.session_state:
        st.session_state.processing_done = False
    if "merge_done" not in st.session_state:
        st.session_state.merge_done = False
    if "sanitizer_result" not in st.session_state:
        st.session_state.sanitizer_result = None
    if "merged_df" not in st.session_state:
        st.session_state.merged_df = None
    if "merge_policies" not in st.session_state:
        st.session_state.merge_policies = {}

    st.sidebar.markdown("### 📁 Cargar Datos")
    uploaded_file = st.sidebar.file_uploader(
        "Sube tu archivo CSV o Excel viejo", 
        type=["csv", "xlsx", "xls"],
        help="El motor autodetecta delimitadores y codificaciones en CSV."
    )
    
    sheet_name = None
    if uploaded_file is not None:
        if "last_uploaded_file" not in st.session_state or st.session_state.last_uploaded_file != uploaded_file.name:
            st.session_state.last_uploaded_file = uploaded_file.name
            st.session_state.processing_done = False
            st.session_state.merge_done = False
            st.session_state.sanitizer_result = None
            st.session_state.merged_df = None
            st.session_state.merge_policies = {}

        if uploaded_file.name.endswith((".xlsx", ".xls")):
            try:
                xl = pd.ExcelFile(uploaded_file)
                sheets = xl.sheet_names
                if len(sheets) > 1:
                    sheet_name = st.sidebar.selectbox("Selecciona la pestaña de Excel", sheets)
                else:
                    sheet_name = sheets[0]
            except Exception as e:
                st.sidebar.error(f"Error al leer hojas de Excel: {e}")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🏭 Modo Pre-Migración SAP")
    sap_mode = st.sidebar.checkbox(
        "Activar Pre-Migración SAP Completa", value=False,
        help="Permite validaciones industriales avanzadas, análisis de costes estándar y salud de inventario."
    )
    
    default_rate = 35.0
    obsolescence_months = 24
    
    bom_file = None
    routing_file = None
    mm_file = None
    stock_file = None
    
    costing_data = None
    inventory_df = None
    
    if sap_mode:
        default_rate = st.sidebar.number_input(
            "Tarifa centro trabajo por defecto (€/h)", 
            min_value=0.0, value=35.0, step=1.0,
            help="Tarifa aplicada si las hojas de ruta no contienen la columna RATE."
        )
        obsolescence_months = st.sidebar.slider(
            "Meses para obsolescencia de stock", 
            min_value=1, max_value=60, value=24,
            help="Umbral de meses sin movimientos en inventario para considerar un material obsoleto."
        )
        
        st.sidebar.markdown("#### 📂 Archivos adicionales SAP")
        
        bom_file = st.sidebar.file_uploader(
            "Lista de Materiales (BOM)", 
            type=["csv", "xlsx", "xls"],
            key="bom_file_upload"
        )
        routing_file = st.sidebar.file_uploader(
            "Hojas de Ruta (Routing)", 
            type=["csv", "xlsx", "xls"],
            key="routing_file_upload"
        )
        
        # Ofrecemos cargar MM y MB52 de forma condicional para completar los datos
        # Si la plantilla no es Material Master, permitimos cargar un maestro complementario
        # Si la plantilla no es Inventario, permitimos cargar Stock complementario
        
        # Se asume que render_mapping_config se ejecuta más abajo para obtener selected_template.
        # Por lo tanto, declaramos cargadores adicionales de forma simple
        mm_file = st.sidebar.file_uploader(
            "Maestro de Materiales (MM) [Opcional]",
            type=["csv", "xlsx", "xls"],
            key="mm_file_upload",
            help="Necesario si el archivo principal de entrada no es el Maestro de Materiales."
        )
        stock_file = st.sidebar.file_uploader(
            "Inventario / Stock (MB52) [Opcional]",
            type=["csv", "xlsx", "xls"],
            key="stock_file_upload",
            help="Necesario si el archivo principal de entrada no es el Inventario."
        )
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Opciones del Motor")
    keep_unmapped = st.sidebar.checkbox(
        "Conservar columnas no mapeadas", value=True
    )
    
    run_deduplication = st.sidebar.checkbox(
        "Buscar duplicados difusos", value=False
    )
    
    dedup_threshold = 85.0
    blocking_method = "first_3_chars"
    if run_deduplication:
        dedup_threshold = st.sidebar.slider("Umbral de similitud (Dedupe)", 50.0, 100.0, 85.0, 1.0)
        blocking_options = {
            "Primeros 3 caracteres del nombre (Recomendado)": "first_3_chars",
            "Primer carácter del nombre": "first_char",
            "Código Postal (2 dígitos) [Avanzado]": "postal_code_2",
            "Provincia [Avanzado]": "province",
            "Sin bloqueo (Búsqueda exhaustiva, lento)": "none"
        }
        selected_blocking_label = st.sidebar.selectbox(
            "Clave de bloqueo (Optimización)",
            options=list(blocking_options.keys()),
            index=0,
            help="El bloqueo reduce comparaciones al agrupar registros por claves antes de aplicar Levenshtein."
        )
        blocking_method = blocking_options[selected_blocking_label]
        
        # Explicación simple del método seleccionado
        if blocking_method == "first_3_chars":
            st.sidebar.caption("💡 **Recomendado**: Agrupa por las 3 primeras letras del nombre. Rápido y seguro, evita perder duplicados por CP erróneo.")
        elif blocking_method == "first_char":
            st.sidebar.caption("💡 **Muy rápido**: Agrupa únicamente por el primer carácter. Excelente para bases de datos masivas.")
        elif blocking_method == "postal_code_2":
            st.sidebar.caption("⚠️ **Avanzado**: Agrupa por los 2 primeros dígitos del CP. Rápido, pero si hay CPs incorrectos se perderán duplicados.")
        elif blocking_method == "province":
            st.sidebar.caption("⚠️ **Avanzado**: Agrupa por provincia exacta. Requiere que la provincia esté bien cargada en el origen.")
        elif blocking_method == "none":
            st.sidebar.caption("⚠️ **Lento (O(N²))**: Compara todos los registros contra todos. Muy preciso pero prohibitivo para conjuntos de datos grandes.")
    tab_run, tab_help, tab_demo, tab_creator = st.tabs(["🚀 Ejecución & Limpieza", "📖 Centro de Ayuda & FAQ", "🎬 Guía de Demo IT SAP", "👤 Sobre el Creador"])

    with tab_help:
        render_help_center()
        
    with tab_demo:
        render_demo_pitch_tab()
        
    with tab_creator:
        render_creator_tab()

    with tab_run:
        
        # Intro layout
        if uploaded_file is None:
            st.info("👈 Sube un archivo CSV o Excel en la barra lateral para comenzar.")
            st.markdown(
                """
                ### ¿Qué hace esta herramienta?
                * **Ingesta Inteligente**: No te preocupes por el formato del archivo o caracteres especiales raros; el motor lo lee de forma transparente.
                * **Diagnóstico de Salud Instantáneo**: Descubre cuántos campos vacíos hay y qué tipo de información tiene cada columna antes de limpiarla.
                * **Validación Matemática**: Verifica dígitos de control en identificadores fiscales de España (NIF/NIE/CIF) e IBANs SEPA.
                * **Autocorrección Geográfica**: Si escribes un Código Postal válido, el motor corregirá automáticamente la provincia si no coincide.
                * **Separación de Direcciones**: Separa tus calles enteras en columnas compatibles con ERP: Tipo de vía, Nombre, Número y Piso.
                * **Detección de Duplicados**: Encuentra registros repetidos o muy parecidos mediante comparación difusa.
                """
            )
            return

        # Process Uploaded File safely via ui_actions
        if not st.session_state.processing_done:
            with st.spinner("Leyendo y analizando archivo de entrada..."):
                try:
                    raw_df, load_logs = load_raw_dataframe(uploaded_file, sheet_name)
                    st.session_state.raw_df = raw_df
                    st.session_state.load_logs = load_logs
                except Exception as e:
                    st.error(str(e))
                    return

        raw_df = st.session_state.raw_df
        for log in st.session_state.load_logs:
            if log["level"] == "DATA":
                st.sidebar.success(log["message"])
            
        # Diagnostics UI
        diagnose = DataDiagnostics(raw_df)
        health = diagnose.run_health_check()
        render_diagnostics(health)
    
        st.markdown("---")
    
        # Mapping UI
        mapping_dict, column_types, selected_template = render_mapping_config(raw_df)
    
        dedup_column_mapped = None
        if run_deduplication:
            mapped_targets = list(mapping_dict.values())
            if "NAME" in mapped_targets:
                orig_name_col = [orig for orig, target in mapping_dict.items() if target == "NAME"][0]
                st.sidebar.markdown(f"Deduplicación configurada sobre: **{orig_name_col}** (como NAME)")
                dedup_column_mapped = "NAME"
            else:
                st.sidebar.warning("⚠️ Debes mapear la columna 'Nombre / Razón Social' para poder usar la deduplicación.")
                run_deduplication = False

        st.markdown("---")
    
        # Cargar datos complementarios de SAP si aplica
        if sap_mode:
            bom_df = None
            routing_df = None
            comp_mm_df = None
            comp_stock_df = None
        
            with st.spinner("Cargando archivos complementarios de SAP..."):
                if bom_file:
                    bom_df, _ = load_raw_dataframe(bom_file)
                if routing_file:
                    routing_df, _ = load_raw_dataframe(routing_file)
                
                # Determinar MM
                if selected_template == "Material Master (MM)":
                    mm_df = raw_df
                else:
                    if mm_file:
                        comp_mm_df, _ = load_raw_dataframe(mm_file)
                    mm_df = comp_mm_df
                
                # Determinar Stock
                if selected_template == "Inventario / Stock (MB52)":
                    inventory_df = raw_df
                else:
                    if stock_file:
                        comp_stock_df, _ = load_raw_dataframe(stock_file)
                    inventory_df = comp_stock_df
                
                if bom_df is not None or routing_df is not None or mm_df is not None:
                    costing_data = {
                        "bom_df": bom_df,
                        "routing_df": routing_df,
                        "mm_df": mm_df
                    }

        st.markdown("---")
        st.markdown("### 🧪 Simulacro de Ejecución (Dry Run)")
        col_dr1, col_dr2 = st.columns([1, 3])
        with col_dr1:
            dr_sample_size = st.selectbox("Muestra de filas", options=[5, 10, 50], index=0)
            trigger_dry_run = st.button("🔍 Previsualizar Cambios (Dry Run)")
            
        if trigger_dry_run:
            if not mapping_dict:
                st.warning("⚠️ Debes mapear al menos una columna antes de simular.")
            else:
                from sanitizer.core import SanitizerEngine
                from sanitizer.mapping import SchemaMapper
                required_fields = list(mapping_dict.values())
                engine_dr = SanitizerEngine(column_types=column_types, mapper=SchemaMapper(column_mapping=mapping_dict, required_target_fields=required_fields))
                with st.spinner("Generando simulacro..."):
                    dr_df = engine_dr.run_dry_run(raw_df, sample_size=dr_sample_size, sap_template=selected_template)
                render_dry_run_panel(dr_df)
        
        st.markdown("---")

        # Execution Button
        if sap_mode:
            trigger_process = st.button("🏭 Ejecutar Pre-Migración SAP Completa")
        else:
            trigger_process = st.button("🚀 Iniciar Proceso de Sanitización")
    
        if trigger_process:
            if not mapping_dict:
                st.warning("⚠️ Debes mapear al menos una columna antes de procesar.")
                return
            
            if sap_mode:
                progress_bar = st.progress(0)
                status_text = st.empty()
            
                import time
                status_text.text("1/5 - Leyendo y validando archivos SAP...")
                progress_bar.progress(15)
                time.sleep(0.3)
            
                status_text.text("2/5 - Mapeando columnas y saneando datos semánticos...")
                progress_bar.progress(40)
                time.sleep(0.3)
            
                status_text.text("3/5 - Aplicando validaciones industriales SAP...")
                progress_bar.progress(60)
                time.sleep(0.3)
            
                status_text.text("4/5 - Calculando costes y analizando inventario...")
                progress_bar.progress(80)
                time.sleep(0.3)
            
                status_text.text("5/5 - Procesando deduplicación difusa y consolidando...")
                progress_bar.progress(100)
                time.sleep(0.2)
            
                status_text.empty()
                progress_bar.empty()
            
            with st.spinner("Procesando pipeline..."):
                try:
                    if sap_mode:
                        result = execute_premigration_pipeline(
                            raw_df=raw_df,
                            mapping_dict=mapping_dict,
                            column_types=column_types,
                            selected_template=selected_template,
                            run_dedup=run_deduplication,
                            dedup_column_mapped=dedup_column_mapped,
                            dedup_threshold=dedup_threshold,
                            keep_unmapped=keep_unmapped,
                            costing_data=costing_data,
                            inventory_df=inventory_df,
                            default_rate=default_rate,
                            obsolescence_months=obsolescence_months,
                            blocking_method=blocking_method
                        )
                    else:
                        result = execute_sanitization_pipeline(
                            raw_df=raw_df,
                            mapping_dict=mapping_dict,
                            column_types=column_types,
                            selected_template=selected_template,
                            run_dedup=run_deduplication,
                            dedup_column_mapped=dedup_column_mapped,
                            dedup_threshold=dedup_threshold,
                            keep_unmapped=keep_unmapped,
                            blocking_method=blocking_method
                        )
                
                    st.session_state.sanitizer_result = result
                    st.session_state.processing_done = True
                    st.session_state.merge_done = False
                    st.session_state.merge_policies = {}
                    st.session_state.merged_df = None
                
                except Exception as ex:
                    import logging
                    logger = logging.getLogger("DataSanitizer")
                    logger.exception("Error general durante la sanitización en app.py")
                    st.error(f"Ocurrió un error general de procesamiento. Por favor, revisa el archivo de logs 'sanitizer_engine.log'.")
                    return

        if st.session_state.processing_done:
            result = st.session_state.sanitizer_result
            st.markdown("### ⚙️ Resultados del Procesamiento")
        
            with st.expander("📁 Ver Consola de logs de procesamiento en tiempo real", expanded=False):
                log_entries = []
                for log in result.logs:
                    log_entries.append(f"[{log['level']}] {log['timestamp']} - {log['message']}")
                st.code("\n".join(log_entries))
            
            render_execution_metrics(result.metrics)
            st.markdown("---")
            
            # Renderizar resumen ejecutivo de pre-migración si sap_mode estaba activo
            if sap_mode:
                st.markdown("---")
                render_premigration_summary(result)
            
                # Panel de Costes
                if result.costing_results is not None:
                    st.markdown("---")
                    render_costing_panel(result.costing_results)
                
                # Panel de Inventarios
                if result.inventory_results is not None:
                    st.markdown("---")
                    render_inventory_panel(result.inventory_results)
                
                st.markdown("---")
            else:
                # KPIs rendering via component
                render_kpis(result.kpis)
            
            st.markdown("---")
            render_rejects_panel(result.rejected_df)
            
            st.markdown("<br>", unsafe_allow_html=True)
        
            # Duplicates handling
            duplicates = result.duplicates
            if run_deduplication and duplicates:
                st.markdown("---")
                st.markdown("### 🤝 Panel de Fusión de Duplicados Difusos")
                st.write("Se han detectado posibles registros duplicados. Revisa cada grupo y selecciona cómo deseas fusionarlos.")
            
                if not st.session_state.merge_done:
                    for g_idx, group in enumerate(duplicates):
                        primary_val = group["primary_value"]
                        primary_indices = group["primary_indices"]
                    
                        all_indices = list(primary_indices)
                        for match in group["matches"]:
                            all_indices.extend(match["indices"])
                    
                        comp_df = result.df.loc[all_indices].copy()
                    
                        cols_to_compare = []
                        main_cols = ["NAME", "TAX_ID", "IBAN", "TELEPHONE", "POSTAL_CODE", "PROVINCIA", "ADDRESS"]
                        for c in main_cols:
                            if c in comp_df.columns:
                                cols_to_compare.append(c)
                        for c in comp_df.columns:
                            if c not in cols_to_compare and not c.endswith(("_VALID", "_ERROR", "_TIPO_VIA", "_NOMBRE_VIA", "_NUMERO", "_PISO")):
                                cols_to_compare.append(c)
                            
                        group_label = f"Grupo {g_idx + 1}: {primary_val} ({len(all_indices)} registros detectados)"
                        with st.expander(group_label, expanded=True):
                            col_left, col_right = st.columns([2, 5])
                            with col_left:
                                policy_options = {
                                   "Combinar campos (Fusión Inteligente)": "merge",
                                    "Conservar registro principal": "keep_primary",
                                    "Conservar primer registro (más antiguo)": "keep_first",
                                    "Conservar último registro (más reciente)": "keep_last",
                                    "No fusionar (Mantener duplicados)": "no_merge"
                                }
                                default_policy = st.session_state.merge_policies.get(g_idx, "merge")
                                default_opt_idx = list(policy_options.values()).index(default_policy)
                            
                                selected_option = st.selectbox(
                                    "Política de fusión",
                                    options=list(policy_options.keys()),
                                    index=default_opt_idx,
                                    key=f"policy_select_{g_idx}"
                                )
                                st.session_state.merge_policies[g_idx] = policy_options[selected_option]
                            
                                if selected_option == "Combinar campos (Fusión Inteligente)":
                                    st.caption("💡 Combina los mejores datos.")
                                elif selected_option == "Conservar registro principal":
                                    st.caption("💡 Conserva solo la fila principal.")
                                elif selected_option == "No fusionar (Mantener duplicados)":
                                    st.caption("⚠️ Conservará todos los registros intactos.")
                                
                            with col_right:
                                st.dataframe(comp_df[cols_to_compare], use_container_width=True)
                            
                    if st.button("💾 Confirmar y Aplicar Fusión de Duplicados"):
                        with st.spinner("Aplicando fusión y re-estructurando datos..."):
                            merged_df = apply_merge_policies(
                                result.df, 
                                duplicates, 
                                st.session_state.merge_policies
                            )
                            st.session_state.merged_df = merged_df
                            st.session_state.merge_done = True
                            st.success("✅ Fusión aplicada con éxito.")
                            st.rerun()
                else:
                    st.success("✅ Se han fusionado los registros duplicados.")
                
                    if st.button("↩️ Deshacer Fusión (Modificar Políticas)"):
                        st.session_state.merge_done = False
                        st.session_state.merged_df = None
                        st.rerun()
            elif run_deduplication:
                st.info("ℹ️ No se detectaron posibles duplicados difusos con el umbral especificado.")
            
            st.markdown("---")
            st.markdown("#### 📥 Visualización y Descarga")
        
            df_to_download = st.session_state.merged_df if st.session_state.merge_done else result.df
        
            st.dataframe(df_to_download.head(100), use_container_width=True)
            csv_data = df_to_download.to_csv(sep=";", index=False, encoding="utf-8-sig")
        
            kpis_to_pass = result.kpis.copy()
            if st.session_state.merge_done and st.session_state.merged_df is not None:
                kpis_to_pass["duplicates_merged"] = len(result.df) - len(st.session_state.merged_df)
            else:
                kpis_to_pass["duplicates_merged"] = 0

            html_report_content = generate_readiness_report(
                df_to_download, 
                column_types, 
                duplicates,
                costing_results=result.costing_results if sap_mode else None,
                inventory_results=result.inventory_results if sap_mode else None,
                kpis=kpis_to_pass,
                rejected_df=result.rejected_df
            )
        
            # Generar ZIP consolidado
            zip_data = create_migration_zip(
                main_df=df_to_download,
                template_name=selected_template,
                costing_results=result.costing_results if sap_mode else None,
                inventory_results=result.inventory_results if sap_mode else None,
                html_report=html_report_content,
                logs=result.logs,
                rejected_df=result.rejected_df
            )
        
            import re
            tpl_clean = selected_template.replace(" ", "_").lower() if selected_template else "custom_mapping"
            tpl_clean = re.sub(r'[^a-z0-9_]', '', tpl_clean)
            zip_filename = f"paquete_migracion_{tpl_clean}.zip"
        
            st.markdown("### 📦 Paquete de Descarga Consolidado (ZIP)")
            st.info("Recomendado: Descarga un único archivo ZIP que contiene la pre-plantilla de carga para staging SAP (limpia de columnas de control), el archivo de auditoría completo con trazabilidad, el reporte de calidad interactivo (HTML), la traza de ejecución de IT y las simulaciones de costes e inventarios.")
        
            st.download_button(
                label="🎁 Descargar Paquete de Migración Completo (.ZIP)",
                data=zip_data,
                file_name=zip_filename,
                mime="application/zip",
                use_container_width=True
            )
        
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 📄 Descargas Individuales Adicionales")
        
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                st.download_button(
                    label="💾 Descargar CSV Sanitizado (Con Columnas de Control)",
                    data=csv_data,
                    file_name=f"sanitized_{uploaded_file.name.split('.')[0]}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col_dl2:
                st.download_button(
                    label="📊 Descargar SAP S/4HANA Readiness Report (HTML)",
                    data=html_report_content,
                    file_name=f"readiness_report_{uploaded_file.name.split('.')[0]}.html",
                    mime="text/html",
                    use_container_width=True
                )
            
            # Descargas individuales para Costing e Inventario
            if sap_mode:
                dl_col1, dl_col2 = st.columns(2)
                if result.costing_results is not None and not result.costing_results["cost_df"].empty:
                    cost_csv = result.costing_results["cost_df"].to_csv(sep=";", index=False, encoding="utf-8-sig")
                    with dl_col1:
                        st.download_button(
                            label="💰 Descargar Simulación de Costes (CSV)",
                            data=cost_csv,
                            file_name=f"costing_simulation_{uploaded_file.name.split('.')[0]}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                if result.inventory_results is not None and result.inventory_results.get("df") is not None:
                    inv_csv = result.inventory_results["df"].to_csv(sep=";", index=False, encoding="utf-8-sig")
                    with dl_col2:
                        st.download_button(
                            label="📦 Descargar Inventario Enriquecido (CSV)",
                            data=inv_csv,
                            file_name=f"inventory_health_{uploaded_file.name.split('.')[0]}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

if __name__ == "__main__":
    main()
