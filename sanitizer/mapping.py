class SchemaMapper:
    """
    Handles translation and structural adjustment of schemas from legacy ERPs to target ERPs.
    """
    def __init__(self, column_mapping, required_target_fields=None, default_values=None):
        """
        - column_mapping: dict mapping {"Source Column": "Target Column"}
        - required_target_fields: list of target fields that MUST exist in the output
        - default_values: dict of {"Target Column": default_value} for missing or empty fields
        """
        self.column_mapping = column_mapping or {}
        self.required_target_fields = required_target_fields or []
        self.default_values = default_values or {}

    def map_dataframe(self, df, keep_unmapped=False):
        """
        Transforms a pandas DataFrame:
        1. Renames mapped columns.
        2. Drops unmapped columns if keep_unmapped is False.
        3. Adds required columns that are missing with their default values.
        """
        # Copy to avoid side-effects
        mapped_df = df.copy()

        # Rename columns
        mapped_df = mapped_df.rename(columns=self.column_mapping)

        # Separate mapped columns
        target_columns = list(self.column_mapping.values())

        if not keep_unmapped:
            # Filter DataFrame to keep only target columns
            # Ensure we only select columns that actually exist in the df now
            existing_targets = [col for col in target_columns if col in mapped_df.columns]
            mapped_df = mapped_df[existing_targets]

        # Add missing required fields
        for field in self.required_target_fields:
            if field not in mapped_df.columns:
                default_val = self.default_values.get(field, "-")
                mapped_df[field] = default_val

        # Fill missing values for required fields with defaults if value is empty/nan
        for field in self.required_target_fields:
            if field in mapped_df.columns:
                # Replace None or empty string or nan with defaults
                default_val = self.default_values.get(field, "-")
                mapped_df[field] = mapped_df[field].fillna(default_val)
                # Replace '-' if it's considered empty and we have a specific default
                if default_val != "-":
                    mapped_df[field] = mapped_df[field].replace("-", default_val)

        return mapped_df
