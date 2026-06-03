# -*- coding: utf-8 -*-
import pandas as pd
from sanitizer.core import SanitizerEngine
from sanitizer.sap_templates import SAP_TEMPLATES

def test_sap_bp_truncation():
    """
    Test that SAP Business Partner template auto-truncates fields exceeding max length.
    """
    # Name has a limit of 80 characters in our SAP template. Let's make one with 90 characters.
    long_name = "A" * 90
    data = {
        "PARTNER_ID": ["BP001"],
        "NAME": [long_name],
        "TAX_ID": ["12345678Z"],
        "POSTAL_CODE": ["08770"],
        "PROVINCE": ["BARCELONA"],
        "COUNTRY": ["ES"],
        "STREET": ["Calle Industria 10"]
    }
    
    df = pd.DataFrame(data)
    
    # We map to the SAP Business Partner schema
    column_types = {
        "PARTNER_ID": "text",
        "NAME": "text",
        "TAX_ID": "tax_id",
        "POSTAL_CODE": "postal_code",
        "PROVINCE": "province",
        "COUNTRY": "text",
        "STREET": "address"
    }
    
    engine = SanitizerEngine(column_types=column_types)
    result = engine.sanitize(df)
    sanitized_df = result.df
    # The name should be truncated to exactly 80 characters
    result_name = sanitized_df.loc[0, "NAME"]
    assert len(result_name) == 80
    assert result_name == "A" * 80
    
    # An error column indicating truncation should be present
    assert "NAME_SAP_VALID" in sanitized_df.columns
    assert sanitized_df.loc[0, "NAME_SAP_VALID"] == False
    assert "truncado" in sanitized_df.loc[0, "NAME_SAP_ERROR"]


def test_sap_required_fields():
    """
    Test that SAP Business Partner template flags empty required fields.
    """
    data = {
        "PARTNER_ID": ["BP002"],
        "NAME": ["Empresa de Prueba"],
        "TAX_ID": ["-"],  # Empty/invalid placeholder
        "POSTAL_CODE": [""],  # Empty string
        "PROVINCE": ["BARCELONA"],
        "COUNTRY": ["ES"],
        "STREET": ["Calle Industria 10"]
    }
    
    df = pd.DataFrame(data)
    
    column_types = {
        "PARTNER_ID": "text",
        "NAME": "text",
        "TAX_ID": "tax_id",
        "POSTAL_CODE": "postal_code",
        "PROVINCE": "province",
        "COUNTRY": "text",
        "STREET": "address"
    }
    
    engine = SanitizerEngine(column_types=column_types)
    result = engine.sanitize(df)
    
    # TAX_ID and POSTAL_CODE are required and missing, so the row is rejected.
    rejected_df = result.rejected_df
    assert len(rejected_df) == 1
    
    assert rejected_df.loc[0, "TAX_ID_SAP_VALID"] == False
    assert "obligatorio" in rejected_df.loc[0, "TAX_ID_SAP_ERROR"]
    
    assert rejected_df.loc[0, "POSTAL_CODE_SAP_VALID"] == False
    assert "obligatorio" in rejected_df.loc[0, "POSTAL_CODE_SAP_ERROR"]
