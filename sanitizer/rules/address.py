import re
from typing import Tuple

# Standard replacements for Spanish street type prefixes
STREET_PREFIXES = {
    r"^(C/|CL\b|CL\.|CALLE\b)": "CALLE",
    r"^(AVDA\b|AVDA\.|AV\b|AV\.|AVENIDA\b|AVINGUDA\b)": "AVENIDA",
    r"^(PZA\b|PZA\.|PLAZA\b|PL\b|PL\.)": "PLAZA",
    r"^(PASEO\b|Pº\b|PSO\b|PSO\.)": "PASEO",
    r"^(CTRA\b|CTRA\.|CARRETERA\b|CRA\b|CRA\.)": "CARRETERA",
    r"^(RDA\b|RDA\.|RONDA\b)": "RONDA",
    r"^(TRAV\b|TRAV\.|TRAVESERA\b|TRAVESIA\b|TRAVESÍA\b)": "TRAVESÍA",
    r"^(PASAJE\b|PSJ\b|PSJ\.)": "PASAJE",
    r"^(CARRER\b)": "CALLE", # Catalan carrer
}

def clean_address(value: str) -> str:
    """
    Cleans an address string:
    - Normalizes multiple spaces to a single space.
    - Strips leading and trailing whitespaces.
    - Converts to uppercase.
    """
    if not value or value == "-":
        return ""
    val_str = str(value).strip()
    val_str = " ".join(val_str.split())
    return val_str.upper()

def split_address(address_str: str) -> Tuple[str, str, str, str]:
    """
    Parses a Spanish address string and splits it into:
    - TIPO_VIA (e.g. CALLE, AVENIDA, PLAZA)
    - NOMBRE_VIA (street name)
    - NUMERO (house number or S/N)
    - PISO (floor, door or other details)
    
    Returns: (tipo_via, nombre_via, numero, piso)
    """
    cleaned = clean_address(address_str)
    if not cleaned:
        return "", "", "", ""

    # 1. Detect and extract street type prefix
    tipo_via = ""
    rest = cleaned
    
    for pattern, normalized in STREET_PREFIXES.items():
        match = re.search(pattern, cleaned, re.IGNORECASE)
        if match:
            tipo_via = normalized
            # Remove the matched prefix from the rest of the string
            rest = cleaned[match.end():].strip()
            break
            
    # Default to empty if no street type matched
    if not tipo_via:
        tipo_via = ""

    # Helper function to clean text pieces (remove leading/trailing commas and spaces)
    def clean_part(text: str) -> str:
        t = text.strip()
        t = re.sub(r"^[\s,.-]+|[\s,.-]+$", "", t)
        return t.strip()

    # 2. Extract number and floor
    nombre_via = ""
    numero = ""
    piso = ""
    
    # Pattern for house number (e.g. 45, 45 BIS, 12-A, S/N, SIN NUMERO, etc.)
    # Match digit followed optionally by letters/BIS, or S/N, or SIN NUMERO
    num_pattern = r"\b(S/N|SIN\s+NUMERO|SIN\s+NÚMERO|\d+(?:\s*[A-Z]\b|\s*BIS\b)?)\b"

    # Option A: Check if there is a comma separating street/number from floor
    if "," in rest:
        parts = rest.split(",", 1)
        left_part = clean_part(parts[0])
        right_part = clean_part(parts[1])
        
        # Check if left part ends with the number pattern
        # (meaning: street name followed directly by number, then comma, then floor)
        end_num_match = re.search(r"\b(S/N|SIN\s+NUMERO|SIN\s+NÚMERO|\d+(?:\s*(?:[A-Z]\b|BIS\b))?)$", left_part, re.IGNORECASE)
        if end_num_match:
            numero = end_num_match.group(1)
            nombre_via = clean_part(left_part[:end_num_match.start()])
            piso = clean_part(right_part)
        else:
            # If it didn't end with a number, maybe the number is in the right part (e.g., Av. Diagonal, 640)
            # Search the whole rest string using standard search
            num_match = re.search(num_pattern, rest, re.IGNORECASE)
            if num_match:
                numero = num_match.group(1)
                nombre_via = clean_part(rest[:num_match.start()])
                piso = clean_part(rest[num_match.end():])
            else:
                nombre_via = clean_part(rest)
                numero = "S/N"
                piso = ""
    else:
        # Option B: No comma. Search the whole string for the number pattern.
        num_match = re.search(num_pattern, rest, re.IGNORECASE)
        if num_match:
            numero = num_match.group(1)
            nombre_via = clean_part(rest[:num_match.start()])
            piso = clean_part(rest[num_match.end():])
        else:
            # No number pattern found at all
            nombre_via = clean_part(rest)
            numero = "S/N"
            piso = ""

    # Standardize empty values to SAP-friendly defaults
    if not numero:
        numero = "S/N"
        
    return tipo_via, nombre_via, numero, piso
