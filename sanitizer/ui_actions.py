import os
import tempfile
import io
import zipfile
import pandas as pd
from typing import Tuple, Dict, Any, Optional

from sanitizer.core import SanitizerEngine
from sanitizer.mapping import SchemaMapper
from sanitizer.result import SanitizerResult
from sanitizer.exporter import generate_sap_staging_excel
from sanitizer.sap_templates import SAP_TEMPLATES

def load_raw_dataframe(uploaded_file, sheet_name: Optional[str] = None) -> Tuple[Optional[pd.DataFrame], list]:
    """
    Safely saves the uploaded Streamlit file to a temporary file,
    loads the raw DataFrame using SanitizerEngine, and cleans up securely.
    Returns (raw_df, load_logs).
    """
    if not uploaded_file:
        return None, []
        
    suffix = os.path.splitext(uploaded_file.name)[1]
    
    # Use context manager to auto-delete the file safely
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name
            
        temp_engine = SanitizerEngine()
        raw_df = temp_engine.load_data(temp_file_path, sheet_name=sheet_name)
        return raw_df, temp_engine.logs
        
    except Exception as e:
        raise Exception(f"Error al cargar los datos: {e}")
        
    finally:
        # Secure cleanup outside the with-block since pandas might need the file closed
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


def execute_sanitization_pipeline(
    raw_df: pd.DataFrame,
    mapping_dict: Dict[str, str],
    column_types: Dict[str, str],
    selected_template: str,
    run_dedup: bool,
    dedup_column_mapped: Optional[str],
    dedup_threshold: float,
    keep_unmapped: bool,
    blocking_method: str = "first_3_chars"
) -> SanitizerResult:
    """
    Executes the full pipeline logic and returns a typed SanitizerResult.
    """
    required_fields = list(mapping_dict.values())
    mapper = SchemaMapper(column_mapping=mapping_dict, required_target_fields=required_fields)
    engine = SanitizerEngine(column_types=column_types, mapper=mapper)
    
    sap_tpl = selected_template if selected_template != "[Ninguna - Mapeo Personalizado]" else None
    
    result = engine.sanitize(
        raw_df,
        run_dedup=run_dedup,
        dedup_column=dedup_column_mapped,
        dedup_threshold=dedup_threshold,
        keep_unmapped=keep_unmapped,
        sap_template=sap_tpl,
        blocking_method=blocking_method
    )
    
    return result

def apply_merge_policies(df, duplicates, policies):
    """
    Applies the selected merge policies for each duplicate group to the DataFrame.
    - df: pd.DataFrame (sanitized_df)
    - duplicates: list of duplicate groups
    - policies: dict mapping group_index -> policy string
    
    Returns:
        pd.DataFrame (new deduplicated and merged DataFrame)
    """
    merged_df = df.copy()
    rows_to_drop = set()
    
    for g_idx, group in enumerate(duplicates):
        policy = policies.get(g_idx, "merge")
        if policy == "no_merge":
            continue
            
        primary_indices = group["primary_indices"]
        rep_idx = primary_indices[0]
        
        # Gather all indices in this group
        all_indices = list(primary_indices)
        for match in group["matches"]:
            all_indices.extend(match["indices"])
            
        # Ensure indices exist in DataFrame
        all_indices = [idx for idx in all_indices if idx in merged_df.index]
        if not all_indices:
            continue
            
        if policy == "keep_primary":
            for idx in all_indices:
                if idx != rep_idx:
                    rows_to_drop.add(idx)
                    
        elif policy == "keep_first":
            first_idx = min(all_indices)
            for idx in all_indices:
                if idx != first_idx:
                    rows_to_drop.add(idx)
                    
        elif policy == "keep_last":
            last_idx = max(all_indices)
            for idx in all_indices:
                if idx != last_idx:
                    rows_to_drop.add(idx)
                    


        elif policy == "merge": # Fusión Inteligente
            for col in merged_df.columns:
                if col.endswith(("_VALID", "_ERROR", "_TIPO_VIA", "_NOMBRE_VIA", "_NUMERO", "_PISO")):
                    continue
                    
                non_empty_vals_with_idx = []
                for idx in all_indices:
                    val = merged_df.loc[idx, col]
                    if not pd.isna(val) and str(val).strip() not in ("", "-", "nan", "NaN", "None"):
                        non_empty_vals_with_idx.append((idx, val))
                        
                if not non_empty_vals_with_idx:
                    continue
                    
                selected_idx = None
                
                valid_col = f"{col}_VALID"
                if valid_col in merged_df.columns:
                    for idx, val in non_empty_vals_with_idx:
                        is_valid = merged_df.loc[idx, valid_col]
                        if is_valid is True or str(is_valid).upper() in ("TRUE", "1", "YES"):
                            selected_idx = idx
                            break
                            
                if selected_idx is None:
                    selected_idx = non_empty_vals_with_idx[0][0]
                    
                selected_val = merged_df.loc[selected_idx, col]
                merged_df.at[rep_idx, col] = selected_val
                
                valid_col = f"{col}_VALID"
                if valid_col in merged_df.columns:
                    merged_df.at[rep_idx, valid_col] = merged_df.loc[selected_idx, valid_col]
                error_col = f"{col}_ERROR"
                if error_col in merged_df.columns:
                    merged_df.at[rep_idx, error_col] = merged_df.loc[selected_idx, error_col]
                    
                if col + "_TIPO_VIA" in merged_df.columns:
                    for suffix in ("_TIPO_VIA", "_NOMBRE_VIA", "_NUMERO", "_PISO"):
                        comp_col = col + suffix
                        if comp_col in merged_df.columns:
                            merged_df.at[rep_idx, comp_col] = merged_df.loc[selected_idx, comp_col]
                            
            for idx in all_indices:
                if idx != rep_idx:
                    rows_to_drop.add(idx)
                    
    merged_df = merged_df.drop(index=list(rows_to_drop))
    return merged_df


