import argparse
import json
import os
import sys
import pandas as pd
from sanitizer.core import SanitizerEngine
from sanitizer.mapping import SchemaMapper
from sanitizer.schema import SchemaEnforcer
from sanitizer.diagnostics import DataDiagnostics

def load_json_option(option_str):
    """
    Attempts to parse option_str as a JSON object, or if it points to a file,
    reads it as JSON.
    """
    if not option_str:
        return {}
        
    if os.path.exists(option_str):
        try:
            with open(option_str, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al cargar archivo JSON '{option_str}': {e}")
            sys.exit(1)
            
    try:
        return json.loads(option_str)
    except json.JSONDecodeError as e:
        print(f"Error: La cadena especificada no es un JSON válido ni un archivo existente: '{option_str}'")
        sys.exit(1)

def print_banner():
    print("=" * 70)
    print("            DATA SANITIZER ERP MIGRATION ENGINE (V4.0.0)")
    print("=" * 70)

def main():
    print_banner()
    
    parser = argparse.ArgumentParser(description="Sanitiza y normaliza datos para migración de ERP.")
    parser.add_argument("-i", "--input", required=True, help="Ruta del archivo CSV o Excel de entrada.")
    parser.add_argument("-o", "--output", help="Ruta de guardado para la salida CSV sanitizada.")
    parser.add_argument("-m", "--mapping", help="JSON de mapeo de columnas ('{\"Origen\": \"Destino\"}') o ruta al archivo JSON.")
    parser.add_argument("-t", "--types", help="JSON de tipos semánticos ('{\"Columna\": \"tax_id/iban/phone/text\"}') o ruta al archivo JSON.")
    parser.add_argument("-d", "--dedup", help="Nombre de la columna (en destino) sobre la que aplicar coincidencia difusa.")
    parser.add_argument("-th", "--threshold", type=float, default=85.0, help="Umbral de similitud para deduplicación (0-100, default: 85.0).")
    parser.add_argument("-r", "--report", help="Ruta para guardar el informe de duplicados en formato JSON.")
    parser.add_argument("--keep-unmapped", action="store_true", help="Conserva las columnas no mapeadas en la salida.")
    
    # Session 1 Arguments
    parser.add_argument("-s", "--schema", help="Ruta al archivo JSON de esquema de validación estructural (Schema Enforcement).")
    parser.add_argument("--sheet", help="Nombre o índice de la hoja de Excel a procesar (solo archivos Excel).")
    parser.add_argument("--health-check", action="store_true", help="Ejecuta y muestra el reporte de diagnóstico de salud inicial antes de limpiar.")
    
    args = parser.parse_args()
    
    # Load settings
    mapping_dict = load_json_option(args.mapping)
    column_types = load_json_option(args.types)
    
    # Configure output files
    input_dir, input_file = os.path.split(args.input)
    input_name, _ = os.path.splitext(input_file)
    
    output_path = args.output or os.path.join(input_dir, f"sanitized_{input_name}.csv")
    report_path = args.report or os.path.join(input_dir, f"duplicates_report_{input_name}.json")
    
    # Setup Mapper
    mapper = None
    if mapping_dict:
        # Require target fields mapped
        required_fields = list(mapping_dict.values())
        mapper = SchemaMapper(column_mapping=mapping_dict, required_target_fields=required_fields)
        
    # Setup Engine
    engine = SanitizerEngine(column_types=column_types, mapper=mapper)
    
    try:
        # Load Raw Data
        df = engine.load_data(args.input, sheet_name=args.sheet)
        
        # Health Check Diagnostics
        if args.health_check:
            diagnose = DataDiagnostics(df)
            health_report = diagnose.run_health_check()
            print(diagnose.format_report(health_report))
            print()
            
        # Schema Enforcement
        if args.schema:
            print(f"[>] Validando restricciones del esquema JSON: {args.schema}")
            enforcer = SchemaEnforcer.load_from_file(args.schema)
            is_valid, schema_errors = enforcer.validate(df)
            if not is_valid:
                print("\n[ERR] El archivo no cumple con el esquema estructural de la tabla de destino:")
                for err in schema_errors:
                    print(f"  - {err}")
                print("\nAbortando proceso para proteger la integridad de la base de datos.")
                sys.exit(1)
            print("[+] Validación de esquema exitosa. Todos los campos requeridos y restricciones son válidos.\n")
        
        # Run Sanitization
        run_dedup = bool(args.dedup)
        clean_df, dup_report = engine.sanitize(
            df,
            run_dedup=run_dedup,
            dedup_column=args.dedup,
            dedup_threshold=args.threshold,
            keep_unmapped=args.keep_unmapped
        )
        
        # Save output CSV (using Semicolon separator and BOM for direct Excel compatibility in Europe)
        print(f"\n[>] Guardando archivo sanitizado en: {output_path}")
        clean_df.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
        
        # Save duplicate report
        if run_dedup and dup_report:
            print(f"[>] Guardando reporte de duplicados en: {report_path}")
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(dup_report, f, indent=2, ensure_ascii=False)
                
        print("\n" + "=" * 70)
        print("                 PROCESO FINALIZADO CON ÉXITO")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n[CRITICAL ERROR] El proceso ha fallado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
