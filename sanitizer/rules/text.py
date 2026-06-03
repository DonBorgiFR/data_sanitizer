import pandas as pd

def clean_text(value, uppercase=True):
    """
    Cleans general text:
    - Replaces nulls/empty values (NULL, N/A, NaN, empty string) with '-'
    - Collapses multiple whitespace characters into a single space
    - Strips leading and trailing whitespaces
    - Optionally converts to uppercase (default: True)
    """
    if pd.isna(value) or value is None:
        return "-"
    
    val_str = str(value).strip()
    
    # Check for common null representations
    if val_str.lower() in ("null", "n/a", "nan", ""):
        return "-"
    
    # Collapse spaces
    cleaned = " ".join(val_str.split())
    
    if uppercase:
        cleaned = cleaned.upper()
        
    return cleaned
