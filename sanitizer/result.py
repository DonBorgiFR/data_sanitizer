from dataclasses import dataclass, field
import pandas as pd
from typing import List, Dict, Any, Optional

@dataclass
class SanitizerResult:
    """
    Typed structure representing the formal outcome of the SanitizerEngine's pipeline.
    """
    df: pd.DataFrame
    rejected_df: Optional[pd.DataFrame] = None
    duplicates: List[Dict[str, Any]] = field(default_factory=list)
    kpis: Dict[str, int] = field(default_factory=lambda: {
        "text": 0, "tax_id_fixes": 0, "tax_id_errors": 0, "iban_fixes": 0, "iban_errors": 0,
        "phone_fixes": 0, "postal_code_fixes": 0, "postal_code_errors": 0, "province_fixes": 0,
        "bic_fixes": 0, "bic_errors": 0, "address_fixes": 0,
        "industrial_errors": 0, "industrial_warnings": 0, "complex_boms": 0, "zero_setup_routes": 0,
        # Costing KPIs (Session 7)
        "cost_deviations_ok": 0, "cost_deviations_warning": 0, "cost_deviations_error": 0,
        "total_overvaluation": 0.0, "total_undervaluation": 0.0,
        # Inventory KPIs (Session 7)
        "negative_stocks": 0, "obsolete_materials": 0, "price_discrepancies": 0,
        "abc_a_count": 0, "abc_b_count": 0, "abc_c_count": 0, "unit_conversions": 0
    })
    metrics: Dict[str, Any] = field(default_factory=lambda: {
        "processed_rows": 0,
        "valid_rows": 0,
        "rejected_rows": 0,
        "rejection_rate": 0.0,
        "process_time_sec": 0.0
    })
    logs: List[Dict[str, str]] = field(default_factory=list)
    active_template: Optional[str] = None
    # Costing analysis results (Session 7)
    costing_results: Optional[Dict[str, Any]] = None
    # Inventory health check results (Session 7)
    inventory_results: Optional[Dict[str, Any]] = None

