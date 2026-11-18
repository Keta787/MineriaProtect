# Reglas de Negocio Extraídas · `7.0_arbol_decision.ipynb`

> **Pregunta central**: *¿El perfil de un oficio separa a las personas que lo repiten de las que lo ejercen por primera vez?*

## Advertencia Metodológica (Lo que las reglas NO dicen)
- **No son reglas causales**: describen asociaciones empíricas en el historial laboral, no causas directas de repetición.
- **Clasifican perfiles de oficios, no individuos**: ninguna regla debe usarse para tomar decisiones automatizadas sobre candidatos o trabajadores individuales (principio de privacidad y ética).
- **Cuidado con la exactitud global**: dado que la clase `reincide = 0` representa ~70% de los registros, una exactitud cercana al 70% puede lograrse sin detectar ningún caso positivo; por ello cada regla se evalúa por su tasa de clase 1 frente a la tasa base (30.01%) y su **Lift**.

### Árbol 1 · ISCO · Regla 1 (Hoja 4)
- **Condiciones**: `NO pertenece a [4 · Personal de apoyo administrativo] Y NO pertenece a [1 · Directores y gerentes] Y NO pertenece a [7 · Oficiales, operarios y artesanos] Y NO pertenece a [8 · Operadores de instalaciones y máquinas]`
- **Lectura en español**: Regla 1 (Árbol 1 · ISCO, Hoja 4): SI el registro de empleo cumple que [NO pertenece a [4 · Personal de apoyo administrativo] Y NO pertenece a [1 · Directores y gerentes] Y NO pertenece a [7 · Oficiales, operarios y artesanos] Y NO pertenece a [8 · Operadores de instalaciones y máquinas]], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 1,017,277 registros (73.13% del total) con una tasa empírica de reincidencia de 32.58% frente a la tasa base de 30.01% (Lift = 1.09x). En Test comprende 254,958 registros con tasa de 32.54% frente a 29.97% base (Lift = 1.09x).

### Árbol 1 · ISCO · Regla 2 (Hoja 7)
- **Condiciones**: `NO pertenece a [4 · Personal de apoyo administrativo] Y SÍ pertenece a [1 · Directores y gerentes]`
- **Lectura en español**: Regla 2 (Árbol 1 · ISCO, Hoja 7): SI el registro de empleo cumple que [NO pertenece a [4 · Personal de apoyo administrativo] Y SÍ pertenece a [1 · Directores y gerentes]], ENTONCES el árbol clasifica el perfil del oficio con baja propensión a reincidencia / ejercicio único (predice reincide = 0). En Train agrupa 81,000 registros (5.82% del total) con una tasa empírica de reincidencia de 22.07% frente a la tasa base de 30.01% (Lift = 0.73x). En Test comprende 19,873 registros con tasa de 21.37% frente a 29.97% base (Lift = 0.71x).

### Árbol 2 · Nivel educativo · Regla 1 (Hoja 4)
- **Condiciones**: `nivel_educativo_ord <= 2.5 (hasta Bachelor (2)) Y nivel_educativo_ord <= 1.5 (hasta Secondary school (1)) Y nivel_educativo_ord > 0.5 (desde Secondary school (1) o superior)`
- **Lectura en español**: Regla 1 (Árbol 2 · Nivel educativo, Hoja 4): SI el registro de empleo cumple que [nivel_educativo_ord <= 2.5 (hasta Bachelor (2)) Y nivel_educativo_ord <= 1.5 (hasta Secondary school (1)) Y nivel_educativo_ord > 0.5 (desde Secondary school (1) o superior)], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 548,687 registros (39.44% del total) con una tasa empírica de reincidencia de 31.09% frente a la tasa base de 30.01% (Lift = 1.04x). En Test comprende 136,581 registros con tasa de 31.20% frente a 29.97% base (Lift = 1.04x).

### Árbol 2 · Nivel educativo · Regla 2 (Hoja 3)
- **Condiciones**: `nivel_educativo_ord <= 2.5 (hasta Bachelor (2)) Y nivel_educativo_ord <= 1.5 (hasta Secondary school (1)) Y nivel_educativo_ord <= 0.5 (hasta No reportado (0))`
- **Lectura en español**: Regla 2 (Árbol 2 · Nivel educativo, Hoja 3): SI el registro de empleo cumple que [nivel_educativo_ord <= 2.5 (hasta Bachelor (2)) Y nivel_educativo_ord <= 1.5 (hasta Secondary school (1)) Y nivel_educativo_ord <= 0.5 (hasta No reportado (0))], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 160,664 registros (11.55% del total) con una tasa empírica de reincidencia de 30.80% frente a la tasa base de 30.01% (Lift = 1.03x). En Test comprende 40,270 registros con tasa de 30.54% frente a 29.97% base (Lift = 1.02x).

