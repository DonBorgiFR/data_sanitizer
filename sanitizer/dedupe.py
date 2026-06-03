import re
import pandas as pd

try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False

def clean_legal_suffixes(text):
    """
    Normalizes company names by temporarily removing common Spanish legal suffixes (S.A., S.L., etc.).
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Casing normalization and stripping
    text_upper = text.strip().upper()
    
    # Spanish legal suffixes: S.A., S.L., S.A.U., S.L.U., S.C., S.C.P., S.COOP., S.R.L.,
    # and their full text versions: SOCIEDAD ANONIMA, SOCIEDAD LIMITADA, etc.
    # We match them at the end of the text, optionally preceded by a comma, hyphen, slash or space.
    pattern = r'\b(S\s*\.?\s*A\s*\.?\s*U\s*\.?|S\s*\.?\s*L\s*\.?\s*U\s*\.?|S\s*\.?\s*A\s*\.?|S\s*\.?\s*L\s*\.?|S\s*\.?\s*C\s*\.?|S\s*\.?\s*C\s*\.?\s*P\s*\.?|S\s*\.?\s*COOP\s*\.?|S\s*\.?\s*R\s*\.?\s*L\s*\.?|SOCIEDAD\s+ANONIMA|SOCIEDAD\s+LIMITADA|SOCIEDAD\s+COOPERATIVA)\s*$'
    
    # Run the substitution
    cleaned = re.sub(pattern, "", text_upper)
    
    # Clean up trailing spaces, commas, dots, or hyphens that might be left over
    cleaned = re.sub(r'[\s,\.\-/]+$', '', cleaned)
    # Clean up leading spaces, commas, dots, or hyphens
    cleaned = re.sub(r'^[\s,\.\-/]+', '', cleaned)
    
    return cleaned.strip()

def levenshtein_distance(s1, s2):
    """Calcula la distancia de edición (Levenshtein) entre dos cadenas."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
        
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def calculate_similarity(s1, s2, clean_suffixes=True):
    """
    Computes a similarity score between 0 and 100 between two strings.
    Uses rapidfuzz if available, otherwise a pure Python Levenshtein fallback.
    If clean_suffixes is True, common Spanish legal suffixes are stripped beforehand.
    """
    if not s1 or not s2:
        return 0.0
        
    if clean_suffixes:
        s1_clean = clean_legal_suffixes(s1)
        s2_clean = clean_legal_suffixes(s2)
    else:
        s1_clean, s2_clean = s1.strip().upper(), s2.strip().upper()
        
    if not s1_clean or not s2_clean:
        return 0.0
    if s1_clean == s2_clean:
        return 100.0

    if HAS_RAPIDFUZZ:
        return fuzz.ratio(s1_clean, s2_clean)
    else:
        dist = levenshtein_distance(s1_clean, s2_clean)
        total_len = len(s1_clean) + len(s2_clean)
        return ((total_len - dist) / total_len) * 100.0 if total_len > 0 else 0.0

