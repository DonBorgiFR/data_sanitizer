# -*- coding: utf-8 -*-
"""
Generates the HTML Data Migration Readiness Report for SAP S/4HANA.
"""

import pandas as pd
import json
from datetime import datetime
import html

def generate_readiness_report(
    df: pd.DataFrame,
    column_types: dict,
    duplicates: list | None = None,
    costing_results: dict | None = None,
    inventory_results: dict | None = None,
    kpis: dict | None = None,
    rejected_df: pd.DataFrame | None = None,
) -> str:
    """
    Generates a premium HTML report documenting data quality and SAP readiness.
    """
    # 1. Total records calculation
    rejected_count = len(rejected_df) if rejected_df is not None else 0
    valid_count = len(df)
    total_records = valid_count + rejected_count
    
    # 2. Duplicate groups
    duplicate_groups = duplicates if duplicates is not None else []
    
    # 3. Calculate business impact KPIs
    kpis = kpis if kpis is not None else {}
    
    total_fix_events = (
        kpis.get("tax_id_fixes", 0) +
        kpis.get("postal_code_fixes", 0) +
        kpis.get("iban_fixes", 0) +
        kpis.get("province_fixes", 0) +
        kpis.get("bic_fixes", 0) +
        kpis.get("address_fixes", 0) +
        kpis.get("phone_fixes", 0) +
        kpis.get("duplicates_merged", 0)
    )
    
    # NOTA: La función asume que el procesamiento finalizó sin abortar, ya que recibe DataFrames resultantes. No existe una señal de aborto explícita en esta etapa.
    if total_fix_events > 0:
        horas_ahorradas = round((
            kpis.get("tax_id_fixes", 0) * 10 +
            kpis.get("postal_code_fixes", 0) * 5 +
            kpis.get("iban_fixes", 0) * 15 +
            kpis.get("province_fixes", 0) * 5 +
            kpis.get("bic_fixes", 0) * 5 +
            kpis.get("address_fixes", 0) * 10 +
            kpis.get("phone_fixes", 0) * 2 +
            kpis.get("duplicates_merged", 0) * 20
        ) / 60, 1)
        nota_basal = False
    elif total_records > 0:
        horas_ahorradas = round(total_records * 0.02, 1)
        nota_basal = True
    else:
        horas_ahorradas = 0.0
        nota_basal = False

    riesgo_evitado = (kpis.get("iban_errors", 0) + kpis.get("iban_fixes", 0)) * 100
    
    ready_to_load_pct = round((valid_count / total_records) * 100, 1) if total_records > 0 else 0.0

    escaped_horas = html.escape(f"{horas_ahorradas:.1f}")
    escaped_riesgo = html.escape(f"{riesgo_evitado:,.0f} €")
    escaped_ready_pct = html.escape(f"{ready_to_load_pct:.1f}%")
    escaped_validos = html.escape(str(valid_count))
    escaped_total = html.escape(str(total_records))
    
    if nota_basal:
        basal_note_html = '<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Estimación basal de ingesta y verificación manual (sin correcciones aplicadas)</div>'
    else:
        basal_note_html = '<div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Tiempo estimado de remediación manual directa evitado</div>'
    
    # Calculate KPIs
    sap_err_cols = [c for c in df.columns if c.endswith("_SAP_ERROR")]
    validity_cols = [c for c in df.columns if c.endswith("_VALID") and not c.endswith("_SAP_VALID")]
    
    # Total distinct validation issues
    total_critical_errors = 0
    total_sap_warnings = 0
    
    # Calculate stats per column
    column_stats = {}
    for col, col_type in column_types.items():
        if col not in df.columns:
            continue
            
        col_nulls = df[col].isna().sum() + (df[col] == "").sum() + (df[col] == "-").sum()
        
        # Check standard errors
        v_col = f"{col}_VALID"
        err_count = 0
        if v_col in df.columns:
            err_count = (df[v_col] == False).sum()
            total_critical_errors += err_count
            
        # Check SAP warnings/errors
        sap_err_col = f"{col}_SAP_ERROR"
        sap_warn_count = 0
        if sap_err_col in df.columns:
            sap_warn_count = (df[sap_err_col] != "").sum()
            total_sap_warnings += sap_warn_count
            
        column_stats[col] = {
            "type": col_type,
            "nulls": int(col_nulls),
            "null_pct": round((col_nulls / total_records) * 100, 1) if total_records > 0 else 0,
            "errors": int(err_count),
            "sap_warnings": int(sap_warn_count)
        }
        
    # Check if there are industrial validation columns
    has_industrial = "IND_VALID" in df.columns
    total_ind_errors = 0
    total_ind_warnings = 0
    ind_section_html = ""
    
    if has_industrial:
        total_ind_errors = (df["IND_VALID"] == False).sum()
        # Parse warnings/errors in IND_ERROR column
        for val in df["IND_ERROR"].dropna():
            if not val:
                continue
            parts = val.split(" | ")
            for part in parts:
                if part.startswith("ERROR:"):
                    pass
                elif part.startswith("WARN:"):
                    total_ind_warnings += 1
                    
        total_critical_errors += total_ind_errors
        total_sap_warnings += total_ind_warnings
        
        # Build industrial section HTML
        ind_issues = []
        for idx in df.index:
            err_str = df.loc[idx, "IND_ERROR"]
            if err_str:
                ident = df.iloc[idx, 0]
                for col_name in ["MATERIAL", "MATERIAL_PARENT", "COST_CENTER", "PARTNER_ID"]:
                    if col_name in df.columns:
                        ident = df.loc[idx, col_name]
                        break
                ind_issues.append({
                    "id": html.escape(str(ident)),
                    "issues": html.escape(str(err_str))
                })
        
        issues_rows = ""
        for issue in ind_issues[:30]:
            issues_rows += f"""
                    <tr>
                        <td><strong>{issue['id']}</strong></td>
                        <td>{issue['issues']}</td>
                    </tr>
            """
        if len(ind_issues) > 30:
            issues_rows += f"""
                    <tr>
                        <td colspan="2" style="text-align: center; color: var(--text-muted);">... y {len(ind_issues) - 30} incidencias más</td>
                    </tr>
            """
            
        if not issues_rows:
            issues_rows = """
                    <tr>
                        <td colspan="2" style="text-align: center; color: var(--color-success); font-weight: 600;">✔ Sin incidencias industriales detectadas</td>
                    </tr>
            """
 
        ind_section_html = f"""
        <div class="section-card">
            <h2 class="section-title">Incidencias de Lógica Industrial (MM/PP/CO)</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1rem;">
                Resultados detallados de validación de reglas de negocio, heurísticas de fabricación y controlling.
            </p>
            <table>
                <thead>
                    <tr>
                        <th style="width: 250px;">Identificador</th>
                        <th>Detalle de Incidencias</th>
                    </tr>
                </thead>
                <tbody>
                    {issues_rows}
                </tbody>
            </table>
        </div>
        """
        
    # Costing and Inventory sections calculations
    costing_section_html = ""
    if costing_results is not None:
        cost_df = costing_results.get("cost_df", pd.DataFrame())
        margin_impact = costing_results.get("margin_impact", {})
        
        if not cost_df.empty and "DEV_STATUS" in cost_df.columns:
            total_critical_errors += int((cost_df["DEV_STATUS"] == "ERROR").sum())
            total_sap_warnings += int((cost_df["DEV_STATUS"] == "WARNING").sum())
            
        cost_rows = ""
        if not cost_df.empty:
            sorted_cost_df = cost_df.sort_values(by="DEVIATION_PCT", ascending=False)
            for _, r in sorted_cost_df.head(20).iterrows():
                dev_pct = r['DEVIATION_PCT']
                status_class = "status-ok"
                if dev_pct > 15.0:
                    status_class = "status-err"
                elif dev_pct > 5.0:
                    status_class = "status-warn"
                
                cost_rows += f"""
                    <tr>
                        <td><strong>{html.escape(str(r['MATERIAL']))}</strong></td>
                        <td>{r['COST_BOM']:.2f} €</td>
                        <td>{r['COST_ROUTING']:.2f} €</td>
                        <td>{r['COST_TOTAL_CALC']:.2f} €</td>
                        <td>{r['COST_LOADED']:.2f} €</td>
                        <td><span class="{status_class}">{r['DEVIATION_ABS']:.2f} € ({dev_pct:.1f}%)</span></td>
                    </tr>
                """
        else:
            cost_rows = "<tr><td colspan='6' style='text-align: center;'>No se calcularon costes.</td></tr>"

        costing_section_html = f"""
        <div class="section-card">
            <h2 class="section-title">Análisis de Costes Estándar (Product Costing)</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1.5rem;">
                Comparativa entre el coste estándar calculado simuladamente (BOM + Hojas de ruta) y el coste cargado en el maestro SAP.
            </p>
            <div class="kpis-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 1.5rem; gap: 1rem;">
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Materiales Analizados</span>
                    <span class="kpi-value" style="font-size: 1.75rem;">{margin_impact.get('materials_total', 0)}</span>
                </div>
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Con Desviación</span>
                    <span class="kpi-value" style="font-size: 1.75rem;">{margin_impact.get('materials_with_deviation', 0)} ({margin_impact.get('pct_with_deviation', 0):.1f}%)</span>
                </div>
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Sobrevaloración Total</span>
                    <span class="kpi-value kpi-errors" style="font-size: 1.75rem;">{margin_impact.get('total_overvaluation', 0.0):,.2f} €</span>
                </div>
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Subvaloración Total</span>
                    <span class="kpi-value kpi-warnings" style="font-size: 1.75rem;">{margin_impact.get('total_undervaluation', 0.0):,.2f} €</span>
                </div>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>Material</th>
                        <th>Coste BOM</th>
                        <th>Coste Ruta</th>
                        <th>Coste Total Calc</th>
                        <th>Coste Maestro</th>
                        <th>Desviación</th>
                    </tr>
                </thead>
                <tbody>
                    {cost_rows}
                </tbody>
            </table>
        </div>
        """

    inventory_section_html = ""
    if inventory_results is not None:
        inv_kpis = inventory_results.get("kpis", {})
        neg_df = inventory_results.get("negative_stocks", pd.DataFrame())
        obs_df = inventory_results.get("obsolete_materials", pd.DataFrame())
        abc_summary = inventory_results.get("abc_classification", {})
        
        total_critical_errors += inv_kpis.get("negative_stocks", 0)
        total_sap_warnings += (inv_kpis.get("obsolete_materials", 0) + inv_kpis.get("price_discrepancies", 0))
        
        pct_val_A = 0.0
        pct_val_B = 0.0
        pct_val_C = 0.0
        pct_items_A = 0.0
        pct_items_B = 0.0
        pct_items_C = 0.0
        
        if abc_summary and "warning" not in abc_summary:
            pct_val_A = abc_summary.get("A", {}).get("pct_value", 0.0)
            pct_val_B = abc_summary.get("B", {}).get("pct_value", 0.0)
            pct_val_C = abc_summary.get("C", {}).get("pct_value", 0.0)
            pct_items_A = abc_summary.get("A", {}).get("pct_items", 0.0)
            pct_items_B = abc_summary.get("B", {}).get("pct_items", 0.0)
            pct_items_C = abc_summary.get("C", {}).get("pct_items", 0.0)
            
        abc_chart_html = ""
        if abc_summary and "warning" not in abc_summary:
            abc_chart_html = f"""
            <div class="abc-chart-wrapper" style="margin-top: 1.5rem; margin-bottom: 1.5rem;">
                <h3 style="font-size: 1rem; margin-bottom: 0.75rem; font-weight: 600;">Distribución de Valor de Inventario (ABC)</h3>
                <svg width="100%" height="30" style="border-radius: 6px; background: var(--border-color); overflow: hidden;">
                    <!-- Segmento A -->
                    <rect x="0" y="0" width="{pct_val_A}%" height="30" fill="var(--accent-primary)"></rect>
                    <!-- Segmento B -->
                    <rect x="{pct_val_A}%" y="0" width="{pct_val_B}%" height="30" fill="var(--color-warning)"></rect>
                    <!-- Segmento C -->
                    <rect x="{pct_val_A + pct_val_B}%" y="0" width="{pct_val_C}%" height="30" fill="var(--text-muted)"></rect>
                </svg>
                <div style="display: flex; justify-content: space-between; margin-top: 0.5rem; font-size: 0.85rem;">
                    <span style="color: var(--accent-primary);">● Clase A: {pct_val_A:.1f}% del valor ({pct_items_A:.1f}% items)</span>
                    <span style="color: var(--color-warning);">● Clase B: {pct_val_B:.1f}% del valor ({pct_items_B:.1f}% items)</span>
                    <span style="color: var(--text-muted);">● Clase C: {pct_val_C:.1f}% del valor ({pct_items_C:.1f}% items)</span>
                </div>
            </div>
            """
            
        inv_issues_rows = ""
        if not neg_df.empty:
            for _, r in neg_df.head(10).iterrows():
                escaped_mat = html.escape(str(r['MATERIAL']))
                escaped_loc = html.escape(str(r.get('STORAGE_LOCATION', 'N/A')))
                escaped_stock = html.escape(str(r['UNRESTRICTED_STOCK']))
                inv_issues_rows += f"""
                    <tr>
                        <td><strong>{escaped_mat}</strong></td>
                        <td><span class="badge-version" style="background: rgba(239, 68, 68, 0.1); color: var(--color-danger); border-color: rgba(239, 68, 68, 0.2);">Stock Negativo</span></td>
                        <td>Almacén: {escaped_loc} - Stock: <span class="status-err">{escaped_stock}</span></td>
                    </tr>
                """
        if not obs_df.empty:
            sorted_obs_df = obs_df.sort_values(by="MONTHS_INACTIVE", ascending=False)
            for _, r in sorted_obs_df.head(10).iterrows():
                escaped_mat = html.escape(str(r['MATERIAL']))
                escaped_date = html.escape(str(r['LAST_MOVEMENT_DATE']))
                inv_issues_rows += f"""
                    <tr>
                        <td><strong>{escaped_mat}</strong></td>
                        <td><span class="badge-version" style="background: rgba(245, 158, 11, 0.1); color: var(--color-warning); border-color: rgba(245, 158, 11, 0.2);">Obsoleto</span></td>
                        <td>Inactivo durante <span class="status-warn">{int(r['MONTHS_INACTIVE'])} meses</span> (Últ. mov: {escaped_date})</td>
                    </tr>
                """
                
        if not inv_issues_rows:
            inv_issues_rows = "<tr><td colspan='3' style='text-align: center; color: var(--color-success); font-weight: 600;'>✔ No se detectaron stocks negativos ni materiales obsoletos</td></tr>"

        inventory_section_html = f"""
        <div class="section-card">
            <h2 class="section-title">Health Check de Inventario</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1.5rem;">
                Diagnóstico del estado de los stocks e identificación de materiales obsoletos o con discrepancias de valoración.
            </p>
            <div class="kpis-grid" style="grid-template-columns: repeat(4, 1fr); margin-bottom: 1.5rem; gap: 1rem;">
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Stocks Negativos</span>
                    <span class="kpi-value kpi-errors" style="font-size: 1.75rem;">{inv_kpis.get('negative_stocks', 0)}</span>
                </div>
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Materiales Obsoletos</span>
                    <span class="kpi-value kpi-warnings" style="font-size: 1.75rem;">{inv_kpis.get('obsolete_materials', 0)}</span>
                </div>
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Discrepancias de Precio</span>
                    <span class="kpi-value kpi-warnings" style="font-size: 1.75rem;">{inv_kpis.get('price_discrepancies', 0)}</span>
                </div>
                <div class="kpi-card" style="padding: 1rem;">
                    <span class="kpi-label">Conversiones de UoM</span>
                    <span class="kpi-value" style="font-size: 1.75rem; color: var(--accent-primary);">{inv_kpis.get('unit_conversions', 0)}</span>
                </div>
            </div>
            
            {abc_chart_html}
            
            <h3 style="font-size: 1rem; margin-bottom: 0.5rem; font-weight: 600; margin-top: 1.5rem;">Listado de Alertas de Inventario</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 200px;">Material</th>
                        <th style="width: 150px;">Tipo Alerta</th>
                        <th>Detalle de Incidencia</th>
                    </tr>
                </thead>
                <tbody>
                    {inv_issues_rows}
                </tbody>
            </table>
        </div>
        """

    # Global Readiness Score
    # Deduct penalty for missing fields and errors
    total_possible_points = total_records * max(1, len(column_types))
    if total_possible_points > 0:
        total_issues = total_critical_errors * 2 + total_sap_warnings
        score = max(0, min(100, round((1 - (total_issues / (total_possible_points * 2))) * 100, 1)))
    else:
        score = 100.0
        
    # Deduplication summary
    total_duplicates_detected = sum(len(group["matches"]) + 1 for group in duplicate_groups)

    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Migration Readiness Report - SAP S/4HANA</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --accent-primary: #38bdf8;
            --accent-secondary: #0ea5e9;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --color-success: #10b981;
            --color-warning: #f59e0b;
            --color-danger: #ef4444;
            --border-color: #334155;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }}
        
        body {{
            background-color: var(--bg-primary);
            color: var(--text-main);
            padding: 2rem;
            line-height: 1.5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .header-title h1 {{
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .header-title p {{
            color: var(--text-muted);
            margin-top: 0.25rem;
        }}
        
        .badge-version {{
            background: rgba(56, 189, 248, 0.1);
            color: var(--accent-primary);
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.85rem;
            border: 1px solid rgba(56, 189, 248, 0.2);
            font-weight: 600;
        }}
        
        .kpis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .kpi-card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            position: relative;
            overflow: hidden;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }}
        
        .kpi-card:hover {{
            transform: translateY(-2px);
            border-color: var(--accent-primary);
        }}
        
        .kpi-value {{
            font-size: 2.25rem;
            font-weight: 700;
            margin-top: 0.5rem;
            color: var(--text-main);
        }}
        
        .kpi-label {{
            font-size: 0.85rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .kpi-score {{
            color: var(--color-success);
        }}
        .kpi-errors {{
            color: var(--color-danger);
        }}
        .kpi-warnings {{
            color: var(--color-warning);
        }}
        
        .section-card {{
            background-color: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
        }}
        
        .section-title {{
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            border-left: 4px solid var(--accent-primary);
            padding-left: 0.75rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        
        th, td {{
            text-align: left;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid var(--border-color);
        }}
        
        th {{
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
        }}
        
        td {{
            font-size: 0.95rem;
        }}
        
        .badge-type {{
            background: rgba(148, 163, 184, 0.1);
            color: var(--text-muted);
            padding: 0.15rem 0.5rem;
            border-radius: 4px;
            font-size: 0.8rem;
        }}
        
        .status-ok {{
            color: var(--color-success);
            font-weight: 600;
        }}
        
        .status-warn {{
            color: var(--color-warning);
            font-weight: 600;
        }}
        
        .status-err {{
            color: var(--color-danger);
            font-weight: 600;
        }}
        
        .chart-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 1rem 0;
        }}
        
        .progress-ring-wrapper {{
            position: relative;
            width: 150px;
            height: 150px;
        }}
        
        .progress-ring-bg {{
            fill: none;
            stroke: var(--border-color);
            stroke-width: 12;
        }}
        
        .progress-ring-circle {{
            fill: none;
            stroke: var(--color-success);
            stroke-width: 12;
            stroke-linecap: round;
            transform: rotate(-90deg);
            transform-origin: 50% 50%;
            transition: stroke-dashoffset 0.35s;
        }}
        
        .progress-score-text {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 1.75rem;
            font-weight: 700;
        }}
        
        footer {{
            text-align: center;
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 3rem;
            padding-top: 1.5rem;
            border-top: 1px solid var(--border-color);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <h1>SAP S/4HANA Readiness Report</h1>
                <p>Generado el {datetime.now().strftime("%d/%m/%Y a las %H:%M")}</p>
            </div>
            <div>
                <span class="badge-version">DataSanitizer V4.0</span>
            </div>
        </header>
        
        <div class="kpis-grid">
            <div class="kpi-card" style="align-items: center; justify-content: center;">
                <div class="progress-ring-wrapper">
                    <svg width="150" height="150">
                        <circle class="progress-ring-bg" cx="75" cy="75" r="60"/>
                        <circle class="progress-ring-circle" id="progress-circle" cx="75" cy="75" r="60" stroke-dasharray="376.99" stroke-dashoffset="0"/>
                    </svg>
                    <div class="progress-score-text">{score}%</div>
                </div>
                <div class="kpi-label" style="margin-top: 0.75rem;">Nivel de Preparación</div>
            </div>
            
            <div class="kpi-card">
                <span class="kpi-label">Registros Procesados</span>
                <span class="kpi-value">{total_records}</span>
            </div>
            
            <div class="kpi-card">
                <span class="kpi-label">Errores Críticos</span>
                <span class="kpi-value kpi-errors">{total_critical_errors}</span>
            </div>
            
            <div class="kpi-card">
                <span class="kpi-label">Advertencias SAP</span>
                <span class="kpi-value kpi-warnings">{total_sap_warnings}</span>
            </div>
        </div>

        <!-- SECCIÓN DE IMPACTO Y VALOR DE NEGOCIO -->
        <div class="section-card" style="margin-bottom: 2rem; background-color: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 12px; padding: 2rem;">
            <h2 class="section-title" style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1.5rem; border-left: none; padding-left: 0;">Impacto y Valor de Negocio</h2>
            <div class="kpis-grid" style="grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); margin-bottom: 0; gap: 1.5rem;">
                <div class="kpi-card" style="background-color: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.5rem; display: flex; flex-direction: column; box-shadow: none;">
                    <span class="kpi-label" style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Trabajo Manual Ahorrado</span>
                    <span class="kpi-value" style="font-size: 2rem; font-weight: 700; margin-top: 0.5rem; color: var(--text-main);">{escaped_horas} h</span>
                    {basal_note_html}
                </div>
                <div class="kpi-card" style="background-color: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.5rem; display: flex; flex-direction: column; box-shadow: none;">
                    <span class="kpi-label" style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Riesgo Financiero Evitado</span>
                    <span class="kpi-value" style="font-size: 2rem; font-weight: 700; margin-top: 0.5rem; color: var(--text-main);">{escaped_riesgo}</span>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">Por corrección o bloqueo preventivo de IBANs no válidos</div>
                </div>
                <div class="kpi-card" style="background-color: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-color); border-radius: 8px; padding: 1.5rem; display: flex; flex-direction: column; box-shadow: none;">
                    <span class="kpi-label" style="font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em;">Tasa de Carga (Ready-to-Load)</span>
                    <span class="kpi-value" style="font-size: 2rem; font-weight: 700; margin-top: 0.5rem; color: var(--text-main);">{escaped_ready_pct}</span>
                    <div style="font-size: 0.75rem; color: var(--text-muted); margin-top: 0.5rem;">{escaped_validos} registros válidos de un total de {escaped_total} analizados</div>
                </div>
            </div>
            <p style="font-size: 0.8rem; color: var(--text-muted); margin-top: 1.25rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem; line-height: 1.4;">
                * <strong>Registros Válidos:</strong> Datos maestros saneados y listos para la importación en SAP S/4HANA.<br/>
                * <strong>Registros Rechazados:</strong> Registros con errores críticos insalvables (como NIF/IBAN erróneos) o campos obligatorios SAP ausentes.
            </p>
        </div>
        
        <div class="section-card">
            <h2 class="section-title">Diagnóstico por Columna</h2>
            <table>
                <thead>
                    <tr>
                        <th>Columna</th>
                        <th>Tipo Semántico</th>
                        <th>Nulos / Vacíos</th>
                        <th>Errores de Validación</th>
                        <th>Incidencias SAP</th>
                        <th>Estado</th>
                    </tr>
                </thead>
                <tbody>
                """
                
    for col, stats in column_stats.items():
        status_html = '<span class="status-ok">✔ Listo</span>'
        if stats["errors"] > 0:
            status_html = f'<span class="status-err">❌ {stats["errors"]} Errores</span>'
        elif stats["sap_warnings"] > 0:
            status_html = f'<span class="status-warn">⚠ {stats["sap_warnings"]} SAP</span>'
            
        escaped_col = html.escape(str(col))
        escaped_type = html.escape(str(stats["type"]))
        html_template += f"""
                    <tr>
                        <td><strong>{escaped_col}</strong></td>
                        <td><span class="badge-type">{escaped_type}</span></td>
                        <td>{stats["nulls"]} ({stats["null_pct"]}%)</td>
                        <td>{stats["errors"]}</td>
                        <td>{stats["sap_warnings"]}</td>
                        <td>{status_html}</td>
                    </tr>
        """
        
    html_template += f"""
                </tbody>
            </table>
        </div>
        
        {ind_section_html}
        
        {costing_section_html}
        
        {inventory_section_html}
        
        <div class="section-card">
            <h2 class="section-title">Resumen de Duplicados e Identidades</h2>
            <p style="color: var(--text-muted); font-size: 0.95rem; margin-bottom: 1rem;">
                Detección de identidades duplicadas y sospechosas basada en lógica difusa y coincidencia exacta de CIF.
            </p>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
                <div>
                    <h3 style="font-size: 1rem; margin-bottom: 0.5rem; font-weight: 600;">Grupos de duplicados detectados</h3>
                    <span class="kpi-value" style="font-size: 2.5rem; color: var(--accent-primary);">{len(duplicate_groups)}</span>
                </div>
                <div>
                    <h3 style="font-size: 1rem; margin-bottom: 0.5rem; font-weight: 600;">Total registros afectados</h3>
                    <span class="kpi-value" style="font-size: 2.5rem; color: var(--color-warning);">{total_duplicates_detected}</span>
                </div>
            </div>
        </div>
        
        <footer>
            <p>DataSanitizer es una herramienta inteligente para la migración limpia de datos a SAP S/4HANA.</p>
            <p style="font-size: 0.75rem; margin-top: 0.5rem; opacity: 0.7;"><strong>Nota de Staging:</strong> El archivo Excel exportado está estructurado para la preparación y staging de los datos, facilitando su validación previa. No pretende sustituir ni emular las plantillas oficiales XML/Spreadsheet descargadas directamente desde SAP S/4HANA Migration Cockpit (LTMC).</p>
        </footer>
    </div>
    
    <script>
        // Animar el círculo de progreso
        const score = {score};
        const circle = document.getElementById('progress-circle');
        const radius = circle.r.baseVal.value;
        const circumference = radius * 2 * Math.PI;
        
        circle.style.strokeDasharray = `${{circumference}} ${{circumference}}`;
        const offset = circumference - (score / 100) * circumference;
        circle.style.strokeDashoffset = offset;
        
        if (score < 50) {{
            circle.style.stroke = 'var(--color-danger)';
        }} else if (score < 85) {{
            circle.style.stroke = 'var(--color-warning)';
        }} else {{
            circle.style.stroke = 'var(--color-success)';
        }}
    </script>
</body>
</html>
"""
    return html_template
