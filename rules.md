# Reglas de Desarrollo y Disciplina Documental — DataSanitizer

Este documento establece las reglas técnicas y el estándar de calidad documental para el desarrollo incremental de **DataSanitizer**.

---

## 🛠️ Estándares Técnicos de Codificación

### 1. Robustez Celda por Celda (Cell-Level Tolerance)
* Toda validación o limpieza ejecutada sobre los datos debe realizarse a nivel de celda individual dentro de un bloque `try-except` extremadamente acotado.
* **Prohibido**: Capturar excepciones generales en bloques amplios de código que envuelvan la iteración de la tabla, la asignación de columnas, o la instanciación de clases.
* Las excepciones controladas del usuario (como datos mal formateados, campos fiscales corruptos, etc.) deben capturarse, registrarse en el log con el prefijo `WARNING|CELL_ERROR` y enviar la fila al dataframe de rechazados (`rejected_df`).

### 2. No Ocultación de Bugs de Programación
* Los errores en el código (como `KeyError`, `IndexError`, `AttributeError` o errores sintácticos) **deben** propagarse hacia arriba y hacer fallar la aplicación con un traceback visible en la consola de ejecución de Python.
* **Prohibido**: Enmascarar fallos de programación estructurales dentro de excepciones genéricas tipo `Exception` que se reporten como una simple celda inválida.

### 3. Cobertura de Pruebas Unitarias
* Cada nueva regla o componente debe estar cubierto por al menos un test unitario en el directorio `tests/`.
* Los tests deben ejecutarse localmente usando `python run_tests.py` antes de presentar una sesión como completada.
* El número total de tests indicado en el `README.md` debe coincidir exactamente con el reporte de ejecución del script de pruebas.

---

## 📄 Disciplina de Actualización Documental

Para mantener la consistencia absoluta en el repositorio, se establece el siguiente flujo de actualización:

1. **Antes de Programar**:
   * Definir y aprobar el Plan de Implementación de la sesión en el artefacto `implementation_plan.md`.
2. **Durante el Desarrollo**:
   * Llevar el control de tareas pendientes en el archivo `task.md`.
   * Modificar el código funcional y las pruebas asociadas.
3. **Al Finalizar la Sesión (Cierre)**:
   * Ejecutar la validación técnica completa.
   * Realizar la validación manual funcional.
   * Actualizar el archivo `roadmap_sesiones.md`, marcando la sesión como completada (`[x]`).
   * Añadir la sección detallada de cambios en `CHANGELOG.md` siguiendo el formato *Keep a Changelog* e incrementando la versión semántica.
   * Modificar `README.md` si cambian las funcionalidades disponibles o el conteo de pruebas unitarias.

---

## 🏆 Definition of Done (DoD) General por Sesión

Una sesión se considera terminada y lista para revisión del Lead Developer cuando cumple con:
- [ ] El código de la sesión está implementado sin mezclar lógica de sesiones futuras.
- [ ] Todos los tests de la suite pasan satisfactoriamente.
- [ ] No existen excepciones capturadas de forma redundante o silenciosa.
- [ ] Se ha realizado una verificación manual de extremo a extremo de las nuevas características en la interfaz Streamlit.
- [ ] El `roadmap_sesiones.md`, `CHANGELOG.md` y `README.md` están actualizados y alineados.
