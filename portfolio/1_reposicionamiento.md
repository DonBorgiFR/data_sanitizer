# Reposicionamiento y Narrativa de Producto — DataSanitizer

Este documento define la narrativa estratégica y el posicionamiento de DataSanitizer, integrando la herramienta de forma coherente dentro del perfil profesional de **Borja Felix Rojas**.

---

## 1. Narrativa de Producto
En proyectos de implantación y migración de sistemas ERP (como SAP S/4HANA, Odoo o Sage), la calidad de los datos de entrada determina la velocidad y viabilidad del *go-live*. Las bases de datos operativas de origen suelen arrastrar años de desorden: identificadores fiscales inválidos, códigos geográficos contradictorios, registros duplicados por variaciones tipográficas y estructuras industriales inconsistentes. 

**DataSanitizer** pone orden en este caos. Es un motor de diagnóstico y sanitización portátil que actúa como un filtro de calidad previo a la carga de datos. Automatiza la depuración semántica, ejecuta validaciones cruzadas y aísla de forma segura los registros erróneos graves. De este modo, los consultores y controllers de gestión dejan de perder horas limpiando archivos Excel de forma manual e ineficiente, y operan sobre un flujo controlado de información lista para el staging.

---

## 2. Propuesta de Valor
*   **Privacidad Radical (Local-First):** Diseñado con una filosofía donde toda la computación ocurre en la máquina local del usuario. Los datos sensibles de negocio, fiscales o bancarios jamás salen del entorno de ejecución local, eliminando riesgos de cumplimiento y seguridad.
*   **Reducción del Rework de Carga:** Identifica, reporta y separa preventivamente registros huérfanos o con errores críticos de formato antes de intentar la importación en el *Migration Cockpit* de SAP, reduciendo a cero los rechazos en la plataforma de destino.
*   **Integración de Reglas de Negocio Industriales:** Valida la coherencia de estructuras lógicas de compras, controlling y producción (Material Master, BOMs, Rutas y Centros de Coste) mediante heurísticas de control cruzadas que ningún validador estándar de bases de datos puede evaluar de forma nativa.

---

## 3. One-Liner (LinkedIn / Web)
> *"Diseño herramientas y sistemas de decisión para convertir la complejidad, el desorden operativo y los datos defectuosos en flujos de información limpios, controlados y listos para sistemas ERP."*

---

## 4. Caso de Uso Real: Saneamiento y Pre-Migración Industrial

*   **El Reto:** Una compañía industrial prepara su migración a SAP S/4HANA. El inventario histórico y el maestro de materiales (10,000 registros) están distribuidos en archivos fragmentados con pesos negativos, unidades de medida inconsistentes, y centros de coste sin responsable asignado. El equipo técnico estima semanas de depuración manual.
*   **La Acción:** Se pasa la base de datos por el motor DataSanitizer aplicando de forma interactiva la plantilla oficial de `Material Master (MM)`. El motor analiza la calidad en frío (Health Check), aplica las transformaciones semánticas, realiza la validación industrial cruzada de controlling y aísla los descartes críticos de forma secuencial en menos de 2 segundos.
*   **El Resultado:** 
    *   **9,295 registros sanitizados** y exportados directamente a plantillas de carga de staging.
    *   **705 registros descartados** aislados automáticamente en un archivo secundario con motivos claros del fallo (ej: campos requeridos vacíos) para su corrección focalizada.
    *   **Cero rechazos** durante la carga en el cockpit de SAP, ahorrando aproximadamente 180 horas de consultoría funcional y depuración manual en Excel.

---

## 5. Pitches de Elevador (Elevator Pitches)

### A. Pitch Técnico (Orientado a Equipos de IT e Integradores de Datos)
> *"DataSanitizer es un motor modular en Python diseñado bajo una arquitectura de pipelines de fases privadas independientes (mapping, cleansing, cross-validation, industrial rules, dedupe y exportación unificada). El sistema valida e implementa transformaciones en tipos complejos (NIF/CIF, IBAN, BIC, CP, Direcciones) aislando a nivel de celda cualquier excepción de ejecución sin interrumpir el procesamiento general de la tabla. Toda la exportación se unifica en un paquete comprimido en memoria (.ZIP) que separa los datos de carga (limpios de columnas de control y codificados con BOM UTF-8 con delimitador ;) de las trazas del log de auditoría detallado para el cumplimiento de estándares de IT."*

### B. Pitch de Negocio (Orientado a CFOs, Directores de Controlling y Operaciones)
> *"El principal cuello de botella en la implantación de un ERP no es la tecnología, sino el caos de datos heredados. Limpiar estos datos manualmente en hojas de cálculo consume cientos de horas de consultores funcionales caros y aumenta la probabilidad de introducir nuevos errores. DataSanitizer industrializa la calidad del dato: procesa y audita miles de registros en segundos, calcula el impacto financiero del riesgo evitado por datos contables erróneos y previene retrasos costosos en el lanzamiento del ERP al asegurar que la información cargada cuadra a la primera."*

### C. Pitch para Hiring Manager / Reclutador (Demostración de Criterio de Producto)
> *"DataSanitizer es una muestra real de mi forma de trabajar: combino la rigurosidad analítica de la ingeniería industrial con la agilidad de la automatización para construir soluciones portables de extremo a extremo. No soy solo un analista de datos; diseño herramientas con criterio de negocio. En este proyecto me responsabilicé de todo el ciclo de vida: desde el análisis de los problemas reales de migración de datos maestros en PYMEs, pasando por el desarrollo de la lógica del motor y su optimización de rendimiento (10k registros limpiados en menos de 2 segundos), hasta la creación de una interfaz visual y un onboarding que permite a perfiles no técnicos operar el sistema con total autonomía."*
