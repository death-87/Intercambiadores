"""Registro del visor desde un módulo importable, independiente de la página."""
from pathlib import Path
import streamlit.components.v1 as components


def declarar_visor():
    return components.declare_component(
        "exchanger_editor", path=str(Path(__file__).resolve().parent)
    )