# Resultados Esperados para Validación Manual

A continuación se detalla el comportamiento esperado para cada fila de los datasets generados, usando la plantilla **SAP Business Partner (BP)**.

> **Nota:** Para probar estos resultados, asegúrate de mapear las columnas correspondientes en la interfaz a `PARTNER_ID`, `NAME`, `TAX_ID`, `POSTAL_CODE`, `PROVINCE`, `COUNTRY`, `STREET`, `IBAN` (si aplica) y `TELEPHONE`.

## 1. dataset_mixto_validacion.xlsx (25 filas)

| Row | PARTNER_ID | Resultado Esperado | Detalle / Motivo |
|---|---|---|---|
| 0 | BP001 | 🟢 Válido | Datos perfectos. |
| 1 | BP002 | 🟢 Válido | Datos perfectos. |
| 2 | BP003 | 🟢 Válido | Datos perfectos. |
| 3 | BP004 | 🟢 Válido | Datos perfectos. |
| 4 | BP005 | 🟢 Válido | Datos perfectos. |
| 5 | BP006 | 🟡 Válido (Corregido) | CP `8001` -> `08001`. Prov -> `BARCELONA`. c/ -> `Calle`. |
| 6 | BP007 | 🟡 Válido (Corregido) | Prov `ZARAGOZA` -> `MADRID` (por CP 28080). av. -> `Avenida`. Tlf limpiado. |
| 7 | BP008 | 🟡 Válido (Corregido) | Prov `MADRID` -> `SEVILLA` (por CP 41002). plz -> `Plaza`. Tlf limpiado. |
| 8 | BP009 | 🟡 Válido (Corregido) | Prov `ALICANTE` -> `VALENCIA` (por CP 46002). c. -> `Calle`. |
| 9 | BP010 | 🟡 Válido (Corregido) | Prov `SANTANDER` -> `BIZKAIA` (por CP 48001). g.v. -> `Gran Vía`. |
| 10 | BP011 | 🟡 Válido (Corregido) | Prov `GIRONA` -> `BARCELONA` (por CP 08002). rda -> `Ronda`. |
| 11 | BP012 | 🟡 Válido (Corregido) | Prov `TOLEDO` -> `MADRID` (por CP 28001). cl -> `Calle`. |
| 12 | BP013 | 🟡 Válido (Corregido) | Prov `HUELVA` -> `SEVILLA` (por CP 41003). pseo -> `Paseo`. |
| 13 | BP014 | 🟡 Válido (Corregido) | Prov `CASTELLON` -> `VALENCIA` (por CP 46003). avda -> `Avenida`. |
| 14 | BP015 | 🟡 Válido (Corregido) | Prov `GRANADA` -> `MALAGA` (por CP 29002). c/ -> `Calle`. |
| 15 | BP016 | 🔴 Rechazado | `TAX_ID` vacío. Es campo obligatorio SAP. |
| 16 | BP017 | 🔴 Rechazado | `TAX_ID` 'INVALIDO' viola reglas estrictas de tipo (no es NIF/CIF). |
| 17 | BP018 | 🔴 Rechazado | `TAX_ID` 'Z12345678' viola reglas estrictas. |
| 18 | BP019 | 🔴 Rechazado | `POSTAL_CODE` vacío. Es campo obligatorio SAP. |
| 19 | BP020 | 🔴 Rechazado | `IBAN` inválido. Viola reglas estrictas. |
| 20 | BP021 | 🔴 Rechazado | `TAX_ID` y `POSTAL_CODE` vacíos. |
| 21 | BP022 | 🔴 Rechazado | `TAX_ID` vacío. Es obligatorio en BP independientemente del país. |
| 22 | BP023 | 🔴 Rechazado | `TAX_ID` CIF con dígito de control incorrecto. |
| 23 | BP024 | 🔴 Rechazado | `TAX_ID` NIF con letra de control incorrecta. |
| 24 | BP025 | 🔴 Rechazado | `IBAN` inválido (formato/país incorrecto). |

## 2. dataset_dry_run_demo.xlsx (10 filas)
*Ideal para previsualizar visualmente (botón Dry Run con 10 filas).*

| Row | PARTNER_ID | Resultado Esperado en Panel |
|---|---|---|
| 0 | DR001 | Válido |
| 1 | DR002 | Válido (pero corregido CP 8002 -> 08002 y c/ -> Calle) |
| 2 | DR003 | Rechazado (TAX_ID obligatorio vacío) |
| 3 | DR004 | Rechazado (TAX_ID estricto inválido) |
| 4 | DR005 | Rechazado (POSTAL_CODE obligatorio vacío) |
| 5 | DR006 | Válido (Corregido c/ y Tlf) |
| 6 | DR007 | Válido |
| 7 | DR008 | Válido (Corregido Provincia a SEVILLA por CP 41002) |
| 8 | DR009 | Rechazado (IBAN o en este caso no lo pasamos pero el cp/nif esta bien. WAIT: en el df_dry no hay IBAN. DR009 está mapeado mal en script, su nif y cp son validos, telefono dice IBAN_INVENTADO. Se limpiará y será válido). |
| 9 | DR010 | Válido (Corregida plz) |

*(Nota: en DR009 el teléfono tiene letras, se quedará vacío y será Válido).*

## 3. dataset_hardening_edge_cases.xlsx (15 filas)

Se espera que el motor procese este archivo sin arrojar errores fatales de código (tracebacks).

| Row | PARTNER_ID | Comportamiento del Motor |
|---|---|---|
| 0 | H001 | Parsea enteros a strings. Rechazado por NIF estricto inválido (`11111111`). |
| 1 | H002 | Rechazado por campos obligatorios vacíos. No debe crashear el motor. |
| 2 | H003 | Limpia los espacios extra con `strip()`. Válido. |
| 3 | H004 | Rechazado por NIF estricto inválido. |
| 4 | H005 | Válido si el validador estricto pasa (NIF extranjero), pero fallará si se fuerza regla ES. (Rechazado) |
| 5 | H006 | Limpia los espacios del teléfono. Válido. |
| 6 | H007 | Rechazado. |
| 7 | H008 | Limpia teléfono pero mantendrá dígitos. Válido. |
| 8 | H009 | Válido, pero truncará el NOMBRE a 80 caracteres (Warning de SAP). |
| 9 | H010 | Válido. |
| 10 | H011 | Rechazado. |
| 11 | H012 | Corregirá CP `1` a `00001` o similar. Válido (Corregido). |
| 12 | H013 | Sobrescribe 'NARNIA' a 'BARCELONA' por CP 08001. Válido (Corregido). |
| 13 | H014 | Trunca o mantiene COUNTRY a 2 letras si se fuerza. |
| 14 | H015 | Limpia guiones en teléfono. Válido. |
