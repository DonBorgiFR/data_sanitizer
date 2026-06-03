# Estrategia de Difusión Profesional — DataSanitizer

Este documento contiene una propuesta de publicación (post) estructurada para LinkedIn, redactada bajo un tono profesional, técnico y realista, evitando cualquier tipo de exageración o marketing vacío para reflejar con total fidelidad el valor del proyecto y el perfil del autor.

---

## 📢 Publicación Propuesta para LinkedIn

**Tema:** Calidad de datos, control de gestión y pre-migración de datos en sistemas ERP.

```text
En la implantación de un ERP (como SAP S/4HANA, Sage u Odoo), hay una fase crítica que suele subestimarse hasta que es demasiado tarde: la migración de datos maestros.

El caos de datos de origen (identificadores fiscales rotos, códigos geográficos contradictorios, duplicados y reglas industriales inconsistentes) no es solo un problema estético de formato; es la causa directa del 80% de los retrasos en los go-live y de facturas de consultoría imprevistas por retrabajo.

Para resolver este dolor operativo de forma automatizada, robusta y reproducible sin depender de hojas de cálculo Excel frágiles, he desarrollado DataSanitizer.

Se trata de un motor portable en Python diseñado con filosofía local-first (los datos nunca salen de tu ordenador local por privacidad) que limpia, valida y audita datos maestros antes de intentar subirlos al sistema.

¿Qué hace exactamente el motor?
1. Sanitización semántica y fiscal: Validación matemática de NIF/CIF y códigos IBAN/BIC.
2. Coherencia geográfica: Autocorrección cruzada de provincias por código postal.
3. Reglas industriales de controlling: Chequea la consistencia de tipos de material, BOMs complejas y tiempos de ruta antes de generar el staging oficial.
4. Deduplicación por bloqueo: Comparación difusa Levenshtein optimizada por cercanía geográfica y primeras letras del nombre comercial.
5. Aislamiento automático: Separa los registros rechazados con motivos de error en una cola secundaria para que el resto del archivo siga su proceso de carga sin interrupciones.

Rendimiento medido (V4.0.0 estable):
- Limpieza semántica e industrial: 10,000 registros procesados en menos de 2 segundos.
- Deduplicación difusa por bloqueo: 2,000 registros analizados en menos de 0.1 segundos.

Este proyecto es la manifestación de mi perfil: la rigurosidad del control de gestión combinada con la agilidad de la automatización técnica. Menos ruido en la operación, más rentabilidad en los sistemas.

He liberado el código del proyecto y he integrado una pequeña interfaz en Streamlit para que cualquier consultor pueda probarlo con sus archivos de staging de SAP.

👉 Enlace al repositorio y documentación técnica: https://github.com/DonBorgiFR/data_sanitizer

¿Cómo gestionan en sus organizaciones la preparación de datos previa a la implantación de un software de gestión? Los leo.

#ControlDeGestión #SAP #DataQuality #Automatización #IngenieríaIndustrial #Python
```
