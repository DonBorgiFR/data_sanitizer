# -*- coding: utf-8 -*-
"""
Certificación de Rendimiento y Estrés de DataSanitizer.
Contiene benchmarks para ingesta/limpieza (10,000 registros) y deduplicación (2,000 registros).
"""
import time
import numpy as np
import pandas as pd
from sanitizer.core import SanitizerEngine
from sanitizer.dedupe import find_duplicates

def generate_10k_mm_data():
    """Genera 10,000 registros sintéticos de Material Master con semilla fija."""
    np.random.seed(42)
    n_records = 10000
    n_invalid = 1000
    n_valid = n_records - n_invalid
    
    mat_types = ["ROH", "FERT", "HALB"]
    uoms = ["PC", "KG", "L"]
    price_ctrls = ["S", "V"]
    
    materials = [f"MAT{i:05d}" for i in range(n_records)]
    descriptions = [f"Material Description {i}" for i in range(n_records)]
    
    # 9,000 registros válidos
    valid_mat_types = np.random.choice(mat_types, n_valid)
    valid_sectors = np.random.choice(["M", "C"], n_valid)
    valid_uoms = np.random.choice(uoms, n_valid)
    valid_groups = np.random.choice(["G01", "G02"], n_valid)
    valid_weights = np.random.uniform(0.1, 100.0, n_valid).round(2).astype(str)
    valid_unit_weights = np.random.choice(["KG", "G"], n_valid)
    valid_price_ctrls = np.random.choice(price_ctrls, n_valid)
    valid_prices = np.random.uniform(1.0, 500.0, n_valid).round(2).astype(str)
    
    # 1,000 registros con incidencias controladas
    invalid_mat_types = np.random.choice(mat_types + ["ZXYZ"], n_invalid)
    invalid_sectors = np.random.choice(["M", "C", ""], n_invalid)
    invalid_uoms = np.random.choice(uoms + ["XXX"], n_invalid)
    invalid_groups = np.random.choice(["G01", "G02", ""], n_invalid)
    invalid_weights = np.random.choice(["-10.0", "5.0", ""], n_invalid)
    invalid_unit_weights = np.random.choice(["KG", "G", ""], n_invalid)
    invalid_price_ctrls = np.random.choice(price_ctrls + ["X"], n_invalid)
    invalid_prices = np.random.choice(["-50.0", "invalid", ""], n_invalid)
    
    df_data = {
        "MATERIAL": materials,
        "DESCRIPTION": descriptions,
        "MAT_TYPE": np.concatenate([valid_mat_types, invalid_mat_types]),
        "INDUSTRY_SECTOR": np.concatenate([valid_sectors, invalid_sectors]),
        "BASE_UOM": np.concatenate([valid_uoms, invalid_uoms]),
        "MAT_GROUP": np.concatenate([valid_groups, invalid_groups]),
        "NET_WEIGHT": np.concatenate([valid_weights, invalid_weights]),
        "UNIT_OF_WEIGHT": np.concatenate([valid_unit_weights, invalid_unit_weights]),
        "PRICE_CTRL": np.concatenate([valid_price_ctrls, invalid_price_ctrls]),
        "PRICE": np.concatenate([valid_prices, invalid_prices]),
    }
    
    df = pd.DataFrame(df_data)
    # Mezclamos de forma reproducible para simular datos reales distribuidos
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    return df

def generate_2k_dedup_data():
    """Genera 2,000 registros sintéticos de clientes/proveedores con semilla fija."""
    np.random.seed(42)
    n_unique = 1500
    n_dupes = 500
    n_records = n_unique + n_dupes
    
    base_names = [
        "CONSTRUCCIONES METALICAS GOMEZ",
        "INDUSTRIAS ALIMENTARIAS MARTINEZ",
        "TALLERES MECANICOS HERNANDEZ",
        "DISTRIBUIDORA DE BEBIDAS SANCHEZ",
        "SERVICIOS INFORMATICOS PEREZ",
        "PROYECTOS Y REFORMAS DIAZ",
        "LOGISTICA Y TRANSPORTES RUIZ",
        "CONTRATAS Y OBRAS ALONSO"
    ]
    
    unique_names = []
    for i in range(n_unique):
        base_word = base_names[i % len(base_names)]
        unique_names.append(f"{base_word} {i}")
        
    duplicate_names = []
    tax_ids = [f"ESA{10000000 + i}" for i in range(n_records)]
    postal_codes = [f"{28000 + (i % 100):05d}" for i in range(n_records)]
    
    for i in range(n_dupes):
        target_idx = i * 2 # duplicamos del primer bloque
        orig_name = unique_names[target_idx]
        
        if i % 3 == 0:
            duplicate_names.append(f"{orig_name} S.L.")
        elif i % 3 == 1:
            duplicate_names.append(f"{orig_name} S.A.")
        else:
            duplicate_names.append(orig_name.replace(" ", "  "))
            
        tax_ids[n_unique + i] = tax_ids[target_idx]
        postal_codes[n_unique + i] = postal_codes[target_idx]
        
    names = unique_names + duplicate_names
    
    df = pd.DataFrame({
        "NAME": names,
        "TAX_ID": tax_ids,
        "POSTAL_CODE": postal_codes
    })
    return df

