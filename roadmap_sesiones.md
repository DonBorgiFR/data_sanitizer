# Roadmap de Desarrollo por Sesiones — DataSanitizer (V3.4 → V4.0)

Este documento sirve como base estructurada para guiar el desarrollo incremental de **DataSanitizer** en **7 sesiones de trabajo robustas**, reenfocado hacia la migración de datos maestros industriales y controlling de costes para implantaciones en **SAP S/4HANA**.

---

## Sesión 1: Ingesta Avanzada, Tipado Estricto y Detección de Codificación
*   **Objetivo:** Asegurar que la entrada de datos sea infalible, detecte problemas de codificación comunes en PYMEs y valide tipos de datos estructurales antes de procesar.

### Subtareas de Desarrollo:
*   [x] **1.1. Ingestor con autodetección de Encoding y Delimitador:**
    *   Implementar detección automática de codificaciones conflictivas comunes en exportaciones españolas (`utf-8`, `utf-8-sig`, `cp1252`, `iso-8859-1`).
    *   Autodetectar separadores de campo en CSV analizando la frecuencia de caracteres no alfanuméricos en la cabecera.
*   [x] **1.2. Lector Multiuso (CSV + Excel de varias pestañas):**
    *   Integrar lectura de archivos Excel (`.xlsx`, `.xls`) usando `openpyxl` como motor de lectura en Pandas, permitiendo especificar opcionalmente el nombre de la hoja de cálculo.
*   [x] **1.3. Motor de Esquemas JSON de Configuración (Schema Enforcement):**
    *   Diseñar una estructura de configuración en JSON que defina las restricciones de la tabla objetivo: nombres de columna obligatorios, tipos esperados y si admiten nulos.
*   [x] **1.4. Reporte de Diagnóstico Inicial (Health Check):**
    *   Programar una función que analice la calidad del archivo crudo antes de limpiar: celdas vacías por columna y tipos de datos inferidos.

---

## Sesión 2: Reglas de Validación Críticas (NIF/CIF) y Coherencia Geográfica
*   **Objetivo:** Priorizar la validación fiscal española (error número 1 en rechazos de ERPs) e integrar coherencia geográfica.

### Subtareas de Desarrollo:
*   [x] **2.1. Validador y Limpiador de NIF/CIF/NIE (Máxima Prioridad SAP):**
    *   Comprobación matemática estricta del dígito de control del NIF (`DNI % 23`), NIE y CIF (algoritmo de sumas pares/impares). Limpieza previa de puntos, guiones y espacios.
*   [x] **2.2. Comprobación y Autocorrección de Códigos Postales y Provincias:**
    *   Implementar validación de Códigos Postales españoles (rango 01000 - 52999).
    *   Crear un diccionario de correspondencia CP-Provincia para corregir automáticamente discrepancias (ej. si el código postal es `08770`, la provincia debe ser obligatoriamente `Barcelona`).
*   [x] **2.3. Validador de Códigos Bancarios BIC/SWIFT:**
    *   Validar la estructura del código BIC y cruzarla con el código de país del IBAN para asegurar coherencia internacional.
*   [x] **2.4. Mapeador y Limpiador de Direcciones Frecuentes:**
    *   Crear un diccionario de reemplazos normativos para tipos de vía españoles (ej: `C/` -> `Calle`, `Av.` -> `Avenida`, `Pza.` -> `Plaza`). SAP requiere separar estos campos (vía, número, piso) para su importación masiva.

---

## Sesión 3: Interfaz de Usuario Local (Streamlit), Diagnóstico y Configuración Interactiva
*   **Objetivo:** Construir la base de la aplicación gráfica local para permitir a usuarios no programadores cargar datos, configurar esquemas de forma interactiva y descargar la salida sanitizada.

### Subtareas de Desarrollo:
*   [x] **3.1. Interfaz Web Streamlit de Carga de Archivos:**
    *   Crear un panel de carga visual para archivos CSV/Excel con detección en pantalla del encoding y separador.
*   [x] **3.2. Dashboard Visual de Diagnóstico de Salud (Health Check):**
    *   Presentar las métricas de calidad de datos crudos (filas, columnas, vacíos por columna, tipos de datos inferidos y duplicados exactos) de forma visual.
