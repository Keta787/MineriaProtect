"""Diccionario de columnas del dataset integrado.

Responsabilidad unica (SOLID-S): describir las 23 columnas y su rol analitico.
El rol no se deduce del dtype: se declara aqui y el cuaderno lo cita.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Columna:
    nombre: str
    rol: str
    descripcion: str
    entra_a_x: str  # "si", "no" o "condicional"


COLUMNAS: tuple[Columna, ...] = (
    Columna("resume_id", "identificador",
            "Persona duena de la hoja de vida; no es un patron.", "no"),
    Columna("start_date", "temporal",
            "Trimestre de inicio de la experiencia (Qn AAAA).", "no"),
    Columna("end_date", "temporal",
            "Trimestre de fin de la experiencia (Qn AAAA).", "no"),
    Columna("university_level", "ordinal",
            "Maximo nivel academico: No reportado < ... < PhD.", "si"),
    Columna("matched_code", "identificador",
            "Codigo con el que se intento el emparejamiento ESCO.", "no"),
    Columna("emparejado", "nominal",
            "Resultado del emparejamiento: ok, unknown o rescatado.", "si"),
    Columna("occupation_code", "nominal_alta_cardinalidad",
            "Codigo ESCO del oficio (2.855 valores).", "condicional"),
    Columna("occupation_label", "texto_redundante",
            "Nombre del oficio; 1:1 con occupation_code.", "no"),
    Columna("isco_group", "nominal",
            "Gran grupo ISCO de un digito (9 valores).", "si"),
    Columna("isco_group_label", "texto_redundante",
            "Nombre del grupo ISCO; 1:1 con isco_group.", "no"),
    Columna("isco_level", "constante",
            "Nivel ISCO; vale 4 en todas las filas.", "no"),
    Columna("n_skills_essential", "conteo",
            "Cantidad total de competencias esenciales del oficio.", "si"),
    Columna("n_skills_competence", "conteo",
            "Cantidad de acciones (saber hacer) del oficio.", "condicional"),
    Columna("n_skills_knowledge", "conteo",
            "Cantidad de conocimientos (saber) del oficio.", "condicional"),
    Columna("n_skills_sin_tipo", "conteo",
            "Cantidad de competencias sin skillType (areas digitales).", "condicional"),
    Columna("veces_ese_oficio", "conteo",
            "Cuantas experiencias de la persona repiten el mismo oficio.", "si"),
    Columna("saber_skills", "binaria_nominal",
            "Estado del emparejamiento: ok o no_clasificado.", "si"),
    Columna("skills", "lista_texto",
            "Acciones del oficio separadas por '|'.", "no"),
    Columna("knowledge", "lista_texto",
            "Temas del oficio separados por '|'.", "no"),
    Columna("sin_tipo", "lista_texto",
            "Competencias digitales sin skillType, separadas por '|'.", "no"),
    Columna("es_unknown_ocupacion", "binaria",
            "Marca 0/1 solo 'unknown'; NO incluye 'rescatado'.", "no"),
    Columna("es_rescatado", "binaria",
            "El oficio se recupero por otra via (subconjunto de unknown).", "si"),
    Columna("es_vigente", "binaria",
            "La experiencia no tiene fecha de fin.", "si"),
)

NOMBRES = tuple(c.nombre for c in COLUMNAS)


def por_rol(rol: str) -> tuple[str, ...]:
    """Devuelve los nombres de las columnas de un rol dado."""
    return tuple(c.nombre for c in COLUMNAS if c.rol == rol)
