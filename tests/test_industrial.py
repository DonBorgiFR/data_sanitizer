# -*- coding: utf-8 -*-
import pandas as pd
from sanitizer.rules.industrial import validate_industrial_rules
from sanitizer.core import SanitizerEngine

def test_validate_material_master():
    """
    Test validation rules for Material Master (MM).
    """
    data = {
        "MATERIAL": ["M001", "M002", "M003", "M004"],
        "MAT_TYPE": ["ROH", "FERT", "HALB", "ZXYZ"], # ZXYZ is invalid mat type
        "BASE_UOM": ["PC", "KG", "XXX", "PC"],      # XXX is invalid UOM
        "PRICE_CTRL": ["S", "V", "X", "S"],          # X is invalid price control
        "PRICE": ["120.50", "0.0", "15", "invalid"], # 0.0 should warn, invalid is error
        "NET_WEIGHT": ["1.5", "-0.5", "10", ""],
        "UNIT_OF_WEIGHT": ["KG", "G", "", ""]
    }
    df = pd.DataFrame(data)
    
    res_df, logs, kpis = validate_industrial_rules(df, "Material Master (MM)")
    
    # Check invalid mat type / invalid price control
    assert res_df.loc[3, "IND_VALID"] == False
    assert "Control de precio" in res_df.loc[2, "IND_ERROR"]
    assert "ZXYZ" in res_df.loc[3, "IND_ERROR"] or "no estándar" in res_df.loc[3, "IND_ERROR"]
    
    # Check price warnings/errors
    assert "Precio negativo" in res_df.loc[1, "IND_ERROR"] or "vacío" in res_df.loc[1, "IND_ERROR"] or "negativo" in res_df.loc[1, "IND_ERROR"] or "0.0" in res_df.loc[1, "IND_ERROR"]
    
    # UOM warning
    assert "XXX" in res_df.loc[2, "IND_ERROR"]
    
    # Negative weight error
    assert res_df.loc[1, "IND_VALID"] == False
    assert "Peso neto negativo" in res_df.loc[1, "IND_ERROR"]

def test_validate_bom():
    """
    Test validation rules for Bill of Materials (BOM).
    """
    # Create a BOM with a parent having more than 50 components to trigger complexity warning
    data = []
    # 51 components for parent P001
    for i in range(51):
        data.append({
            "MATERIAL_PARENT": "P001",
            "COMPONENT": f"C{i:03d}",
            "QUANTITY": "2.0",
            "UOM": "PC"
        })
    # Normal parent P002
    data.append({
        "MATERIAL_PARENT": "P002",
        "COMPONENT": "C999",
        "QUANTITY": "0.0", # Error: <= 0
        "UOM": "PC"
    })
    # High qty component
    data.append({
        "MATERIAL_PARENT": "P002",
        "COMPONENT": "C998",
        "QUANTITY": "9999", # Warning
        "UOM": "PC"
    })
    
    df = pd.DataFrame(data)
    res_df, logs, kpis = validate_industrial_rules(df, "Bill of Materials (BOM)")
    
    # Assert P001 records are marked as complex BOMs
    assert "BOM Compleja" in res_df.loc[0, "IND_ERROR"]
    assert kpis["complex_boms"] == 51
    
    # Assert quantity <= 0 is an error
    idx_err = len(data) - 2
    assert res_df.loc[idx_err, "IND_VALID"] == False
    assert "menor o igual a cero" in res_df.loc[idx_err, "IND_ERROR"]
    
    # Assert quantity 9999 is a warning
    idx_warn = len(data) - 1
    assert "atípica" in res_df.loc[idx_warn, "IND_ERROR"]

