# Changelog

All notable changes to the **DataSanitizer ERP Migration Engine** project will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] - 2026-06-03

Esta versión implementa la **Sesión 12** de la hoja de ruta y consolida la versión de producción estable **V4.0.0** de **DataSanitizer**, optimizando el lanzador Windows y añadiendo una suite dedicada para certificación de rendimiento y benchmarks de estrés.

### Post-Release (2026-06-03)
* **Sesión 13: Activos de Portfolio y Narrativa Profesional:**
  - Creación del directorio de activos profesionales `portfolio/`.
  - Añadido el reposicionamiento estratégico, one-liner y pitches diferenciados en `portfolio/1_reposicionamiento.md`.
  - Añadida la ficha pública de proyecto en primera persona con lecciones aprendidas en `portfolio/2_ficha_proyecto.md`.
  - Añadido el guion cronometrado de demostración ejecutiva (3-5 min) en `portfolio/3_guion_demo.md`.
  - Añadido el bloque destacado de copia para la página web en `portfolio/4_bloque_web.md`.
  - Añadida la propuesta de difusión corta para LinkedIn en `portfolio/5_linkedin_post.md`.
  - Actualizado el roadmap del repositorio para incluir este hito.

### Added
* **Suite de Certificación de Rendimiento (`tests/test_performance.py`):**
  - Implementación de `test_performance_ingesta_limpieza_10k` para validar la latencia y la eficiencia de la limpieza e industrial MM en 10,000 registros (SLA < 15s).
  - Implementación de `test_performance_deduplicacion_2k_blocking` para certificar la velocidad del algoritmo de comparación difusa utilizando el método de bloqueo oficial `"first_3_chars"` (SLA < 25s).
  - Ambas pruebas emplean semillas aleatorias reproducibles (`seed=42`).
* **Soporte de Bandera de Rendimiento (`run_tests.py`):**
  - Incorporación del argumento `--include-performance` que permite ejecutar e informar los benchmarks de rendimiento por separado de la suite funcional.

### Changed
* **Lanzador de Windows (`Iniciar_Interfaz.bat`):**
  - Optimizado el script de arranque para buscar de forma secuencial y ordenada el intérprete (`py -3.10` -> `py` -> `python`) verificando que la versión sea igual o superior a 3.10.
  - Implementada comprobación estricta de importación para `streamlit`, `pandas` y `openpyxl` dentro de `.venv` para saltar reinstalaciones redundantes y acelerar el inicio en subsecuentes arranques.
  - El primer arranque limpio tiene un SLA oficial de < 60s, mientras que el arranque subsecuente tiene un objetivo orientativo no bloqueante de < 10s.
  - Control de errores explícito que aborta e informa claramente al usuario si falla la creación del entorno virtual o la instalación de requerimientos.
* **Pruebas Totales del Sistema:**
  - Separación formal de la suite de pruebas: **50 pruebas funcionales** en la suite por defecto y **2 pruebas de rendimiento** aisladas.

### Performance
* **Procesamiento de Ingesta y Limpieza (10K):**
  - Latencia reducida a ~1.9s para 10,000 registros (muy por debajo del SLA de 15s).
* **Deduplicación Difusa con Blocking (2K):**
  - Latencia reducida a ~0.09s para 2,000 registros con el método de bloqueo `"first_3_chars"` (muy por debajo del SLA de 25s).

## [3.8.0] - 2026-06-03

Esta versión implementa la **Sesión 11** de la hoja de ruta, unificando los entregables en un paquete de migración comprimido (.ZIP) estructurado para IT y añadiendo indicadores de impacto financiero/operativo y un panel de demostración técnica corporativa.

### Added
* **Empaquetador de Pre-Migración SAP (.ZIP) (`sanitizer/ui_actions.py`):**
  - Implementación de un empaquetado estructurado unificado que contiene `datos_limpios.csv`, `registros_rechazados.csv`, `readiness_report.html` y `auditoria_ejecucion.log`.
  - Los archivos auxiliares heredados de la Sesión 8 (Excel de staging, Excel completo de auditoría, costes e inventario) ahora se incluyen como anexos opcionales únicamente si se cuenta con datos aplicables.
