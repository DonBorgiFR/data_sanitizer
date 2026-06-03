# -*- coding: utf-8 -*-
from sanitizer.ui_components import render_help_center, MAP_TOOLTIPS

def test_help_center_imports():
    """
    Test that render_help_center can be successfully imported and has correct docstring.
    """
    assert render_help_center is not None
    assert "renderiza" in render_help_center.__doc__.lower() or "renders" in render_help_center.__doc__.lower()

def test_map_tooltips_content():
    """
    Test that MAP_TOOLTIPS has the expected keys and they are strings.
    """
    assert isinstance(MAP_TOOLTIPS, dict)
    assert "NAME" in MAP_TOOLTIPS
    assert "TAX_ID" in MAP_TOOLTIPS
    assert "IBAN" in MAP_TOOLTIPS
    assert isinstance(MAP_TOOLTIPS["NAME"], str)
    assert len(MAP_TOOLTIPS["NAME"]) > 0


def test_all_template_columns_have_tooltips():
    """
    Test that every column name defined in SAP_TEMPLATES has a tooltip in MAP_TOOLTIPS.
    """
    from sanitizer.sap_templates import SAP_TEMPLATES
    for template_name, template_info in SAP_TEMPLATES.items():
        for col_name in template_info["columns"]:
            assert col_name in MAP_TOOLTIPS, f"La columna '{col_name}' de la plantilla '{template_name}' no tiene tooltip en MAP_TOOLTIPS"
