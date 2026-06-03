# -*- coding: utf-8 -*-
"""
Unit tests for Session 11: SAP pre-migration packaging, encoding validation, business KPIs rendering,
empty rejects ZIP packaging, and deduplication merged KPI logic.
"""
import io
import zipfile
import pandas as pd
from sanitizer.ui_actions import create_migration_zip, apply_merge_policies
from sanitizer.reports import generate_readiness_report

def test_zip_contains_required_session11_files():
    """
    Verifies that the ZIP file contains exactly the 4 required files for Session 11
    when no optional/legacy costing or inventory data is provided.
    """
    data = {
        "PARTNER_ID": ["BP001", "BP002"],
        "NAME": ["Empresa A", "Empresa B"],
        "TAX_ID": ["ESA12345678", "ESB87654321"]
    }
    df = pd.DataFrame(data)
    html_report = "<html><body>Readiness Report Mock</body></html>"
    logs = [{"timestamp": "12:00:00", "level": "INFO", "message": "Proceso iniciado"}]
    
    zip_bytes = create_migration_zip(
        main_df=df,
        template_name="Business Partner (BP)",
        costing_results=None,
        inventory_results=None,
        html_report=html_report,
        logs=logs
    )
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        files = z.namelist()
        assert "datos_limpios.csv" in files
        assert "registros_rechazados.csv" in files
        assert "readiness_report.html" in files
        assert "auditoria_ejecucion.log" in files
        assert len(files) == 4


def test_datos_limpios_csv_encoding_and_delimiter():
    """
    Validates that the generated clean data CSV file (datos_limpios.csv) inside the ZIP
    is encoded as UTF-8-sig (with BOM) and uses the semicolon (;) as the delimiter.
    """
    data = {
        "PARTNER_ID": ["BP001", "BP002"],
        "NAME": ["Empresa A", "Empresa B"],
        "TAX_ID": ["ESA12345678", "ESB87654321"]
    }
    df = pd.DataFrame(data)
    html_report = "<html><body>Readiness Report Mock</body></html>"
    logs = []
    
    zip_bytes = create_migration_zip(
        main_df=df,
        template_name="Business Partner (BP)",
        costing_results=None,
        inventory_results=None,
        html_report=html_report,
        logs=logs
    )
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        csv_bytes = z.read("datos_limpios.csv")
        # UTF-8-sig starts with BOM \xef\xbb\xbf
        assert csv_bytes.startswith(b'\xef\xbb\xbf')
        
        csv_text = csv_bytes.decode("utf-8-sig")
        lines = csv_text.splitlines()
        assert len(lines) > 1
        
        # Semicolon delimiter check
        assert ";" in lines[0]
        assert ";" in lines[1]


def test_business_kpis_rendered_in_html():
    """
    Verifies that the readiness report correctly calculates and renders corporate KPIs:
    - hours_ahorradas (fixes-based vs basal estimation),
    - activation of the basal footnote,
    - riesgo_evitado,
    - ready_to_load_pct (correct calculation with valid and rejected records).
    """
    df = pd.DataFrame({
        "PARTNER_ID": ["BP001", "BP002", "BP003"],
        "NAME": ["Empresa A", "Empresa B", "Empresa C"],
        "TAX_ID": ["ESA12345678", "ESB87654321", "ESC11223344"],
        "IBAN": ["ES1234", "ES5678", "ES9012"]
    })
    rejected_df = pd.DataFrame({
        "PARTNER_ID": ["BP_REJ1"],
        "NAME": ["Empresa Rej"],
        "TAX_ID": ["INVALID"],
        "IBAN": ["ES_ERR"]
    })
    
    # Case 1: Active fixes formula
    kpis_active = {
        "tax_id_fixes": 1,       # 10m
        "postal_code_fixes": 2,  # 10m
        "iban_fixes": 1,         # 15m
        "province_fixes": 1,     # 5m
        "bic_fixes": 1,          # 5m
        "address_fixes": 1,      # 10m
        "phone_fixes": 1,        # 2m
        "duplicates_merged": 1,  # 20m
        "iban_errors": 2
    }
    # Total fix events = 9
    # Hours saved = (10 + 10 + 15 + 5 + 5 + 10 + 2 + 20) / 60 = 77 / 60 = 1.283 -> round(x, 1) = 1.3
    # Riesgo evitado = (iban_errors + iban_fixes) * 100 = (2 + 1) * 100 = 300 €
    # Ready to load % = 3 / 4 = 75.0%
    
    html_active = generate_readiness_report(
        df=df,
        column_types={"PARTNER_ID": "text", "NAME": "text", "TAX_ID": "tax_id", "IBAN": "iban"},
        duplicates=[],
        kpis=kpis_active,
        rejected_df=rejected_df
    )
    
    assert "1.3 h" in html_active
    assert "300 €" in html_active
    assert "75.0%" in html_active
    assert "3 registros válidos de un total de 4 analizados" in html_active
    # Footnote check (no basal, should display direct remediation note)
    assert "Tiempo estimado de remediación manual directa evitado" in html_active
    assert "Estimación basal de ingesta y verificación manual (sin correcciones aplicadas)" not in html_active
    
    # Case 2: Zero fixes (activates basal estimation)
    kpis_basal = {
        "tax_id_fixes": 0,
        "postal_code_fixes": 0,
        "iban_fixes": 0,
        "province_fixes": 0,
        "bic_fixes": 0,
        "address_fixes": 0,
        "phone_fixes": 0,
        "duplicates_merged": 0,
        "iban_errors": 0
    }
    # Total records = 4
    # Hours saved = 4 * 0.02 = 0.08 -> round(x, 1) = 0.1
    # Riesgo evitado = (0 + 0) * 100 = 0 €
    
    html_basal = generate_readiness_report(
        df=df,
        column_types={"PARTNER_ID": "text", "NAME": "text", "TAX_ID": "tax_id", "IBAN": "iban"},
        duplicates=[],
        kpis=kpis_basal,
        rejected_df=rejected_df
    )
    
    assert "0.1 h" in html_basal
    assert "0 €" in html_basal
    assert "75.0%" in html_basal
    assert "3 registros válidos de un total de 4 analizados" in html_basal
    # Footnote check (basal activated)
    assert "Estimación basal de ingesta y verificación manual (sin correcciones aplicadas)" in html_basal
    assert "Tiempo estimado de remediación manual directa evitado" not in html_basal


