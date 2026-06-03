import pandas as pd
from sanitizer.rules.geo import validate_postal_code, get_province_by_cp, clean_postal_code
from sanitizer.rules.bic import validate_bic, clean_bic
from sanitizer.rules.address import split_address, clean_address
from sanitizer.core import SanitizerEngine

def test_postal_code_validation():
    # Valid CP
    is_valid, cleaned, err = validate_postal_code("08770")
    assert is_valid is True
    assert cleaned == "08770"
    
    # 4-digit CP should be padded
    is_valid, cleaned, err = validate_postal_code("8770")
    assert is_valid is True
    assert cleaned == "08770"
    
    # Out of range CP
    is_valid, cleaned, err = validate_postal_code("99999")
    assert is_valid is False
    assert err == "Código postal fuera del rango de España (01000 - 52999)"
    
    # Non-numeric CP
    is_valid, cleaned, err = validate_postal_code("08A70")
    assert is_valid is False

def test_province_lookup():
    assert get_province_by_cp("08770") == "BARCELONA"
    assert get_province_by_cp("28001") == "MADRID"
    assert get_province_by_cp("01001") == "ALAVA"
    assert get_province_by_cp("99999") is None

def test_bic_validation():
    # Valid 8 chars BIC
    is_valid, cleaned, err = validate_bic("DEUTDEDB")
    assert is_valid is True
    assert cleaned == "DEUTDEDB"
    
    # Valid 11 chars BIC
    is_valid, cleaned, err = validate_bic("DEUTDEDBAXX")
    assert is_valid is True
    assert cleaned == "DEUTDEDBAXX"
    
    # Invalid structure
    is_valid, cleaned, err = validate_bic("DEUTD")
    assert is_valid is False
    
    # Check consistency with IBAN country code (matches)
    is_valid, cleaned, err = validate_bic("DEUTDEDB", country_code="DE")
    assert is_valid is True
    
    # Check consistency with IBAN country code (mismatch)
    is_valid, cleaned, err = validate_bic("DEUTDEDB", country_code="ES")
    assert is_valid is False
    assert "Discrepancia" in err

def test_address_splitting():
    # Standard format
    tipo, nombre, numero, piso = split_address("C/ Gran Vía 45, 3º B")
    assert tipo == "CALLE"
    assert nombre == "GRAN VÍA"
    assert numero == "45"
    assert piso == "3º B"
    
    # Another format with Av.
    tipo, nombre, numero, piso = split_address("Av. Diagonal, 640, 4-A")
    assert tipo == "AVENIDA"
    assert nombre == "DIAGONAL"
    assert numero == "640"
    assert piso == "4-A"
    
    # No number format
    tipo, nombre, numero, piso = split_address("Plaza Mayor S/N")
    assert tipo == "PLAZA"
    assert nombre == "MAYOR"
    assert numero == "S/N"
    assert piso == ""
    
    # Suffix BIS
    tipo, nombre, numero, piso = split_address("Carretera de Barcelona 12 Bis")
    assert tipo == "CARRETERA"
    assert nombre == "DE BARCELONA"
    assert numero == "12 BIS"
    assert piso == ""

    # Catalan carrer
    tipo, nombre, numero, piso = split_address("Carrer Balmes 99, 1-1")
    assert tipo == "CALLE"
    assert nombre == "BALMES"
    assert numero == "99"
    assert piso == "1-1"

def test_engine_session2_integration():
    # Test dataset containing:
    # 1. Geographic autocorrection: CP 08770 (valid) -> Province MADRID (mismatch, should be corrected to BARCELONA)
    # 2. Bank country consistency: IBAN ES... -> BIC DEUTDEDB (mismatch, should be flagged invalid)
    # 3. Address splitting: C/ Gran Vía 45, 3º B
    data = {
        "CODIGO_POSTAL": ["8770", "28080"],
        "PROVINCIA": ["MADRID", "MADRID"],
        "IBAN": ["ES9121000418450200051332", "ES9121000418450200051332"],
        "BIC": ["DEUTDEDB", "DEUTESDB"],
        "DIRECCION": ["C/ Gran Vía 45, 3º B", "Av. Diagonal, 640, 4-A"]
    }
    df = pd.DataFrame(data)
    
    col_types = {
        "CODIGO_POSTAL": "postal_code",
        "PROVINCIA": "province",
        "IBAN": "iban",
        "BIC": "bic",
        "DIRECCION": "address"
    }
    
    engine = SanitizerEngine(column_types=col_types)
    result = engine.sanitize(df)
    sanitized_df = result.df
    
    # 1. Check CP normalization
    assert sanitized_df.loc[0, "CODIGO_POSTAL"] == "08770"
    assert sanitized_df.loc[0, "CODIGO_POSTAL_VALID"] == True
    
    # 2. Check Province auto-correction (MADRID -> BARCELONA for 08770)
    assert sanitized_df.loc[0, "PROVINCIA"] == "BARCELONA"
    # For row 1, 28080 is Madrid, so it should stay MADRID
    assert sanitized_df.loc[1, "PROVINCIA"] == "MADRID"
    
    # 3. Check bank mismatch
    # Row 0: IBAN (ES) and BIC (DE) -> BIC should be invalid
    assert sanitized_df.loc[0, "BIC_VALID"] == False
    assert "Discrepancia de país" in sanitized_df.loc[0, "BIC_ERROR"]
    
    # Row 1: IBAN (ES) and BIC (ES) -> BIC should be valid
    assert sanitized_df.loc[1, "BIC_VALID"] == True
    
    # 4. Check address splitting
    assert sanitized_df.loc[0, "DIRECCION_TIPO_VIA"] == "CALLE"
    assert sanitized_df.loc[0, "DIRECCION_NOMBRE_VIA"] == "GRAN VÍA"
    assert sanitized_df.loc[0, "DIRECCION_NUMERO"] == "45"
    assert sanitized_df.loc[0, "DIRECCION_PISO"] == "3º B"
    
    assert sanitized_df.loc[1, "DIRECCION_TIPO_VIA"] == "AVENIDA"
    assert sanitized_df.loc[1, "DIRECCION_NOMBRE_VIA"] == "DIAGONAL"
    assert sanitized_df.loc[1, "DIRECCION_NUMERO"] == "640"
    assert sanitized_df.loc[1, "DIRECCION_PISO"] == "4-A"
