"""Componente de ensamblaje 3D de piping."""
from pathlib import Path
import streamlit.components.v1 as components


def declarar_piping():
    return components.declare_component('jndigital_piping',path=str(Path(__file__).resolve().parent))
