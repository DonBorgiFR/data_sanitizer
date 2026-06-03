# -*- coding: utf-8 -*-
"""
Validation rules and heuristics for SAP S/4HANA Industrial Master Data (MM/PP/CO).
"""
import pandas as pd
import re

# Standard SAP UOM codes
VALID_BASE_UOMS = {"PC", "KG", "G", "L", "M", "M2", "M3", "HR", "MIN", "ST", "UN", "EA", "MTR", "DM", "CM", "MM"}
VALID_WEIGHT_UOMS = {"KG", "G", "TON", "LB", "OZ", "LBR", "GRM"}

def clean_numeric(val):
    """
    Cleans a numeric string (removes whitespace, replaces comma with dot, etc.)
    and returns a float, or None if invalid.
    """
    if pd.isna(val):
        return None
    val_str = str(val).strip().replace(" ", "").replace(",", ".")
    try:
        return float(val_str)
    except ValueError:
        return None

def validate_industrial_rules(df: pd.DataFrame, template_name: str):
    """
    Applies industrial-specific business logic and heuristics based on the template.
    Modifies the DataFrame by adding:
    - IND_VALID: bool, indicating if all critical checks passed
    - IND_ERROR: str, list of error/warning messages separated by |
    
    Returns:
        df: pd.DataFrame
        logs: list of log messages (dict with level, message)
        kpis: dict of counters
    """
    logs = []
    kpis = {
        "industrial_errors": 0,
        "industrial_warnings": 0,
        "complex_boms": 0,
        "zero_setup_routes": 0
    }
    
    # Initialize validation columns
    df["IND_VALID"] = True
    df["IND_ERROR"] = ""
    
    if template_name == "Material Master (MM)":
        for idx in df.index:
            errors = []
            warnings = []
            
            # 1. Material Type Check
            mat_type = str(df.loc[idx, "MAT_TYPE"]).strip().upper() if "MAT_TYPE" in df.columns else ""
            if mat_type not in ["ROH", "HALB", "FERT"]:
                warnings.append(f"Tipo de material '{mat_type}' no estándar (ROH, HALB, FERT esperado)")
                kpis["industrial_warnings"] += 1
                
            # 2. UOM Check
            base_uom = str(df.loc[idx, "BASE_UOM"]).strip().upper() if "BASE_UOM" in df.columns else ""
            if base_uom and base_uom not in VALID_BASE_UOMS:
                warnings.append(f"Unidad de medida base '{base_uom}' no estándar en SAP")
                kpis["industrial_warnings"] += 1
                
            weight_uom = str(df.loc[idx, "UNIT_OF_WEIGHT"]).strip().upper() if "UNIT_OF_WEIGHT" in df.columns else ""
            if weight_uom and weight_uom not in VALID_WEIGHT_UOMS:
                warnings.append(f"Unidad de peso '{weight_uom}' no estándar en SAP")
                kpis["industrial_warnings"] += 1
                
            # 3. Weight consistency
            net_weight_val = clean_numeric(df.loc[idx, "NET_WEIGHT"]) if "NET_WEIGHT" in df.columns else None
            if net_weight_val is not None:
                if net_weight_val < 0:
                    errors.append(f"Peso neto negativo: {net_weight_val}")
                    kpis["industrial_errors"] += 1
                elif net_weight_val > 0 and not weight_uom:
                    errors.append("Peso neto indicado pero falta unidad de peso (UNIT_OF_WEIGHT)")
                    kpis["industrial_errors"] += 1
            
            # 4. Price Control Cross-validation
            price_ctrl = str(df.loc[idx, "PRICE_CTRL"]).strip().upper() if "PRICE_CTRL" in df.columns else ""
            price_val = clean_numeric(df.loc[idx, "PRICE"]) if "PRICE" in df.columns else None
            
            if price_ctrl not in ["S", "V"]:
                errors.append(f"Control de precio '{price_ctrl}' incorrecto (Debe ser S o V)")
                kpis["industrial_errors"] += 1
                
            if price_val is not None:
                if price_val < 0:
                    errors.append(f"Precio negativo no permitido: {price_val}")
                    kpis["industrial_errors"] += 1
                elif price_val == 0:
                    warnings.append("Precio del material es 0.0 (Posible falta de valoración)")
                    kpis["industrial_warnings"] += 1
            else:
                errors.append("Precio del material no es un valor numérico válido")
                kpis["industrial_errors"] += 1
                
            # Heuristic for ROH
            if mat_type == "ROH":
                if price_ctrl == "S" and (price_val is not None and price_val > 100000):
                    # Warning for unusually high ROH price with standard costing
                    warnings.append(f"Precio estándar de ROH inusualmente alto: {price_val}")
                    kpis["industrial_warnings"] += 1
                    
            if errors or warnings:
                all_msgs = []
                if errors:
                    all_msgs.extend([f"ERROR: {e}" for e in errors])
                if warnings:
                    all_msgs.extend([f"WARN: {w}" for w in warnings])
                
                df.at[idx, "IND_ERROR"] = " | ".join(all_msgs)
                if errors:
                    df.at[idx, "IND_VALID"] = False
                    
        num_errs = (df["IND_VALID"] == False).sum()
        if num_errs > 0:
            logs.append({"level": "WARNING", "message": f"Material Master: Se detectaron {num_errs} registros con errores de validación industrial."})
            
    elif template_name == "Bill of Materials (BOM)":
        # First group by parent to check complexity
        parent_counts = {}
        if "MATERIAL_PARENT" in df.columns:
            parent_counts = df["MATERIAL_PARENT"].value_counts().to_dict()
            
        for idx in df.index:
            errors = []
            warnings = []
            
            # 1. Quantity Validation
            quantity_val = clean_numeric(df.loc[idx, "QUANTITY"]) if "QUANTITY" in df.columns else None
            if quantity_val is not None:
                if quantity_val <= 0:
                    errors.append(f"Cantidad de componente menor o igual a cero: {quantity_val}")
                    kpis["industrial_errors"] += 1
                elif quantity_val >= 9999:
                    warnings.append(f"Cantidad de componente atípica / extremadamente alta: {quantity_val}")
                    kpis["industrial_warnings"] += 1
            else:
                errors.append("Cantidad de componente no es un valor numérico válido")
                kpis["industrial_errors"] += 1
                
            # 2. Base UOM Validation
            uom = str(df.loc[idx, "UOM"]).strip().upper() if "UOM" in df.columns else ""
            if uom and uom not in VALID_BASE_UOMS:
                warnings.append(f"Unidad de medida '{uom}' no estándar en SAP")
                kpis["industrial_warnings"] += 1
                
            # 3. Complexity Heuristic
            parent = str(df.loc[idx, "MATERIAL_PARENT"]).strip() if "MATERIAL_PARENT" in df.columns else ""
            if parent and parent_counts.get(parent, 0) > 50:
                warnings.append(f"BOM Compleja: El material padre '{parent}' tiene {parent_counts[parent]} componentes.")
                kpis["complex_boms"] += 1
                kpis["industrial_warnings"] += 1
                
            if errors or warnings:
                all_msgs = []
                if errors:
                    all_msgs.extend([f"ERROR: {e}" for e in errors])
                if warnings:
                    all_msgs.extend([f"WARN: {w}" for w in warnings])
                df.at[idx, "IND_ERROR"] = " | ".join(all_msgs)
                if errors:
                    df.at[idx, "IND_VALID"] = False
                    
        num_errs = (df["IND_VALID"] == False).sum()
        if num_errs > 0:
            logs.append({"level": "WARNING", "message": f"BOM: Se detectaron {num_errs} posiciones con cantidades no permitidas."})
        if kpis["complex_boms"] > 0:
            logs.append({"level": "INFO", "message": f"BOM: Se identificaron {kpis['complex_boms']} registros asociados a BOMs complejas (>50 componentes)."})
            
    elif template_name == "Rutas de Operaciones (Routing)":
        for idx in df.index:
            errors = []
            warnings = []
            
            # 1. Puesto de trabajo
            work_center = str(df.loc[idx, "WORK_CENTER"]).strip() if "WORK_CENTER" in df.columns else ""
            if not work_center or work_center == "-":
                errors.append("Puesto de trabajo (WORK_CENTER) vacío o no especificado")
                kpis["industrial_errors"] += 1
                
            # 2. Tiempos
            setup_time = clean_numeric(df.loc[idx, "SETUP_TIME"]) if "SETUP_TIME" in df.columns else None
            machine_time = clean_numeric(df.loc[idx, "MACHINE_TIME"]) if "MACHINE_TIME" in df.columns else None
            labor_time = clean_numeric(df.loc[idx, "LABOR_TIME"]) if "LABOR_TIME" in df.columns else None
            
            # Validations on Setup Time
            if setup_time is not None:
                if setup_time < 0:
                    errors.append(f"Tiempo de preparación negativo: {setup_time}")
                    kpis["industrial_errors"] += 1
                elif setup_time == 0:
                    errors.append("SETUP_TIME crítico: tiempo de preparación es 0 en una ruta activa")
                    kpis["zero_setup_routes"] += 1
                    kpis["industrial_errors"] += 1
            else:
                errors.append("Tiempo de preparación no es un valor numérico válido")
                kpis["industrial_errors"] += 1
                
            # Machine and Labor time validations
            if machine_time is not None:
                if machine_time < 0:
                    errors.append(f"Tiempo de máquina negativo: {machine_time}")
                    kpis["industrial_errors"] += 1
                elif machine_time == 0 and (labor_time is not None and labor_time == 0):
                    warnings.append("Ambos tiempos de máquina y mano de obra son 0")
                    kpis["industrial_warnings"] += 1
            else:
                errors.append("Tiempo de máquina no es un valor numérico válido")
                kpis["industrial_errors"] += 1
                
            if labor_time is not None:
                if labor_time < 0:
                    errors.append(f"Tiempo de mano de obra negativo: {labor_time}")
                    kpis["industrial_errors"] += 1
            else:
                errors.append("Tiempo de mano de obra no es un valor numérico válido")
                kpis["industrial_errors"] += 1
                
            if errors or warnings:
                all_msgs = []
                if errors:
                    all_msgs.extend([f"ERROR: {e}" for e in errors])
                if warnings:
                    all_msgs.extend([f"WARN: {w}" for w in warnings])
                df.at[idx, "IND_ERROR"] = " | ".join(all_msgs)
                if errors:
                    df.at[idx, "IND_VALID"] = False
                    
        num_errs = (df["IND_VALID"] == False).sum()
        if num_errs > 0:
            logs.append({"level": "WARNING", "message": f"Routing: Se detectaron {num_errs} operaciones con errores críticos (ej. preparación nula)."})
            
    elif template_name == "Centro de Coste (Cost Center)":
        date_pattern_1 = re.compile(r"^\d{4}\d{2}\d{2}$") # YYYYMMDD
        date_pattern_2 = re.compile(r"^\d{2}\.\d{2}\.\d{4}$") # DD.MM.YYYY
        
        for idx in df.index:
            errors = []
            warnings = []
            
            # 1. Responsable (Person in Charge)
            pic = str(df.loc[idx, "PERSON_IN_CHARGE"]).strip() if "PERSON_IN_CHARGE" in df.columns else ""
            if not pic or pic == "-":
                errors.append("Falta responsable asignado al Centro de Coste (PERSON_IN_CHARGE)")
                kpis["industrial_errors"] += 1
                
            # 2. Área Funcional
            fa = str(df.loc[idx, "FUNCTIONAL_AREA"]).strip() if "FUNCTIONAL_AREA" in df.columns else ""
            if not fa or fa == "-":
                errors.append("Falta área funcional obligatoria (FUNCTIONAL_AREA)")
                kpis["industrial_errors"] += 1
                
            # 3. Grupo Jerárquico
            hg = str(df.loc[idx, "HIERARCHY_GROUP"]).strip() if "HIERARCHY_GROUP" in df.columns else ""
            if not hg or hg == "-":
                errors.append("Grupo de jerarquía estándar (HIERARCHY_GROUP) no especificado")
                kpis["industrial_errors"] += 1
                
            # 4. Valid Dates check
            valid_from = str(df.loc[idx, "VALID_FROM"]).strip() if "VALID_FROM" in df.columns else ""
            valid_to = str(df.loc[idx, "VALID_TO"]).strip() if "VALID_TO" in df.columns else ""
            
            if valid_from:
                if not (date_pattern_1.match(valid_from) or date_pattern_2.match(valid_from)):
                    warnings.append(f"Formato de fecha inicio '{valid_from}' no estándar (YYYYMMDD o DD.MM.YYYY esperado)")
                    kpis["industrial_warnings"] += 1
                    
            if valid_to:
                if not (date_pattern_1.match(valid_to) or date_pattern_2.match(valid_to)):
                    warnings.append(f"Formato de fecha fin '{valid_to}' no estándar (YYYYMMDD o DD.MM.YYYY esperado)")
                    kpis["industrial_warnings"] += 1
                    
            if errors or warnings:
                all_msgs = []
                if errors:
                    all_msgs.extend([f"ERROR: {e}" for e in errors])
                if warnings:
                    all_msgs.extend([f"WARN: {w}" for w in warnings])
                df.at[idx, "IND_ERROR"] = " | ".join(all_msgs)
                if errors:
                    df.at[idx, "IND_VALID"] = False
                    
        num_errs = (df["IND_VALID"] == False).sum()
        if num_errs > 0:
            logs.append({"level": "WARNING", "message": f"Cost Center: Se detectaron {num_errs} registros con inconsistencias de controlling."})
            
    return df, logs, kpis
