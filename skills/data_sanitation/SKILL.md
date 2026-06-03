---
name: data-sanitation-validation
description: Valida y limpia NIF/CIF/NIE, IBAN (Módulo 97), teléfonos (E.164), y datos maestros industriales SAP (Material Master, BOMs, CA01/CA02, Controlling CO y Costeo Estándar).
---

# Skill de Sanitización y Validación de Datos

Esta habilidad enseña al agente las especificaciones matemáticas e internacionales necesarias para limpiar y verificar datos maestros (administrativos e industriales) con destino a sistemas ERP, especialmente **SAP S/4HANA**.

---

## 1. Identificación Fiscal Española (NIF, NIE, CIF)

La validación fiscal es crítica. SAP rechaza de forma estricta cualquier número fiscal cuyo dígito de control no sea matemáticamente coherente.

### Limpieza Previa
Antes de validar, se deben:
1. Eliminar espacios, guiones, puntos y barras diagonales.
2. Convertir todo a mayúsculas.

### NIF (Personas Físicas con DNI)
- **Estructura**: 8 números + 1 letra de control.
- **Validación**:
  1. Tomar los 8 dígitos numéricos.
  2. Calcular el residuo de la división por 23: `residuo = numero % 23`.
  3. Mapear el residuo a la letra correspondiente usando la cadena de control:
     `0=T, 1=R, 2=W, 3=A, 4=G, 5=M, 6=Y, 7=F, 8=P, 9=D, 10=X, 11=B, 12=N, 13=J, 14=Z, 15=S, 16=Q, 17=V, 18=H, 19=L, 20=C, 21=K, 22=E`.

### NIE (Extranjeros)
- **Estructura**: 1 letra inicial (X, Y o Z) + 7 números + 1 letra de control.
- **Validación**:
  1. Reemplazar la letra inicial por un número: `X` -> `0`, `Y` -> `1`, `Z` -> `2`.
  2. Concatenar este número sustituido con los 7 dígitos centrales para formar un número de 8 dígitos.
  3. Validar con el mismo algoritmo de residuo del NIF (% 23).

### CIF (Personas Jurídicas/Sociedades)
- **Estructura**: 1 letra de tipo de organización (A-H, J, N, P-R, S, U, V, W) + 7 números + 1 dígito de control (puede ser número o letra según el tipo).
- **Algoritmo de Control (Módulo 10)**:
  1. Sumar los dígitos en posiciones pares (2ª, 4ª y 6ª posición):
     `S_pares = digito_2 + digito_4 + digito_6`.
  2. Para cada dígito en posición impar (1ª, 3ª, 5ª y 7ª):
     - Multiplicar por 2.
     - Si el resultado es de dos dígitos, sumar sus dígitos constituyentes (ej. `6 * 2 = 12` -> `1 + 2 = 3`).
     - Sumar todos estos valores resultantes: `S_impares`.
  3. Sumar ambos resultados parciales: `S_total = S_pares + S_impares`.
  4. Obtener el dígito de las unidades de `S_total` (ej. si es 24, tomar 4): `unidades = S_total % 10`.
  5. Calcular el dígito de control teórico: `control = (10 - unidades) % 10`.
  6. **Correspondencia del dígito de control**:
     - Si el CIF empieza con `P, Q, S, W`, el control es **obligatoriamente una letra**: `1=A, 2=B, 3=C, 4=D, 5=E, 6=F, 7=G, 8=H, 9=I, 0=J`.
     - Si empieza con `A, B, E, H`, el control es **obligatoriamente un número**.
     - Para el resto de letras, puede ser **indistintamente número o letra**.

---

## 2. Validación de IBAN (ISO 13616)

La validación de IBAN previene errores de conciliación bancaria y fallos en mandatos SEPA.