def find_duplicates(df, text_column, tax_id_column=None, postal_code_column=None, province_column=None, threshold=85.0, blocking_method="first_3_chars"):
    """
    Analyzes a DataFrame's text column and optional tax_id/postal_code/province columns
    to identify potential duplicate groups using configurable blocking keys for optimization.
    
    Returns a list of duplicate groups:
    [
      {
        "primary_value": "BODEGAS TORRES S.A.",
        "primary_indices": [0, 5],
        "matches": [
          {"value": "TORRES BODEGAS SL", "score": 100.0, "indices": [1], "match_type": "tax_id"},
          {"value": "BODEGA TORRES", "score": 92.5, "indices": [4], "match_type": "fuzzy"}
        ]
      }
    ]
    """
    if text_column not in df.columns:
        return []

    # 1. Group by Tax ID (CIF/NIF exact match) globally
    tax_id_matches = {} # rep_idx -> list of match dicts
    seen_by_tax_id = set()
    
    if tax_id_column and tax_id_column in df.columns:
        tax_id_groups = {}
        for idx, tax_val in df[tax_id_column].items():
            if pd.isna(tax_val) or str(tax_val).strip() in ("", "-", "nan", "NaN", "None"):
                continue
            
            clean_tax = str(tax_val).replace(" ", "").replace(".", "").replace("-", "").upper()
            if len(clean_tax) < 7:
                continue
                
            if clean_tax not in tax_id_groups:
                tax_id_groups[clean_tax] = []
            tax_id_groups[clean_tax].append(idx)

        # For each tax id group, select first as representative, mark others as duplicates
        for clean_tax, idx_list in tax_id_groups.items():
            if len(idx_list) > 1:
                rep_idx = idx_list[0]
                tax_id_matches[rep_idx] = []
                for dup_idx in idx_list[1:]:
                    seen_by_tax_id.add(dup_idx)
                    tax_id_matches[rep_idx].append({
                        "value": df.loc[dup_idx, text_column] if pd.notna(df.loc[dup_idx, text_column]) else "-",
                        "score": 100.0,
                        "indices": [dup_idx],
                        "match_type": "tax_id"
                    })

    # Active rows are those not marked as duplicates by Tax ID
    active_indices = [idx for idx in df.index if idx not in seen_by_tax_id]

    # 2. Partition active rows by Block Key
    blocks = {}
    method = str(blocking_method).lower() if blocking_method else "none"
    
    for idx in active_indices:
        val = df.loc[idx, text_column]
        if pd.isna(val) or str(val).strip() in ("", "-", "nan", "NaN", "None"):
            continue
            
        clean_name = clean_legal_suffixes(str(val))
        
        block_key = None
        if method == "none":
            block_key = "_all_"
        elif method == "first_char":
            block_key = clean_name[0] if clean_name else "_empty_"
        elif method == "first_3_chars":
            block_key = clean_name[:3] if len(clean_name) >= 3 else (clean_name if clean_name else "_empty_")
        elif method == "postal_code_2":
            if postal_code_column and postal_code_column in df.columns:
                cp_val = str(df.loc[idx, postal_code_column]).strip()
                if cp_val and cp_val not in ("", "-", "nan", "NaN", "None"):
                    cp_digits = "".join(filter(str.isdigit, cp_val))
                    if cp_digits:
                        cp_digits = cp_digits.zfill(5)
                        block_key = cp_digits[:2]
            if not block_key:
                # Fallback to first 3 chars if CP is invalid or missing
                block_key = clean_name[:3] if len(clean_name) >= 3 else (clean_name if clean_name else "_empty_")
        elif method == "province":
            if province_column and province_column in df.columns:
                prov_val = str(df.loc[idx, province_column]).strip().upper()
                if prov_val and prov_val not in ("", "-", "nan", "NaN", "None"):
                    block_key = prov_val
            if not block_key:
                # Fallback
                block_key = clean_name[:3] if len(clean_name) >= 3 else (clean_name if clean_name else "_empty_")
        else:
            # Fallback
            block_key = clean_name[:3] if len(clean_name) >= 3 else (clean_name if clean_name else "_empty_")

        if block_key not in blocks:
            blocks[block_key] = []
        blocks[block_key].append(idx)

    # 3. Process each block independently
    groups_dict = {}
    
    for block_key, block_indices in blocks.items():
        # Group by exact name within the block
        unique_names_in_block = {}
        for idx in block_indices:
            val = str(df.loc[idx, text_column]).strip()
            if val not in unique_names_in_block:
                unique_names_in_block[val] = []
            unique_names_in_block[val].append(idx)
            
        block_reps = []
        for name_val, idx_list in unique_names_in_block.items():
            rep_idx = idx_list[0]
            block_reps.append(rep_idx)
            
            # Initialize group structure
            groups_dict[rep_idx] = {
                "primary_value": name_val,
                "primary_indices": idx_list,
                "matches": []
            }
            
            # Add any Tax ID matches for this representative
            if rep_idx in tax_id_matches:
                groups_dict[rep_idx]["matches"].extend(tax_id_matches[rep_idx])

        # Pairwise fuzzy comparison within block representatives
        seen_fuzzy = set()
        for i, rep1 in enumerate(block_reps):
            if rep1 in seen_fuzzy:
                continue
                
            for rep2 in block_reps[i+1:]:
                if rep2 in seen_fuzzy:
                    continue
                    
                val1 = df.loc[rep1, text_column]
                val2 = df.loc[rep2, text_column]
                
                score = calculate_similarity(val1, val2, clean_suffixes=True)
                if score >= threshold:
                    seen_fuzzy.add(rep2)
                    
                    # Add rep2's exact indices as fuzzy matches
                    groups_dict[rep1]["matches"].append({
                        "value": val2,
                        "score": round(score, 2),
                        "indices": groups_dict[rep2]["primary_indices"],
                        "match_type": "fuzzy"
                    })
                    
                    # Transfer any existing matches (like tax_id matches or other fuzzy matches)
                    for match in groups_dict[rep2]["matches"]:
                        groups_dict[rep1]["matches"].append(match)
                        
                    # Remove rep2 from groups_dict
                    groups_dict.pop(rep2, None)
            
            seen_fuzzy.add(rep1)

    # 4. Build final duplicate groups (must have matches or len(primary_indices) > 1)
    duplicate_groups = []
    for rep_idx, group in groups_dict.items():
        if group["matches"] or len(group["primary_indices"]) > 1:
            duplicate_groups.append(group)

    return duplicate_groups
