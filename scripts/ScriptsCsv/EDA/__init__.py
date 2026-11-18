"""Exploratory data analysis package for the JobPath project.

The package implements CRISP-DM phase 2 (Data Understanding) as a formal
iteration executed after the preparation notebooks 2.0 and 3.0.  Every heavy
computation lives in a module; the notebook only orchestrates and interprets.
"""

from .config import EDAConfig, default_config
from .pipeline import EDAPipeline

__all__ = ["EDAConfig", "EDAPipeline", "default_config"]
