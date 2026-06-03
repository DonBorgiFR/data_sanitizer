import sys
from tests.test_rules import (
    test_clean_text,
    test_tax_id_cleansing,
    test_tax_id_validation,
    test_iban_validation,
    test_phone_normalization
)
from tests.test_dedupe import (
    test_similarity_calculation,
    test_find_duplicates,
    test_clean_legal_suffixes,
    test_find_duplicates_tax_id,
    test_find_duplicates_blocking
)
from tests.test_ingestion import (
    test_encoding_and_delimiter_detection,
    test_schema_enforcer,
    test_diagnostics
)
from tests.test_rules_session2 import (
    test_postal_code_validation,
    test_province_lookup,
    test_bic_validation,
    test_address_splitting,
    test_engine_session2_integration
)
from tests.test_sap import test_sap_bp_truncation, test_sap_required_fields
from tests.test_industrial import (
    test_validate_material_master,
    test_validate_bom,
    test_validate_routing,
    test_validate_cost_center,
    test_engine_industrial_integration,
    test_standard_cost_calculation,
    test_cost_deviation_detection,
    test_margin_impact_estimation,
    test_negative_stock_detection,
    test_obsolete_material_detection,
    test_price_discrepancy_detection,
    test_abc_classification
)
from tests.test_edge_cases import (
    test_empty_dataframe,
    test_all_null_values,
    test_missing_mapped_columns,
    test_unexpected_types_in_dataframe,
    test_isolate_rejects,
    test_dry_run,
    test_cell_processing_exception_handling
)
from tests.test_exporter import (
    test_sap_excel_generation,
    test_migration_zip_packaging,
    test_deduplication_blocking_performance
)
from tests.test_help_center import (
    test_help_center_imports,
    test_map_tooltips_content,
    test_all_template_columns_have_tooltips
)
from tests.test_session11 import (
    test_zip_contains_required_session11_files,
    test_datos_limpios_csv_encoding_and_delimiter,
    test_business_kpis_rendered_in_html,
    test_zip_handles_empty_or_none_rejected_df,
    test_duplicates_merged_kpi_logic
)


