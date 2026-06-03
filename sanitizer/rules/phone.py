import re

def clean_phone(value):
    """
    Cleans phone numbers:
    - Removes spaces, hyphens, brackets, dots, slashes.
    - Preserves leading '+' or digits.
    - If it starts with '00', replaces it with '+' (standard international prefix notation).
    """
    if not value or value == "-":
        return ""
        
    val_str = str(value).strip()
    
    # Replace double zero prefix with +
    if val_str.startswith("00"):
        val_str = "+" + val_str[2:]
        
    # Keep only digits and '+'
    cleaned = re.sub(r"[^0-9+]", "", val_str)
    return cleaned

def normalize_phone(phone, default_country_code="+34"):
    """
    Normalizes a phone number to an E.164-like standard format.
    - If the number doesn't have an international prefix (does not start with '+'),
      and matches the national pattern of the default country (e.g. 9 digits for Spain),
      it prepends the default_country_code.
    """
    cleaned = clean_phone(phone)
    
    if not cleaned:
        return "-"
        
    # Guess prefix for Spain if no '+' is present and it is a standard 9-digit number
    if not cleaned.startswith("+"):
        if default_country_code == "+34" and len(cleaned) == 9 and cleaned[0] in "6789":
            return f"+34{cleaned}"
        else:
            # For other cases where prefix is missing, we prepend the default code as fallback
            return f"{default_country_code}{cleaned}"
            
    return cleaned