*   [x] **3.3. Configuración Interactiva de Columnas y Mapeo:**
    *   Implementar selectores desplegables (`st.selectbox`) para asociar campos de origen con nombres de destino y asignar tipos semánticos (`NIF/CIF`, `IBAN`, `BIC`, `CP`, `Dirección`, etc.).
*   [x] **3.4. Motor de Ejecución y Descarga Excel-Compatible:**
    *   Conectar la interfaz web al motor `SanitizerEngine`, mostrar el progreso y permitir la descarga directa del CSV resultante con separador de punto y coma y BOM UTF-8.

---

## Sesión 4: Resolución de Entidades, Deduplicación Difusa y Panel de Fusión Visual
*   **Objetivo:** Optimizar la deduplicación para grandes volúmenes y agregar una interfaz interactiva de revisión y fusión de registros duplicados en Streamlit.

### Subtareas de Desarrollo:
*   [x] **4.1. Normalización de Formas Jurídicas:**
    *   Implementar limpiador de sufijos legales (`S.L.`, `S.A.`, etc.) de forma temporal antes de ejecutar el algoritmo de Levenshtein.
*   [x] **4.2. Regla de CIF Exacto:**
    *   Detección directa de duplicados cuando el identificador fiscal coincida, saltando la distancia difusa.
*   [x] **4.3. Optimización mediante Indexación/Bloqueo (Blocking):**
    *   Reducir coste temporal agrupando registros por código postal o primera letra del nombre comercial antes de procesar Levenshtein.
*   [x] **4.4. Panel de Fusión Interactiva (Merge Panel):**
    *   Añadir pantalla en la UI para listar grupos de sospechosos, aplicar políticas de fusión ("más reciente", "priorizar IBAN") y validar con botones de aprobación manual.

---

## Sesión 5: Adaptadores S/4HANA, Plantillas de Mapeo y HTML Readiness Report
*   **Objetivo:** Adaptar los flujos a las plantillas técnicas de carga de SAP y certificar el estado de los datos con un reporte estético formal de preparación.

### Subtareas de Desarrollo:
*   [x] **5.1. Plantillas de Mapeo Predefinidas (SAP Migration Cockpit):**
    *   Integrar botones en la UI que configuren automáticamente el mapeo y los tipos semánticos para cargar plantillas de **Business Partner (BP)** y **Material Master (MM)**.
*   [x] **5.2. Adaptadores de Exportación Técnica SAP S/4HANA:**
    *   Adecuar la salida CSV/Excel con las cabeceras técnicas, longitudes y códigos esperados por el Migration Cockpit de SAP.
*   [x] **5.3. Generación de Data Migration Readiness Report (HTML):**
    *   Generar un informe gráfico interactivo descargable que resuma la calidad del archivo: porcentaje de preparación global, KPIs de nulos en campos obligatorios, y Top 10 de clientes/proveedores con incidencias.
*   [x] **5.4. Pipeline de Integración Continua (CI/CD) con Pytest:**
    *   Configurar tests y workflows automatizados en GitHub Actions para validar regresiones y lógicas de deduplicación con cada cambio.

---

## Sesión 6: Validación de Datos Maestros Industriales y Heurísticas (MM/PP/CO)
*   **Objetivo:** Incorporar la lógica industrial de materiales, estructuras de fabricación (BOM) y controlling contable (Centros de Coste) de SAP.

### Subtareas de Desarrollo:
*   [x] **6.1. Validador de Material Master (MM):**
    *   Validar lógicas de tipos de material (ROH, HALB, FERT), consistencia de unidades de medida (longitud, peso, volumen) y obligatoriedad de campos críticos por tipo de material.
*   [x] **6.2. Validador de BOMs (CS01/CS02) y Rutas de Operaciones (CA01/CA02):**
    *   Detectar cantidades atípicas en componentes BOM (ej. cantidades 0, 9999).
    *   Identificar operaciones en rutas con tiempos nulos o absurdos y puestos de trabajo inexistentes.
