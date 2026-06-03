import pandas as pd

from sanitizer.rules.text import clean_text
from sanitizer.rules.tax_id import validate_tax_id, clean_tax_id
from sanitizer.rules.iban import validate_iban, clean_iban
from sanitizer.rules.phone import normalize_phone, clean_phone

def test_clean_text():
    assert clean_text("  hello   world  ") == "HELLO WORLD"
    assert clean_text("N/A") == "-"
    assert clean_text("null") == "-"
    assert clean_text(None) == "-"
    assert clean_text("valid", uppercase=False) == "valid"

def test_tax_id_cleansing():
    assert clean_tax_id("b-64.613.201") == "B64613201"
    assert clean_tax_id(" 12345678-z ") == "12345678Z"
    assert clean_tax_id(None) == ""

def test_tax_id_validation():
    # Valid NIF
    is_valid, cleaned, err = validate_tax_id("12345678Z")
    assert is_valid is True
    assert cleaned == "12345678Z"

    # Valid NIE
    is_valid, cleaned, err = validate_tax_id("X1234567L")
    assert is_valid is True
    assert cleaned == "X1234567L"

    # Valid CIF (New Group Maquinaria Moderna)
    is_valid, cleaned, err = validate_tax_id("B64613201")
    assert is_valid is True
    assert cleaned == "B64613201"

    # Invalid NIF (wrong letter)
    is_valid, _, _ = validate_tax_id("12345678A")
    assert is_valid is False

    # Invalid CIF (wrong digit)
    is_valid, _, _ = validate_tax_id("B64613202")
    assert is_valid is False

    # Invalid format (too short)
    is_valid, _, _ = validate_tax_id("123")
    assert is_valid is False

def test_iban_validation():
    # Valid Spanish IBAN
    valid_iban = "ES91 2100 0418 4502 0005 1332"
    is_valid, cleaned, err = validate_iban(valid_iban)
    assert is_valid is True
    assert cleaned == "ES9121000418450200051332"

    # Invalid Spanish IBAN (modified check digit)
    invalid_iban = "ES92 2100 0418 4502 0005 1332"
    is_valid, _, _ = validate_iban(invalid_iban)
    assert is_valid is False

    # Invalid length
    is_valid, _, _ = validate_iban("ES91")
    assert is_valid is False

def test_phone_normalization():
    # Spain phone without country code
    assert normalize_phone("662384698") == "+34662384698"
    assert normalize_phone("931234567") == "+34931234567"
    
    # Spain phone with spaces/dashes
    assert normalize_phone("93-123 45 67") == "+34931234567"
    
    # Phone with international code
    assert normalize_phone("+33123456789") == "+33123456789"
    assert normalize_phone("0033123456789") == "+33123456789"
