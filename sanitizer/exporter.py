# -*- coding: utf-8 -*-
"""
Exporter module to generate Excel staging workbooks for SAP S/4HANA Migration Cockpit (LTMC)
and to coordinate ZIP packaging of all cleansing outputs.
"""
import io
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sanitizer.sap_templates import SAP_TEMPLATES

def generate_sap_staging_excel(df: pd.DataFrame, template_name: str) -> bytes:
    """
    Generates an Excel workbook formatted for SAP S/4HANA Migration Cockpit (staging).
    
    If the template is an official SAP template, it:
    1. Filters and reorders columns to contain ONLY the official business fields.
    2. Writes three header rows:
       - Row 1: Technical Field Name (e.g. MATERIAL).
       - Row 2: Language Label/Description (e.g. Número de material).
       - Row 3: Format Metadata (e.g. C(40) * for required, C(40) for optional).
    3. Writes the data starting from Row 4.
    4. Applies clean visual styling (Segoe UI, header background, thin borders)
       and auto-adjusts column widths.
    
    If the template is custom or not found, it exports a clean Excel sheet with standard headers.
    """
    # 1. Fallback for custom or missing templates
    if not template_name or template_name not in SAP_TEMPLATES:
        output = io.BytesIO()
        # Clean control/technical columns from custom export as well to keep it neat
        clean_cols = [c for c in df.columns if not (c.endswith(("_VALID", "_ERROR")) or c in ("_CLEAN_LOG", "_CLEANSED"))]
        df_clean = df[clean_cols].copy()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_clean.to_excel(writer, sheet_name="Data", index=False)
            
        return output.getvalue()
        
    template_info = SAP_TEMPLATES[template_name]
    columns_def = template_info["columns"]
    
    # 2. Initialize workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Staging Data"
    
    # Ensure grid lines are visible even with fills applied
    ws.views.sheetView[0].showGridLines = True
    
    # 3. Define styles
    # Corporate SAP-like Dark Blue Palette
    fill_header = PatternFill(start_color="1E3C72", end_color="1E3C72", fill_type="solid")
    font_header = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
    align_header = Alignment(horizontal="left", vertical="center", wrap_text=True)
    border_header = Border(
        left=Side(style='thin', color='4F81BD'), 
        right=Side(style='thin', color='4F81BD'), 
        top=Side(style='thin', color='4F81BD'), 
        bottom=Side(style='thin', color='4F81BD')
    )
    
    font_data = Font(name="Segoe UI", size=10)
    align_data = Alignment(horizontal="left", vertical="center")
    border_data = Border(
        left=Side(style='thin', color='D9D9D9'), 
        right=Side(style='thin', color='D9D9D9'), 
        top=Side(style='thin', color='D9D9D9'), 
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # 4. Write Header Rows (1, 2, 3)
    official_columns = list(columns_def.keys())
    
    for col_idx, col_name in enumerate(official_columns, start=1):
        col_meta = columns_def[col_name]
        
        # Row 1: Technical Name
        cell_r1 = ws.cell(row=1, column=col_idx, value=col_name)
        
        # Row 2: Description
        cell_r2 = ws.cell(row=2, column=col_idx, value=col_meta.get("description", ""))
        
        # Row 3: Format Metadata
        length = col_meta.get("length")
        required = col_meta.get("required", False)
        req_indicator = " *" if required else ""
        meta_str = f"C({length}){req_indicator}" if length else f"C{req_indicator}"
        cell_r3 = ws.cell(row=3, column=col_idx, value=meta_str)
        
        # Apply header styling
        for cell in (cell_r1, cell_r2, cell_r3):
            cell.font = font_header
            cell.fill = fill_header
            cell.alignment = align_header
            cell.border = border_header
            
    # Set header row heights for premium spacing
    ws.row_dimensions[1].height = 25
    ws.row_dimensions[2].height = 25
    ws.row_dimensions[3].height = 20
    
    # 5. Write Data Rows (4 to N)
    for row_idx, df_idx in enumerate(df.index, start=4):
        ws.row_dimensions[row_idx].height = 20
        for col_idx, col_name in enumerate(official_columns, start=1):
            val = ""
            # Retrieve value if it exists in the clean dataframe
            if col_name in df.columns:
                raw_val = df.loc[df_idx, col_name]
                val = str(raw_val).strip() if pd.notna(raw_val) else ""
                
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_data
            cell.alignment = align_data
            cell.border = border_data
            
    # 6. Auto-fit Column Widths (based on content length)
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or '')
            # If multi-line (e.g. descriptions), find the longest line
            lines = val_str.split('\n')
            for line in lines:
                if len(line) > max_len:
                    max_len = len(line)
        # Apply width with safety margin
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    # Save to buffer and return bytes
    output = io.BytesIO()
    wb.save(output)
    return output.getvalue()