* **Métricas Financieras y Operativas en Reporte HTML (`sanitizer/reports.py`):**
  - Cálculo de horas estimadas de trabajo manual de Excel ahorradas con fórmula ponderada basada en fixes corregidos.
  - Implementación de una estimación basal por registro (`total_records * 0.02` horas) con pie de página aclaratorio cuando no existen correcciones aplicadas y el procesamiento es exitoso.
  - Cálculo de riesgo financiero evitado por IBANs no válidos/bloqueados (`100 €` por evento).
  - Cálculo del porcentaje real de carga exitosa (Ready-to-Load %) sobre el total analizado.
* **Pestaña interactiva de Demo IT SAP (`sanitizer/ui_components.py`, `app.py`):**
  - Nueva pestaña `Guía de Demo IT SAP` con un guion detallado de 6 pasos de demostración técnica y argumentos de valor.
* **Suite de Pruebas de la Sesión 11 (`tests/test_session11.py`):**
  - 5 nuevos tests unitarios creados que verifican el empaquetado ZIP principal, codificación UTF-8-sig y delimitadores, renderizado dinámico de KPIs e indicador basal en HTML, exportación de rechazos vacíos/nulos y lógica de deduplicación de duplicados.

### Changed
* **Pruebas Unitarias Totales:**
  - Incremento en el número total de tests de 45 a 50 con un 100% de éxito.

---

## [3.7.0] - 2026-06-03

Esta versión implementa la **Sesión 10** de la hoja de ruta, introduciendo mejoras de robustez operativa, panel de Dry Run para previsualizar cambios, segregación de registros rechazados con errores críticos y manejo robusto de excepciones por celda sin caída de la aplicación.

### Added
* **Panel de Simulacro (Dry Run) (`sanitizer/core.py`, `app.py`):**
  - Permite a los usuarios previsualizar los cambios de limpieza antes de procesar el archivo completo a través de una tabla tabulada comparativa interactiva.
* **Segregación de Registros Rechazados (`sanitizer/core.py`, `sanitizer/result.py`):**
  - Separación física de registros con errores críticos insalvables (como NIFs vacíos o incorrectos en plantillas estrictas) a un DataFrame secundario descargable (`rejected_df`).
* **Manejo Resiliente de Excepciones por Celda (`sanitizer/core.py`):**
  - Implementación de capturas de excepciones controladas y acotadas a nivel de validación/limpieza de celda individual, evitando caídas completas del motor (tracebacks) y registrando incidencias con estructura clara (`WARNING|CELL_ERROR`).
* **Pruebas de Hardening de Robustez (`tests/test_edge_cases.py`):**
  - Nuevos tests unitarios y de integración para validar la tolerancia del motor a fallos de base de datos simulados y capturas de excepciones en celdas rotas.

### Changed
* **Pruebas Unitarias Totales:**
  - Incremento en el número total de tests de 38 a 45 con 100% de éxito.

---

## [3.6.0] - 2026-06-03

Esta versión implementa la **Sesión 9** de la hoja de ruta, incorporando un Onboarding Interactivo y Centro de Ayuda integrado directamente en la UI web local.

### Added
* **Centro de Ayuda y FAQ en UI (`sanitizer/ui_components.py`, `app.py`):**
  - Pestaña dedicada con glosario de términos, guía paso a paso del flujo de migración y respuestas detalladas a 5+ incidencias frecuentes de calidad de datos en ERPs.
* **Ayudas Visuales Contextuales y Tooltips (`sanitizer/ui_components.py`):**
  - Explicaciones interactivas sobre los tipos semánticos y reglas aplicadas en el mapeo de columnas.
* **Pruebas de la Interfaz y Documentación (`tests/test_help_center.py`):**
  - Tests unitarios que verifican que todos los campos del mapeo tienen tooltips detallados asociados y que el glosario carga correctamente.

### Changed
* **Pruebas Unitarias Totales:**
  - Incremento en el número total de tests de 35 a 38 con 100% de éxito.

---

## [3.5.0] - 2026-06-03