def run_costing_analysis(
    bom_df: pd.DataFrame,
    routing_df: pd.DataFrame,
    mm_df: pd.DataFrame,
    default_rate: float = 35.0
) -> Tuple[pd.DataFrame, list, str]:
    """
    Executes standard costing simulation and deviation detection.
    Returns (cost_df_with_status, logs, method_info).
    """
    from sanitizer.costing import calculate_standard_cost, detect_cost_deviations
    cost_df, logs, method_info = calculate_standard_cost(
        bom_df, routing_df, mm_df, default_rate
    )
    if not cost_df.empty:
        cost_df, dev_logs, _ = detect_cost_deviations(cost_df)
        logs.extend(dev_logs)
    return cost_df, logs, method_info


def run_inventory_health(
    stock_df: pd.DataFrame,
    obsolescence_months: int = 24
) -> Tuple[pd.DataFrame, list, dict]:
    """
    Executes inventory health check and returns results.
    Returns (enriched_df, logs, kpis).
    """
    from sanitizer.inventory import run_inventory_health_check
    res = run_inventory_health_check(stock_df, obsolescence_months=obsolescence_months)
    return res.get("df"), res.get("logs", []), res.get("kpis", {})


def execute_premigration_pipeline(
    raw_df: pd.DataFrame,
    mapping_dict: Dict[str, str],
    column_types: Dict[str, str],
    selected_template: str,
    run_dedup: bool,
    dedup_column_mapped: Optional[str],
    dedup_threshold: float,
    keep_unmapped: bool,
    costing_data: Optional[Dict[str, pd.DataFrame]] = None,
    inventory_df: Optional[pd.DataFrame] = None,
    default_rate: float = 35.0,
    obsolescence_months: int = 24,
    blocking_method: str = "first_3_chars"
) -> SanitizerResult:
    """
    Executes the complete SAP S/4HANA pre-migration pipeline including costing
    and inventory health checks when additional files are provided.
    """
    required_fields = list(mapping_dict.values())
    mapper = SchemaMapper(column_mapping=mapping_dict, required_target_fields=required_fields)
    engine = SanitizerEngine(column_types=column_types, mapper=mapper)
    
    sap_tpl = selected_template if selected_template != "[Ninguna - Mapeo Personalizado]" else None
    
    result = engine.sanitize(
        raw_df,
        run_dedup=run_dedup,
        dedup_column=dedup_column_mapped,
        dedup_threshold=dedup_threshold,
        keep_unmapped=keep_unmapped,
        sap_template=sap_tpl,
        costing_data=costing_data,
        inventory_df=inventory_df,
        default_rate=default_rate,
        obsolescence_months=obsolescence_months,
        blocking_method=blocking_method
    )
    
    return result


