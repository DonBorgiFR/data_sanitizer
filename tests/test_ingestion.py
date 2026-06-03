import os
import pandas as pd
from sanitizer.core import SanitizerEngine
from sanitizer.schema import SchemaEnforcer
from sanitizer.diagnostics import DataDiagnostics

def test_encoding_and_delimiter_detection():
    # 1. Create a temporary CSV file encoded in CP1252 with Semicolon separator
    test_filepath = "test_cp1252_semi.csv"
    test_content = "ID;NOMBRE;VALOR\n1;España;100\n2;Colón;200\n"
    
    with open(test_filepath, "w", encoding="cp1252") as f:
        f.write(test_content)
        
    try:
        engine = SanitizerEngine()
        df = engine.load_data(test_filepath)
        
        # Verify correctness
        assert len(df) == 2
        assert list(df.columns) == ["ID", "NOMBRE", "VALOR"]
        assert df.iloc[0]["NOMBRE"] == "España"
        assert df.iloc[1]["NOMBRE"] == "Colón"
    finally:
        if os.path.exists(test_filepath):
            os.remove(test_filepath)

def test_schema_enforcer():
    schema_dict = {
        "columns": {
            "ID": {"required": True, "nullable": False, "type": "int"},
            "NOMBRE": {"required": True, "nullable": False, "type": "str"},
            "TELEFONO": {"required": False, "nullable": True, "type": "str"}
        }
    }
    
    enforcer = SchemaEnforcer(schema_dict)
    
    # Valid DF
    valid_df = pd.DataFrame([
        {"ID": "1", "NOMBRE": "Juan", "TELEFONO": "600112233"},
        {"ID": "2", "NOMBRE": "Pedro", "TELEFONO": None}
    ])
    is_valid, errors = enforcer.validate(valid_df)
    assert is_valid is True
    assert len(errors) == 0
    
    # Missing required column ID
    invalid_df_missing = pd.DataFrame([
        {"NOMBRE": "Juan", "TELEFONO": "600112233"}
    ])
    is_valid, errors = enforcer.validate(invalid_df_missing)
    assert is_valid is False
    assert any("Falta la columna obligatoria" in err for err in errors)
    
    # Null in non-nullable column NOMBRE
    invalid_df_null = pd.DataFrame([
        {"ID": "1", "NOMBRE": "  ", "TELEFONO": "600112233"}
    ])
    is_valid, errors = enforcer.validate(invalid_df_null)
    assert is_valid is False
    assert any("no permite nulos" in err for err in errors)

def test_diagnostics():
    df = pd.DataFrame([
        {"A": "1", "B": "Texto", "C": ""},
        {"A": "2", "B": "Otro", "C": "2026-06-02"},
        {"A": "1", "B": "Texto", "C": ""}, # exact duplicate of row 0
        {"A": None, "B": "Más", "C": "2026-06-03"}
    ])
    
    diagnostics = DataDiagnostics(df)
    report = diagnostics.run_health_check()
    
    assert report["total_rows"] == 4
    assert report["total_columns"] == 3
    assert report["exact_duplicates"] == 1
    assert report["columns"]["A"]["null_count"] == 1
    assert report["columns"]["C"]["null_count"] == 2
    assert report["columns"]["A"]["inferred_type"] == "integer"
    assert report["columns"]["B"]["inferred_type"] == "text"
    
    # Format and check it compiles without error
    text_report = diagnostics.format_report(report)
    assert "INFORME DE DIAGNÓSTICO DE SALUD" in text_report