Esta versión implementa la **Sesión 8** de la hoja de ruta, introduciendo la exportación de cuadernos de staging compatibles para SAP S/4HANA (Migration Cockpit - LTMC), la descarga de un paquete de migración consolidado en formato comprimido (.ZIP) con doble salida (datos de carga y datos de auditoría completa), y la optimización del rendimiento en la deduplicación difusa mediante blocking keys configurables desde la UI.

### Added
* **Exportador Excel compatible con Staging SAP (`sanitizer/exporter.py`):**
  - Generación de libros Excel estructurados con 3 filas de cabecera (nombres técnicos, etiquetas de idioma y metadatos visuales de longitud y obligatoriedad `C(n) *`).
  - Filtrado y exclusión estricta de columnas técnicas/logs en las hojas de carga para evitar rechazos en el Cockpit de SAP.
  - Auto-ajuste de columnas y cuadrícula para máxima legibilidad.
* **Empaquetado ZIP de Migración Consolidado (`sanitizer/ui_actions.py`):**
  - Compresión en memoria con `zipfile` y `BytesIO` que unifica los entregables:
    1. `staging_sap_load.xlsx` (Carga limpia de SAP).
    2. `full_audit_sanitized.xlsx` (Auditoría completa con columnas técnicas de logs y estado).
    3. `readiness_report.html` (Reporte de preparación interactivo HTML).
    4. `migration_cleanse_audit.txt` (Log detallado de la ejecución con metadatos del run y fecha).
    5. `costing_simulation.csv` e `inventory_health.csv` (Archivos de controlling y stock si aplican, con codificación UTF-8-sig con BOM y separador `;`).
* **Optimización y Flexibilidad en Deduplicación difusa (`sanitizer/dedupe.py`):**
  - Soporte para claves de bloqueo (`blocking_method`): `"first_3_chars"` (por defecto), `"first_char"`, `"postal_code_2"`, `"province"`, y `"none"` (exhaustivo).
  - Caída de seguridad (*fallback*) a `"first_3_chars"` ante la ausencia o error de datos geográficos para no perder duplicados difusos legítimos.
  - Selector visual interactivo en la barra lateral de Streamlit (`app.py`) con explicaciones dinámicas de cada método de optimización.
* **Hardening de Seguridad y Auditoría (`sanitizer/reports.py`):**
  - Escapado estricto con `html.escape()` de todos los campos e incidencias dinámicas inyectadas en el HTML Readiness Report para mitigar riesgos de Stored XSS provenientes de CSVs.
  - Metadatos de IT con auditoría, total de registros, plantilla, columnas y marcas de tiempo en el log de trazas del ZIP.
* **Suite de Pruebas Automatizadas (`tests/test_exporter.py`):**
  - Añadidos tests específicos para validar las 3 cabeceras del Excel de staging, la integridad del ZIP de doble salida con BOM de UTF-8-sig y delimitadores `;`, y la precisión sin pérdida de duplicados del algoritmo con bloqueo.
  - Total de pruebas en `run_tests.py` incrementado de 32 a 35 con 100% de éxito.

## [3.4.0] - 2026-06-03

Esta versión implementa la **Sesión 6** de la hoja de ruta, introduciendo la validación de datos maestros industriales y heurísticas de negocio para SAP (Material Master, BOMs, Rutas y Controlling).

### Added
* **Validación de Material Master (MM):**
  * Verificación de consistencia entre tipos de material (ROH, HALB, FERT) y su control de precio (`S` o `V`).
  * Validación de unidades de medida (ej. PCE, KG, M, L).
* **Validación de Listas de Materiales (BOMs) y Rutas (PP):**
  * Detección de BOMs complejas (más de 50 componentes).
  * Alertas críticas por tiempos de preparación nulos en rutas de fabricación.
* **Validación de Controlling (CO):**
  * Verificación de Centros de Coste (KS01), validando la asignación de responsable, área funcional y jerarquía.
* **Integración y UI (`sanitizer/core.py`, `app.py`, `sanitizer/reports.py`):**
  * Integración de las heurísticas industriales en el pipeline principal según la plantilla detectada.
  * Añadida sección de KPIs de incidencias industriales al Readiness Report HTML.
  * Nuevos selectores de plantillas (BOM, Routing, Cost Center) en la interfaz gráfica.
