# DataSanitizer: ERP Data Quality & Pre-Migration Suite (V4.0.0)

[![Demo en Vivo](https://img.shields.io/badge/Demo%20en%20Vivo-https%3A%2F%2Fbfr--datasanitizer.streamlit.app%2F-red?style=for-the-badge&logo=streamlit&logoColor=white)](https://bfr-datasanitizer.streamlit.app/)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Borja%20Felix%20Rojas-blue?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/borjafelixrojas/)

**DataSanitizer** es una plataforma integral de diagnóstico, sanitización, validación matemática y deduplicación de datos maestros de negocio. Diseñada específicamente para dar soporte a **implantaciones y migraciones de ERPs (SAP S/4HANA, Sage, Odoo, etc.)**, esta herramienta permite mitigar el caos de datos previo a la carga, asegurando el cumplimiento estricto de las reglas fiscales y la integridad del modelo de datos de producción.

---

## 💼 Valor de Negocio en Migraciones SAP/ERP

En todo proyecto de implantación de sistemas ERP, la calidad de la carga de datos crudos es uno de los mayores cuellos de botella (causando retrasos en el go-live y fallos reiterados en el *Migration Cockpit* de SAP). DataSanitizer resuelve esto en tres frentes:

1. **Garantía Fiscal e Integridad Bancaria:** Validación matemática rigurosa de NIF/NIE/CIF (España) e IBAN/BIC internacional antes de intentar la importación.
2. **Validación de Lógica Industrial y Controlling (MM/PP/CO):** Comprobaciones cruzadas de consistencia en maestros de materiales (ROH/FERT), listas de materiales (BOMs), rutas de fabricación con tiempos y jerarquías de centros de coste (CO).
3. **Deduplicación Difusa Inteligente:** Agrupación y fusión de clientes/proveedores repetidos con nombres ligeramente variados mediante comparación difusa (Levenshtein) optimizada con bloqueo (*blocking*).

---

## 🚀 Guía de Inicio Rápido (Usuarios No Programadores)

Si eres consultor funcional, analista de negocio o usuario clave de migración:

1. Localiza la carpeta del proyecto en tu explorador de archivos.
2. Haz **doble clic** en el archivo **`Iniciar_Interfaz.bat`**.
3. Se abrirá automáticamente la plataforma visual en tu navegador web (por defecto en `http://localhost:8501`).
4. **Flujo de Trabajo:**
   * **Paso 1: Carga y Diagnóstico:** Sube tu archivo sucio. Obtén un Health Check visual del estado del archivo.
   * **Paso 2: Mapeo:** Asocia tus columnas al formato SAP usando plantillas predefinidas.
   * **Paso 3: Fusión:** Evalúa y fusiona los duplicados sugeridos.
   * **Paso 4: Descarga:** Descarga tus datos limpios y tu Readiness Report HTML ejecutivo.

---

## 🛠️ Estructura del Ecosistema

- **`app.py`**: Interfaz de usuario interactiva y visual basada en Streamlit.
- **`Iniciar_Interfaz.bat`**: Lanzador automatizado para Windows (cero configuración).
- **`cli.py`**: Interfaz de comandos (CLI) de alto rendimiento para automatizaciones e integración de scripts.
- **`sanitizer/`**:
  * `core.py`: Motor orquestador que ejecuta la sanitización dividida en fases privadas claras.
  * `dedupe.py`: Motor de deduplicación difusa y políticas de fusión.
  * `reports.py`: Generador de informes de preparación (Readiness Report) interactivos HTML.
  * `diagnostics.py`: Diagnóstico de salud e inferencia de tipos de datos en frío.
  * `sap_templates.py`: Plantillas técnicas predefinidas del Migration Cockpit (BP, MM, BOM, Routings, Cost Centers).
  * `rules/`: Módulos de limpieza especializada (Fiscales, IBAN, BIC, Geográficos, Direcciones).
- **`tests/`**: Suite de 50 pruebas funcionales automatizadas que certifican la robustez matemática del motor, además de 2 pruebas dedicadas de rendimiento.

---

## 📦 Paquete de Descarga de Migración Consolidado (ZIP)

El botón de descarga del paquete genera un archivo comprimido unificado en formato `.ZIP` con la salida oficial de migración y auditoría requerida por IT:

### Contenido obligatorio del ZIP (Versión V4.0.0):
*   **`datos_limpios.csv`**: Tabla de datos maestros saneados y listos para la importación, codificado en UTF-8-sig (con BOM) y con delimitador de punto y coma (`;`). Se excluyen todas las columnas auxiliares de control (`*_VALID`, `*_ERROR`, `_CLEAN_LOG`).
*   **`registros_rechazados.csv`**: Registros con errores críticos descartados durante la sanitización para permitir procesar el archivo. Si no hay rechazos, se exporta vacío únicamente con la fila de cabeceras de columnas.
*   **`readiness_report.html`**: Reporte visual e interactivo de preparación de datos (Readiness Report), con indicadores clave de negocio (horas ahorradas, riesgo financiero evitado, tasa de carga) y diagnóstico detallado.
*   **`auditoria_ejecucion.log`**: Registro de ejecución detallado con metadatos (fecha, plantilla, registros procesados) y logs de advertencias/errores por celda.

### Anexos Opcionales (Heredados de Sesión 8):
*   **`staging_sap_load.xlsx` (o `staging_load.xlsx`)**: El libro Excel de preparación/staging de SAP. Se incluye si existen resultados de análisis de costes estándar o salud de inventario.
*   **`full_audit_sanitized.xlsx`**: El libro Excel completo de auditoría de datos, incluyendo columnas técnicas del motor.
*   **`costing_simulation.csv`**: Tabla de simulación de costes de controlling (se genera al procesar estructuras de coste con BOM y hojas de ruta).
*   **`inventory_health.csv`**: Tabla enriquecida del estado del stock con análisis ABC.

> [!NOTE]
> **Compatibilidad SAP**: El archivo Excel de staging se ofrece como un cuaderno de preparación intermedio para la validación previa de los datos de migración. No sustituye ni pretende emular al 100% las plantillas oficiales en formato XML Spreadsheet 2003 descargadas directamente desde el *Migration Cockpit* de SAP (LTMC).

---

## 🖥️ Uso por Consola (Desarrolladores y Automatización)

Para integrar DataSanitizer en pipelines automatizados de ETL:

```bash
python cli.py --input "datos_sucios.csv" --types "{\"CIF\": \"tax_id\", \"CP\": \"postal_code\", \"DIRECCION\": \"address\"}"
```

### Argumentos del CLI

- `-i`, `--input`: Ruta al archivo CSV/Excel de entrada (Obligatorio).
- `-o`, `--output`: Ruta de salida para el CSV limpio (Opcional, por defecto `sanitized_<nombre>.csv`).
- `-m`, `--mapping`: JSON con la equivalencia de nombres de cabecera.
- `-t`, `--types`: JSON definiendo los tipos semánticos para cada columna.
- `-d`, `--dedup`: Nombre de columna mapeada sobre la que buscar duplicados difusos.
- `--health-check`: Muestra una auditoría rápida de nulos por consola.

---

## 📊 Tipos Semánticos Soportados

El motor aplica transformaciones específicas basadas en el tipado de columna configurado:
- **`text`**: Limpieza de dobles espacios, mayúsculas normativas y eliminación de caracteres de escape.
- **`tax_id`**: Validación estricta del algoritmo del dígito de control de NIF/NIE/CIF (España). Genera columnas de estado `_VALID` y `_ERROR`.
- **`iban`**: Comprobación matemática SEPA módulo 97 y validación de longitud según país.
- **`bic`**: Chequeo de estructura SWIFT de 8 u 11 caracteres y verificación de correspondencia país con el IBAN.
- **`postal_code`**: Validación del rango de códigos postales españoles (01000 - 52999) y corrección de ceros a la izquierda.
- **`province`**: Autocorrección y normalización inteligente a partir del Código Postal detectado.
- **`address`**: Estandarización de tipos de vía españoles (C/, Calle, Av.) y división física en: `_TIPO_VIA`, `_NOMBRE_VIA`, `_NUMERO` y `_PISO`.

---

## 🧪 Pruebas Unitarias y Certificación de Rendimiento

El motor cuenta con pruebas robustas ejecutadas automáticamente para certificar la calidad:
* **Pruebas Funcionales (50 pruebas):** Ejecutadas por defecto para asegurar la estabilidad lógica y matemática.
  ```bash
  python run_tests.py
  ```
* **Pruebas de Rendimiento (2 pruebas):** Aisladas de la suite por defecto para evitar fallos de hardware en CI, pero ejecutables de forma explícita:
  - **Ejecución directa:**
    ```bash
    python -m tests.test_performance
    ```
  - **Integrada con la suite funcional:**
    ```bash
    python run_tests.py --include-performance
    ```

---

## 📅 Roadmap de Producto (Ciclo de Vida Ampliado)

El desarrollo del proyecto está estructurado en hitos incrementales para llevar el motor a un nivel comercial estable:

1. **Sesión 1 a 11 (Completadas ✅):** Carga inteligente, validaciones (NIF/IBAN/BIC/CP), UI interactiva, dedupe difuso, reglas industriales MM/PP/CO, costes estándar, inventario, wizard guiado, onboarding, tolerancia extrema, empaquetado ZIP principal, KPIs financieros/operativos de negocio, y Guía de Demostración.
2. **Sesión 12 (Certificación Final V4.0.0 🏁):** Pruebas de estrés de 10K registros, optimización del lanzador `.bat` y congelación de release estable (Completada ✅).