*   [x] **6.3. Validación de Controlling (CO) - Centros de Coste (KS01):**
    *   Chequear consistencia en las jerarquías estándar de controlling, centros de coste sin responsable asignado o sin áreas funcionales.
*   [x] **6.4. Reglas Inteligentes y Heurísticas Industriales:**
    *   Añadir validaciones cruzadas lógicas:
        *   Si un material es `ROH` (materia prima) -> debe estar asignado a precio estándar o medio variable.
        *   Si una BOM supera 50 componentes -> marcar como "compleja".
        *   Si una ruta de fabricación tiene tiempo 0 en coste de preparación -> alertar de error crítico.

---

## Sesión 7: Costes Estándar, Salud de Inventario y Modo "Pre-Migración SAP" (Consolidación Técnica)
*   **Objetivo:** Consolidar el Product Costing (controlling de producción), el saneamiento de inventarios y la ejecución de validaciones de maestros en un modo unificado de pre-migración de datos.

### Subtareas de Desarrollo:
*   [x] **7.1. Validador de Coste Estándar (Product Costing):**
    *   Recálculo simulativo del coste: `BOM × precios + Rutas × tarifas`.
    *   Detección de desviaciones contra el coste cargado en el Material Master.
    *   Generar un informe de impacto estimado en el margen bruto si se corrigen errores.
*   [x] **7.2. Health Check de Inventarios previo a Migración:**
    *   Detectar stocks negativos, obsolescencia (materiales sin consumo en 24 meses) y discrepancias entre precio medio variable y precio estándar.
    *   Conversión y estandarización automática de unidades de stock, y análisis de clasificación ABC.
*   [x] **7.3. Modo "Pre-Migración SAP" consolidado:**
    *   Agregar un botón maestro en la UI para ejecutar todas las lógicas técnicas (Health check, dedupe, validación de costes y maestros) de forma secuencial y permitir la descarga directa de las tablas resultantes sanitizadas de forma individual.

### Definition of Done (DoD):
*   **Archivos tocados:** `sanitizer/core.py` (lógica de costes e inventarios), `sanitizer/ui_actions.py` (ejecución conjunta), `sanitizer/ui_components.py` (pantalla de controlling), `app.py` (integración visual de costes).
*   **Tests afectados:** Nuevos tests en `tests/test_industrial.py` cubriendo recálculos de costes, desvíos y alertas de stock obsoleto/negativo.
*   **Validación manual:** Cargar archivos de prueba con maestros de materiales, BOMs y rutas. Presionar "Calcular Costes Estándar" y validar que las desviaciones y márgenes calculados coincidan matemáticamente en la UI.
*   **Riesgos residuales:** El cálculo de costes asume estructuras lineales simples; no soporta rutas alternativas complejas ni sub-productos.
*   **Límites de lo implementado:** No genera el archivo ZIP unificado (postergado a la Sesión 11) ni reportes ejecutivos con cálculo de ahorro financiero en esta sesión.

---

## Sesión 8: Generación de Plantillas de Staging SAP, Empaquetado ZIP y Optimización de Dedupe (Consolidación)
*   **Objetivo:** Consolidar la exportación del DataSanitizer para su carga directa en SAP S/4HANA mediante la generación de archivos Excel (.xlsx) que sigan el formato de metadatos del Migration Cockpit (LTMC) para staging, habilitar la descarga de un paquete de migración comprimido (.zip) con doble salida (carga + auditoría) y optimizar el rendimiento de la deduplicación difusa mediante blocking keys.

### Subtareas de Desarrollo:
*   [x] **8.1. Excel Compatible para Staging SAP S/4HANA (.xlsx):**
    *   Generar archivos Excel de staging limpios que incluyan únicamente las columnas oficiales definidas por el objeto SAP.
    *   Escribir las tres filas de cabecera: nombres técnicos, etiquetas de idioma y metadatos de formato (ej. `C(80) *`).
    *   Aplicar estilos limpios (cuadrícula, anchos automáticos) excluyendo columnas de control (`*_VALID`, `*_ERROR`, `_CLEAN_LOG`).
