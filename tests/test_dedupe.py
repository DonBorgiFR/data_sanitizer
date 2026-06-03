import pandas as pd
from sanitizer.dedupe import calculate_similarity, find_duplicates, clean_legal_suffixes

def test_clean_legal_suffixes():
    assert clean_legal_suffixes("BODEGAS TORRES S.A.") == "BODEGAS TORRES"
    assert clean_legal_suffixes("FREIXENET, S.L.U.") == "FREIXENET"
    assert clean_legal_suffixes("CODORNIU SA") == "CODORNIU"
    assert clean_legal_suffixes("S.A. CONSTRUCTORA") == "S.A. CONSTRUCTORA" # S.A. at start shouldn't be stripped
    assert clean_legal_suffixes("BODEGA LIMITADA S.L.") == "BODEGA LIMITADA"
    assert clean_legal_suffixes("COMPAÑIA SOCIEDAD ANONIMA") == "COMPAÑIA"

def test_similarity_calculation():
    # Exact matches
    assert calculate_similarity("BODEGAS TORRES", "BODEGAS TORRES") == 100.0
    
    # Suffixes should be normalized out, so similarity is based on names
    assert calculate_similarity("BODEGAS TORRES S.A.", "BODEGAS TORRES") == 100.0
    
    # Slight spelling differences
    sim1 = calculate_similarity("BODEGAS TORRES S.A.", "BODEGA TORRES")
    assert sim1 > 70.0
    
    # Empty inputs
    assert calculate_similarity("", "SOMETHING") == 0.0

def test_find_duplicates():
    data = {
        "CLIENTE": [
            "BODEGAS TORRES S.A.",
            "BODEGA TORRES",
            "FREIXENET S.A.",
            "FREIXENET",
            "CODORNIU",
            "BODEGAS TORRES S.A."  # Duplicate exact
        ]
    }
    df = pd.DataFrame(data)
    
    # Run duplicate finder
    groups = find_duplicates(df, "CLIENTE", threshold=75.0)
    
    assert len(groups) >= 2  # Torres and Freixenet should form groups
    
    # Check Torres group
    torres_group = next(g for g in groups if "TORRES" in g["primary_value"])
    assert len(torres_group["primary_indices"]) == 2  # indices 0 and 5
    assert len(torres_group["matches"]) == 1
    assert torres_group["matches"][0]["value"] == "BODEGA TORRES"
    assert torres_group["matches"][0]["indices"] == [1]

def test_find_duplicates_tax_id():
    data = {
        "CLIENTE": [
            "BODEGAS TORRES",
            "TORRES BODEGAS SL",  # Name typo, same CIF
            "OTRO CLIENTE S.A.",
            "OTRO CLIENTE"
        ],
        "CIF": [
            "A08000001",
            "A08000001",
            "B28000002",
            "B28000002"
        ]
    }
    df = pd.DataFrame(data)
    
    groups = find_duplicates(df, "CLIENTE", tax_id_column="CIF", threshold=75.0)
    
    assert len(groups) == 2
    
    torres_group = next(g for g in groups if "TORRES" in g["primary_value"])
    assert len(torres_group["matches"]) == 1
    assert torres_group["matches"][0]["match_type"] == "tax_id"
    assert torres_group["matches"][0]["indices"] == [1]

def test_find_duplicates_blocking():
    data = {
        "CLIENTE": [
            "RAMON BILBAO S.A.",
            "RAMON BILBAO S.A.",  # Same name, different province -> should not be compared/matched
            "RAMON BILBAO S.A.",
        ],
        "CP": [
            "26200", # Block 26
            "28001", # Block 28
            "26201", # Block 26
        ]
    }
    df = pd.DataFrame(data)
    
    # When using blocking, row 0 and row 2 should be in block '26' and thus matched.
    # Row 1 is in block '28' and should NOT be matched since they are in different blocks.
    groups = find_duplicates(df, "CLIENTE", postal_code_column="CP", threshold=95.0, blocking_method="postal_code_2")
    
    assert len(groups) == 1
    group = groups[0]
    assert set(group["primary_indices"]) == {0, 2}
    assert len(group["matches"]) == 0