def create_migration_zip(
    main_df: pd.DataFrame,
    template_name: str,
    costing_results: Optional[dict],
    inventory_results: Optional[dict],
    html_report: str,
    logs: list,
    rejected_df: Optional[pd.DataFrame] = None
) -> bytes:
    """
    Creates a ZIP archive in memory containing:
    1. datos_limpios.csv (Clean main data without technical columns)
    2. registros_rechazados.csv (Rejected records or empty with headers)
    3. readiness_report.html (Data Quality Readiness Report)
    4. auditoria_ejecucion.log (Detailed motor execution log for IT compliance)
    Legacy/optional files:
    - staging_sap_load.xlsx / staging_load.xlsx
    - full_audit_sanitized.xlsx
    - costing_simulation.csv
    - inventory_health.csv
    """
    zip_buffer = io.BytesIO()
    
    # Check if legacy SAP/Costing/Inventory files should be included
    has_costing = costing_results is not None and "cost_df" in costing_results and not costing_results["cost_df"].empty
    has_inventory = inventory_results is not None and "df" in inventory_results and not inventory_results["df"].empty
    include_legacy = has_costing or has_inventory
    
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # A. MANDATORY FILES FOR SESSION 11
        
        # 1. datos_limpios.csv
        clean_cols = [c for c in main_df.columns if not (c.endswith(("_VALID", "_ERROR")) or c in ("_CLEAN_LOG", "_CLEANSED"))]
        clean_df = main_df[clean_cols].copy()
        clean_csv_bytes = clean_df.to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")
        zip_file.writestr("datos_limpios.csv", clean_csv_bytes)
        
        # 2. registros_rechazados.csv
        if rejected_df is None:
            rejected_export_df = pd.DataFrame(columns=clean_cols)
        elif rejected_df.empty:
            rejected_export_df = rejected_df.copy()
        else:
            rejected_export_df = rejected_df.copy()
            
        rejected_csv_bytes = rejected_export_df.to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")
        zip_file.writestr("registros_rechazados.csv", rejected_csv_bytes)
        
        # 3. readiness_report.html
        zip_file.writestr("readiness_report.html", html_report)
        
        # 4. auditoria_ejecucion.log
        import datetime
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metadata_header = [
            "======================================================================",
            "        DATASANITIZER ERP MIGRATION ENGINE - AUDIT EXECUTION LOG",
            "======================================================================",
            f"Fecha de Generacion: {now_str}",
            f"Plantilla de Carga: {template_name if template_name else '[Ninguna - Personalizada]'}",
            f"Registros Procesados: {len(main_df)}",
            f"Columnas Totales: {len(main_df.columns)}",
            "======================================================================",
            ""
        ]
        
        audit_log_lines = []
        for log in logs:
            audit_log_lines.append(f"[{log.get('level', 'INFO')}] {log.get('timestamp', '')} - {log.get('message', '')}")
            
        if rejected_df is None or rejected_df.empty:
            audit_log_lines.append("REGISTROS_RECHAZADOS: 0 — archivo exportado con cabeceras únicamente")
            
        audit_log_text = "\n".join(metadata_header + audit_log_lines)
        zip_file.writestr("auditoria_ejecucion.log", audit_log_text)
        
        # B. OPTIONAL/LEGACY FILES FROM SESSION 8
        if include_legacy:
            # 1. staging_sap_load.xlsx (Clean staging sheet without technical columns)
            excel_sap_bytes = generate_sap_staging_excel(main_df, template_name)
            file_label = "staging_sap_load.xlsx" if template_name and template_name in SAP_TEMPLATES else "staging_load.xlsx"
            zip_file.writestr(file_label, excel_sap_bytes)
            
            # 2. full_audit_sanitized.xlsx (Complete sheet with all columns & technical logs)
            audit_excel_buffer = io.BytesIO()
            with pd.ExcelWriter(audit_excel_buffer, engine='openpyxl') as writer:
                main_df.to_excel(writer, sheet_name="Full Audit", index=False)
            zip_file.writestr("full_audit_sanitized.xlsx", audit_excel_buffer.getvalue())
            
            # 3. costing_simulation.csv (Optional, if product costing results exist)
            if has_costing:
                cost_df = costing_results["cost_df"]
                cost_csv_bytes = cost_df.to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")
                zip_file.writestr("costing_simulation.csv", cost_csv_bytes)
                
            # 4. inventory_health.csv (Optional, if stock health results exist)
            if has_inventory:
                inv_df = inventory_results["df"]
                inv_csv_bytes = inv_df.to_csv(sep=";", index=False, encoding="utf-8-sig").encode("utf-8-sig")
                zip_file.writestr("inventory_health.csv", inv_csv_bytes)
                
    return zip_buffer.getvalue()