*   [x] **8.2. Empaquetado de Migración Unificado (.ZIP) con Doble Salida:**
    *   Crear un empaquetado en memoria de los entregables:
        *   `staging_sap_load.xlsx`: Plantilla limpia sin columnas de control.
        *   `full_audit_sanitized.xlsx`: Plantilla con todas las columnas de auditoría y log.
        *   `readiness_report.html` (Readiness Report escapado contra XSS).
        *   `migration_cleanse_audit.txt` (Log detallado con metadatos del run).
        *   CSVs de simulación de costes e inventarios (con codificación UTF-8-sig y separador `;`).
*   [x] **8.3. Optimización de Deduplicación Difusa mediante Blocking:**
    *   Implementar métodos de bloqueo (`first_3_chars` por defecto, `first_char`, `postal_code_2`, `province`, `none`) para reducir comparaciones difusas en bases de datos masivas.
    *   Integrar selector visual interactivo en la barra lateral de Streamlit con explicaciones dinámicas de cada método.

### Definition of Done (DoD):
*   **Archivos tocados:** `sanitizer/exporter.py` (nuevo módulo), `sanitizer/ui_actions.py` (zip unificado), `sanitizer/dedupe.py` y `sanitizer/core.py` (optimización por blocking), `app.py` (descargas y UI).
*   **Tests afectados:** Nuevos tests en `tests/test_exporter.py` (validando staging, ZIP con BOM y separador `;`, y precisión de blocking), integrados con éxito en `run_tests.py` (35 tests en total aprobados).
*   **Validación manual:** Ejecución del pipeline con 1,500 registros sintéticos, descarga de ZIP y validación estructural del staging.
*   **Riesgos residuales:** El uso de bloqueo geográfico (`postal_code_2`, `province`) es avanzado y puede omitir duplicados si el dato origen está corrupto. Se establece `first_3_chars` como default.
*   **Límites de lo implementado:** La exportación a staging no sustituye al 100% el formato XML de carga final de SAP, sino que sirve de staging intermedio.

---

## Sesión 9: Onboarding Interactivo y Centro de Ayuda (On-App Documentation)
*   **Objetivo:** Dotar a la aplicación de un centro de documentación, glosarios y ayudas contextuales integradas que permitan su uso de forma 100% autónoma por perfiles ajenos a la programación.

### Por qué aporta valor real:
*   Un producto profesional no debe depender del desarrollador para ser configurado o comprendido. El onboarding interactivo capacita a los consultores funcionales a validar tipos de datos por sí mismos.

### Subtareas concretas:
*   [x] **9.1. Tooltips Contextuales de Tipado Semántico:**
    *   Añadir explicaciones cortas y de fácil comprensión en los selectores de mapeo de la UI (ej: explicar qué limpia la regla de `address` o qué valida `tax_id`).
*   [x] **9.2. Centro de Ayuda Integrado (FAQ & Glosario):**
    *   Agregar una pestaña o sección desplegable dedicada en Streamlit que contenga explicaciones paso a paso de los tipos de datos admitidos y cómo solucionar errores típicos de formato.
*   [x] **9.3. Leyenda Interactiva de Reglas:**
    *   Diseñar un panel donde el usuario pueda consultar las fórmulas lógicas aplicadas (ej. algoritmo mod-97 de IBAN o DNI % 23 de NIF) de forma simplificada.

### Riesgos o dependencias:
*   Aumento de la carga visual en Streamlit si se sobresatura de textos explicativos.

### Entregables:
*   Centro de Ayuda integrado en `sanitizer/ui_components.py` con FAQs y glosario.
*   Manual de ayuda rápida en formato Markdown visible dentro de la UI.

### Criterios de aceptación:
*   Cada campo seleccionable en el mapeo de columnas tiene un botón o tooltip explicativo.
*   El FAQ cubre al menos 5 incidencias típicas de archivos CSV y Excel.

### Cómo verificarla manualmente:
1. Abrir la sección "Centro de Ayuda" en la barra lateral o barra de navegación.
2. Desplegar los expanders de preguntas frecuentes y confirmar la correcta lectura de la guía.

