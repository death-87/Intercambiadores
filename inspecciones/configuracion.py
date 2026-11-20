"""Configuración privada compartida por las herramientas de inspección."""
import json
import os
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import streamlit as st


def configuracion_google():
    """Admite los secrets actuales o el mismo TOML en una variable de Render."""
    raw = os.environ.get("INSPECCIONES_SECRETS_TOML", "").strip()
    try:
        if raw:
            config = dict(tomllib.loads(raw)["connections"]["gsheets"])
        elif os.environ.get("INSPECCIONES_GOOGLE_CREDENTIALS_JSON", "").strip():
            config = dict(json.loads(os.environ["INSPECCIONES_GOOGLE_CREDENTIALS_JSON"]))
        else:
            config = dict(st.secrets["connections"]["gsheets"])
    except Exception:
        raise ValueError("Configura las credenciales de Google de Informes de Inspección en Render.") from None
    if not all(config.get(k) for k in ("client_email", "private_key", "token_uri")):
        raise ValueError("La configuración de Google está incompleta.")
    return config


def google_configurado():
    try:
        configuracion_google()
        return True
    except ValueError:
        return False
