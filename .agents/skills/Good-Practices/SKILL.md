---
name: scripts-pesados-solid
description: Reglas obligatorias para escribir código en proyectos Python/Jupyter. Siempre que el usuario pida un notebook, pipeline, preprocesamiento, limpieza de datos, módulo, clase o cualquier script con lógica extensa o costosa, usa esta skill: la lógica pesada se genera en archivos .py dentro de la carpeta que el usuario indique (por ejemplo src/ScriptCsv/) y el notebook u orquestador solo la importa y la llama. Además, aplica siempre los principios SOLID. Úsala aunque el usuario no mencione "SOLID" ni "módulos", y cada vez que se hable de organizar código, refactorizar o separar responsabilidades.
---

# Scripts pesados en carpeta indicada + SOLID

## 1. Carpeta de destino

1. Antes de escribir código, identifica la carpeta que el usuario indicó para los módulos (ej. `src/ScriptCsv/`). Si no la indicó, PREGÚNTALE; no la inventes.
2. Si la carpeta no existe, créala junto con un `__init__.py`.
3. Toda lógica pesada va en archivos `.py` dentro de esa carpeta. Se considera pesada si cumple al menos una:
   - Más de ~15 líneas o varias etapas encadenadas.
   - Carga, transformación, imputación, validación, exportación o cálculos costosos.
   - Se reutiliza o podría reutilizarse.
4. El notebook (.ipynb) o el script principal solo debe:
   - Importar en la primera celda todas las librerías y los módulos.
   - Llamar funciones/clases del módulo.
   - Mostrar resultados y explicarlos con celdas markdown.
5. Al terminar, explica brevemente qué hace cada módulo y cómo lo llama el notebook, confirmando que la lógica pesada no quedó en el notebook.

## 2. Principios SOLID (siempre)

- **S, responsabilidad única:** una clase o módulo por tarea (cargar, diagnosticar, imputar, validar, exportar). Si un archivo hace dos cosas distintas, sepáralo.
- **O, abierto/cerrado:** agregar un nuevo método (p. ej. otro imputador) se hace creando una clase nueva, no editando las existentes. Usa clases base abstractas (`abc.ABC`) o `Protocol`.
- **L, sustitución de Liskov:** las subclases deben poder reemplazar a su base sin romper el flujo (misma firma y mismo tipo de retorno).
- **I, segregación de interfaces:** interfaces pequeñas y específicas; ninguna clase obligada a implementar métodos que no usa.
- **D, inversión de dependencias:** el orquestador recibe sus dependencias por parámetro (inyección) y depende de abstracciones, no de clases concretas.

## 3. Buenas prácticas de código

- Type hints y docstrings en toda función y clase pública.
- Rutas relativas y semillas fijas para que el notebook corra completo (Run All) en otro equipo.
- No modificar archivos de entrada: trabajar sobre copias en memoria (`df.copy()`), salvo que el usuario pida lo contrario.
- Funciones puras cuando sea posible; evitar variables globales.
- Registrar en una bitácora las decisiones y los cambios aplicados.

## 4. Antes de entregar, verifica

- [ ] ¿Toda la lógica pesada está en la carpeta indicada?
- [ ] ¿El notebook solo importa y llama?
- [ ] ¿Cada módulo tiene una sola responsabilidad?
- [ ] ¿Se puede agregar un comportamiento nuevo sin editar código existente?
- [ ] ¿Las dependencias se inyectan?
- [ ] ¿Hay type hints, docstrings y explicación de cada módulo?
- [ ] ¿Aclaré con el usuario toda duda en lugar de asumir?