def test_validate_routing():
    """
    Test validation rules for Hojas de Ruta (Routing).
    """
    data = {
        "MATERIAL": ["M001", "M002", "M003", "M004"],
        "WORK_CENTER": ["WC01", "", "WC02", "WC03"],
        "SETUP_TIME": ["10", "5", "0", "-1"], # 0 is critical setup error, -1 is error
        "MACHINE_TIME": ["20", "15", "10", "10"],
        "LABOR_TIME": ["5", "5", "5", "5"]
    }
    df = pd.DataFrame(data)
    
    res_df, logs, kpis = validate_industrial_rules(df, "Rutas de Operaciones (Routing)")
    
    # Empty work center
    assert res_df.loc[1, "IND_VALID"] == False
    assert "WORK_CENTER" in res_df.loc[1, "IND_ERROR"]
    
    # Setup time is 0 (critical error)
    assert res_df.loc[2, "IND_VALID"] == False
    assert "SETUP_TIME crítico" in res_df.loc[2, "IND_ERROR"]
    assert kpis["zero_setup_routes"] == 1
    
    # Setup time is negative
    assert res_df.loc[3, "IND_VALID"] == False
    assert "preparación negativo" in res_df.loc[3, "IND_ERROR"]

def test_validate_cost_center():
    """
    Test validation rules for Centros de Coste (Cost Center).
    """
    data = {
        "COST_CENTER": ["CC01", "CC02", "CC03"],
        "CONTROLLING_AREA": ["1000", "1000", "1000"],
        "VALID_FROM": ["20260101", "2026.01.01", "invalid_date"],
        "VALID_TO": ["99991231", "31.12.9999", "20261231"],
        "PERSON_IN_CHARGE": ["Juan Perez", "", "Maria Gomez"],
        "FUNCTIONAL_AREA": ["Ventas", "Admin", ""],
        "HIERARCHY_GROUP": ["H01", "H01", ""]
    }
    df = pd.DataFrame(data)
    
    res_df, logs, kpis = validate_industrial_rules(df, "Centro de Coste (Cost Center)")
    
    # Row 0: Valid
    assert res_df.loc[0, "IND_VALID"] == True
    
    # Row 1: Missing person in charge
    assert res_df.loc[1, "IND_VALID"] == False
    assert "PERSON_IN_CHARGE" in res_df.loc[1, "IND_ERROR"]
    
    # Row 2: Invalid date format & missing functional area & hierarchy group
    assert "invalid_date" in res_df.loc[2, "IND_ERROR"]
    assert "FUNCTIONAL_AREA" in res_df.loc[2, "IND_ERROR"]
    assert "HIERARCHY_GROUP" in res_df.loc[2, "IND_ERROR"]

def test_engine_industrial_integration():
    """
    Test that SanitizerEngine correctly runs industrial rules when mapped.
    """
    data = {
        "COD_MAT": ["M001"],
        "DESC": ["Materia Prima A"],
        "TIPO": ["ROH"],
        "PRECIO": ["5.50"],
        "CONTROL": ["S"]
    }
    df = pd.DataFrame(data)
    
    column_types = {
        "MATERIAL": "text",
        "DESCRIPTION": "text",
        "MAT_TYPE": "text",
        "PRICE": "text",
        "PRICE_CTRL": "text"
    }
    
    # Schema mappings
    mapping = {
        "COD_MAT": "MATERIAL",
        "DESC": "DESCRIPTION",
        "TIPO": "MAT_TYPE",
        "PRECIO": "PRICE",
        "CONTROL": "PRICE_CTRL"
    }
    
    from sanitizer.mapping import SchemaMapper
    mapper = SchemaMapper(column_mapping=mapping, required_target_fields=["MATERIAL"])
    
    engine = SanitizerEngine(column_types=column_types, mapper=mapper)
    result = engine.sanitize(df, sap_template="Material Master (MM)")
    sanitized_df = result.df
    
    # Sanitized df should contain IND_VALID and IND_ERROR columns
    assert "IND_VALID" in sanitized_df.columns
    assert "IND_ERROR" in sanitized_df.columns
    assert sanitized_df.loc[0, "IND_VALID"] == True