def test_performance_ingesta_limpieza_10k():
    """Prueba el rendimiento del motor limpiando 10k registros (SLA < 15 segundos)."""
    df = generate_10k_mm_data()
    
    column_types = {
        "MATERIAL": "text",
        "DESCRIPTION": "text",
        "MAT_TYPE": "text",
        "INDUSTRY_SECTOR": "text",
        "BASE_UOM": "text",
        "MAT_GROUP": "text",
        "NET_WEIGHT": "text",
        "UNIT_OF_WEIGHT": "text",
        "PRICE_CTRL": "text",
        "PRICE": "text"
    }
    
    engine = SanitizerEngine(column_types=column_types)
    
    t0 = time.time()
    result = engine.sanitize(df, sap_template="Material Master (MM)")
    duration = time.time() - t0
    
    valid_count = result.metrics.get("valid_rows", 0)
    rejected_count = result.metrics.get("rejected_rows", 0)
    
    print("\n------------------------------------------------------------")
    print("BENCHMARK A: INGESTA Y LIMPIEZA 10K REGISTROS")
    print(f"Interprete: SanitizerEngine.sanitize()")
    print(f"Tiempo medido: {duration:.4f} s")
    print(f"Registros validos: {valid_count}")
    print(f"Registros rechazados: {rejected_count}")
    print(f"SLA Objetivo: < 15.0 s")
    print("------------------------------------------------------------")
    
    assert duration < 15.0, f"Excedido el tiempo de procesamiento de ingesta/limpieza: {duration:.2f}s >= 15s"
    assert valid_count > 0, "No se sanitizaron registros de forma valida"

def test_performance_deduplicacion_2k_blocking():
    """Prueba el rendimiento de la deduplicacion difusa con blocking (SLA < 25 segundos)."""
    df = generate_2k_dedup_data()
    
    t0 = time.time()
    dupes = find_duplicates(
        df, 
        text_column="NAME", 
        tax_id_column="TAX_ID", 
        postal_code_column="POSTAL_CODE", 
        threshold=85.0, 
        blocking_method="first_3_chars"
    )
    duration = time.time() - t0
    
    groups_found = len(dupes)
    
    print("\n------------------------------------------------------------")
    print("BENCHMARK B: DEDUPLICACION DIFUSA 2K (first_3_chars)")
    print(f"Interprete: find_duplicates()")
    print(f"Tiempo medido: {duration:.4f} s")
    print(f"Grupos duplicados encontrados: {groups_found}")
    print(f"SLA Objetivo: < 25.0 s")
    print("------------------------------------------------------------")
    
    assert duration < 25.0, f"Excedido el tiempo de procesamiento de deduplicacion: {duration:.2f}s >= 25s"
    assert groups_found > 0, "No se encontro ningun grupo de duplicados esperado"

if __name__ == "__main__":
    print("=" * 60)
    print("      EJECUCION DIRECTA DE CERTIFICACION DE RENDIMIENTO")
    print("=" * 60)
    try:
        test_performance_ingesta_limpieza_10k()
        test_performance_deduplicacion_2k_blocking()
        print("\n[OK] Certificacion de Rendimiento COMPLETADA con exito.")
    except AssertionError as e:
        print(f"\n[FALLO] Incumplimiento de SLA o error de asercion: {e}")
        import sys
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Ocurrio un error inesperado: {e}")
        import sys
        sys.exit(1)
