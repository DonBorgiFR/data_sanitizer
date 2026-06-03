# Gobernanza de Agentes de IA — DataSanitizer

Este documento define la estructura de gobernanza, roles de los agentes de IA y límites de modificación en el repositorio del proyecto **DataSanitizer**.

---

## 🤖 Roles de Agentes y Responsabilidades

| Rol | Agente Responsable | Ámbito de Modificación | Herramientas Permitidas | Límites Estrictos |
| :--- | :--- | :--- | :--- | :--- |
| **Developer Assistant** | `Antigravity` | Código funcional (`sanitizer/`, `app.py`, `cli.py`), tests y documentación. | Edición de código, creación de archivos, ejecución de comandos locales. | No puede saltarse sesiones del roadmap. No puede mezclar lógica de sesiones pendientes. |
| **Codebase Researcher** | Subagente `research` | Ninguno (Lectura exclusiva). | Búsqueda grep, visualización de archivos, lectura de URLs. | Tiene estrictamente prohibido usar herramientas de escritura o modificar archivos. |
| **Lead Developer (Humano)** | `USER` | Todo el repositorio. | Interfaz Streamlit, git, despliegues. | Autoridad última sobre la aprobación de planes de implementación y cierre de sesiones. |

---

## 🚧 Zonas de Control y Modificación

### 1. Código Funcional (`sanitizer/`)
* **Propósito**: Contiene el motor de sanitización, lógica de deduplicación, generación de reportes y reglas de validación.
* **Política de modificación**: Solo se permite modificar archivos directamente relacionados con la sesión aprobada y activa. Cualquier refactorización estructural fuera de este alcance requiere un plan de refactorización previo aprobado.

### 2. Suite de Pruebas (`tests/`)
* **Propósito**: Validar la robustez matemática, de rendimiento e integración del motor.
* **Política de modificación**: Cada regla o funcionalidad añadida en una sesión debe ir acompañada de su test unitario o de integración correspondiente en el directorio de pruebas. Las pruebas existentes no deben alterarse para camuflar fallos, sino corregirse si los requisitos de negocio cambian.

### 3. Documentación del Repositorio (`.md`)
* **Propósito**: Servir como la fuente de verdad operativa y de control del ciclo de vida.
* **Política de modificación**: Debe actualizarse incrementalmente en cada sesión. Ningún agente puede modificar archivos de código sin que la documentación refleje con total fidelidad el estado actual.

---

## ⚠️ Protocolo ante Desviaciones de Agentes
Si un agente de IA detecta una inconsistencia o comete un error de implementación (por ejemplo, una discrepancia en los resultados de validación):
1. **Pausa de Ejecución**: Detener el desarrollo activo.
2. **Reconocimiento Explícito**: Documentar y presentar al usuario la desviación exacta entre el comportamiento esperado y el observado.
3. **Plan de Acción de Corrección**: Presentar una corrección acotada y directa para corregir el bug antes de proponer cualquier otra funcionalidad nueva.