def test_standard_cost_calculation():
    """
    Test standard cost calculation logic using BOM, Routing, and Material Master.
    """
    from sanitizer.costing import calculate_standard_cost
    
    bom_data = {
        "MATERIAL_PARENT": ["M001", "M001"],
        "COMPONENT": ["C001", "C002"],
        "QUANTITY": ["2.0", "1.5"],
        "UOM": ["PC", "KG"]
    }
    bom_df = pd.DataFrame(bom_data)
    
    routing_data = {
        "MATERIAL": ["M001"],
        "WORK_CENTER": ["WC01"],
        "SETUP_TIME": ["0.1"],
        "MACHINE_TIME": ["0.2"],
        "LABOR_TIME": ["0.3"]
    }
    routing_df = pd.DataFrame(routing_data)
    
    mm_data = {
        "MATERIAL": ["C001", "C002", "M001"],
        "PRICE": ["10.0", "20.0", "55.0"]
    }
    mm_df = pd.DataFrame(mm_data)
    
    cost_df, logs, method_info = calculate_standard_cost(
        bom_df=bom_df,
        routing_df=routing_df,
        mm_df=mm_df,
        default_rate=10.0
    )
    
    # Expected BOM Cost = 2 * 10.0 + 1.5 * 20.0 = 50.0
    # Expected Routing Cost = (0.1 + 0.2 + 0.3) * 10.0 = 6.0
    # Total Calculated Cost = 56.0
    # Loaded Cost = 55.0
    # Deviation Abs = 1.0
    # Deviation Pct = 1.0 / 56.0 * 100 = 1.785%
    
    m001_row = cost_df[cost_df["MATERIAL"] == "M001"].iloc[0]
    assert abs(m001_row["COST_BOM"] - 50.0) < 0.001
    assert abs(m001_row["COST_ROUTING"] - 6.0) < 0.001
    assert abs(m001_row["COST_TOTAL_CALC"] - 56.0) < 0.001
    assert abs(m001_row["COST_LOADED"] - 55.0) < 0.001
    assert abs(m001_row["DEVIATION_ABS"] - 1.0) < 0.001
    assert abs(m001_row["DEVIATION_PCT"] - 1.7857) < 0.01
    assert method_info == "default_rate"


def test_cost_deviation_detection():
    """
    Test severity classification of cost deviations.
    """
    from sanitizer.costing import detect_cost_deviations
    
    cost_data = {
        "MATERIAL": ["M001", "M002", "M003"],
        "COST_BOM": [50.0, 50.0, 50.0],
        "COST_ROUTING": [6.0, 6.0, 6.0],
        "COST_TOTAL_CALC": [56.0, 56.0, 56.0],
        "COST_LOADED": [55.0, 62.0, 100.0], # 1.78% dev, 10.7% dev, 78.5% dev
        "DEVIATION_ABS": [1.0, 6.0, 44.0],
        "DEVIATION_PCT": [1.78, 10.71, 78.57]
    }
    cost_df = pd.DataFrame(cost_data)
    
    res_df, logs, kpis = detect_cost_deviations(cost_df, tolerance_pct=5.0)
    
    assert res_df.loc[0, "DEV_STATUS"] == "OK"
    assert res_df.loc[1, "DEV_STATUS"] == "WARNING" # between 5% and 15%
    assert res_df.loc[2, "DEV_STATUS"] == "ERROR"   # > 15%
    
    assert res_df.loc[0, "DEV_DIRECTION"] == "undervalued" # calculated (56) > loaded (55)
    assert res_df.loc[1, "DEV_DIRECTION"] == "overvalued"  # calculated (56) < loaded (62)
    
    assert kpis["cost_deviations_ok"] == 1
    assert kpis["cost_deviations_warning"] == 1
    assert kpis["cost_deviations_error"] == 1


def test_margin_impact_estimation():
    """
    Test margin impact calculation metrics.
    """
    from sanitizer.costing import estimate_margin_impact
    
    cost_data = {
        "MATERIAL": ["M001", "M002", "M003"],
        "COST_TOTAL_CALC": [56.0, 56.0, 56.0],
        "COST_LOADED": [55.0, 62.0, 56.0],
        "DEVIATION_ABS": [1.0, 6.0, 0.0],
        "DEVIATION_PCT": [1.78, 10.71, 0.0]
    }
    cost_df = pd.DataFrame(cost_data)
    
    impact = estimate_margin_impact(cost_df)
    
    # Overvaluation (M002): 6.0
    # Undervaluation (M001): 1.0
    # Materials with deviation: 2 of 3 (66.67%)
    assert impact["total_overvaluation"] == 6.0
    assert impact["total_undervaluation"] == 1.0
    assert impact["materials_with_deviation"] == 2
    assert impact["materials_total"] == 3
    assert impact["pct_with_deviation"] == 66.67


