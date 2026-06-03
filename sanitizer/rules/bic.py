import re
from typing import Tuple

def clean_bic(value) -> str:
    """
    Cleans a BIC/SWIFT code value:
    - Removes non-alphanumeric characters and converts to uppercase.
    """
    if not value or value == "-":
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(value).strip())
    return cleaned.upper()

def validate_bic(bic, country_code: str | None = None) -> Tuple[bool, str, str]:
    """
    Validates a BIC/SWIFT code.
    Must be 8 or 11 characters long and conform to ISO 9362 structure:
    - 4 letters: institution code
    - 2 letters: country code (ISO 3166-1 alpha-2)
    - 2 alphanumeric characters: location code
    - 3 alphanumeric characters (optional): branch code
    
    If country_code is provided, verifies that it matches the country code in the BIC.
    Returns: (is_valid, cleaned_bic, error_message)
    """
    cleaned = clean_bic(bic)
    
    if not cleaned:
        return False, "-", "Valor vacío o no válido"
        
    if len(cleaned) not in (8, 11):
        return False, cleaned, f"Longitud incorrecta: {len(cleaned)} caracteres (deben ser 8 u 11)"
        
    # Regex matching structural format
    bic_pattern = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")
    if not bic_pattern.match(cleaned):
        return False, cleaned, "Estructura de BIC/SWIFT no válida"
        
    # Check consistency with IBAN country code if provided
    bic_country = cleaned[4:6]
    if country_code:
        expected_country = str(country_code).strip().upper()
        if len(expected_country) >= 2:
            expected_country = expected_country[:2]
            if bic_country != expected_country:
                return False, cleaned, f"Discrepancia: el país del BIC '{bic_country}' no coincide con el del IBAN '{expected_country}'"
                
    return True, cleaned, ""
