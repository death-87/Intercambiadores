"""Recursos corporativos incluidos con el módulo, sin descargas adicionales."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = 'https://raw.githubusercontent.com/death-87/app-inspecciones/main/'


def imagen_corporativa(url):
    for nombre in ('logo.png', 'logoenap.png', 'franja.png'):
        if url == BASE + nombre:
            ruta = ROOT / nombre
            if ruta.is_file():
                return ruta.read_bytes()
    return None