### Definition of Done (DoD):
*   **Archivos tocados:** `sanitizer/ui_components.py` (centro de ayuda y tooltips), `app.py` (integración de la pestaña de ayuda).
*   **Tests afectados:** No aplica directamente a tests de lógica del motor backend. Se añaden verificaciones visuales sencillas en `tests/test_ui_flow.py`.
*   **Validación manual:** Navegar al "Centro de Ayuda" en la UI, desplegar las preguntas de FAQ y verificar que cada dropdown de mapeo muestre su tooltip al pasar el ratón.
*   **Riesgos residuales:** La documentación se mantiene estática; cualquier nueva regla añadida al motor requerirá actualización manual en esta interfaz de ayuda.
*   **Límites de lo implementado:** No incluye asistencia guiada interactiva paso a paso en tiempo real sobre la tabla de datos cargada.

---

## Sesión 10: Robustez Operativa y Hardening de Producto (Product Hardening)
*   **Objetivo:** Desarrollar tolerancia a fallos extrema frente a archivos corruptos, visualización previa de modificaciones ("Dry Run") y segregación de registros erróneos graves.

### Por qué aporta valor real:
*   Las migraciones reales ERP se enfrentan a datos de entrada con formatos rotos. Evitar la caída de la aplicación entera y dar visibilidad antes de escribir cambios es crucial para ganarse la confianza del usuario corporativo.

### Subtareas concretas:
*   [x] **10.1. Modo Simulacro (Dry Run) y Previsualización de Cambios:**
    *   Mostrar una tabla comparativa del "Antes" y "Después" para las primeras 5 filas que van a ser procesadas antes de iniciar la sanitización completa.
*   [x] **10.2. Aislamiento y Exportación de Registros Rechazados:**
    *   Crear una salida secundaria de "Rechazos Críticos" (filas con datos obligatorios ausentes o fallos de esquema fatales) permitiendo procesar el 99% restante de forma fluida.
*   [x] **10.3. Captura e Informe de Excepciones del Motor:**
    *   Implementar un logger en UI de fallos de celdas específicas sin que la app muestre tracebacks técnicos de Python.

### Riesgos o dependencias:
*   Degradación de rendimiento al realizar la copia comparativa dry-run en archivos de cientos de miles de registros.

### Entregables:
*   Panel comparativo Dry Run en la UI.
*   Dataframe de registros rechazados devuelto en `SanitizerResult`.

### Criterios de aceptación:
*   Si una fila tiene un error de tipado insalvable en un campo obligatorio (ej: NIF vacío en plantilla de BP), no interrumpe el flujo y se añade a la cola de rechazos descargable.
*   La previsualización comparativa se muestra en un formato tabulado interactivo de Streamlit.

### Cómo verificarla manualmente:
1. Cargar un archivo con al menos 1 registro totalmente inválido (ej: letras en el código postal y NIF vacío).
2. Procesar y verificar la descarga de los registros correctos por un lado, y el reporte de descartes por otro.

### Definition of Done (DoD):
*   **Archivos tocados:** `sanitizer/core.py` (aislamiento de errores e hilo de procesamiento por fila), `sanitizer/result.py` (adición del dataframe de rechazos), `sanitizer/ui_components.py` (visualización Dry Run y tabla de descartes).
*   **Tests afectados:** Modificar `tests/test_edge_cases.py` para asegurar que el motor captura y aísla celdas erróneas sin abortar la ejecución de la tabla completa.
*   **Validación manual:** Subir un archivo con filas correctas y filas que violen restricciones obligatorias de SAP. Validar que la tabla "Antes y Después" del dry run es legible y que tras procesar se listan las filas correctas y las rechazadas en paneles independientes.
*   **Riesgos residuales:** Un volumen masivo de errores en el dry-run (ej. 90% del archivo corrupto) puede degradar levemente el tiempo de renderizado de la UI en Streamlit.
*   **Límites de lo implementado:** El aislamiento de registros inválidos se realiza a nivel de validez semántica básica; no corrige discrepancias complejas de forma automática en esta etapa.

---

## Sesión 11: Demo Profesional y Paquete de Pre-Migración SAP (ZIP)
*   **Objetivo:** Unificar la entrega final en un paquete estructurado descargable (.ZIP) y añadir analíticas de impacto financiero/operativo de la limpieza de datos.

