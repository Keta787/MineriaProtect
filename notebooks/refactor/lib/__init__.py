"""Paquete de apoyo del refactor.

Cada modulo tiene una sola responsabilidad y no imprime: los cuadernos
formatean la salida. Ver `SOLID.md` para el mapeo completo.
"""

from . import calidad, carga, categorias, columnas, competencias, config, figuras, periodo

__all__ = [
    "calidad",
    "carga",
    "categorias",
    "columnas",
    "competencias",
    "config",
    "figuras",
    "periodo",
]
