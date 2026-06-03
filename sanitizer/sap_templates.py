# -*- coding: utf-8 -*-
"""
SAP S/4HANA Migration Cockpit templates definition and helper functions.
"""

SAP_TEMPLATES = {
    "Business Partner (BP)": {
        "description": "Plantilla de Business Partner (Clientes y Proveedores) para SAP S/4HANA",
        "columns": {
            "PARTNER_ID": {
                "type": "text",
                "length": 10,
                "required": True,
                "description": "ID del BP / Deudor / Acreedor (numérico o alfanumérico)"
            },
            "NAME": {
                "type": "text",
                "length": 80,
                "required": True,
                "description": "Nombre de la empresa o persona física"
            },
            "TAX_ID": {
                "type": "tax_id",
                "length": 20,
                "required": True,
                "description": "Identificador Fiscal (NIF, CIF, NIE) en España"
            },
            "IBAN": {
                "type": "iban",
                "length": 34,
                "required": False,
                "description": "Número de Cuenta Bancaria en formato IBAN"
            },
            "BIC": {
                "type": "bic",
                "length": 11,
                "required": False,
                "description": "Código BIC / SWIFT del Banco"
            },
            "TELEPHONE": {
                "type": "phone",
                "length": 30,
                "required": False,
                "description": "Número de teléfono en formato E.164"
            },
            "POSTAL_CODE": {
                "type": "postal_code",
                "length": 10,
                "required": True,
                "description": "Código Postal"
            },
            "PROVINCE": {
                "type": "province",
                "length": 35,
                "required": True,
                "description": "Provincia o Región"
            },
            "COUNTRY": {
                "type": "text",
                "length": 3,
                "required": True,
                "description": "Código de País ISO de 2 letras (ej. ES)"
            },
            "STREET": {
                "type": "address",
                "length": 60,
                "required": True,
                "description": "Calle / Vía de dirección"
            }
        }
    },
    "Material Master (MM)": {
        "description": "Plantilla de Material Master (Materiales y Repuestos) para SAP S/4HANA",
        "columns": {
            "MATERIAL": {
                "type": "text",
                "length": 40,
                "required": True,
                "description": "Número o Código de Material en SAP"
            },
            "DESCRIPTION": {
                "type": "text",
                "length": 40,
                "required": True,
                "description": "Descripción corta del material"
            },
            "MAT_TYPE": {
                "type": "text",
                "length": 4,
                "required": True,
                "description": "Tipo de Material (ej. ROH, HALB, FERT)"
            },
            "INDUSTRY_SECTOR": {
                "type": "text",
                "length": 1,
                "required": True,
                "description": "Sector industrial (ej. M para Mecánica, C para Química)"
            },
            "BASE_UOM": {
                "type": "text",
                "length": 3,
                "required": True,
                "description": "Unidad de Medida Base (ej. PC, KG, L)"
            },
            "MAT_GROUP": {
                "type": "text",
                "length": 9,
                "required": True,
                "description": "Grupo de Artículos / Materiales"
            },
            "NET_WEIGHT": {
                "type": "text",
                "length": 15,
                "required": False,
                "description": "Peso Neto del Material"
            },
            "UNIT_OF_WEIGHT": {
                "type": "text",
                "length": 3,
                "required": False,
                "description": "Unidad de Peso (ej. KG, G)"
            },
            "PRICE_CTRL": {
                "type": "text",
                "length": 1,
                "required": True,
                "description": "Control de precio (S=Estándar, V=Medio Variable)"
            },
            "PRICE": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Precio unitario o de valoración"
            }
        }
    },
    "Bill of Materials (BOM)": {
        "description": "Plantilla de Lista de Materiales (BOM - CS01/CS02) para SAP S/4HANA",
        "columns": {
            "MATERIAL_PARENT": {
                "type": "text",
                "length": 40,
                "required": True,
                "description": "Código de material padre (cabecera)"
            },
            "COMPONENT": {
                "type": "text",
                "length": 40,
                "required": True,
                "description": "Código de material componente (hijo)"
            },
            "QUANTITY": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Cantidad requerida del componente"
            },
            "UOM": {
                "type": "text",
                "length": 3,
                "required": True,
                "description": "Unidad de medida del componente (ej. PC, KG)"
            }
        }
    },
    "Rutas de Operaciones (Routing)": {
        "description": "Plantilla de Hojas de Ruta / Operaciones de Fabricación (CA01/CA02) para SAP S/4HANA",
        "columns": {
            "MATERIAL": {
                "type": "text",
                "length": 40,
                "required": True,
                "description": "Código de material asociado a la ruta"
            },
            "WORK_CENTER": {
                "type": "text",
                "length": 8,
                "required": True,
                "description": "Código del Puesto de Trabajo (Work Center)"
            },
            "OPERATION_NUMBER": {
                "type": "text",
                "length": 4,
                "required": True,
                "description": "Número de operación (ej. 0010, 0020)"
            },
            "SETUP_TIME": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Tiempo de preparación de máquina (Setup Time)"
            },
            "MACHINE_TIME": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Tiempo de ejecución de máquina (Machine Time)"
            },
            "LABOR_TIME": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Tiempo de mano de obra (Labor Time)"
            }
        }
    },
    "Centro de Coste (Cost Center)": {
        "description": "Plantilla de Centros de Coste (KS01) para SAP S/4HANA",
        "columns": {
            "COST_CENTER": {
                "type": "text",
                "length": 10,
                "required": True,
                "description": "Código identificador del Centro de Coste"
            },
            "CONTROLLING_AREA": {
                "type": "text",
                "length": 4,
                "required": True,
                "description": "Sociedad de Controlling (Controlling Area)"
            },
            "VALID_FROM": {
                "type": "text",
                "length": 10,
                "required": True,
                "description": "Inicio de validez del Centro de Coste"
            },
            "VALID_TO": {
                "type": "text",
                "length": 10,
                "required": True,
                "description": "Fin de validez del Centro de Coste"
            },
            "PERSON_IN_CHARGE": {
                "type": "text",
                "length": 20,
                "required": True,
                "description": "Responsable del centro de coste"
            },
            "FUNCTIONAL_AREA": {
                "type": "text",
                "length": 16,
                "required": True,
                "description": "Área funcional asociada (ej. Ventas, Admin)"
            },
            "HIERARCHY_GROUP": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Grupo de jerarquía estándar de CO"
            }
        }
    },
    "Inventario / Stock (MB52)": {
        "description": "Plantilla de Inventario y Stocks (MB52) para saneamiento previo a migración SAP S/4HANA",
        "columns": {
            "MATERIAL": {
                "type": "text",
                "length": 40,
                "required": True,
                "description": "Código de material en SAP"
            },
            "PLANT": {
                "type": "text",
                "length": 4,
                "required": True,
                "description": "Centro logístico / Planta (Plant)"
            },
            "STORAGE_LOCATION": {
                "type": "text",
                "length": 4,
                "required": False,
                "description": "Almacén (Storage Location)"
            },
            "UNRESTRICTED_STOCK": {
                "type": "text",
                "length": 15,
                "required": True,
                "description": "Stock de libre utilización"
            },
            "BLOCKED_STOCK": {
                "type": "text",
                "length": 15,
                "required": False,
                "description": "Stock bloqueado"
            },
            "QUALITY_STOCK": {
                "type": "text",
                "length": 15,
                "required": False,
                "description": "Stock en control de calidad"
            },
            "BASE_UOM": {
                "type": "text",
                "length": 3,
                "required": True,
                "description": "Unidad de medida base (ej. PC, KG, L)"
            },
            "STANDARD_PRICE": {
                "type": "text",
                "length": 15,
                "required": False,
                "description": "Precio estándar del material"
            },
            "MOVING_AVG_PRICE": {
                "type": "text",
                "length": 15,
                "required": False,
                "description": "Precio medio variable (Moving Average Price)"
            },
            "TOTAL_VALUE": {
                "type": "text",
                "length": 15,
                "required": False,
                "description": "Valor total del stock (precio × cantidad)"
            },
            "LAST_MOVEMENT_DATE": {
                "type": "text",
                "length": 10,
                "required": False,
                "description": "Fecha del último movimiento de mercancías"
            },
            "PRICE_CTRL": {
                "type": "text",
                "length": 1,
                "required": True,
                "description": "Control de precio (S=Estándar, V=Medio Variable)"
            }
        }
    }
}

def get_sap_template_definition(name):
    """
    Returns the columns, types, lengths, requirements for a template.
    """
    return SAP_TEMPLATES.get(name)
