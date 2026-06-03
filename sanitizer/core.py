import pandas as pd
from datetime import datetime
import time

from sanitizer.rules.text import clean_text
from sanitizer.rules.tax_id import validate_tax_id
from sanitizer.rules.iban import validate_iban
from sanitizer.rules.phone import normalize_phone
from sanitizer.rules.geo import validate_postal_code, get_province_by_cp
from sanitizer.rules.bic import validate_bic
from sanitizer.rules.address import clean_address, split_address
from sanitizer.dedupe import find_duplicates
from sanitizer.sap_templates import SAP_TEMPLATES
from sanitizer.logging_config import setup_logger
from sanitizer.result import SanitizerResult

logger = setup_logger("DataSanitizer")

class SanitizerEngine:
    """
    Main orchestrator for data cleansing, validation, mapping and deduplication.
    Refactored into private phases for testability and structural clarity.
    """
    def __init__(self, column_types=None, mapper=None):
        self.column_types = column_types or {}
        self.mapper = mapper
        self.logs = []

    def _add_log(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append({"timestamp": timestamp, "level": level, "message": message})
        # Use formal logger based on level
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        else:
            logger.info(message)

    def _detect_encoding(self, file_path: str) -> str:
        encodings = ["utf-8-sig", "utf-8", "cp1252", "iso-8859-1"]
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(10240)
        except Exception as e:
            self._add_log("WARNING", f"No se pudo leer archivo para detectar codificación: {e}")
            return "utf-8"

        for enc in encodings:
            try:
                chunk.decode(enc)
                return enc
            except UnicodeDecodeError:
                continue
        return "utf-8"

    def _detect_delimiter(self, file_path: str, encoding: str) -> str:
        common_separators = [";", ",", "\t", "|"]
        try:
            with open(file_path, "r", encoding=encoding, errors="ignore") as f:
                first_line = f.readline()
        except Exception as e:
            self._add_log("WARNING", f"No se pudo leer cabecera para detectar delimitador: {e}")
            return ","

        counts = {sep: first_line.count(sep) for sep in common_separators}
        max_sep = max(counts, key=counts.get)
        if counts[max_sep] == 0:
            return ","
        return max_sep

    def load_data(self, file_path: str, sheet_name: str | None = None) -> pd.DataFrame:
        self._add_log("SYSTEM", f"Cargando archivo: {file_path}")
        try:
            if file_path.endswith(".xlsx") or file_path.endswith(".xls"):
                sheet_to_read = sheet_name if sheet_name is not None else 0
                self._add_log("SYSTEM", f"Leyendo archivo Excel, hoja: {sheet_to_read}")
                df = pd.read_excel(file_path, sheet_name=sheet_to_read, dtype=str)
            else:
                encoding = self._detect_encoding(file_path)
                self._add_log("DATA", f"Codificación detectada: '{encoding}'")
                
                separator = self._detect_delimiter(file_path, encoding)
                self._add_log("DATA", f"Separador detectado: '{separator}'")
                
                df = pd.read_csv(file_path, sep=separator, dtype=str, encoding=encoding)
                
            self._add_log("DATA", f"Ingesta completada: {len(df)} registros y {len(df.columns)} columnas detectadas.")
            return df
        except Exception as e:
            self._add_log("ERROR", f"Error al cargar archivo: {str(e)}")
            raise e

    def _determine_active_template(self, sap_template: str) -> str:
        active_template = sap_template
        if not active_template:
            best_match_template = None
            max_matches = 0
            for t_name, t_info in SAP_TEMPLATES.items():
                matches = sum(1 for col in self.column_types.keys() if col.upper() in t_info["columns"])
                if matches > max_matches:
                    max_matches = matches
                    best_match_template = t_name
            if max_matches >= 2:
                active_template = best_match_template
        return active_template

    def _phase_mapping(self, df: pd.DataFrame, keep_unmapped: bool) -> pd.DataFrame:
        if self.mapper:
            self._add_log("SYSTEM", "Aplicando mapeo de columnas...")
            processed_df = self.mapper.map_dataframe(df, keep_unmapped=keep_unmapped)
            self._add_log("SYSTEM", f"Columnas resultantes tras mapeo: {list(processed_df.columns)}")
            return processed_df
        return df.copy()

    def _phase_cleansing(self, df: pd.DataFrame, result: SanitizerResult):
        for col, col_type in self.column_types.items():
            if col not in df.columns:
                self._add_log("WARNING", f"Columna '{col}' declarada en tipos pero no encontrada en los datos.")
                continue

            self._add_log("SYSTEM", f"Procesando columna '{col}' como tipo '{col_type}'...")
            
            valid_col_name = f"{col}_VALID"
            error_col_name = f"{col}_ERROR"
            
            clean_values = []
            validity = []
            errors = []
            
            addr_tipo_via = []
            addr_nombre_via = []
            addr_numero = []
            addr_piso = []

            for idx, val in enumerate(df[col]):
                if pd.isna(val):
                    val = ""
                    
                cleaned_val = str(val)
                is_valid = True
                err_msg = ""
                t_via, n_via, num, pis = "", "", "", ""
                has_exception = False
                exception_obj = None

                try:
                    if col_type == "text":
                        cleaned_val = clean_text(val)
                    elif col_type == "tax_id":
                        is_valid, cleaned_val, err_msg = validate_tax_id(val)
                    elif col_type == "iban":
                        is_valid, cleaned_val, err_msg = validate_iban(val)
                    elif col_type == "phone":
                        cleaned_val = normalize_phone(val)
                    elif col_type == "postal_code":
                        is_valid, cleaned_val, err_msg = validate_postal_code(val)
                    elif col_type == "province":
                        cleaned_val = clean_text(val)
                    elif col_type == "bic":
                        is_valid, cleaned_val, err_msg = validate_bic(val)
                    elif col_type == "address":
                        cleaned_val = clean_address(val)
                        t_via, n_via, num, pis = split_address(val)
                    else:
                        cleaned_val = clean_text(val, uppercase=False)
                except Exception as e:
                    has_exception = True
                    exception_obj = e

                if not has_exception:
                    clean_values.append(cleaned_val)
                    if col_type == "text":
                        result.kpis["text"] += 1
                    elif col_type == "tax_id":
                        validity.append(is_valid)
                        errors.append(err_msg if not is_valid else "")
                        if is_valid:
                            if str(val).strip().upper() != cleaned_val:
                                result.kpis["tax_id_fixes"] += 1
                        else:
                            result.kpis["tax_id_errors"] += 1
                    elif col_type == "iban":
                        validity.append(is_valid)
                        errors.append(err_msg if not is_valid else "")
                        if is_valid:
                            if str(val).replace(" ", "").upper() != cleaned_val:
                                result.kpis["iban_fixes"] += 1
                        else:
                            result.kpis["iban_errors"] += 1
                    elif col_type == "phone":
                        if str(val).strip() != cleaned_val:
                            result.kpis["phone_fixes"] += 1
                    elif col_type == "postal_code":
                        validity.append(is_valid)
                        errors.append(err_msg if not is_valid else "")
                        if is_valid:
                            if str(val).strip() != cleaned_val:
                                result.kpis["postal_code_fixes"] += 1
                        else:
                            result.kpis["postal_code_errors"] += 1
                    elif col_type == "province":
                        if str(val).strip().upper() != cleaned_val:
                            result.kpis["province_fixes"] += 1
                    elif col_type == "bic":
                        validity.append(is_valid)
                        errors.append(err_msg if not is_valid else "")
                        if is_valid:
                            if str(val).strip().upper() != cleaned_val:
                                result.kpis["bic_fixes"] += 1
                        else:
                            result.kpis["bic_errors"] += 1
                    elif col_type == "address":
                        addr_tipo_via.append(t_via)
                        addr_nombre_via.append(n_via)
                        addr_numero.append(num)
                        addr_piso.append(pis)
                        if str(val).strip().upper() != cleaned_val:
                            result.kpis["address_fixes"] += 1
                else:
                    is_strict = "True" if col_type in ("tax_id", "iban") else "False"
                    self._add_log(
                        "WARNING",
                        f"WARNING|CELL_ERROR|col={col}|row={idx}|value={repr(val)}|strict={is_strict}|error={type(exception_obj).__name__}: {str(exception_obj)}"
                    )
                    
                    clean_values.append(str(val))
                    if col_type in ("tax_id", "iban", "postal_code", "bic"):
                        validity.append(False)
                        errors.append(f"Error inesperado: {str(exception_obj)}")
                        if col_type == "tax_id":
                            result.kpis["tax_id_errors"] += 1
                        elif col_type == "iban":
                            result.kpis["iban_errors"] += 1
                        elif col_type == "postal_code":
                            result.kpis["postal_code_errors"] += 1
                        elif col_type == "bic":
                            result.kpis["bic_errors"] += 1
                    elif col_type == "address":
                        addr_tipo_via.append("")
                        addr_nombre_via.append("")
                        addr_numero.append("")
                        addr_piso.append("")

            df[col] = clean_values
            
            if col_type in ("tax_id", "iban", "postal_code", "bic"):
                df[valid_col_name] = validity
                df[error_col_name] = errors
                
            if col_type == "address":
                df[f"{col}_TIPO_VIA"] = addr_tipo_via
                df[f"{col}_NOMBRE_VIA"] = addr_nombre_via
                df[f"{col}_NUMERO"] = addr_numero
                df[f"{col}_PISO"] = addr_piso

            # SAP POST-VALIDATION
            for sap_template_name, template_info in SAP_TEMPLATES.items():
                col_upper = col.upper()
                if col_upper in template_info["columns"]:
                    col_meta = template_info["columns"][col_upper]
                    max_len = col_meta.get("length")
                    is_required = col_meta.get("required", False)
                    
                    sap_validity_col = f"{col}_SAP_VALID"
                    sap_error_col = f"{col}_SAP_ERROR"
                    
                    df[sap_validity_col] = True
                    df[sap_error_col] = ""
                    
                    sap_val = []
                    sap_err = []
                    
                    for idx in range(len(df)):
                        val_to_check = clean_values[idx]
                        val_str = str(val_to_check).strip() if pd.notna(val_to_check) else ""
                        errs = []
                        
                        if is_required and (val_str == "" or val_str == "-"):
                            errs.append("Campo obligatorio en SAP vacío")
                            
                        if max_len and len(val_str) > max_len:
                            truncated = val_str[:max_len]
                            clean_values[idx] = truncated
                            errs.append(f"Valor truncado de {len(val_str)} a {max_len} caracteres")
                            
                        if errs:
                            sap_val.append(False)
                            sap_err.append(" | ".join(errs))
                        else:
                            sap_val.append(True)
                            sap_err.append("")
                            
                    df[col] = clean_values
                    df[sap_validity_col] = sap_val
                    df[sap_error_col] = sap_err

    def _phase_cross_validation(self, df: pd.DataFrame, result: SanitizerResult):
        # 1. Geographic coherence
        postal_code_cols = [c for c, t in self.column_types.items() if t == "postal_code" and c in df.columns]
        province_cols = [c for c, t in self.column_types.items() if t == "province" and c in df.columns]
        
        if postal_code_cols and province_cols:
            pc_col = postal_code_cols[0]
            prov_col = province_cols[0]
            
            self._add_log("SYSTEM", f"Aplicando coherencia geográfica cruzada entre '{pc_col}' y '{prov_col}'...")
            geo_corrected = 0
            for idx in df.index:
                cp_val = df.loc[idx, pc_col]
                cp_valid = df.loc[idx, f"{pc_col}_VALID"] if f"{pc_col}_VALID" in df.columns else True
                
                if cp_valid and cp_val and cp_val != "-":
                    expected_province = get_province_by_cp(cp_val)
                    if expected_province:
                        current_prov = df.loc[idx, prov_col]
                        if current_prov != expected_province:
                            df.loc[idx, prov_col] = expected_province
                            geo_corrected += 1
            if geo_corrected > 0:
                self._add_log("LEAN ALGORITHM", f"Coherencia geográfica: Se autocorrigieron {geo_corrected} provincias.")

        # 2. Bank coherence
        iban_cols = [c for c, t in self.column_types.items() if t == "iban" and c in df.columns]
        bic_cols = [c for c, t in self.column_types.items() if t == "bic" and c in df.columns]
        
        if iban_cols and bic_cols:
            iban_col = iban_cols[0]
            bic_col = bic_cols[0]
            
            self._add_log("SYSTEM", f"Verificando coincidencia de país entre IBAN '{iban_col}' y BIC '{bic_col}'...")
            bank_discrepancies = 0
            for idx in df.index:
                iban_val = df.loc[idx, iban_col]
                bic_val = df.loc[idx, bic_col]
                
                iban_valid = df.loc[idx, f"{iban_col}_VALID"] if f"{iban_col}_VALID" in df.columns else True
                bic_valid = df.loc[idx, f"{bic_col}_VALID"] if f"{bic_col}_VALID" in df.columns else True
                    
                if iban_valid and bic_valid and iban_val and bic_val and iban_val != "-" and bic_val != "-":
                    iban_country = iban_val[:2].upper()
                    bic_country = bic_val[4:6].upper()
                    
                    if iban_country != bic_country:
                        df.loc[idx, f"{bic_col}_VALID"] = False
                        current_err = df.loc[idx, f"{bic_col}_ERROR"]
                        new_err = f"Discrepancia de país: BIC '{bic_country}' vs IBAN '{iban_country}'"
                        df.loc[idx, f"{bic_col}_ERROR"] = f"{current_err} | {new_err}" if current_err else new_err
                        bank_discrepancies += 1
            if bank_discrepancies > 0:
                self._add_log("WARNING", f"Verificación bancos: {bank_discrepancies} discrepancias IBAN/BIC.")

    def _phase_industrial(self, df: pd.DataFrame, active_template: str, result: SanitizerResult):
        ind_templates = ["Material Master (MM)", "Bill of Materials (BOM)", "Rutas de Operaciones (Routing)", "Centro de Coste (Cost Center)"]
        if active_template in ind_templates:
            self._add_log("SYSTEM", f"Aplicando validaciones industriales para '{active_template}'...")
            from sanitizer.rules.industrial import validate_industrial_rules
            df_updated, ind_logs, ind_kpis = validate_industrial_rules(df, active_template)
            for log in ind_logs:
                self._add_log(log["level"], log["message"])
            result.kpis.update(ind_kpis)
            return df_updated
        return df

    def _phase_deduplication(self, df: pd.DataFrame, dedup_column: str, threshold: float, blocking_method: str, result: SanitizerResult):
        if dedup_column and dedup_column in df.columns:
            self._add_log("SYSTEM", f"Iniciando deduplicación en '{dedup_column}' (Umbral: {threshold}%)...")
            self._add_log("SYSTEM", f"Configuración de optimización: Clave de bloqueo '{blocking_method}'")
            
            tax_id_col = next((c for c, t in self.column_types.items() if t == "tax_id" and c in df.columns), None)
            postal_code_col = next((c for c, t in self.column_types.items() if t == "postal_code" and c in df.columns), None)
            province_col = next((c for c, t in self.column_types.items() if t == "province" and c in df.columns), None)
            
            duplicates = find_duplicates(
                df, 
                text_column=dedup_column, 
                tax_id_column=tax_id_col, 
                postal_code_column=postal_code_col, 
                province_column=province_col,
                threshold=threshold,
                blocking_method=blocking_method
            )
            result.duplicates = duplicates
            self._add_log("LEAN ALGORITHM", f"Deduplicación finalizada. {len(duplicates)} grupos duplicados identificados.")
        elif dedup_column:
            self._add_log("WARNING", f"Imposible deduplicar: Columna '{dedup_column}' no encontrada.")

    def _phase_costing(self, bom_df, routing_df, mm_df, default_rate: float, result: SanitizerResult):
        """
        Fase opcional de cálculo de Coste Estándar simulado.
        Calcula BOM × Precios + Rutas × Tarifas y detecta desviaciones.
        Lógica delegada a sanitizer/costing.py (core.py solo orquesta).
        """
        self._add_log("SYSTEM", "Iniciando cálculo de Coste Estándar (Product Costing)...")
        try:
            from sanitizer.costing import calculate_standard_cost, detect_cost_deviations, estimate_margin_impact
            
            # 1. Cálculo de coste estándar
            cost_df, cost_logs, method_info = calculate_standard_cost(
                bom_df=bom_df,
                routing_df=routing_df,
                mm_df=mm_df,
                default_rate=default_rate
            )
            for log in cost_logs:
                self._add_log(log["level"], log["message"])
            
            if cost_df.empty:
                self._add_log("WARNING", "No se pudo calcular el coste estándar (datos insuficientes).")
                return
            
            # 2. Detección de desviaciones
            cost_df, dev_logs, dev_kpis = detect_cost_deviations(cost_df)
            for log in dev_logs:
                self._add_log(log["level"], log["message"])
            result.kpis.update(dev_kpis)
            
            # 3. Estimación de impacto en margen
            margin_impact = estimate_margin_impact(cost_df)
            result.kpis["total_overvaluation"] = margin_impact.get("total_overvaluation", 0.0)
            result.kpis["total_undervaluation"] = margin_impact.get("total_undervaluation", 0.0)
            
            # 4. Almacenar resultados en el SanitizerResult
            result.costing_results = {
                "cost_df": cost_df,
                "method_info": method_info,
                "margin_impact": margin_impact
            }
            
            self._add_log("LEAN ALGORITHM", 
                f"Coste Estándar calculado para {len(cost_df)} materiales. "
                f"Método de tarifa: {'columna RATE' if method_info == 'column_rate' else f'tarifa por defecto ({default_rate}€/h)'}. "
                f"Desviaciones: {dev_kpis.get('cost_deviations_error', 0)} críticas, "
                f"{dev_kpis.get('cost_deviations_warning', 0)} advertencias.")
                
        except Exception as e:
            self._add_log("ERROR", f"Error en el cálculo de Coste Estándar: {str(e)}")

    def _phase_inventory(self, inventory_df: pd.DataFrame, obsolescence_months: int, result: SanitizerResult):
        """
        Fase opcional de Health Check de Inventarios pre-migración.
        Detecta stocks negativos, obsolescencia, discrepancias de precios y clasificación ABC.
        Lógica delegada a sanitizer/inventory.py (core.py solo orquesta).
        """
        self._add_log("SYSTEM", "Iniciando Health Check de Inventarios...")
        try:
            from sanitizer.inventory import run_inventory_health_check
            
            inv_results = run_inventory_health_check(
                df=inventory_df,
                obsolescence_months=obsolescence_months
            )
            
            # Propagar logs
            for log in inv_results.get("logs", []):
                self._add_log(log["level"], log["message"])
            
            # Propagar KPIs
            inv_kpis = inv_results.get("kpis", {})
            for key in ["negative_stocks", "obsolete_materials", "price_discrepancies",
                        "abc_a_count", "abc_b_count", "abc_c_count", "unit_conversions"]:
                if key in inv_kpis:
                    result.kpis[key] = inv_kpis[key]
            
            # Almacenar resultados completos
            result.inventory_results = inv_results
            
            self._add_log("LEAN ALGORITHM",
                f"Health Check de Inventario finalizado. "
                f"Stocks negativos: {inv_kpis.get('negative_stocks', 0)}, "
                f"Materiales obsoletos: {inv_kpis.get('obsolete_materials', 0)}, "
                f"Discrepancias de precio: {inv_kpis.get('price_discrepancies', 0)}.")
                
        except Exception as e:
            self._add_log("ERROR", f"Error en el Health Check de Inventarios: {str(e)}")

    def _phase_isolate_rejects(self, df: pd.DataFrame, result: SanitizerResult) -> pd.DataFrame:
        """
        Scans for critical errors (e.g., SAP required fields missing, strict type violations).
        Isolates those rows into result.rejected_df and removes them from the main df.
        """
        self._add_log("SYSTEM", "Aislando registros con errores críticos...")
        
        reject_indices = []
        motivos = []
        campos = []
        sugerencias = []
        
        sap_err_cols = [c for c in df.columns if c.endswith("_SAP_ERROR")]
        type_err_cols = [c for c in df.columns if c.endswith("_ERROR") and not c.endswith("_SAP_ERROR")]
        
        for idx in df.index:
            is_rejected = False
            motivo = ""
            campo = ""
            sugerencia = ""
            
            for c in sap_err_cols:
                err_val = df.loc[idx, c]
                if pd.notna(err_val) and err_val != "":
                    if "obligatorio" in err_val.lower():
                        is_rejected = True
                        motivo = err_val
                        campo = c.replace("_SAP_ERROR", "")
                        sugerencia = "Rellenar el campo obligatorio para SAP."
                        break
            
            if not is_rejected:
                for c in type_err_cols:
                    err_val = df.loc[idx, c]
                    if pd.notna(err_val) and err_val != "":
                        base_col = c.replace("_ERROR", "")
                        col_type = self.column_types.get(base_col)
                        if col_type in ["tax_id", "iban"]:
                            is_rejected = True
                            motivo = err_val
                            campo = base_col
                            sugerencia = f"Revisar el formato del {col_type.upper()}."
                            break
                            
            if is_rejected:
                reject_indices.append(idx)
                motivos.append(motivo)
                campos.append(campo)
                sugerencias.append(sugerencia)
                
        if reject_indices:
            rejected_df = df.loc[reject_indices].copy()
            rejected_df["MOTIVO_RECHAZO"] = motivos
            rejected_df["CAMPO_AFECTADO"] = campos
            rejected_df["SUGERENCIA"] = sugerencias
            result.rejected_df = rejected_df
            
            df_clean = df.drop(index=reject_indices)
            self._add_log("WARNING", f"Se aislaron {len(reject_indices)} registros por errores críticos.")
            return df_clean
        else:
            result.rejected_df = pd.DataFrame()
            return df

    def run_dry_run(self, df: pd.DataFrame, sample_size: int = 5, sap_template: str = None) -> pd.DataFrame:
        """
        Ejecuta un simulacro sobre una muestra de filas para visualizar el Antes y el Después.
        """
        if df.empty:
            return pd.DataFrame()
        
        sample_df = df.head(sample_size).copy()
        
        old_logs = self.logs.copy()
        
        result = self.sanitize(
            df=sample_df,
            run_dedup=False,
            sap_template=sap_template,
            keep_unmapped=True
        )
        
        self.logs = old_logs
        
        comparison_rows = []
        res_df = result.df
        
        for idx in range(len(sample_df)):
            orig_row = sample_df.iloc[idx]
            orig_idx = sample_df.index[idx]
            
            if orig_idx in res_df.index:
                clean_row = res_df.loc[orig_idx]
                estado = "Válido"
            else:
                if result.rejected_df is not None and orig_idx in result.rejected_df.index:
                    clean_row = result.rejected_df.loc[orig_idx]
                    estado = f"Rechazado ({clean_row.get('CAMPO_AFECTADO', 'N/A')})"
                else:
                    clean_row = pd.Series(dtype=str)
                    estado = "Desconocido"
            
            row_data = {"Fila": idx + 1, "Estado": estado}
            
            for col in self.column_types.keys():
                orig_val = orig_row.get(col, "")
                clean_val = clean_row.get(col, "")
                if pd.isna(orig_val): orig_val = ""
                if pd.isna(clean_val): clean_val = ""
                
                row_data[f"{col} (Origen)"] = orig_val
                row_data[f"{col} (Limpio)"] = clean_val
                
            comparison_rows.append(row_data)
            
        return pd.DataFrame(comparison_rows)

    def sanitize(self, df, run_dedup=False, dedup_column=None, dedup_threshold=85.0,
                 keep_unmapped=False, sap_template=None,
                 costing_data=None, inventory_df=None,
                 default_rate=35.0, obsolescence_months=24,
                 blocking_method="first_3_chars") -> SanitizerResult:
        """
        Orquestador principal del pipeline de sanitización.
        """
        start_time = time.time()
        self.logs = []
        self._add_log("SYSTEM", "Iniciando proceso de sanitización...")
        
        result = SanitizerResult(df=pd.DataFrame())
        result.active_template = self._determine_active_template(sap_template)
        
        total_rows = len(df)
        result.metrics["processed_rows"] = total_rows
        
        try:
            # 1. Mapping
            processed_df = self._phase_mapping(df, keep_unmapped)
            
            # 2. Cleansing
            self._phase_cleansing(processed_df, result)
            
            # 3. Cross Validation
            self._phase_cross_validation(processed_df, result)
            
            # 4. Industrial Rules
            processed_df = self._phase_industrial(processed_df, result.active_template, result)
            
            # 4.5. Isolate Rejects
            processed_df = self._phase_isolate_rejects(processed_df, result)
            
            # 5. Product Costing (Session 7 — opcional)
            if costing_data is not None:
                self._phase_costing(
                    bom_df=costing_data.get("bom_df"),
                    routing_df=costing_data.get("routing_df"),
                    mm_df=costing_data.get("mm_df"),
                    default_rate=default_rate,
                    result=result
                )
            
            # 6. Inventory Health Check (Session 7 — opcional)
            if inventory_df is not None:
                self._phase_inventory(inventory_df, obsolescence_months, result)
            
            # 7. Deduplication
            if run_dedup and not processed_df.empty:
                self._phase_deduplication(processed_df, dedup_column, dedup_threshold, blocking_method, result)
                
            self._add_log("LEAN ALGORITHM", f"Procesamiento finalizado. {len(processed_df)} registros sanitizados.")
            
        except Exception as e:
            self._add_log("ERROR", f"Error fatal durante la sanitización: {str(e)}")
            processed_df = pd.DataFrame()
            
        # Actualizar métricas finales
        valid_rows = len(processed_df)
        rejected_rows = len(result.rejected_df) if result.rejected_df is not None else 0
        
        result.metrics["valid_rows"] = valid_rows
        result.metrics["rejected_rows"] = rejected_rows
        if total_rows > 0:
            result.metrics["rejection_rate"] = round((rejected_rows / total_rows) * 100, 2)
            
        end_time = time.time()
        result.metrics["process_time_sec"] = round(end_time - start_time, 2)
        
        result.df = processed_df
        result.logs = self.logs
        return result

