import json
import pandas as pd
from typing import Dict, Any, List, Tuple

class SchemaEnforcer:
    """
    Enforces structure and constraints on pandas DataFrames using JSON-defined schemas.
    """
    def __init__(self, schema_dict: Dict[str, Any] | None = None):
        """
        - schema_dict: Dictionary containing schema configuration. E.g.:
          {
            "columns": {
              "CIF": {"required": True, "nullable": False, "type": "str"},
              "IBAN": {"required": True, "nullable": True, "type": "str"},
              "TELEFONO": {"required": False, "nullable": True, "type": "str"}
            }
          }
        """
        self.schema = schema_dict or {}
        self.columns_config = self.schema.get("columns", {})

    @classmethod
    def load_from_file(cls, filepath: str) -> "SchemaEnforcer":
        """
        Loads a schema from a JSON file path.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                schema_dict = json.load(f)
            return cls(schema_dict)
        except Exception as e:
            raise ValueError(f"Error cargando archivo de esquema JSON '{filepath}': {e}")

    def validate(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validates the DataFrame against the configured schema.
        Returns:
            Tuple[bool, List[str]]: (isValid, list_of_error_messages)
        """
        errors = []
        
        # 1. Check for required columns
        for col_name, config in self.columns_config.items():
            is_required = config.get("required", False)
            if is_required and col_name not in df.columns:
                errors.append(f"Error de esquema: Falta la columna obligatoria '{col_name}'.")
                
        # If required columns are missing, we cannot proceed with other checks on those columns
        for col_name in df.columns:
            if col_name not in self.columns_config:
                continue
                
            config = self.columns_config[col_name]
            nullable = config.get("nullable", True)
            expected_type = config.get("type", "str")
            
            # 2. Check for null values (only if nullable is False)
            if not nullable:
                # In pandas, a value is null if it is NaN, None, or empty string after stripping
                null_mask = df[col_name].isna() | (df[col_name].astype(str).str.strip() == "") | (df[col_name].astype(str) == "nan")
                null_indices = df.index[null_mask].tolist()
                
                if null_indices:
                    # Limit the list of index errors shown to avoid massive outputs
                    shown_indices = [idx + 1 for idx in null_indices[:10]] # 1-indexed row numbers
                    total_nulls = len(null_indices)
                    errors.append(
                        f"Error de restricciones: La columna '{col_name}' no permite nulos, "
                        f"pero se encontraron {total_nulls} celdas vacías (Filas: {shown_indices}"
                        f"{'...' if total_nulls > 10 else ''})."
                    )
            
            # 3. Check for basic types (best effort)
            if expected_type == "int":
                # Check if values can be parsed as integers (excluding nulls)
                non_null_series = df[col_name].dropna()
                non_null_series = non_null_series[non_null_series.astype(str).str.strip() != ""]
                for idx, val in non_null_series.items():
                    try:
                        int(float(val)) # handles '12.0' as well
                    except (ValueError, TypeError):
                        errors.append(f"Error de tipo: Fila {idx + 1}, columna '{col_name}' espera tipo entero, valor encontrado: '{val}'.")
                        break # report first type mismatch per column to avoid clutter
                        
            elif expected_type == "float":
                non_null_series = df[col_name].dropna()
                non_null_series = non_null_series[non_null_series.astype(str).str.strip() != ""]
                for idx, val in non_null_series.items():
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        errors.append(f"Error de tipo: Fila {idx + 1}, columna '{col_name}' espera tipo decimal, valor encontrado: '{val}'.")
                        break

        is_valid = len(errors) == 0
        return is_valid, errors
