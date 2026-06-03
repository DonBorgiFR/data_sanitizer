import re
from typing import Tuple

# Mapping of the first two digits of Spanish Postal Codes to their respective Province names (standardized uppercase)
PROVINCES_MAP = {
    "01": "ALAVA",
    "02": "ALBACETE",
    "03": "ALICANTE",
    "04": "ALMERIA",
    "05": "AVILA",
    "06": "BADAJOZ",
    "07": "BALEARES",
    "08": "BARCELONA",
    "09": "BURGOS",
    "10": "CACERES",
    "11": "CADIZ",
    "12": "CASTELLON",
    "13": "CIUDAD REAL",
    "14": "CORDOBA",
    "15": "A CORUÑA",
    "16": "CUENCA",
    "17": "GIRONA",
    "18": "GRANADA",
    "19": "GUADALAJARA",
    "20": "GIPUZKOA",
    "21": "HUELVA",
    "22": "HUESCA",
    "23": "JAEN",
    "24": "LEON",
    "25": "LLEIDA",
    "26": "LA RIOJA",
    "27": "LUGO",
    "28": "MADRID",
    "29": "MALAGA",
    "30": "MURCIA",
    "31": "NAVARRA",
    "32": "OURENSE",
    "33": "ASTURIAS",
    "34": "PALENCIA",
    "35": "LAS PALMAS",
    "36": "PONTEVEDRA",
    "37": "SALAMANCA",
    "38": "SANTA CRUZ DE TENERIFE",
    "39": "CANTABRIA",
    "40": "SEGOVIA",
    "41": "SEVILLA",
    "42": "SORIA",
    "43": "TARRAGONA",
    "44": "TERUEL",
    "45": "TOLEDO",
    "46": "VALENCIA",
    "47": "VALLADOLID",
    "48": "BIZKAIA",
    "49": "ZAMORA",
    "50": "ZARAGOZA",
    "51": "CEUTA",
    "52": "MELILLA",
}

def clean_postal_code(value) -> str:
    """
    Cleans a postal code value:
    - Removes non-numeric characters.
    - Pads with leading zeros if it is 4 digits long.
    """
    if not value or value == "-":
        return ""
    
    # Strip and extract only digits
    cleaned = re.sub(r"\D", "", str(value).strip())
    
    # Pad to 5 digits if it's 4 digits
    if len(cleaned) == 4:
        cleaned = "0" + cleaned
        
    return cleaned

def validate_postal_code(postal_code) -> Tuple[bool, str, str]:
    """
    Validates a Spanish postal code.
    Must be exactly 5 digits and within the range 01000 - 52999.
    Returns: (is_valid, cleaned_code, error_message)
    """
    cleaned = clean_postal_code(postal_code)
    
    if not cleaned:
        return False, "-", "Valor vacío o no válido"
        
    if len(cleaned) != 5:
        return False, cleaned, f"Longitud incorrecta: {len(cleaned)} dígitos (deben ser 5)"
        
    if not (1000 <= int(cleaned) <= 52999):
        return False, cleaned, "Código postal fuera del rango de España (01000 - 52999)"
        
    return True, cleaned, ""

def get_province_by_cp(postal_code: str) -> str | None:
    """
    Given a postal code, returns the corresponding standardized province name.
    If the postal code is invalid or has no mapping, returns None.
    """
    cleaned = clean_postal_code(postal_code)
    if len(cleaned) != 5:
        return None
    
    prefix = cleaned[:2]
    return PROVINCES_MAP.get(prefix)