### Por qué aporta valor real:
*   Sirve como el principal activo demostrable para procesos de postulación profesional. En lugar de ofrecer descargas desorganizadas, se entrega un "Paquete de Migración SAP" profesional que reduce tiempos de aprobación de negocio.

### Subtareas concretas:
*   [x] **11.1. Empaquetador Maestro (.ZIP):**
    *   Desarrollar la lógica de compresión en Python para descargar un único archivo ZIP conteniendo: `datos_limpios.csv`, `readiness_report.html`, `registros_rechazados.csv` y `auditoria_ejecucion.log`.
*   [x] **11.2. Indicador Financiero y Operativo de Impacto:**
    *   Calcular métricas de valor dentro del Readiness Report HTML: horas estimadas de trabajo manual de Excel ahorradas, coste de riesgo financiero evitado por IBANs no válidos y métricas agregadas de preparación de carga (Ready-to-Load %).
*   [x] **11.3. Narrativa de Producto y Guía de Demostración Técnica:**
    *   Añadir un apartado visual en la app con un guión paso a paso explicando cómo usar la demo para presentar el proyecto a un equipo de IT de SAP.

### Riesgos o dependencias:
*   Depende de librerías de compresión del sistema, aunque se utilizará `zipfile` de la librería estándar de Python para máxima portabilidad.

### Entregables:
*   Generador de archivo comprimido estructurado (.ZIP).
*   Sección de métricas financieras de calidad de datos en el reporte HTML.

### Criterios de aceptación:
*   El botón de descarga del ZIP genera un archivo descargable con el nombre estructurado correspondiente.
*   El ZIP contiene los cuatro archivos y no incluye rutas relativas internas corruptas.

### Cómo verificarla manualmente:
1. Realizar una sanitización de datos de prueba completa.
2. Hacer clic en "Descargar Paquete de Pre-Migración SAP (.ZIP)".
3. Descomprimir localmente el archivo y comprobar la presencia y formato de las cuatro piezas.

### Definition of Done (DoD):
*   **Archivos tocados:** `sanitizer/reports.py` (cálculo de impacto en el reporte HTML), `sanitizer/ui_actions.py` (empaquetado y compresión zip), `app.py` (botón de descarga ZIP y panel de narrativa).
*   **Tests afectados:** Nuevos tests en `tests/test_sap.py` o un archivo específico de reportes para validar la integridad del archivo ZIP generado y las fórmulas de los KPIs financieros.
*   **Validación manual:** Correr la sanitización, descargar el ZIP, descomprimirlo y validar que contiene exactamente los 4 archivos perfectamente estructurados y que las fórmulas del HTML reflejan los valores correctos.
*   **Riesgos residuales:** El cálculo del riesgo financiero es una aproximación estadística basada en costes típicos de devoluciones bancarias y tiempos estándar de remediación manual.
*   **Límites de lo implementado:** El paquete ZIP no está encriptado con contraseña ni incluye control de acceso en esta fase.

---

## Sesión 12: Release Candidate y Certificación de Calidad
*   **Objetivo:** Consolidar la versión candidata V4.0.0 a través de pruebas de rendimiento realistas, optimización de scripts de arranque y congelación de releases.

### Por qué aporta valor real:
*   Garantiza que cualquier usuario, al clonar el repositorio y hacer doble clic en `Iniciar_Interfaz.bat`, tenga una ejecución impecable sin importar su nivel técnico.

### Subtareas concretas:
*   [x] **12.1. Lanzador de Windows Autoinstalable:**
    *   Optimizar `Iniciar_Interfaz.bat` para verificar automáticamente si Python está en PATH, crear un entorno virtual e instalar dependencias antes de lanzar Streamlit.
*   [x] **12.2. Pruebas de Estrés y Rendimiento:**
    *   Generar y validar un test de rendimiento con un archivo de 10,000 registros para comprobar la latencia y la eficiencia de la deduplicación y las reglas de validación cruzada.
*   [x] **12.3. Congelación de Versión y Changelog Definitivo:**
    *   Documentar el control de versiones y compilar el archivo CHANGELOG.md definitivo de la versión V4.0.0.

### Riesgos o dependencias:
*   Restricciones locales de ejecución de scripts en sistemas de usuarios corporativos Windows.