def test_negative_stock_detection():
    """
    Test detection of negative stocks in restricted/blocked/quality stock columns.
    """
    from sanitizer.inventory import detect_negative_stocks
    
    data = {
        "MATERIAL": ["M001", "M002", "M003", "M004"],
        "UNRESTRICTED_STOCK": ["100.5", "-5.0", "50", "0"],
        "BLOCKED_STOCK": ["0", "0", "-2,5", "10"],
        "QUALITY_STOCK": ["0", "0", "0", "0"]
    }
    df = pd.DataFrame(data)
    
    neg_df, logs = detect_negative_stocks(df)
    
    # Negative stocks should be detected on M002 (-5.0 unrestricted) and M003 (-2,5 blocked)
    assert len(neg_df) == 2
    assert set(neg_df["MATERIAL"]) == {"M002", "M003"}


def test_obsolete_material_detection():
    """
    Test obsolete materials check based on inactive months.
    """
    from sanitizer.inventory import detect_obsolete_materials
    from datetime import datetime, timedelta
    
    now = datetime.now()
    date_recent = (now - timedelta(days=30)).strftime("%d.%m.%Y")
    date_old = (now - timedelta(days=800)).strftime("%Y%m%d") # > 24 months
    
    data = {
        "MATERIAL": ["M001", "M002"],
        "LAST_MOVEMENT_DATE": [date_recent, date_old]
    }
    df = pd.DataFrame(data)
    
    obs_df, logs = detect_obsolete_materials(df, months=24)
    
    assert len(obs_df) == 1
    assert obs_df.iloc[0]["MATERIAL"] == "M002"
    assert obs_df.iloc[0]["MONTHS_INACTIVE"] >= 26


def test_price_discrepancy_detection():
    """
    Test standard vs moving average price discrepancies check.
    """
    from sanitizer.inventory import detect_price_discrepancies
    
    data = {
        "MATERIAL": ["M001", "M002", "M003"],
        "STANDARD_PRICE": ["100.0", "100.0", "100.0"],
        "MOVING_AVG_PRICE": ["100.0", "85.0", "70.0"] # 0% dev, 15% dev, 30% dev
    }
    df = pd.DataFrame(data)
    
    disc_df, logs, kpis = detect_price_discrepancies(df, threshold_pct=10.0)
    
    # Should flag M002 (WARNING, 15%) and M003 (ERROR, 30%)
    assert len(disc_df) == 2
    assert set(disc_df["MATERIAL"]) == {"M002", "M003"}
    assert kpis["ok"] == 1
    assert kpis["warning"] == 1
    assert kpis["error"] == 1


def test_abc_classification():
    """
    Test ABC classification logic by cumulative total value.
    """
    from sanitizer.inventory import classify_abc
    
    data = {
        "MATERIAL": ["M01", "M02", "M03", "M04", "M05"],
        "TOTAL_VALUE": ["800.0", "150.0", "40.0", "8.0", "2.0"] # Total = 1000
    }
    df = pd.DataFrame(data)
    
    res_df, summary = classify_abc(df)
    
    # Cumulative percentages:
    # M01: 800 (80.0%) -> Class A
    # M02: 950 (95.0%) -> Class B
    # M03: 990 (99.0%) -> Class C
    # M04: 998 (99.8%) -> Class C
    # M05: 1000 (100.0%) -> Class C
    
    # Since we sorted during ABC classification, look up by material code
    m01 = res_df[res_df["MATERIAL"] == "M01"].iloc[0]
    m02 = res_df[res_df["MATERIAL"] == "M02"].iloc[0]
    m03 = res_df[res_df["MATERIAL"] == "M03"].iloc[0]
    
    assert m01["ABC_CLASS"] == "A"
    assert m02["ABC_CLASS"] == "B"
    assert m03["ABC_CLASS"] == "C"
    
    assert summary["A"]["count"] == 1
    assert summary["B"]["count"] == 1
    assert summary["C"]["count"] == 3