### Árbol 2 · Nivel educativo · Regla 3 (Hoja 5)
- **Condiciones**: `nivel_educativo_ord <= 2.5 (hasta Bachelor (2)) Y nivel_educativo_ord > 1.5 (desde Bachelor (2) o superior)`
- **Lectura en español**: Regla 3 (Árbol 2 · Nivel educativo, Hoja 5): SI el registro de empleo cumple que [nivel_educativo_ord <= 2.5 (hasta Bachelor (2)) Y nivel_educativo_ord > 1.5 (desde Bachelor (2) o superior)], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 473,842 registros (34.06% del total) con una tasa empírica de reincidencia de 30.75% frente a la tasa base de 30.01% (Lift = 1.02x). En Test comprende 118,038 registros con tasa de 30.64% frente a 29.97% base (Lift = 1.02x).

### Árbol 3 · Competencias · Regla 1 (Hoja 28)
- **Condiciones**: `n_skills_competence > 18.5 (19 o más) Y n_skills_essential > 20.5 (21 o más) Y n_skills_knowledge > 25.5 (26 o más) Y n_skills_competence > 38.00`
- **Lectura en español**: Regla 1 (Árbol 3 · Competencias, Hoja 28): SI el registro de empleo cumple que [n_skills_competence > 18.5 (19 o más) Y n_skills_essential > 20.5 (21 o más) Y n_skills_knowledge > 25.5 (26 o más) Y n_skills_competence > 38.00], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 12,616 registros (0.91% del total) con una tasa empírica de reincidencia de 63.68% frente a la tasa base de 30.01% (Lift = 2.12x). En Test comprende 3,053 registros con tasa de 63.15% frente a 29.97% base (Lift = 2.11x).

### Árbol 3 · Competencias · Regla 2 (Hoja 21)
- **Condiciones**: `n_skills_competence > 18.5 (19 o más) Y n_skills_essential <= 20.5 (20 o menos) Y n_skills_knowledge > 0.5 (1 o más)`
- **Lectura en español**: Regla 2 (Árbol 3 · Competencias, Hoja 21): SI el registro de empleo cumple que [n_skills_competence > 18.5 (19 o más) Y n_skills_essential <= 20.5 (20 o menos) Y n_skills_knowledge > 0.5 (1 o más)], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 76,910 registros (5.53% del total) con una tasa empírica de reincidencia de 53.38% frente a la tasa base de 30.01% (Lift = 1.78x). En Test comprende 19,213 registros con tasa de 52.94% frente a 29.97% base (Lift = 1.77x).

### Árbol 3 · Competencias · Regla 3 (Hoja 7)
- **Condiciones**: `n_skills_competence <= 18.5 (18 o menos) Y n_skills_essential <= 10.5 (10 o menos) Y n_skills_essential > 9.5 (10 o más) Y n_skills_knowledge <= 3.5 (3 o menos)`
- **Lectura en español**: Regla 3 (Árbol 3 · Competencias, Hoja 7): SI el registro de empleo cumple que [n_skills_competence <= 18.5 (18 o menos) Y n_skills_essential <= 10.5 (10 o menos) Y n_skills_essential > 9.5 (10 o más) Y n_skills_knowledge <= 3.5 (3 o menos)], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 85,327 registros (6.13% del total) con una tasa empírica de reincidencia de 34.94% frente a la tasa base de 30.01% (Lift = 1.16x). En Test comprende 21,317 registros con tasa de 34.98% frente a 29.97% base (Lift = 1.17x).

### Árbol 3 · Competencias · Regla 4 (Hoja 24)
- **Condiciones**: `n_skills_competence > 18.5 (19 o más) Y n_skills_essential > 20.5 (21 o más) Y n_skills_knowledge <= 25.5 (25 o menos) Y n_skills_knowledge <= 7.5 (7 o menos)`
- **Lectura en español**: Regla 4 (Árbol 3 · Competencias, Hoja 24): SI el registro de empleo cumple que [n_skills_competence > 18.5 (19 o más) Y n_skills_essential > 20.5 (21 o más) Y n_skills_knowledge <= 25.5 (25 o menos) Y n_skills_knowledge <= 7.5 (7 o menos)], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 455,363 registros (32.74% del total) con una tasa empírica de reincidencia de 34.48% frente a la tasa base de 30.01% (Lift = 1.15x). En Test comprende 113,501 registros con tasa de 34.35% frente a 29.97% base (Lift = 1.15x).

### Árbol 3 · Competencias · Regla 5 (Hoja 20)
- **Condiciones**: `n_skills_competence > 18.5 (19 o más) Y n_skills_essential <= 20.5 (20 o menos) Y n_skills_knowledge <= 0.5 (0 o menos) Y n_skills_essential > 19.5 (20 o más)`
- **Lectura en español**: Regla 5 (Árbol 3 · Competencias, Hoja 20): SI el registro de empleo cumple que [n_skills_competence > 18.5 (19 o más) Y n_skills_essential <= 20.5 (20 o menos) Y n_skills_knowledge <= 0.5 (0 o menos) Y n_skills_essential > 19.5 (20 o más)], ENTONCES el árbol clasifica el perfil del oficio con propensión a reincidencia (predice reincide = 1). En Train agrupa 34,053 registros (2.45% del total) con una tasa empírica de reincidencia de 34.26% frente a la tasa base de 30.01% (Lift = 1.14x). En Test comprende 8,680 registros con tasa de 35.01% frente a 29.97% base (Lift = 1.17x).