def main():
    include_perf = "--include-performance" in sys.argv
    
    print("=" * 60)
    print("            EJECUCIÓN DE PRUEBAS UNITARIAS (SINE-PYTEST)")
    print("=" * 60)
    
    tests = [
        ("test_clean_text", test_clean_text),
        ("test_tax_id_cleansing", test_tax_id_cleansing),
        ("test_tax_id_validation", test_tax_id_validation),
        ("test_iban_validation", test_iban_validation),
        ("test_phone_normalization", test_phone_normalization),
        ("test_clean_legal_suffixes", test_clean_legal_suffixes),
        ("test_similarity_calculation", test_similarity_calculation),
        ("test_find_duplicates", test_find_duplicates),
        ("test_find_duplicates_tax_id", test_find_duplicates_tax_id),
        ("test_find_duplicates_blocking", test_find_duplicates_blocking),
        ("test_encoding_and_delimiter_detection", test_encoding_and_delimiter_detection),
        ("test_schema_enforcer", test_schema_enforcer),
        ("test_diagnostics", test_diagnostics),
        ("test_postal_code_validation", test_postal_code_validation),
        ("test_province_lookup", test_province_lookup),
        ("test_bic_validation", test_bic_validation),
        ("test_address_splitting", test_address_splitting),
        ("test_engine_session2_integration", test_engine_session2_integration),
        ("test_sap_bp_truncation", test_sap_bp_truncation),
        ("test_sap_required_fields", test_sap_required_fields),
        ("test_validate_material_master", test_validate_material_master),
        ("test_validate_bom", test_validate_bom),
        ("test_validate_routing", test_validate_routing),
        ("test_validate_cost_center", test_validate_cost_center),
        ("test_engine_industrial_integration", test_engine_industrial_integration),
        ("test_standard_cost_calculation", test_standard_cost_calculation),
        ("test_cost_deviation_detection", test_cost_deviation_detection),
        ("test_margin_impact_estimation", test_margin_impact_estimation),
        ("test_negative_stock_detection", test_negative_stock_detection),
        ("test_obsolete_material_detection", test_obsolete_material_detection),
        ("test_price_discrepancy_detection", test_price_discrepancy_detection),
        ("test_abc_classification", test_abc_classification),
        ("test_sap_excel_generation", test_sap_excel_generation),
        ("test_migration_zip_packaging", test_migration_zip_packaging),
        ("test_deduplication_blocking_performance", test_deduplication_blocking_performance),
        ("test_empty_dataframe", test_empty_dataframe),
        ("test_all_null_values", test_all_null_values),
        ("test_missing_mapped_columns", test_missing_mapped_columns),
        ("test_unexpected_types_in_dataframe", test_unexpected_types_in_dataframe),
        ("test_isolate_rejects", test_isolate_rejects),
        ("test_dry_run", test_dry_run),
        ("test_cell_processing_exception_handling", test_cell_processing_exception_handling),
        ("test_help_center_imports", test_help_center_imports),
        ("test_map_tooltips_content", test_map_tooltips_content),
        ("test_all_template_columns_have_tooltips", test_all_template_columns_have_tooltips),
        ("test_zip_contains_required_session11_files", test_zip_contains_required_session11_files),
        ("test_datos_limpios_csv_encoding_and_delimiter", test_datos_limpios_csv_encoding_and_delimiter),
        ("test_business_kpis_rendered_in_html", test_business_kpis_rendered_in_html),
        ("test_zip_handles_empty_or_none_rejected_df", test_zip_handles_empty_or_none_rejected_df),
        ("test_duplicates_merged_kpi_logic", test_duplicates_merged_kpi_logic)
    ]
    
    passed_func = 0
    failed_func = 0
    
    print("[INFO] Iniciando ejecucion de Pruebas Funcionales (50 tests)...")
    for name, test_func in tests:
        try:
            print(f"[>] Ejecutando {name}...", end=" ")
            test_func()
            print("OK")
            passed_func += 1
        except AssertionError as e:
            print("FALLO")
            print(f"    Error: AssertionError")
            failed_func += 1
        except Exception as e:
            print("FALLO")
            print(f"    Error inesperado: {e}")
            failed_func += 1
            
    passed_perf = 0
    failed_perf = 0
    
    if include_perf:
        print("\n" + "=" * 60)
        print("          EJECUCIÓN DE PRUEBAS DE RENDIMIENTO Y ESTRÉS")
        print("=" * 60)
        print("[INFO] Cargando y ejecutando pruebas de rendimiento (2 tests)...")
        try:
            from tests.test_performance import (
                test_performance_ingesta_limpieza_10k,
                test_performance_deduplicacion_2k_blocking
            )
            perf_tests = [
                ("test_performance_ingesta_limpieza_10k", test_performance_ingesta_limpieza_10k),
                ("test_performance_deduplicacion_2k_blocking", test_performance_deduplicacion_2k_blocking)
            ]
            for name, test_func in perf_tests:
                try:
                    print(f"[>] Ejecutando {name}...", end=" ")
                    test_func()
                    print("OK")
                    passed_perf += 1
                except AssertionError as e:
                    print("FALLO")
                    print(f"    Error de SLA/Asercion: {e}")
                    failed_perf += 1
                except Exception as e:
                    print("FALLO")
                    print(f"    Error inesperado: {e}")
                    failed_perf += 1
        except Exception as e:
            print(f"[ERROR] No se pudieron cargar las pruebas de rendimiento: {e}")
            failed_perf = 2
            
    print("=" * 60)
    print("                     RESUMEN DE RESULTADOS")
    print("=" * 60)
    print(f"Pruebas Funcionales:  {passed_func} aprobadas, {failed_func} fallidas (Total: 50)")
    if include_perf:
        print(f"Pruebas Rendimiento:  {passed_perf} aprobadas, {failed_perf} fallidas (Total: 2)")
    print("=" * 60)
    
    if failed_func > 0 or failed_perf > 0:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
