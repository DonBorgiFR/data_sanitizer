import pytest
import pandas as pd
from sanitizer.core import SanitizerEngine
from sanitizer.result import SanitizerResult

def test_empty_dataframe():
    """
    Test that SanitizerEngine correctly handles an empty dataframe without crashing.
    """
    df = pd.DataFrame(columns=["NAME", "TAX_ID", "POSTAL_CODE"])
    col_types = {
        "NAME": "text",
        "TAX_ID": "tax_id",
        "POSTAL_CODE": "postal_code"
    }
    
    engine = SanitizerEngine(column_types=col_types)
    result = engine.sanitize(df)
    
    assert isinstance(result, SanitizerResult)
    assert len(result.df) == 0
    assert result.kpis["text"] == 0
    assert result.kpis["tax_id_fixes"] == 0
    
def test_all_null_values():
    """
    Test that the engine handles rows consisting entirely of NaN/None gracefully.
    """
    data = {
        "NAME": [None, None],
        "TAX_ID": [None, pd.NA],
        "POSTAL_CODE": [pd.NA, None]
    }
    df = pd.DataFrame(data)
    
    col_types = {
        "NAME": "text",
        "TAX_ID": "tax_id",
        "POSTAL_CODE": "postal_code"
    }
    
    engine = SanitizerEngine(column_types=col_types)
    result = engine.sanitize(df)
    
    sanitized_df = result.df
    # Both rows are isolated because TAX_ID is strict and empty
    assert len(sanitized_df) == 0
    assert len(result.rejected_df) == 2
    
    # TAX_ID error should be registered if it's evaluated empty
    assert "TAX_ID_VALID" in result.rejected_df.columns
    assert not result.rejected_df.loc[0, "TAX_ID_VALID"]

def test_missing_mapped_columns():
    """
    Test how the engine reacts if a declared column in column_types is missing from the df.
    """
    data = {
        "NAME": ["Empresa A", "Empresa B"],
        # TAX_ID is missing from the actual dataframe
    }
    df = pd.DataFrame(data)
    
    col_types = {
        "NAME": "text",
        "TAX_ID": "tax_id"  # Defined but missing
    }
    
    engine = SanitizerEngine(column_types=col_types)
    result = engine.sanitize(df)
    
    sanitized_df = result.df
    assert "NAME" in sanitized_df.columns
    assert "TAX_ID" not in sanitized_df.columns
    
    # Check that a WARNING log was registered
    logs = result.logs
    warning_logs = [log for log in logs if log["level"] == "WARNING"]
    assert any("TAX_ID" in log["message"] for log in warning_logs)

def test_unexpected_types_in_dataframe():
    """
    Test that integer or float objects in the dataframe don't crash text processors.
    """
    data = {
        "NAME": [12345, 99.99],
        "POSTAL_CODE": [8001, 28080] # as integers
    }
    df = pd.DataFrame(data)
    
    col_types = {
        "NAME": "text",
        "POSTAL_CODE": "postal_code"
    }
    
    engine = SanitizerEngine(column_types=col_types)
    result = engine.sanitize(df)
    
    sanitized_df = result.df
    assert sanitized_df.loc[0, "NAME"] == "12345.0"
    assert sanitized_df.loc[0, "POSTAL_CODE"] == "08001"
    assert sanitized_df.loc[1, "POSTAL_CODE"] == "28080"

def test_isolate_rejects():
    """
    Test that critical errors (like invalid TAX_ID) isolate the row to rejected_df.
    """
    data = {
        "NAME": ["Empresa A", "Empresa B", "Empresa C"],
        "TAX_ID": ["12345678Z", "INVALID_NIF", "11111111H"]
    }
    df = pd.DataFrame(data)
    col_types = {"NAME": "text", "TAX_ID": "tax_id"}
    
    engine = SanitizerEngine(column_types=col_types)
    result = engine.sanitize(df)
    
    assert len(result.df) == 2
    assert result.rejected_df is not None
    assert len(result.rejected_df) == 1
    assert "INVALIDNIF" in result.rejected_df.iloc[0]["TAX_ID"]
    assert "MOTIVO_RECHAZO" in result.rejected_df.columns
    assert "CAMPO_AFECTADO" in result.rejected_df.columns
    
    assert result.metrics["processed_rows"] == 3
    assert result.metrics["valid_rows"] == 2
    assert result.metrics["rejected_rows"] == 1

def test_dry_run():
    """
    Test that dry run returns a comparison DataFrame without crashing and doesn't mutate state unexpectedly.
    """
    data = {
        "NAME": ["A", "B", "C", "D", "E", "F", "G"],
        "TAX_ID": ["12345678Z", "INVALID"] + ["11111111H"] * 5
    }
    df = pd.DataFrame(data)
    col_types = {"NAME": "text", "TAX_ID": "tax_id"}
    
    engine = SanitizerEngine(column_types=col_types)
    dry_df = engine.run_dry_run(df, sample_size=3)
    
    assert len(dry_df) == 3
    assert "Estado" in dry_df.columns
    assert "Rechazado" in dry_df.loc[1, "Estado"]

def test_cell_processing_exception_handling():
    """
    Test that an unexpected exception during cell validation is caught, logged in a structured WARNING,
    and isolates the row if the field is strict.
    """
    from unittest.mock import patch
    data = {
        "NAME": ["Empresa A", "Empresa B"],
        "TAX_ID": ["12345678Z", "87654321X"]
    }
    df = pd.DataFrame(data)
    col_types = {"NAME": "text", "TAX_ID": "tax_id"}
    
    def mock_validate_tax_id(val):
        if val == "87654321X":
            raise ValueError("Conexion a base de datos fiscal caida")
        from sanitizer.rules.tax_id import validate_tax_id
        return validate_tax_id(val)
        
    engine = SanitizerEngine(column_types=col_types)
    
    with patch("sanitizer.core.validate_tax_id", side_effect=mock_validate_tax_id):
        result = engine.sanitize(df)
        
    assert len(result.df) == 1
    assert len(result.rejected_df) == 1
    
    log_messages = [log["message"] for log in result.logs]
    cell_errors = [msg for msg in log_messages if msg.startswith("WARNING|CELL_ERROR")]
    assert len(cell_errors) == 1
    error_msg = cell_errors[0]
    
    assert "col=TAX_ID" in error_msg
    assert "row=1" in error_msg
    assert "value='87654321X'" in error_msg
    assert "strict=True" in error_msg
    assert "error=ValueError: Conexion a base de datos fiscal caida" in error_msg

