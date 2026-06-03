# Guion de Demostración Práctica (3 a 5 Minutos) — DataSanitizer

Este documento define el guion estructurado y cronometrado para realizar demostraciones visuales de DataSanitizer ante consultores ERP, responsables de controlling, directores de IT o reclutadores en procesos de selección.

---

## 📋 Ficha Técnica de la Demo
*   **Duración Objetivo:** 4 minutos (240 segundos).
*   **Perfil de la Audiencia:** Consultores SAP, Controllers de Gestión, Directores de IT o Hiring Managers.
*   **Dataset a utilizar:** Un archivo sintético de 10,000 registros de Maestro de Materiales (`Material Master`) con incidencias controladas (semilla 42, generado en `tests/test_performance.py`).
*   **Objetivo de Comunicación:** Demostrar que el software resuelve un punto de dolor real de migración con velocidad, resiliencia y resguardo estricto de la privacidad (local-first).

---

## ⏱️ Estructura Minuto a Minuto

### Minuto 0:00 - 0:45 | Apertura y Diagnóstico de Salud (Health Check)
*   **Acción Visual:** Compartir la interfaz de Streamlit vacía. Cargar el archivo de demostración en la barra lateral. Mostrar cómo aparece instantáneamente el panel de **Diagnóstico de Salud**.
*   **Frase de Apertura (Hook):** 
    > *"La mala calidad de los datos es la causa principal del retraso en las migraciones de sistemas ERP. Hoy les mostraré cómo DataSanitizer automatiza la depuración y validación lógica de un maestro de 10,000 materiales en menos de dos segundos, garantizando la compatibilidad de carga antes de iniciar la importación."*
*   **Mensaje Clave:** Resaltar la filosofía *Local-First* del proyecto: la carga y el procesamiento ocurren estrictamente en el navegador/máquina local, asegurando que ningún dato financiero o confidencial sea transmitido a la nube. Mostrar en el gráfico circular del diagnóstico el porcentaje inicial de celdas vacías y duplicados exactos en frío.

### Minuto 0:45 - 1:45 | Mapeo Automatizado y Reglas Industriales
*   **Acción Visual:** Desplegar el selector de plantillas en la barra lateral y seleccionar **`Material Master (MM)`**. Mostrar cómo el mapeador de columnas asocia de forma automática las cabeceras de origen con los campos destino oficiales de SAP S/4HANA y les asigna sus tipos semánticos.
*   **Narrativa:** 
    > *"El sistema asocia automáticamente los campos y preconfigura el tipado semántico. Pero no se limita a un formateo de texto básico: al seleccionar la plantilla de Materiales, el motor activa validaciones industriales cruzadas de controlling y producción. Comprueba si los materiales ROH o FERT tienen sus controles de precio asignados correctamente y detecta incoherencias en las unidades de medida."*

### Minuto 1:45 - 2:45 | Previsualización (Dry Run) y Velocidad de Ejecución
*   **Acción Visual:** Hacer clic en **🔍 Previsualizar Cambios (Dry Run)**. Mostrar la tabla comparativa tabulada del "Antes y Después" para las primeras 5 filas. Explicar el cambio y hacer clic en **Ejecutar Pre-Migración SAP Completa**.
*   **Narrativa:**
    > *"Antes de lanzar un procesamiento masivo, el consultor puede verificar en un Dry Run interactivo exactamente cómo se transformarán sus datos. Al dar inicio a la sanitización, el motor procesa, normaliza y valida los 10,000 registros de forma resiliente: si un dato en una celda aislada está corrupto o lanza una excepción, el sistema lo captura, lo registra en el log y continúa la ejecución sin caídas de la aplicación."*
*   **Métricas a Destacar:** Mostrar en pantalla el tiempo de procesamiento reportado por la UI: **menos de 2 segundos** para los 10,000 materiales.

### Minuto 2:45 - 4:00 | Segregación de Rechazados y Entrega del Paquete ZIP
*   **Acción Visual:** Mostrar el panel de **Registros Rechazados**. Destacar que las filas con errores insalvables (como campos requeridos vacíos) se separaron de la tabla principal para no bloquear la carga. Finalmente, hacer clic en el botón de descarga del **Paquete de Pre-Migración (.ZIP)**.
*   **Narrativa:**
    > *"Los registros que harían fallar la importación en SAP se aíslan automáticamente en una cola de rechazos con motivos detallados. El resto se empaqueta en un archivo .ZIP consolidado de doble salida que contiene el archivo de carga limpio de columnas técnicas de control y codificado para compatibilidad Excel, el reporte ejecutivo HTML con indicadores financieros como las horas de trabajo manual ahorradas, y el registro de trazas detallado para la aprobación técnica de IT."*
*   **Frase de Cierre Memorable:**
    > *"DataSanitizer demuestra que no hace falta sobredimensionar la infraestructura de software para obtener control y fiabilidad operativa: con lógica de negocio clara y automatización local, los datos de migración cuadran a la primera."*

---

## 🚫 Qué NO Enseñar (Para No Perder Foco)
*   **No abrir VS Code ni mostrar código fuente:** La audiencia del demo busca validar la usabilidad y la resolución del problema de negocio, no el desarrollo sintáctico de Python.
*   **No explicar la suite de pruebas Pytest:** Es una garantía de ingeniería interna; se menciona como respaldo de calidad pero no se enseña su ejecución en terminal.
*   **No profundizar en las expresiones regulares de validación:** Evitar explicar las matemáticas detrás de la validación del IBAN o NIF/CIF para no aburrir a perfiles de negocio.
