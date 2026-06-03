import re

# ISO 13616 Country IBAN lengths for countries related to Spain, Portugal, Italy, France, Germany, UK
COUNTRY_LENGTHS = {
    "ES": 24, # España
    "PT": 25, # Portugal
    "IT": 27, # Italia
    "FR": 27, # Francia
    "DE": 22, # Alemania
    "GB": 22, # Reino Unido
    "AD": 24, # Andorra
    "BE": 16, # Bélgica
    "NL": 18, # Países Bajos
    "CH": 21, # Suiza
    "IE": 22, # Irlanda
}

def clean_iban(value):
    """
    Cleans an IBAN string by removing non-alphanumeric characters
    and converting to uppercase.
    """
    if not value or value == "-":
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(value))
    return cleaned.upper()

def validate_iban(iban):
    """
    Validates an IBAN using the standard ISO 13616 Modulo-97 algorithm.
    Returns: (is_valid, cleaned_iban, error_message)
    """
    cleaned = clean_iban(iban)
    
    if not cleaned:
        return False, "-", "Valor vacío o no válido"
        
    if len(cleaned) < 15 or len(cleaned) > 34:
        return False, cleaned, f"Longitud incorrecta: {len(cleaned)} caracteres (debe estar entre 15 y 34)"

    country_code = cleaned[:2]
    if not country_code.isalpha():
        return False, cleaned, "El IBAN debe comenzar con un código de país de 2 letras"

    # Validate country-specific length if known
    if country_code in COUNTRY_LENGTHS:
        expected_len = COUNTRY_LENGTHS[country_code]
        if len(cleaned) != expected_len:
            return False, cleaned, f"Longitud incorrecta para país {country_code}: {len(cleaned)} (deberían ser {expected_len})"

    # Reorder: move country code & check digits to the end
    reordered = cleaned[4:] + cleaned[:4]
    
    # Convert letters to numbers (A=10, B=11 ... Z=35)
    numeric_parts = []
    for char in reordered:
        if char.isalpha():
            # ord('A') is 65, we want A=10, B=11 ... so ord(char) - 55
            numeric_parts.append(str(ord(char) - 55))
        else:
            numeric_parts.append(char)
            
    numeric_string = "".join(numeric_parts)
    
    # Mathematical validation: numeric_string mod 97 must equal 1
    try:
        modulo_result = int(numeric_string) % 97
        if modulo_result != 1:
            return False, cleaned, "Algoritmo de control (Módulo 97) fallido: IBAN matemáticamente incorrecto"
    except ValueError:
        return False, cleaned, "El IBAN transformado contiene caracteres no numéricos inesperados"
        
    return True, cleaned, ""
