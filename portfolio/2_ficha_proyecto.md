# Ficha Pública de Proyecto — DataSanitizer

Este documento sirve como ficha técnica e informativa para la presentación pública de DataSanitizer en portfolios y redes profesionales. Está redactada en primera persona profesional, reflejando el rigor de la ingeniería de procesos y del control de gestión.

---

## 1. Título del Proyecto
**DataSanitizer: Motor de Calidad de Datos y Pre-Migración ERP**

## 2. Subtítulo de una Línea
*Saneamiento automatizado, validación cruzada y deduplicación de datos maestros industriales sin salir de tu máquina local.*

## 3. Problema que Resuelve
En todo proyecto de migración o implantación de un ERP (como SAP S/4HANA), la calidad de los datos de entrada es el principal cuello de botella. Las herramientas de carga oficiales rechazan de forma repetida las plantillas de importación debido a errores sencillos de formato, campos obligatorios vacíos o inconsistencias de datos lógicos. Tradicionalmente, los consultores funcionales y controllers dedican cientos de horas a depurar y cruzar estos datos de forma manual y artesanal en Microsoft Excel, un proceso lento, costoso y propenso a introducir nuevos errores de tipeo.

## 4. Qué Hace el Sistema
DataSanitizer industrializa la preparación de datos maestros mediante un pipeline estructurado en cinco fases automatizadas:
*   **Diagnóstico de Salud (Health Check):** Analiza en frío el archivo de entrada para identificar vacíos, formatos extraños y codificaciones problemáticas.
*   **Validación Semántica y Fiscal:** Aplica el algoritmo matemático del dígito de control para NIF/CIF/NIE españoles, validación de IBANs europeos (módulo 97) y códigos de identificación BIC.
*   **Coherencia Geográfica Cruzada:** Autocorrige provincias en función del código postal detectado y comprueba la concordancia de país entre cuentas bancarias y códigos BIC.
*   **Reglas de Lógica Industrial (MM/PP/CO):** Detecta inconsistencias críticas en el maestro de materiales (ROH/FERT vs precio estándar), alertas de stock negativo u obsoleto, BOMs complejas (más de 50 componentes), y tiempos nulos en rutas de fabricación.
*   **Deduplicación por Bloqueo:** Agrupa y sugiere la fusión de clientes/proveedores repetidos con variaciones tipográficas mediante el algoritmo Levenshtein, optimizado con claves de bloqueo geográfico para evitar comparaciones N² innecesarias.
*   **Aislamiento de Rechazos:** Separa automáticamente los registros con fallos insalvables a un archivo secundario detallando el motivo de error, permitiendo que el 99% de los registros correctos sigan su flujo de carga.

## 5. Stack Técnico Real
*   **Python 3.10+** como núcleo y orquestador del motor de sanitización.
*   **Pandas** para la manipulación, mapeo e indexación de DataFrames de alto rendimiento.
*   **RapidFuzz** para el cálculo optimizado de similitudes de cadenas mediante distancia de Levenshtein.
*   **Openpyxl** para la estructuración y formateo nativo de libros Excel de staging con sus cabeceras técnicas oficiales de SAP.
*   **Streamlit** como framework ligero para la construcción de la interfaz gráfica interactiva y local.
*   **Zipfile** para el empaquetado en memoria de los entregables en un paquete unificado (.ZIP) sin almacenar datos de usuario.

## 6. Qué Valor Aporta a un Equipo SAP / Negocio / Controlling
*   **Al equipo de migración SAP:** Agiliza la carga de staging eliminando las iteraciones de prueba y error en el Migration Cockpit.
*   **Al negocio:** Reduce drásticamente las horas de trabajo administrativo y de consultoría, acelerando los tiempos del proyecto de migración y reduciendo el riesgo de retrasar el *go-live*.
*   **Al área de Controlling:** Garantiza que los maestros de costes y materiales entren limpios a producción, previniendo errores de valoración de inventarios y desvíos contables posteriores.

## 7. Qué lo Diferencia de una Limpieza Manual en Excel
Microsoft Excel carece de motores de validación matemática complejos integrados de forma nativa para formatos como IBAN o NIF, y las macros de VBA para búsquedas difusas son difíciles de mantener y lentas para grandes volúmenes. DataSanitizer ejecuta estas reglas en milisegundos bajo un pipeline reproducible. Su motor procesa y sanitiza 10,000 registros en **menos de 2 segundos** y realiza la deduplicación de 2,000 registros con bloqueo en **menos de 0.1 segundos**, aislando errores celdas por celda sin riesgo de caídas del software.

## 8. Qué Aprendí Construyéndolo
*   **La importancia del enfoque Local-First:** En datos financieros y maestros de negocio, la privacidad es innegociable. Diseñar una herramienta que no requiere enviar datos a APIs externas en la nube facilita la aprobación de uso por parte de departamentos de IT corporativos.
*   **Hardening y tolerancia a fallos:** El software real debe ser tolerante al desorden. Aprendí a estructurar capturas de excepciones a nivel de celda individual; un error en una fila aislada jamás debe tirar el procesamiento de un archivo de miles de registros.
*   **Autonomía técnica:** Consolidé la capacidad de utilizar Inteligencia Artificial como traductor de mi criterio y lógica de negocio hacia una arquitectura de desarrollo de software limpia, estructurada y profesional.

## 9. Estado Actual del Proyecto
*   **Versión Estable V4.0.0** finalizada y testeada.
*   Suite de pruebas robusta con **50 tests funcionales** integrados que pasan con un 100% de éxito, y **2 pruebas de rendimiento** separadas que certifican los acuerdos de nivel de servicio (SLA) de procesamiento.
*   Lanzador Windows autoinstalable (`Iniciar_Interfaz.bat`) operativo que gestiona de forma autónoma el entorno virtual y el inicio del sistema.

## 10. Próximos Pasos Razonables
*   **Adaptadores adicionales:** Desarrollar plantillas de exportación formateadas para otros ERPs populares como Odoo, Sage y Microsoft Dynamics.
*   **Internacionalización fiscal:** Expandir las reglas de validación de identificaciones fiscales a otros países europeos (ej. VAT/IVA intracomunitario, códigos fiscales en Alemania y Francia).
*   **Modo API/CLI:** Habilitar el motor como un paquete Python importable para pipelines ETL de datos en la nube.
