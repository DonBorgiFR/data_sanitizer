import pandas as pd
from typing import Dict, Any, List

class DataDiagnostics:
    """
    Analyzes quality of raw data before sanitization and creates a health check report.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def run_health_check(self) -> Dict[str, Any]:
        """
        Executes diagnostic analysis.
        Returns:
            Dict containing health metrics.
        """
        total_rows = len(self.df)
        total_cols = len(self.df.columns)
        
        # 1. Null statistics per column
        column_metrics = {}
        for col in self.df.columns:
            # A cell is null if NaN or stripped value is empty
            null_count = self.df[col].isna().sum() + (self.df[col].astype(str).str.strip() == "").sum() + (self.df[col].astype(str) == "nan").sum()
            null_percentage = (null_count / total_rows * 100) if total_rows > 0 else 0
            
            # Infer data types based on pandas and contents
            inferred_type = self._infer_column_type(col)
            
            column_metrics[col] = {
                "null_count": int(null_count),
                "null_percentage": float(round(null_percentage, 2)),
                "inferred_type": inferred_type
            }
            
        # 2. Duplicate rows (exact matches)
        exact_duplicates = int(self.df.duplicated().sum())
        
        return {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "columns": column_metrics,
            "exact_duplicates": exact_duplicates
        }

    def _infer_column_type(self, column: str) -> str:
        """
        Infers the type of values in a column.
        """
        non_null = self.df[column].dropna()
        non_null = non_null[non_null.astype(str).str.strip() != ""]
        non_null = non_null[non_null.astype(str) != "nan"]
        
        if len(non_null) == 0:
            return "empty"
            
        # Try numeric (int)
        try:
            non_null.astype(float).apply(lambda x: x.is_integer()).all()
            # If all are integers, check if it's integer
            pd.to_numeric(non_null, errors="raise")
            # If it could contain leading zeros (like zip codes or phone numbers), it's treated as numeric_str
            # But let's check if they look like simple integers
            if any(val.startswith("0") and len(val) > 1 for val in non_null.astype(str)):
                return "numeric_str (leads 0)"
            return "integer"
        except (ValueError, TypeError, OverflowError):
            pass
            
        # Try numeric (float)
        try:
            pd.to_numeric(non_null, errors="raise")
            return "decimal"
        except (ValueError, TypeError):
            pass
            
        # Try datetime
        try:
            pd.to_datetime(non_null, errors="raise", format="mixed")
            return "datetime"
        except (ValueError, TypeError):
            pass
            
        return "text"

    def format_report(self, report: Dict[str, Any]) -> str:
        """
        Formats the health check dictionary as a human-readable text report.
        """
        lines = []
        lines.append("=" * 60)
        lines.append("                INFORME DE DIAGNÓSTICO DE SALUD")
        lines.append("=" * 60)
        lines.append(f"Total registros: {report['total_rows']}")
        lines.append(f"Total columnas:  {report['total_columns']}")
        lines.append(f"Registros duplicados exactos: {report['exact_duplicates']}")
        lines.append("-" * 60)
        lines.append(f"{'Columna':<20} | {'Tipo Inferido':<20} | {'Vacíos (%)':<12}")
        lines.append("-" * 60)
        
        for col, metrics in report["columns"].items():
            col_trunc = col[:20]
            lines.append(
                f"{col_trunc:<20} | "
                f"{metrics['inferred_type']:<20} | "
                f"{metrics['null_count']} ({metrics['null_percentage']}%)"
            )
            
        lines.append("=" * 60)
        return "\n".join(lines)