### Algoritmo de Módulo 97 (ISO 7064)
1. **Limpieza**: Eliminar espacios y caracteres especiales. Deber tener entre 15 y 34 caracteres (24 para España).
2. **Reordenación**: Mover los 4 primeros caracteres (Código de país + 2 dígitos de control) al final de la cadena.
3. **Conversión Numérica**: Reemplazar cada letra por su valor numérico de dos dígitos (donde `A` = 10, `B` = 11, ..., `Z` = 35).
   - `E` -> 14, `S` -> 28.
   - `ES21` se convierte en `142821`.
4. **Cálculo Matemático**: Dividir el número gigante resultante por 97 y obtener el resto: `resto = numero_gigante % 97`.
5. **Resultado**: El IBAN es **válido** si y solo si el residuo final es exactamente **1** (`resto == 1`).

---

## 3. Validación de Teléfono (Formato E.164)

- **Estructura**: `+[código_país][número_abonado]` sin espacios, guiones ni paréntesis.
- **Longitud máxima**: 15 dígitos.
- **Normalización**:
  - Si el número comienza con `00`, reemplazar `00` por `+`.
  - Si no empieza con `+`, y conocemos el país de destino (ej. España), añadir el prefijo por defecto (`+34`).
  - Eliminar cualquier carácter que no sea numérico o el `+` inicial.

---

## 4. Validación de Datos Maestros Industriales SAP (S/4HANA)

### A. Maestro de Materiales (Material Master — MM01/MM02)
*   **Tipos de Material (Material Types)**:
    *   `ROH` (Materia Prima / Raw Materials): No suele tener lista de componentes (BOM). Su valoración puede ser precio medio variable (`V`) o estándar (`S`).
    *   `HALB` (Semielaborado / Semi-finished Product): Producto intermedio fabricado internamente. Requiere tanto BOM como Ruta de fabricación. Normalmente valorado a precio estándar (`S`).
    *   `FERT` (Producto Terminado / Finished Product): Producto final listo para la venta. Requiere BOM y Ruta. Valorado obligatoriamente a precio estándar (`S`).
*   **Unidades de Medida (UoM)**:
    *   La unidad de medida base (Base UoM) debe ser consistente y no combinarse erróneamente (ej. usar `M` y luego comprar en `MM` sin factores de conversión explícitos).
*   **Precio de Valoración**:
    *   Materiales con tipo de valoración `S` deben tener cargado un precio estándar. Alertar si el precio es `0` o cantidades incoherentes (ej: `99999`).

### B. Listas de Materiales (BOMs — CS01/CS02)
*   **Validación de Cantidades**:
    *   Cantidades negativas solo se permiten en subproductos (co-products) de producción.
    *   Alertar sobre cantidades nulas (`0`) o anomalías (ej: `0.0001` o `> 999`).
*   **Coherencia Estructural**:
    *   Todos los materiales componentes listados en la BOM deben existir previamente en el Maestro de Materiales (MM).

### C. Rutas de Operaciones (CA01/CA02) y Puestos de Trabajo
*   **Tiempos de Operación**:
    *   Tiempos de máquina, preparación (setup) y mano de obra deben ser superiores a `0` para materiales del tipo `HALB` o `FERT` a menos que sean operaciones de inspección de calidad sin costes.
*   **Puestos de Trabajo (Work Centers)**:
    *   Cada operación de la ruta debe estar asociada a un puesto de trabajo existente.

### D. Centros de Coste (KS01)
*   **Obligatoriedad**:
    *   Cada centro de coste debe tener definido un responsable (`VERAK`) y una asignación válida a un Área Funcional para asegurar la imputación contable de costes de fabricación.

### E. Product Costing y Salud de Inventario
*   **Recálculo de Coste Estándar**:
    *   `Coste_Total = Suma(Componentes BOM × Precio_Material) + Suma(Tiempos_Operación CA01/CA02 × Tarifa_Puesto_Trabajo)`.
    *   Detección de discrepancias mayores a un % umbral tolerado entre el coste recalculado y el precio estándar del Material Master.
*   **Saneamiento de Inventario**:
    *   Los stocks no pueden ser negativos en la pre-migración.
    *   Identificar materiales obsoletos (sin consumo en los últimos 24 meses) para excluirlos de la carga en SAP.
