import re

def clean_tax_id(value):
    """
    Cleans a Spanish Tax ID (NIF/CIF/NIE) by:
    - Removing dots, hyphens, spaces, and other non-alphanumeric chars
    - Converting to uppercase
    """
    if not value or value == "-":
        return ""
    cleaned = re.sub(r"[^a-zA-Z0-9]", "", str(value))
    return cleaned.upper()

def validate_tax_id(tax_id):
    """
    Validates a Spanish NIF, NIE, or CIF.
    Returns: (is_valid, cleaned_id, error_message)
    """
    cleaned = clean_tax_id(tax_id)
    
    if not cleaned:
        return False, "-", "Valor vacío o no válido"
        
    if len(cleaned) != 9:
        return False, cleaned, f"Longitud incorrecta: {len(cleaned)} caracteres (deben ser 9)"

    # Identify type
    first_char = cleaned[0]
    last_char = cleaned[-1]

    # Case 1: NIE (Starts with X, Y, Z)
    if first_char in ("X", "Y", "Z"):
        # Replace prefix with numeric representation
        prefix_map = {"X": "0", "Y": "1", "Z": "2"}
        numeric_nie = prefix_map[first_char] + cleaned[1:]
        
        # Now NIE behaves exactly like NIF (8 digits + 1 letter)
        if not numeric_nie[:-1].isdigit():
            return False, cleaned, "NIE con caracteres no numéricos en la parte central"
            
        calculated_letter = _calculate_nif_letter(int(numeric_nie[:-1]))
        if calculated_letter != last_char:
            return False, cleaned, f"Dígito de control incorrecto. Esperado '{calculated_letter}', recibido '{last_char}'"
        return True, cleaned, ""

    # Case 2: Standard NIF/DNI (Starts with a digit, 8 digits + 1 letter)
    elif first_char.isdigit():
        if not cleaned[:-1].isdigit():
            return False, cleaned, "NIF con caracteres no numéricos en la parte central"
            
        calculated_letter = _calculate_nif_letter(int(cleaned[:-1]))
        if calculated_letter != last_char:
            return False, cleaned, f"Dígito de control incorrecto. Esperado '{calculated_letter}', recibido '{last_char}'"
        return True, cleaned, ""

    # Case 3: CIF (Starts with a letter A-H, J, N, P, Q, R, S, U, V, W, 7 digits + 1 control char)
    elif first_char in "ABCDEFGHJNPRSUVW":
        cif_digits = cleaned[1:8]
        if not cif_digits.isdigit():
            return False, cleaned, "CIF con caracteres no numéricos en la parte central"
            
        # Sum of even positions (indices 2, 4, 6 of the 0-indexed cleaned string)
        even_sum = int(cleaned[2]) + int(cleaned[4]) + int(cleaned[6])
        
        # Sum of odd positions (indices 1, 3, 5, 7), multiplied by 2, sum digits of result
        odd_sum = 0
        for i in (1, 3, 5, 7):
            val = int(cleaned[i]) * 2
            odd_sum += (val // 10) + (val % 10)
            
        total_sum = even_sum + odd_sum
        control_val = (10 - (total_sum % 10)) % 10
        
        # Mapping to letters: 1=A, 2=B, 3=C, 4=D, 5=E, 6=F, 7=G, 8=H, 9=I, 0=J
        letter_map = {
            1: "A", 2: "B", 3: "C", 4: "D", 5: "E",
            6: "F", 7: "G", 8: "H", 9: "I", 0: "J"
        }
        
        calculated_digit = str(control_val)
        calculated_letter = letter_map[control_val]
        
        # Determine allowed control types
        # P, Q, S, W: Control must be a letter
        # A, B, E, H: Control must be a digit
        # Others (C, D, F, G, J, N, V, R, U): Can be letter or digit
        if first_char in ("P", "Q", "S", "W"):
            if last_char != calculated_letter:
                return False, cleaned, f"Dígito de control de CIF debe ser la letra '{calculated_letter}'"
        elif first_char in ("A", "B", "E", "H"):
            if last_char != calculated_digit:
                return False, cleaned, f"Dígito de control de CIF debe ser el número '{calculated_digit}'"
        else:
            if last_char != calculated_digit and last_char != calculated_letter:
                return False, cleaned, f"Dígito de control de CIF incorrecto. Esperado '{calculated_digit}' o '{calculated_letter}'"
                
        return True, cleaned, ""

    else:
        return False, cleaned, f"Tipo de Tax ID no identificado o prefijo '{first_char}' inválido"

def _calculate_nif_letter(number):
    return "TRWAGMYFPDXBNJZSQVHLCKE"[number % 23]