def test_zip_handles_empty_or_none_rejected_df():
    """
    Validates that the ZIP packager safely handles empty or None rejected_df objects,
    producing an empty file with only the header row and adding a specific compliance
    warning to the execution audit log.
    """
    data = {
        "PARTNER_ID": ["BP001", "BP002"],
        "NAME": ["Empresa A", "Empresa B"],
        "TAX_ID": ["ESA12345678", "ESB87654321"]
    }
    df = pd.DataFrame(data)
    html_report = "<html><body>Readiness Report Mock</body></html>"
    logs = [{"timestamp": "12:00:00", "level": "INFO", "message": "Proceso iniciado"}]
    
    # 1. None rejected_df
    zip_bytes_none = create_migration_zip(
        main_df=df,
        template_name="Business Partner (BP)",
        costing_results=None,
        inventory_results=None,
        html_report=html_report,
        logs=logs,
        rejected_df=None
    )
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes_none)) as z:
        log_content = z.read("auditoria_ejecucion.log").decode("utf-8")
        assert "REGISTROS_RECHAZADOS: 0 — archivo exportado con cabeceras únicamente" in log_content
        
        rejected_bytes = z.read("registros_rechazados.csv")
        rejected_str = rejected_bytes.decode("utf-8-sig")
        lines = rejected_str.splitlines()
        assert lines[0] == "PARTNER_ID;NAME;TAX_ID"
        assert len(lines) == 1 or (len(lines) == 2 and lines[1] == "")
        
    # 2. Empty DataFrame rejected_df
    empty_rejected_df = pd.DataFrame(columns=["PARTNER_ID", "NAME", "TAX_ID"])
    zip_bytes_empty = create_migration_zip(
        main_df=df,
        template_name="Business Partner (BP)",
        costing_results=None,
        inventory_results=None,
        html_report=html_report,
        logs=logs,
        rejected_df=empty_rejected_df
    )
    
    with zipfile.ZipFile(io.BytesIO(zip_bytes_empty)) as z:
        log_content = z.read("auditoria_ejecucion.log").decode("utf-8")
        assert "REGISTROS_RECHAZADOS: 0 — archivo exportado con cabeceras únicamente" in log_content
        
        rejected_bytes = z.read("registros_rechazados.csv")
        rejected_str = rejected_bytes.decode("utf-8-sig")
        lines = rejected_str.splitlines()
        assert lines[0] == "PARTNER_ID;NAME;TAX_ID"
        assert len(lines) == 1 or (len(lines) == 2 and lines[1] == "")


def test_duplicates_merged_kpi_logic():
    """
    Explicitly tests and verifies the adopted criterion for the duplicates_merged KPI:
    duplicates_merged = len(df_original_sanitized) - len(df_merged)
    where df_merged is the resulting DataFrame after entity resolution policies are applied.
    """
    data = {
        "PARTNER_ID": ["BP001", "BP002", "BP003", "BP004"],
        "NAME": ["Empresa A", "Empresa A", "Empresa B", "Empresa B"],
        "TAX_ID": ["ESA12345678", "ESA12345678", "ESB87654321", "ESB87654321"],
        "NAME_VALID": [True, True, True, True]
    }
    df = pd.DataFrame(data, index=[0, 1, 2, 3])
    
    duplicates = [
        {
            "primary_indices": [0],
            "primary_value": "Empresa A",
            "matches": [{"value": "Empresa A", "indices": [1], "match_type": "tax_id"}]
        },
        {
            "primary_indices": [2],
            "primary_value": "Empresa B",
            "matches": [{"value": "Empresa B", "indices": [3], "match_type": "tax_id"}]
        }
    ]
    
    policies = {
        0: "merge",
        1: "merge"
    }
    
    merged_df = apply_merge_policies(df, duplicates, policies)
    
    # Adopted Business Logic criterion calculation:
    duplicates_merged = len(df) - len(merged_df)
    
    assert len(df) == 4
    assert len(merged_df) == 2
    assert duplicates_merged == 2