### Entregables:
*   Lanzador `.bat` mejorado.
*   Pipeline CI/CD actualizado con comprobaciones de calidad finales.
*   Garantía de rendimiento certificada.

### Criterios de aceptación / Criterios de Rendimiento Realistas:
*   **Rendimiento en Ingesta y Limpieza:** Procesamiento de 10,000 registros (limpieza semántica e industrial básica) en menos de 15 segundos en un procesador local estándar de 4 núcleos.
*   **Rendimiento en Deduplicación Difusa:** Búsqueda difusa en menos de 25 segundos para 2,000 registros (umbral 85.0 y bloqueo geográfico activo) o en menos de 90 segundos para 10,000 registros.
*   **Arranque del Lanzador:** El script `.bat` arranca correctamente la app en un sistema Windows limpio con Python 3.10+ en menos de 60 segundos (incluyendo la creación del entorno virtual si no existiera).

### Cómo verificarla manualmente:
1. Eliminar el entorno virtual temporal local.
2. Ejecutar `Iniciar_Interfaz.bat`.
3. Comprobar la instalación limpia y el inicio del navegador.

### Definition of Done (DoD):
*   **Archivos tocados:** `Iniciar_Interfaz.bat` (arranque autoinstalable), `tests/test_performance.py` (test de estrés de 10K), `CHANGELOG.md` (congelación).
*   **Tests afectados:** Ejecución completa de la suite (ahora ~35 tests) con 100% de éxito. Test de rendimiento que certifique tiempos estables.
*   **Validación manual:** Borrar la carpeta `.venv` local, ejecutar `Iniciar_Interfaz.bat`, confirmar que se crea el entorno, se instalan las dependencias de `requirements.txt` y se levanta la app automáticamente en el navegador.
*   **Riesgos residuales:** En computadores extremadamente antiguos, los tiempos de procesamiento de deduplicación difusa pueden aumentar exponencialmente debido al algoritmo Levenshtein si no se usa el bloqueo geográfico adecuado.
*   **Límites de lo implementado:** El script `.bat` es compatible únicamente con sistemas Windows (PowerShell/CMD); no se provee un instalador `.sh` equivalente para Mac/Linux.

---

## Sesión 13: Activos de Portfolio y Narrativa Profesional (Post-Release)
*   **Objetivo:** Desarrollar e integrar los activos de comunicación y posicionamiento profesional de DataSanitizer en el repositorio para alinearlo formalmente con la marca personal de Borja Felix Rojas.

### Subtareas concretas:
*   [x] **13.1. Reposicionamiento del Producto:**
    *   Definir la narrativa en español, propuesta de valor, one-liner y pitches diferenciados por audiencia en `portfolio/1_reposicionamiento.md`.
*   [x] **13.2. Ficha Pública de Proyecto:**
    *   Redactar la ficha técnica estructurada en primera persona profesional con stack real y aprendizajes en `portfolio/2_ficha_proyecto.md`.
*   [x] **13.3. Guion de Demostración Práctica:**
    *   Escribir el guion cronometrado de 3 a 5 minutos optimizado para perfiles ocupados en `portfolio/3_guion_demo.md`.
*   [x] **13.4. Bloque Web Odoo:**
    *   Generar los bloques de copia web alineados al diseño e identidad de la marca personal del autor en `portfolio/4_bloque_web.md`.
*   [x] **13.5. Difusión Profesional:**
    *   Elaborar la propuesta de publicación LinkedIn en `portfolio/5_linkedin_post.md`.

### Definition of Done (DoD):
*   **Archivos creados/tocados:** `portfolio/1_reposicionamiento.md`, `portfolio/2_ficha_proyecto.md`, `portfolio/3_guion_demo.md`, `portfolio/4_bloque_web.md`, `portfolio/5_linkedin_post.md`, `roadmap_sesiones.md`, `CHANGELOG.md`.
*   **Versionado:** Se mantiene fijo el software en la versión estable V4.0.0.
*   **Validación manual:** Confirmar que los 5 archivos en `portfolio/` se leen correctamente y siguen el tono e identidad personal del usuario de forma coherente.