* **Suite de Pruebas Unitarias (`tests/test_industrial.py`):**
  * Añadidos tests específicos para reglas de MM, PP y CO.
  * Total de tests automatizados elevados de 20 a 25.

## [3.3.0] - 2026-06-03

Esta versión implementa la **Sesión 5** de la hoja de ruta, integrando adaptadores SAP S/4HANA, plantillas de migración predefinidas, un reporte HTML de preparación de datos y un pipeline de integración continua.

### Added
* **Plantillas de Mapeo SAP Predefinidas (`sanitizer/sap_templates.py`):**
  * Diccionario `SAP_TEMPLATES` con plantillas para **Business Partner (BP)** y **Material Master (MM)**.
  * Cada plantilla define mapeo de columnas, tipos semánticos, longitudes máximas SAP y campos obligatorios.
  * Selector de plantillas integrado en la interfaz Streamlit con aplicación automática de mapeo y tipos.
* **Validación y Adaptación SAP S/4HANA (`sanitizer/core.py`):**
  * Post-validación SAP que aplica **truncamiento automático** de valores que superan la longitud máxima permitida por SAP.
  * Detección y reporte de **campos obligatorios vacíos** según la plantilla seleccionada.
  * Cada corrección y advertencia se notifica en las columnas de reporte (`_CLEAN_LOG`) y en los logs del motor.
* **Generación de Readiness Report HTML (`sanitizer/reports.py`):**
  * Informe HTML autocontenido y descargable con KPIs visuales: porcentaje de preparación global, campos con errores críticos, advertencias y resumen de acciones aplicadas.
  * Gráfico de progreso circular SVG animado y tabla de métricas con estética profesional.
  * Botón de descarga integrado en la interfaz Streamlit.
* **Pipeline CI/CD con GitHub Actions (`.github/workflows/pytest.yml`):**
  * Workflow automatizado que ejecuta la suite de 20 tests en cada push y pull request a `main`.
  * Configurado con Python 3.11 sobre Ubuntu latest.
* **Tests SAP (`tests/test_sap.py`):**
  * Test de truncamiento automático: verifica que valores más largos que el máximo SAP se recortan correctamente.
  * Test de campos obligatorios: verifica la detección de campos vacíos según la plantilla.

### Changed
* **Interfaz Streamlit (`app.py`):**
  * Añadido selector de plantillas SAP (BP/MM) en la barra lateral que pre-configura automáticamente el mapeo y los tipos semánticos.
  * Añadido botón de descarga directa del Readiness Report HTML junto al CSV sanitizado.
* **Orquestador Central (`sanitizer/core.py`):**
  * Integrada fase de post-validación SAP tras la limpieza de tipos: ejecuta truncamiento y detección de campos obligatorios vacíos.
* **Suite de Tests (`run_tests.py`):**
  * Ampliada a **20 tests** con la adición de `test_sap_bp_truncation` y `test_sap_required_fields`.

## [3.2.1] - 2026-06-03

Parche de calidad documental tras auditoría de cierre de la **Sesión 4**. Se detectaron y corrigieron 6 discrepancias entre documentación, código y versionado.

### Fixed
* **`README.md`:** Corregido conteo de tests (15 → 18) y de sesiones del roadmap (5 → 7).
* **`README.md`:** Alineada versión del título con el CHANGELOG real (V4.0 → V3.2).
* **`README.md`:** Añadido `test_ingestion.py` al inventario de archivos de test (faltaba).
* **`cli.py`:** Actualizado banner de versión de V3.1 a V3.2.
* **`app.py`:** Eliminado `import json` no utilizado.
* **`roadmap_sesiones.md`:** Corregido título de versión para reflejar progresión (V3.2 → V4.0).

## [3.2.0] - 2026-06-03

Esta versión implementa la **Sesión 4** de la hoja de ruta, introduciendo la normalización de formas jurídicas, la regla de CIF exacto, la optimización mediante bloqueo (blocking) geográfico y el Panel de Fusión interactivo en la interfaz Streamlit.

### Added
* **Normalización de Formas Jurídicas:**
  * Implementada función `clean_legal_suffixes` para remover de forma no destructiva sufijos legales españoles (`S.A.`, `S.L.`, `S.L.U.`, etc.) al calcular similitudes.
* **Detección Directa por CIF Exacto:**
  * Implementado agrupamiento global prioritario si el identificador fiscal (`TAX_ID`) coincide exactamente.
* **Optimización por Bloqueo (CP/Nombre):**
  * Implementado agrupamiento por Código Postal (provincia) o por letra del nombre antes de Levenshtein para optimizar el coste de comparación.
* **Panel de Fusión en la Interfaz (Streamlit):**
  * Creado panel interactivo de fusión que lista los sospechosos en acordeones.
  * Soporte para selección de políticas de fusión: *Fusión Inteligente (Combinar campos)*, *Conservar principal/primer/último* o *No fusionar*.
  * Consolidación y deduplicación real del DataFrame final compatible con descarga directa.
* **Archivos de Prueba y Pruebas Unitarias:**
  * Creados 3 archivos CSV de pruebas en `tests/samples/`.
  * Agregados 3 tests unitarios nuevos en `tests/test_dedupe.py` logrando 18 tests exitosos en total.

## [3.1.0] - 2026-06-03

Esta versión representa el pivot y rediseño de la hoja de ruta para orientar la herramienta a usuarios no programadores mediante una interfaz gráfica, además de integrar las reglas críticas de validación fiscal española, coherencia geográfica y bancaria.

### Added
* **Interfaz de Usuario Web Local (Streamlit):**
  * Creado el panel interactivo principal en `app.py`.
  * Soporte para carga de archivos CSV/Excel con detección en pantalla de delimitador y encoding.
  * Dashboard de diagnóstico visual (Health Check) mostrando total de registros, columnas, vacíos y duplicados exactos.
  * Mapeador interactivo con auto-sugerencias de nombres de columnas y tipos de datos.
  * Consola de ejecución integrada y visor de logs técnicos en tiempo real.
  * Botón de descarga directa de archivos sanitizados compatible con Microsoft Excel (punto y coma y BOM UTF-8).
* **Lanzador Directo de Windows:**
  * Creado `Iniciar_Interfaz.bat` que permite iniciar el servidor web y abrir el navegador haciendo doble clic, resolviendo de forma transparente problemas con el PATH de Python/Streamlit.
* **Regla Geográfica (España):**
  * Creada validación de códigos postales españoles (5 dígitos, rango `01000`-`52999`) y padding automático de 4 a 5 dígitos (`sanitizer/rules/geo.py`).
  * Diccionario de correspondencia CP-Provincia basado en los dos primeros dígitos del código postal.
* **Regla Bancaria BIC/SWIFT:**
  * Creada validación de longitud y formato regex oficial (`sanitizer/rules/bic.py`).
  * Validación de coherencia del país del BIC cruzado con el país del IBAN.
* **Regla de Direcciones:**
  * Normalización de prefijos de vía estándar en España (`C/` -> `CALLE`, `Avda.` -> `AVENIDA`, etc.).
  * Algoritmo de división automática de dirección completa en: Tipo de vía, Nombre, Número de portal y Piso/Puerta (`sanitizer/rules/address.py`).
* **Pruebas de la Sesión 2 e Integración:**
  * Creado archivo de tests unitarios y de integración `tests/test_rules_session2.py`.

### Changed
* **Orquestador Central (`sanitizer/core.py`):**
  * Modificado para integrar los nuevos tipos semánticos (`postal_code`, `province`, `bic`, `address`).
  * Añadida lógica de inyección de columnas de estado de validación y de componentes de direcciones.
  * Añadidas validaciones cruzadas (autocorrección de provincia por CP, y detección de discrepancias de país en datos bancarios).
* **Configuración del Proyecto:**
  * Actualizado `requirements.txt` para incluir las dependencias de `streamlit` y `openpyxl`.
  * Modificado `run_tests.py` para incluir y ejecutar automáticamente las nuevas pruebas unitarias (15 tests OK).
  * Modificado `roadmap_sesiones.md` para reflejar el pivot del proyecto hacia UI-First y registrar las tareas de las sesiones 1, 2 y 3 como completadas.
