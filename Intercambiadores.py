"""Página principal. Ejecutar: streamlit run Intercambiadores.py (Python 3.10 o posterior)."""
from pathlib import Path
from io import BytesIO, StringIO
from datetime import datetime
import base64
import hashlib
import json
import math
import re
import unicodedata
import urllib.parse
import uuid
import zipfile
from html import escape

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, Image, KeepTogether
from visor_3d import declarar_visor

st.set_page_config(page_title="Control de Intercambiadores de Calor", layout="wide")
ROOT = Path(__file__).resolve().parent
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"
HOJA_3D = "Diseño3D"
HOJA_OPERACION = "Datos Operacionales"
GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/10hv3MlaXaL4rZkQrssnROAX18ms_31rc"
# Los primeros 11 índices se conservan para no alterar diseños históricos.
DIAMETROS = ['1/2"', '3/4"', '1"', '1 1/2"', '2"', '3"', '4"', '6"',
             '8"', '10"', '12"', '2 1/2"', '14"', '16"', '18"', '20"', '24"']
DIAMETROS_PULGADAS = [0.5, 0.75, 1, 1.5, 2, 3, 4, 6, 8, 10, 12, 2.5,
                      14, 16, 18, 20, 24]
COLORES = {"CHEQUEADO": "#28a745", "NO CHEQUEADO": "#dc3545", "SIN INFORMACIÓN": "#6c757d"}


def aplicar_diseno():
    st.markdown("""
    <style>
    .block-container { max-width: 1480px; padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128,145,165,.18); }
    [data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
    h1,h2,h3 { letter-spacing: -.025em; }
    [data-testid="stCaptionContainer"] { opacity: .85; }
    [data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
    [data-testid="stTable"] th { text-align: left; font-size: .8rem; }
    [data-testid="stTable"] td { font-size: .85rem; }
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button,
    [data-testid="stLinkButton"] a { border-radius: 8px; min-height: 2.6rem; font-weight: 600; }
    button[kind="primary"] { background: #0f766e; border-color: #0f766e; color: white; }
    button[kind="primary"]:hover { background: #115e59; border-color: #115e59; color: white; }
    [data-baseweb="tab-list"] { gap: 1.6rem; border-bottom: 1px solid rgba(128,145,165,.2); }
    [data-baseweb="tab"] { font-weight: 600; padding: .75rem 0; }
    .hx-brand { display: flex; align-items: center; gap: .7rem; margin-bottom: 1.5rem; }
    .hx-brand-mark { background: #0f766e; color: #fff; border-radius: 10px; padding: .65rem;
      font-size: .8rem; font-weight: 800; letter-spacing: .07em; }
    .hx-brand strong { display: block; font-size: .95rem; }
    .hx-brand small { font-size: .7rem; opacity: .65; }
    .hx-hero { display: flex; align-items: center; justify-content: space-between; gap: 2rem;
      padding: 2.2rem 2.4rem; border-radius: 16px; background: #142638; color: #f5f8fc;
      border: 1px solid #2b4258; margin: .3rem 0 1.5rem; position: relative; overflow: hidden; }
    .hx-hero:before { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: #40c7b0; }
    .hx-eyebrow { color: #6ad7c4; text-transform: uppercase; letter-spacing: .16em;
      font-size: .68rem; font-weight: 700; margin-bottom: .7rem; }
    .hx-hero h1 { font-size: clamp(1.7rem, 3vw, 2.5rem); color: #f5f8fc;
      line-height: 1.15; margin: 0 0 .75rem; padding: 0; font-weight: 650; }
    .hx-hero p { color: #b4c4d4; font-size: .92rem; margin: 0; max-width: 620px; line-height: 1.6; }
    .hx-hero svg { width: 220px; flex-shrink: 0; opacity: .85; }
    .hx-kpis { display: grid; grid-template-columns: repeat(4,minmax(0,1fr)); gap: 1rem; margin: .3rem 0 1.6rem; }
    .hx-kpi { padding: 1.15rem 1.25rem; border: 1px solid rgba(128,145,165,.24);
      border-radius: 12px; background: var(--secondary-background-color,rgba(128,145,165,.05)); }
    .hx-kpi-label { font-size: .72rem; font-weight: 650; text-transform: uppercase; letter-spacing: .06em; opacity: .72; }
    .hx-kpi-value { font-size: 2rem; font-weight: 650; letter-spacing: -.04em; margin: .3rem 0; line-height: 1.2; }
    .hx-kpi-note { font-size: .75rem; opacity: .7; line-height: 1.5; }
    .hx-section { margin: 1.35rem 0 .8rem; display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .hx-section h2 { margin: 0 0 .25rem; padding: 0; font-size: 1.2rem; font-weight: 650; }
    .hx-section p { font-size: .82rem; opacity: .7; margin: 0; }
    .hx-pill { display: inline-block; border: 1px solid rgba(128,145,165,.3); border-radius: 30px;
      padding: .3rem .7rem; font-size: .7rem; white-space: nowrap; }
    .hx-detail { padding: 1.35rem 1.5rem; border: 1px solid rgba(128,145,165,.24);
      border-left: 4px solid #0f9385; border-radius: 12px; margin: .5rem 0 1.25rem; }
    .hx-detail h2 { margin: .25rem 0 .6rem; padding: 0; font-size: 1.8rem; }
    .hx-detail .hx-eyebrow { color: inherit; opacity: .65; }
    .hx-detail-meta { display: flex; gap: .6rem; flex-wrap: wrap; align-items: center; font-size: .82rem; }
    .hx-empty { padding: 1.6rem; border: 1px dashed rgba(128,145,165,.4); border-radius: 12px;
      text-align: center; margin: 1rem 0; }
    .hx-empty strong { display: block; margin-bottom: .35rem; }
    .hx-empty span { font-size: .85rem; opacity: .7; }
    @media(max-width: 850px) { .hx-hero svg { display: none; } .hx-kpis { grid-template-columns: repeat(2,minmax(0,1fr)); } }
    @media(max-width: 480px) { .hx-hero { padding: 1.5rem; } .hx-kpis { gap: .6rem; }
      .hx-kpi { padding: .9rem; } .hx-kpi-value { font-size: 1.65rem; } .hx-section { flex-wrap: wrap; } }
    </style>
    """, unsafe_allow_html=True)


def seccion(titulo, descripcion, etiqueta=""):
    pill = f'<span class="hx-pill">{escape(str(etiqueta))}</span>' if etiqueta else ""
    st.markdown(f'<div class="hx-section"><div><h2>{escape(titulo)}</h2>'
                f'<p>{escape(descripcion)}</p></div>{pill}</div>', unsafe_allow_html=True)


def indicadores(items):
    cards = "".join(
        f'<div class="hx-kpi"><div class="hx-kpi-label">{escape(str(label))}</div>'
        f'<div class="hx-kpi-value">{escape(str(value))}</div>'
        f'<div class="hx-kpi-note">{escape(str(note))}</div></div>'
        for label, value, note in items
    )
    st.markdown(f'<div class="hx-kpis">{cards}</div>', unsafe_allow_html=True)


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto).strip())
    return " ".join("".join(c for c in texto if not unicodedata.combining(c)).upper().split())


def informado(valor):
    return normalizar(valor) not in {"", "NAN", "NONE", "NULL", "SIN INFORMACION", "N/A"}


def es_columna_conn(nombre):
    """Oculta columnas auxiliares Conn, Conn1, Conn2... sin ocultar CONEXIONES ROSCADAS."""
    compacto = re.sub(r"[\s_.-]+", "", normalizar(nombre))
    return re.fullmatch(r"CONN\d*", compacto) is not None


def es_columna_auxiliar(nombre):
    """Cantidad se conserva en la planilla para conteos, pero no es un dato técnico."""
    return es_columna_conn(nombre) or normalizar(nombre) == "CANTIDAD"


def buscar_columna(columnas, exactas, fragmentos=()):
    for nombre in exactas:
        for col in columnas:
            if normalizar(col) == nombre:
                return col
    return next((c for c in columnas if any(x in normalizar(c) for x in fragmentos)), None)


def datos_operacionales(registro):
    """Selecciona los circuitos con datos y conserva entrada/salida por separado."""
    columnas = list(registro.index) if hasattr(registro, "index") else list(registro.keys())
    def buscar_valor(campo, variantes, extremo=""):
        nombres = tuple(campo + " " + lado + (" " + extremo if extremo else "") for lado in variantes)
        columna = buscar_columna(columnas, nombres)
        if columna is None:
            columna = next((c for c in columnas if any(normalizar(c).startswith(n + " (")
                            or normalizar(c).startswith(n + " [") for n in nombres)), None)
        valor = registro[columna] if columna is not None else None
        return valor if informado(valor) else ""
    horquilla = any(re.search(r'\b(?:INNER|OUTER|OUTLET)\s+PIPE\b', normalizar(c))
                    and informado(registro[c]) for c in columnas)
    lados = (("Inner pipe", ("INNER PIPE",)), ("Outer pipe", ("OUTER PIPE", "OUTLET PIPE"))) if horquilla else (
        ("Tubos", ("TUBOS",)), ("Carcasa", ("CARCASA", "CARCAZA")))
    filas = []
    parametros = [("Temperatura IN (°C)", "TEMPERATURA", "IN"),
                  ("Temperatura OUT (°C)", "TEMPERATURA", "OUT"),
                  ("Temperatura (°C)", "TEMPERATURA", ""),
                  ("Presión (kg/cm²g)", "PRESION", ""), ("Producto", "PRODUCTO", "")]
    for etiqueta, campo, extremo in parametros:
        fila = {"Parámetro": etiqueta}
        for lado, variantes in lados:
            fila[lado] = buscar_valor(campo, variantes, extremo)
        if any(informado(fila[lado]) for lado, _ in lados):
            filas.append(fila)
    activos = [lado for lado, _ in lados if any(informado(f[lado]) for f in filas)]
    return [{k: f[k] for k in ("Parámetro", *activos)} for f in filas]


def datos_tecnicos(registro, registro_operacional=None):
    """Combina la ficha base con los datos operacionales vinculados al equipo."""
    def es_operacional(nombre):
        texto = normalizar(nombre)
        return any(texto.startswith(campo + " " + lado) for campo in ("TEMPERATURA", "PRESION", "PRODUCTO")
                   for lado in ("TUBOS", "CARCAZA", "CARCASA", "INNER PIPE", "OUTER PIPE", "OUTLET PIPE"))
    datos = [(k, v) for k, v in registro.items()
             if not es_columna_auxiliar(k)
             and normalizar(k) not in {"DETALLE", "FOTO DE REFERENCIA", "DENOMINACION"}
             and not es_operacional(k)]
    fuente = registro_operacional or {}
    denominacion = buscar_columna(list(fuente), ("DENOMINACION",))
    if denominacion is not None and informado(fuente[denominacion]):
        datos.append(("Denominación", fuente[denominacion]))
    for fila in datos_operacionales(fuente):
        for lado in (k for k in fila if k != "Parámetro"):
            if not informado(fila[lado]):
                continue
            etiqueta = fila["Parámetro"].split(" (", 1)
            nombre = etiqueta[0] + " " + lado.lower()
            if len(etiqueta) == 2:
                nombre += " (" + etiqueta[1]
            datos.append((nombre, fila[lado]))
    return datos


def leer_csv(hoja):
    response = requests.get(
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq",
        params={"tqx": "out:csv", "sheet": hoja, "nc": uuid.uuid4().hex}, timeout=25,
    )
    response.raise_for_status()
    if response.text.lstrip().startswith("<"):
        raise ValueError("Google devolvió HTML en lugar de CSV. Revisa permisos y nombre de la hoja.")
    return pd.read_csv(StringIO(response.text), dtype=str, keep_default_na=False)


def vincular_operacionales(filas, tags, columna_denominacion):
    """Relaciona TAG completos del inventario y rechaza asignaciones ambiguas."""
    patrones = {normalizar(tag): re.compile(r"(?<![A-Z0-9])" + re.escape(normalizar(tag)) + r"(?![A-Z0-9])")
                for tag in tags if informado(tag)}
    candidatos, avisos = {}, []
    for numero, fila in enumerate(filas, start=2):
        texto = normalizar(fila.get(columna_denominacion, ""))
        columna_ubicacion = next((c for c in fila if normalizar(c) in {
            "UBICAC.TECNICA", "UBICAC. TECNICA", "UBICACION TECNICA"}), None)
        ubicacion = normalizar(fila.get(columna_ubicacion, "")) if columna_ubicacion else ""
        tag_tecnico = re.search(r'([A-Z]+[0-9]+[A-Z]?)$', ubicacion)
        if tag_tecnico:
            # La ubicación identifica el equipo; un TAG entre paréntesis puede
            # ser solo una referencia a otro activo, como F970 (C953).
            coincidencias = [tag_tecnico[1]] if tag_tecnico[1] in patrones else []
        else:
            principal = re.sub(r'\([^)]*\)', ' ', texto)
            coincidencias = [tag for tag, patron in patrones.items() if patron.search(principal)]
            tiene_tag_principal = re.search(r'(?<![A-Z0-9])[A-Z]+[0-9]{3,}[A-Z]?(?![A-Z0-9])', principal)
            if not coincidencias and not tiene_tag_principal:
                coincidencias = [tag for tag, patron in patrones.items() if patron.search(texto)]
        if len(coincidencias) != 1:
            if any(informado(v) for v in fila.values()):
                motivo = "varios equipos: " + ", ".join(coincidencias) if coincidencias else "ningún equipo de Hoja 1"
                avisos.append(f"Fila {numero}: {motivo} ({fila.get(columna_denominacion, '')}).")
            continue
        candidatos.setdefault(coincidencias[0], []).append(fila)
    resultado = {}
    for tag, registros in candidatos.items():
        if len(registros) == 1:
            resultado[tag] = registros[0]
        else:
            avisos.append(f"{tag}: aparece en {len(registros)} filas; no se asignaron valores.")
    return resultado, avisos


@st.cache_data(ttl=300, show_spinner=False)
def cargar_operacionales():
    data = leer_csv(HOJA_OPERACION)
    data.columns = [" ".join(str(c).split()) for c in data.columns]
    denominacion = buscar_columna(data.columns, ("DENOMINACION",))
    if denominacion is None:
        raise ValueError("La hoja Datos Operacionales necesita una columna Denominación (columna E).")
    return data.to_dict("records"), denominacion


@st.cache_data(ttl=300, show_spinner=False)
def cargar_datos():
    data = leer_csv(NOMBRE_HOJA)
    nombres, usados = [], set()
    for raw in data.columns:
        base = " ".join(str(raw).split()) or "Sin título"
        nombre, n = base, 2
        while nombre in usados:
            nombre = f"{base} ({n})"
            n += 1
        nombres.append(nombre)
        usados.add(nombre)
    data.columns = nombres
    for col in data.columns:
        data[col] = data[col].str.strip()
        data[col] = data[col].map(lambda v: v if informado(v) else "Sin información")
    return data


def validar_diseno(data, _nivel=0):
    if not isinstance(data, dict) or not isinstance(data.get("nozzles"), list):
        raise ValueError("se esperaba un objeto con una lista nozzles")
    if data.get("model", "A") not in ("A", "B", "C", "D", "E", "F", "H"):
        raise ValueError("modelo desconocido")
    dimensions = data.get("dimensions", {})
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions debe ser un objeto")
    limits = {
        "shellLength": (0.5, 7.0), "reducerLength": (0.2, 2.0),
        "channelLength": (0.2, 2.0), "bonnetLength": (0.2, 2.0),
        "shellDiameter": (0.2, 2.0), "channelDiameter": (0.2, 2.0),
        "bonnetDiameter": (0.2, 2.0), "hairpinGap": (0.05, 2.0),
        "hairpinTubeDiameter": (0.02, 1.4),
        "hairpinUpperDiameter": (0.0334, 2.0), "hairpinLowerDiameter": (0.0334, 2.0),
        "hairpinInnerUpperDiameter": (0.02, 1.4), "hairpinInnerLowerDiameter": (0.02, 1.4),
    }
    for field, value in dimensions.items():
        if field not in limits:
            continue
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"{field} debe ser numérico")
        low, high = limits[field]
        if not low <= value <= high:
            raise ValueError(f"{field} fuera de rango")
    if dimensions.get("hairpinHeadStyle", "flatIntegral") not in {"flatIntegral", "ellipticalIntegral", "flatBolted", "ellipticalBolted"}:
        raise ValueError("tipo de cabezal de horquilla inválido")
    if dimensions.get("hairpinHeadContour", "oval") not in {"oval", "circular"}:
        raise ValueError("contorno del bonete de horquilla inválido")
    pernos = dimensions.get("hairpinBoltCount", 24)
    if type(pernos) is not int or not 4 <= pernos <= 120:
        raise ValueError("la cantidad de pernos del bonete debe ser un entero entre 4 y 120")
    for nivel in ("Upper", "Lower"):
        if dimensions.get("hairpinSpool" + nivel + "Rating", "150#") not in {"150#", "300#", "600#"}:
            raise ValueError("clase de brida de carrete inválida")
        lado = dimensions.get("hairpinSpool" + nivel + "SquareSizeMM", 0)
        if type(lado) not in (int, float) or not math.isfinite(lado) or not (lado == 0 or 25.4 <= lado <= 5000):
            raise ValueError("lado exterior de brida cuadrada fuera de rango")
        if dimensions.get("hairpinSpool" + nivel + "Shape", "round") not in {"round", "square"}:
            raise ValueError("forma de brida de carrete inválida")
        if not isinstance(dimensions.get("hairpinSpool" + nivel + "NippleOnly", False), bool):
            raise ValueError("la opción de niple simple debe ser booleana")
        if not isinstance(dimensions.get("hairpinSpool" + nivel + "Enabled", True), bool):
            raise ValueError("la opción de agregar carrete debe ser booleana")
        for tramo in ("InletLength", "OutletLength"):
            largo_tramo = dimensions.get("hairpinSpool" + nivel + tramo, 0)
            if type(largo_tramo) not in (int, float) or not math.isfinite(largo_tramo) or not 0 <= largo_tramo <= 10:
                raise ValueError("largo del tramo recto del carrete fuera de rango")
        giro = dimensions.get("hairpinSpool" + nivel + "Bend", 0)
        if type(giro) not in (int, float) or giro not in {0, 45, 90, 180}:
            raise ValueError("recorrido del carrete inválido")
        for sufijo, minimo, maximo in (("Length", .2, 10), ("Rotation", 0, 359)):
            valor_carrete = dimensions.get("hairpinSpool" + nivel + sufijo, .8 if sufijo == "Length" else 0)
            if type(valor_carrete) not in (int, float) or not math.isfinite(valor_carrete) or not minimo <= valor_carrete <= maximo:
                raise ValueError("largo o giro de carrete fuera de rango")
        pernos_carrete = dimensions.get("hairpinSpool" + nivel + "Bolts", 0)
        if type(pernos_carrete) is not int or not (pernos_carrete == 0 or 4 <= pernos_carrete <= 120):
            raise ValueError("pernos de carrete: usa 0 para estándar o un entero entre 4 y 120")
    for field in ("nameplate", "vent", "drain"):
        if field in data and not isinstance(data[field], str):
            raise ValueError(f"{field} debe ser texto")
    if data.get("nameplateSide", "front") not in {"front", "rear"}:
        raise ValueError("cara del nameplate inválida")
    apilado = data.get("stackedEquipment")
    if apilado is not None:
        if _nivel >= 1 or not isinstance(apilado, dict) or not isinstance(apilado.get("data"), dict):
            raise ValueError("el conjunto admite un solo equipo superior")
        for campo, limites in (("gap", (0, 5)), ("offsetX", (-20, 20))):
            valor = apilado.get(campo, .4 if campo == "gap" else 0)
            if type(valor) not in (int, float) or not math.isfinite(valor) or not limites[0] <= valor <= limites[1]:
                raise ValueError(f"{campo} del conjunto fuera de rango")
        validar_diseno(apilado["data"], _nivel=1)
        inferior, superior = normalizar(data.get("nameplate", "")), normalizar(apilado["data"].get("nameplate", ""))
        if inferior and not superior:
            raise ValueError("el equipo superior necesita su propio TAG")
        if inferior and inferior == superior:
            raise ValueError("los dos equipos deben tener TAG distintos")
    for n in data["nozzles"]:
        if not isinstance(n, dict):
            raise ValueError("boquilla inválida")
        idx = n.get("diaIndex")
        if type(idx) is not int or not 0 <= idx < len(DIAMETROS):
            raise ValueError("diaIndex fuera de la tabla de diámetros")
        largo_salida = n.get("elbowOutletLength", 0)
        if type(largo_salida) not in (int, float) or not math.isfinite(largo_salida) or not 0 <= largo_salida <= 10:
            raise ValueError("largo recto de salida del codo fuera de rango")
        pipe_idx = n.get("pipeDiaIndex", idx)
        if type(pipe_idx) is not int or not 0 <= pipe_idx < len(DIAMETROS):
            raise ValueError("diámetro del niple/codo inválido")
        if n.get("connectionType", "flanged") == "flanged" and DIAMETROS_PULGADAS[pipe_idx] > DIAMETROS_PULGADAS[idx]:
            raise ValueError("el niple/codo no puede superar la medida de la brida")
        if n.get("connectionType") in {"threaded", "sw"} and pipe_idx != idx:
            raise ValueError("el diámetro independiente del niple/codo requiere una brida")
        base_idx = n.get("baseDiaIndex", idx)
        if type(base_idx) is not int or not 0 <= base_idx < len(DIAMETROS):
            raise ValueError("diámetro de entrada fuera de la tabla")
        if DIAMETROS_PULGADAS[base_idx] < DIAMETROS_PULGADAS[idx]:
            raise ValueError("el diámetro en el equipo no puede ser menor que el de la brida")
        if n.get("connectionType", "flanged") in {"threaded", "sw"} and base_idx != idx:
            raise ValueError("la reducción requiere una boquilla enflanchada")
        if data.get("model") == "H":
            n["bodyPart"] = {"tubeUpper":"shell", "tubeLower":"shellLower"}.get(n.get("bodyPart"), n.get("bodyPart"))
        if n.get("flangeShape", "auto") not in {"auto", "round", "square"}:
            raise ValueError("forma de brida de boquilla inválida")
        for extremo, defecto in (("inletFlange", False), ("outletFlange", True)):
            if not isinstance(n.get(extremo, defecto), bool):
                raise ValueError("la opción de flange por extremo debe ser booleana")
        lado = n.get("flangeSquareSizeMM", 0)
        if type(lado) not in (int, float) or not math.isfinite(lado) or not (lado == 0 or 25.4 <= lado <= 5000):
            raise ValueError("lado exterior de brida cuadrada fuera de rango")
        pernos_brida = n.get("flangeBoltCount", 0)
        if type(pernos_brida) is not int or not (pernos_brida == 0 or 4 <= pernos_brida <= 120):
            raise ValueError("cantidad de pernos de boquilla inválida")
        if n.get("bodyPart") not in {"shell", "transition", "channel", "bonnet", "bonnetLeft", "shellLower", "tubeUpper", "tubeLower"}:
            raise ValueError("cuerpo de boquilla inválido")
        if n.get("connectionType", "flanged") not in {"flanged", "threaded", "sw"}:
            raise ValueError("tipo de conexión inválido")
        if n.get("connectionType") == "sw":
            if n.get("rating") not in {"3000#", "6000#"}:
                raise ValueError("la clase SW debe ser 3000# o 6000#")
            if n.get("swEnd", "none") not in {"none", "valve", "flange"}:
                raise ValueError("terminación SW inválida")
            if n.get("swFlangeRating", "150#") not in {"150#", "300#", "600#"}:
                raise ValueError("clase del flange SW inválida")
        if n.get("service", "process") not in {"process", "vent", "drain"}:
            raise ValueError("servicio de conexión inválido")
        if n.get("face", "RF") not in {"RF", "FF"}:
            raise ValueError("cara de brida inválida")
        if n.get("pos") not in {"superior", "inferior", "front", "rear", "axialMinus", "axialPlus"}:
            raise ValueError("posición de boquilla inválida")
        x = n.get("valX")
        if type(x) not in (int, float) or not math.isfinite(x):
            raise ValueError("posición X inválida")
        for field in ("offsetY", "offsetZ"):
            value = n.get(field, 0)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"{field} debe ser numérico y finito")
        for field in ("angleNS", "angleFS"):
            value = n.get(field, 0)
            if type(value) not in (int, float) or not math.isfinite(value) or not -180 <= value <= 180:
                raise ValueError(f"{field} fuera de rango")
        if not isinstance(n.get("headMount", False), bool):
            raise ValueError("montaje sobre el bonete inválido")
        curva = n.get("headAngle", 45)
        if type(curva) not in (int, float) or not math.isfinite(curva) or not 0 <= curva <= 90:
            raise ValueError("ángulo del sector elíptico fuera de rango")
        if n.get("sideAxis", "Z") not in {"X", "Y", "Z", "+X", "+Y", "+Z", "-X", "-Y", "-Z", "perimeter"}:
            raise ValueError("eje de conexiones del codo inválido")
        if n.get("sideMount", "straight") not in {"straight", "elbow"}:
            raise ValueError("ubicación de conexiones NS/FS inválida")
        if not isinstance(n.get("elbow90", False), bool):
            raise ValueError("elbow90 debe ser booleano")
        giro_codo = n.get("elbowRotation", 0)
        if type(giro_codo) not in (int, float) or not math.isfinite(giro_codo) or not 0 <= giro_codo < 360:
            raise ValueError("giro del codo fuera de rango")
        if n.get("elbow90", False) and n.get("connectionType", "flanged") != "flanged":
            raise ValueError("el codo de salida requiere una boquilla enflanchada")
        if n.get("direction", "radial") not in {"radial", "+X", "-X", "+Y", "-Y", "+Z", "-Z"}:
            raise ValueError("dirección de boquilla inválida")
        angle = n.get("angleDeg")
        if angle is not None and (
            type(angle) not in (int, float) or not math.isfinite(angle)
            or not 0 <= angle < 360
        ):
            raise ValueError("ángulo perimetral fuera de rango")
        neck_length = n.get("neckLength")
        if neck_length is not None and (
            type(neck_length) not in (int, float) or not math.isfinite(neck_length)
            or not 0.10 <= neck_length <= 10
        ):
            raise ValueError("largo del niple fuera de rango")
        for field in ("hasNS", "hasFS"):
            if field in n and not isinstance(n[field], bool):
                raise ValueError(f"{field} debe ser booleano")
        for field in ("tagName", "rating", "flangeType", "face", "service",
                      "sizeNS", "tagNS", "ratingNS", "sizeFS", "tagFS", "ratingFS"):
            if field in n and not isinstance(n[field], str):
                raise ValueError(f"{field} debe ser texto")
        for field in ("ratingNS", "ratingFS"):
            if field in n and n[field] not in {"3000#", "6000#"}:
                raise ValueError(f"{field} debe ser 3000# o 6000#")
        for field in ("subFront", "subRear"):
            config = n.get(field)
            if config is None:
                continue
            if not isinstance(config, dict):
                raise ValueError(f"{field} debe ser un objeto")
            angle = config.get("angle", 0)
            if type(angle) not in (int, float) or not math.isfinite(angle) or not -180 <= angle <= 180:
                raise ValueError(f"{field}.angle fuera de rango")
            if not isinstance(config.get("enabled", False), bool):
                raise ValueError(f"{field}.enabled debe ser booleano")
            if not isinstance(config.get("tag", ""), str):
                raise ValueError(f"{field}.tag debe ser texto")
            sub_idx = config.get("diaIndex")
            if type(sub_idx) is not int or not 0 <= sub_idx < len(DIAMETROS):
                raise ValueError(f"{field}.diaIndex fuera de la tabla")
            if DIAMETROS_PULGADAS[sub_idx] > DIAMETROS_PULGADAS[idx]:
                raise ValueError(f"{field} no puede superar el diámetro principal")
    return data


@st.cache_data(ttl=15, show_spinner=False)
def cargar_disenos():
    data = leer_csv(HOJA_3D)
    if len(data.columns) < 2:
        raise ValueError("Diseño3D necesita dos columnas con encabezados: TAG y datos JSON.")
    db, errores, vistos = {}, {}, set()
    for _, row in data.iterrows():
        tag, raw = row.iloc[0].strip(), row.iloc[1].strip()
        if not informado(tag):
            continue
        clave = normalizar(tag)
        if clave in vistos:
            errores[clave] = f"TAG duplicado: {tag}"
            db.pop(clave, None)
            continue
        vistos.add(clave)
        try:
            cfg = validar_diseno(json.loads(raw))
            db[clave] = {"tag": tag, "data": cfg}
        except (ValueError, TypeError) as exc:
            errores[clave] = f"{tag}: {exc}"
    propietarios = {}
    for owner, entry in list(db.items()):
        upper = entry["data"].get("stackedEquipment", {}).get("data")
        if not upper:
            continue
        tag = upper["nameplate"].strip()
        key = normalizar(tag)
        if key in propietarios or key == owner:
            errores[key] = f"TAG superior duplicado en conjuntos: {tag}"
            db.pop(key, None)
            continue
        propietarios[key] = owner
        if key not in errores:
            db[key] = {"tag": tag, "data": {**upper, "assemblyContext": {"lower": entry["data"]}}}
    return db, errores


def nombre_cuerpo(valor, modelo=None):
    if modelo == "H":
        return {"shell":"TUBO SUPERIOR", "shellLower":"TUBO INFERIOR",
            "tubeUpper":"TUBO SUPERIOR", "tubeLower":"TUBO INFERIOR",
            "channel":"BONETE"}.get(valor, str(valor or "").upper())
    if valor == "bonnet" and modelo == "E":
        return "CHANNEL"
    if (valor == "bonnet" and modelo in {"C", "D"}) or (valor == "bonnetLeft" and modelo in {"D", "E"}):
        return "SHELL"
    return {
        "shell": "SHELL", "transition": "TRANSICIÓN", "channel": "CHANNEL",
        "bonnet": "BONETE", "bonnetLeft": "BONETE",
    }.get(valor, str(valor or "").upper())


def filas_boquillas(config):
    filas = []
    for n in config.get("nozzles", []):
        legacy_ns = "sizeNS" not in n
        legacy_fs = "sizeFS" not in n
        medida_ns = (n.get("tagNS") if legacy_ns else n.get("sizeNS")) or "Sin medida"
        medida_fs = (n.get("tagFS") if legacy_fs else n.get("sizeFS")) or "Sin medida"
        tag_ns = "" if legacy_ns else (n.get("tagNS") or "")
        tag_fs = "" if legacy_fs else (n.get("tagFS") or "")
        rating_ns = n.get("ratingNS") or "3000#"
        rating_fs = n.get("ratingFS") or "3000#"
        detalle_ns = medida_ns + f" · {rating_ns}" + (f" · TAG {tag_ns}" if tag_ns else "")
        detalle_fs = medida_fs + f" · {rating_fs}" + (f" · TAG {tag_fs}" if tag_fs else "")
        roscada = n.get("connectionType", "flanged") == "threaded"
        tipo = "ROSCADA" if roscada else f"WN-{n.get('face', 'RF')}"
        if n.get("connectionType") == "sw":
            tipo = "SW"
        servicio = {"process": "PROCESO", "vent": "VENTEO", "drain": "DRENAJE"}.get(
            n.get("service", "process"), "PROCESO")
        posicion = {"superior": "SUPERIOR", "inferior": "INFERIOR",
                    "front": "FRENTE", "rear": "POSTERIOR",
                    "axialMinus": "AXIAL −X", "axialPlus": "AXIAL +X"}.get(n.get("pos"), n.get("pos", ""))
        filas.append({
            "MK": n.get("tagName") or "Sin TAG", "QT": 1,
            "SERVICIO": servicio,
            "DIÁMETRO": (f'{DIAMETROS[n["baseDiaIndex"]]} → {DIAMETROS[n["diaIndex"]]}'
                         if n.get("baseDiaIndex", n["diaIndex"]) != n["diaIndex"]
                         else DIAMETROS[n["diaIndex"]]),
            "RATING": n.get("rating") or ("3000#" if roscada else "Sin información"),
            "TIPO": tipo,
            "CUERPO": nombre_cuerpo(n["bodyPart"], config.get("model", "A")), "POSICIÓN": posicion,
            "NS": detalle_ns if n.get("hasNS", False) else "—",
            "FS": detalle_fs if n.get("hasFS", False) else "—",
        })
    # Los diseños antiguos guardan estos plugs fuera de la lista nozzles.
    servicios = {n.get("service") for n in config.get("nozzles", [])}
    for campo, servicio, tag, posicion in (
        ("vent", "VENTEO", "VENT", "SUPERIOR"),
        ("drain", "DRENAJE", "DRAIN", "INFERIOR"),
    ):
        medida = config.get(campo, "")
        if campo not in servicios and informado(medida):
            filas.append({
                "MK": tag, "QT": 1, "SERVICIO": servicio,
                "DIÁMETRO": medida, "RATING": "3000#", "TIPO": "ROSCADA",
                "CUERPO": nombre_cuerpo("bonnet"), "POSICIÓN": posicion,
                "NS": "—", "FS": "—",
            })
    return filas


def cantidad_entera(valor):
    if not informado(valor):
        return None
    try:
        n = float(str(valor).strip().replace(",", "."))
        return int(n) if math.isfinite(n) and n >= 0 and n.is_integer() else None
    except (ValueError, TypeError):
        return None


def sin_roscas_declarado(registro):
    columnas = list(registro.index) if hasattr(registro, "index") else list(registro.keys())
    columna = buscar_columna(columnas, ("COMENTARIO", "COMENTARIOS"), ("COMENTARIO",))
    return columna is not None and texto_sin_conexiones(registro[columna])


def estado_conexiones_roscadas(registro, cantidad, config=None):
    declarado = sin_roscas_declarado(registro)
    if declarado or cantidad == 0:
        if (cantidad is not None and cantidad > 0) or registro_roscas(config, registro):
            return "Revisar discrepancia"
        return "Sin conexiones roscadas"
    return "Con conexiones roscadas" if cantidad is not None and cantidad > 0 else "Sin información"


def contar_conexiones(registro, col_roscadas, config, incluir_bonete):
    n = cantidad_entera(registro[col_roscadas]) if col_roscadas else None
    if n is not None:
        return n, "Total declarado en planilla"
    if sin_roscas_declarado(registro) and not registro_roscas(config, registro):
        return 0, "Sin conexiones roscadas declarado en comentarios"
    if config is None:
        conexiones = filas_roscas_planilla(registro)
        return (len(conexiones), "Contado desde las columnas H–AC de Hoja 1") if conexiones else (
            None, "Sin cantidad válida ni conexiones disponibles")
    n = sum(
        1 if noz.get("connectionType", "flanged") == "threaded"
        else int(noz.get("hasNS", False)) + int(noz.get("hasFS", False))
        for noz in config.get("nozzles", [])
    )
    if incluir_bonete:
        servicios = {noz.get("service") for noz in config.get("nozzles", [])}
        # Compatibilidad con diseños antiguos que aún no migraron ambos plugs a nozzles.
        n += int("vent" not in servicios and informado(config.get("vent", "")))
        n += int("drain" not in servicios and informado(config.get("drain", "")))
    return n, "Calculado del diseño: conexiones de la lista + NS/FS"


def extraer_coordenadas(valor):
    texto = str(valor).strip()
    # Decimales con punto separados por coma/espacio; con coma, separar por ;.
    if ";" in texto:
        partes = [x.strip().replace(",", ".") for x in texto.split(";")]
    else:
        partes = re.split(r"\s*,\s*|\s+", texto.strip("()[] "))
    if len(partes) != 2:
        return None
    try:
        lat, lon = map(float, partes)
        return (lat, lon) if -90 <= lat <= 90 and -180 <= lon <= 180 else None
    except ValueError:
        return None


def ir_editor(tag, como_plantilla=False):
    for nombre in ("diseno.py", "Diseño.py", "diseño.py", "Diseno.py", "editor_3d.py"):
        destino = ROOT / "pages" / nombre
        if destino.is_file():
            clave = "tag_para_plantilla" if como_plantilla else "tag_para_diseño"
            st.session_state[clave] = str(tag).strip()
            st.switch_page(str(destino))
            return
    st.error("No se encontró la página del editor dentro de pages/.")


def normalizar_medida_rosca(valor):
    texto = str(valor or "").replace("″", '\"').replace("“", '\"').replace("”", '\"')
    texto = re.sub(r"\s*NPT\s*", "", texto, flags=re.I).strip()
    texto = re.sub(r'"(?:\s*")+', '\"', texto)
    return re.sub(r"\s+", " ", texto)


def texto_sin_conexiones(valor):
    texto = normalizar(valor)
    return bool(re.search(r'\bSIN (?:BOQUILLAS CON )?CONEXIONES ROSCADAS\b|\bNO (?:HAY|TIENE) CONEXIONES ROSCADAS\b', texto))


def celdas_roscas_planilla(registro):
    """H–AC de Hoja 1: una conexión por celda, conservando el orden original."""
    return [(columna, str(valor).strip()) for columna, valor in list(registro.items())[7:29]
            if informado(valor) and not texto_sin_conexiones(valor)
            and normalizar(valor) not in {"-", "—", "0", "NO", "NO APLICA"}]


def filas_roscas_planilla(registro):
    filas = []
    for columna, texto in celdas_roscas_planilla(registro):
        texto = texto.replace("″", '"').replace("“", '"').replace("”", '"')
        limpio = normalizar(texto)
        # Fracciones antes de enteros para no convertir 3/4 en 4.
        medida = re.search(r'(?<![A-Z0-9/])(\d+\s+\d+/\d+|\d+/\d+|\d+(?:[.,]\d+)?)\s*"', limpio)
        rating = re.search(r'\b(150|300|600|900|1500|2500|3000|6000|9000)\s*(?:#|LB\b|"|$)', limpio)
        lado = re.search(r'(?<![A-Z0-9])(NS|FS)(?![A-Z0-9])', limpio)
        origen = "—"
        parentesis_origen = None
        for grupo in re.finditer(r'\(([^()]*)\)', limpio):
            contenido = grupo[1].strip()
            contenido = re.sub(r'^BOQ(?:UILLA)?\.?\s*', '', contenido)
            candidato = re.split(r'[,;]|\b(?:NS|FS)\b', contenido)[0].strip()
            if candidato and candidato not in {"SUPERIOR", "INFERIOR", "NORTE", "SUR", "NS", "FS"}:
                parentesis_origen = grupo
                origen = candidato
                break
        # Los códigos fuera del origen son TAG, nunca determinan el servicio.
        texto_tag = re.sub(r'\([^()]*\)', ' ', limpio)
        tag = re.search(r'\bTAG(?:\s+(?:PLUG|CPLG))?\s*[:=]\s*([A-Z0-9_-]+)', texto_tag)
        if not tag:
            tag = re.search(r'(?<![A-Z0-9])([A-Z]+\d+[A-Z]?|SV|SD|CV|CD|VC|DC|V|D)(?![A-Z0-9])', texto_tag)
        cuerpo = "—"
        if re.search(r'\b(?:BONETE|BONNET)\b', limpio):
            cuerpo = "BONETE"
        elif re.search(r'\b(?:CHANNEL|CHANN)\b', limpio):
            cuerpo = "CHANNEL"
        elif re.search(r'\b(?:SHELL|CARCAZA|CARCASA)\b', limpio):
            cuerpo = "SHELL"
        servicio = None
        if re.search(r'\b(?:VENTEO|VENT|VENTING)\b', limpio):
            servicio = "VENTEO"
        elif re.search(r'\b(?:DRENAJE|DRAIN)\b', limpio):
            servicio = "DRENAJE"
        tag_texto = tag[1] if tag else "—"
        posicion_texto = re.search(r'\b(SUPERIOR|INFERIOR)\b', limpio)
        lado_texto = lado[1] if lado else (posicion_texto[1] if posicion_texto else "—")
        if lado and posicion_texto:
            lado_texto += " · " + posicion_texto[1]
        if servicio:
            descripcion = servicio + (" " + cuerpo if cuerpo != "—" else "")
            lado_texto = descripcion + (" · " + lado[1] if lado else "")
        filas.append({"BOQUILLA / ORIGEN": origen or "—", "LADO": lado_texto,
                      "MEDIDA": re.sub(r'\s+', ' ', medida[1]) + '\"' if medida else "—",
                      "TIPO": "NPT" if re.search(r'\bNPT\b', limpio) else "ROSCADA",
                      "RATING": rating[1] + "#" if rating else "—",
                      "TAG CPLG": tag_texto, "CUERPO": cuerpo})
    return filas


def registro_roscas(config, registro):
    # Un diseño existente conserva prioridad, incluso si no contiene roscas.
    return filas_roscas(config) if config is not None else filas_roscas_planilla(registro)


def filas_roscas(config):
    """Registro técnico de conexiones roscadas, compartido por pantalla y PDF."""
    filas = []
    def agregar(origen, lado, medida, rating, tag, cuerpo):
        filas.append({"BOQUILLA / ORIGEN": origen or "Sin TAG", "LADO": lado,
                      "MEDIDA": normalizar_medida_rosca(medida) or "Sin medida",
                      "TIPO": "NPT", "RATING": rating or "3000#",
                      "TAG CPLG": tag or "—", "CUERPO": nombre_cuerpo(cuerpo, config.get("model", "A"))})
    for n in config.get("nozzles", []):
        if n.get("connectionType", "flanged") == "threaded":
            servicio = {"vent": "VENTEO", "drain": "DRENAJE"}.get(n.get("service"))
            if servicio:
                lado = servicio + " " + nombre_cuerpo(n.get("bodyPart"), config.get("model", "A"))
                agregar("—", lado, DIAMETROS[n["diaIndex"]], n.get("rating"), n.get("tagName"), n.get("bodyPart"))
            else:
                posicion = {"superior": "SUPERIOR", "inferior": "INFERIOR",
                            "front": "NS", "rear": "FS", "axialPlus": "AXIAL +X",
                            "axialMinus": "AXIAL −X"}.get(n.get("pos"), "—")
                agregar(n.get("tagName"), posicion, DIAMETROS[n["diaIndex"]], n.get("rating"), "", n.get("bodyPart"))
            continue
        for lado in ("NS", "FS"):
            if n.get("has" + lado, False):
                legacy = "size" + lado not in n
                medida = n.get("tag" + lado) if legacy else n.get("size" + lado)
                tag = "" if legacy else n.get("tag" + lado)
                agregar(n.get("tagName"), lado, medida or "Sin medida", n.get("rating" + lado), tag, n.get("bodyPart"))
    servicios = {n.get("service") for n in config.get("nozzles", [])}
    for campo, lado in (("vent", "VENTEO"), ("drain", "DRENAJE")):
        if campo not in servicios and informado(config.get(campo, "")):
            agregar("—", lado + " BONETE", config[campo], "3000#", "", "bonnet")
    return filas


def comparar_roscas(excel, modelo):
    """Cruza conexiones con identidad inequívoca; nunca empareja por orden."""
    campos = ["BOQUILLA / ORIGEN", "TAG CPLG", "LADO", "MEDIDA", "RATING", "TIPO", "CUERPO"]
    def clave(valor, campo):
        texto = normalizar(valor or "")
        if not informado(texto) or texto in {"—", "-", "SIN TAG", "SIN MEDIDA"}:
            return ""
        if campo == "MEDIDA":
            texto = re.sub(r'\s*(?:NPT|["″])', '', texto).strip()
            try:
                partes = texto.replace(',', '.').split()
                return str(sum(float(p.split('/')[0]) / float(p.split('/')[1]) if '/' in p else float(p) for p in partes))
            except (ValueError, ZeroDivisionError):
                return texto
        if campo == "LADO":
            lado = re.search(r'\b(NS|FS|SUPERIOR|INFERIOR)\b', texto)
            return lado[1] if lado else texto
        if campo == "RATING":
            return texto.replace('#', '').strip()
        if campo == "TIPO" and texto in {"ROSCADA", "NPT"}:
            return "NPT"  # Equivalentes para la comparación de este proyecto.
        return texto
    def valor(fila, campo):
        return clave(fila.get(campo), campo)
    propuestas = {}
    ambiguas = set()
    for i, fila in enumerate(excel):
        tag = valor(fila, "TAG CPLG")
        candidatos = [j for j, otra in enumerate(modelo) if tag and tag == valor(otra, "TAG CPLG")]
        if not candidatos:
            origen, lado = valor(fila, "BOQUILLA / ORIGEN"), valor(fila, "LADO")
            candidatos = [j for j, otra in enumerate(modelo)
                          if origen and origen == valor(otra, "BOQUILLA / ORIGEN")
                          and (not lado or not valor(otra, "LADO") or lado == valor(otra, "LADO"))]
            if not candidatos and origen:
                # Permite detectar un lado distinto si el origen identifica una sola conexión.
                candidatos = [j for j, otra in enumerate(modelo) if origen == valor(otra, "BOQUILLA / ORIGEN")]
        if len(candidatos) == 1:
            propuestas[i] = candidatos[0]
        elif candidatos:
            ambiguas.add(i)
    repetidas = {j for j in propuestas.values() if list(propuestas.values()).count(j) > 1}
    usados, resultados = set(), []
    for i, fila in enumerate(excel):
        j = propuestas.get(i)
        otra = modelo[j] if j is not None and j not in repetidas else None
        if otra is None:
            estado = "Coincidencia ambigua" if i in ambiguas or j in repetidas else "Sin correspondencia identificada"
            diferencias = "Revisar TAG y boquilla de origen; no se asignó una pareja automáticamente."
        else:
            usados.add(j)
            distintos, incompletos = [], []
            for campo in campos:
                a, b = valor(fila, campo), valor(otra, campo)
                if not a or not b:
                    incompletos.append(campo)
                elif a != b:
                    distintos.append(campo)
            estado = "Diferencias" if distintos else "Revisión incompleta" if incompletos else "Coincide"
            diferencias = ("Distintos: " + ", ".join(distintos) + ". " if distintos else "") + (
                "Sin datos para verificar: " + ", ".join(incompletos) if incompletos else "")
        detalle = {"EXCEL #": str(i + 1), "MODELO #": str(j + 1) if otra is not None else "—",
                   "RESULTADO": estado, "OBSERVACIÓN": diferencias or "Datos coincidentes."}
        for campo in campos:
            detalle[campo] = f"Excel: {fila.get(campo, '—')} | 3D: {otra.get(campo, '—') if otra is not None else '—'}"
        resultados.append(detalle)
    for j, otra in enumerate(modelo):
        if j not in usados:
            detalle = {"EXCEL #": "—", "MODELO #": str(j + 1), "RESULTADO": "Sin correspondencia en Excel",
                       "OBSERVACIÓN": "No se encontró una fila inequívoca de Hoja 1 para esta conexión."}
            detalle.update({campo: f"Excel: — | 3D: {otra.get(campo, '—')}" for campo in campos})
            resultados.append(detalle)
    return resultados


def resumen_tipos_sap(registros, cantidades, columna_tipo):
    grupos = {}
    for registro, cantidad in zip(registros, cantidades):
        tipo = registro.get(columna_tipo, "")
        tipo = str(tipo).strip() if informado(tipo) else "Sin información"
        grupo = grupos.setdefault(tipo, {"TIPO SAP": tipo, "EQUIPOS": 0,
            "CONEXIONES ROSCADAS": 0, "EQUIPOS SIN CONTEO": 0})
        grupo["EQUIPOS"] += 1
        if cantidad is None:
            grupo["EQUIPOS SIN CONTEO"] += 1
        else:
            grupo["CONEXIONES ROSCADAS"] += cantidad
    for grupo in grupos.values():
        if grupo["EQUIPOS"] == grupo["EQUIPOS SIN CONTEO"]:
            grupo["CONEXIONES ROSCADAS"] = "Sin datos"
    return sorted(grupos.values(), key=lambda grupo: grupo["TIPO SAP"])


def aviso_diferencia_roscas(registro, config):
    if config is None:
        return None
    columnas = list(registro.index) if hasattr(registro, "index") else list(registro.keys())
    columna = buscar_columna(columnas, ("CONEXIONES ROSCADAS", "CANTIDAD PLUGS"), ("ROSCAD", "PLUG"))
    total_excel = cantidad_entera(registro[columna]) if columna is not None else None
    if total_excel is None:
        return None
    total_modelo = len(filas_roscas(config))
    if total_excel == total_modelo:
        return None
    return (f"Diferencia en conexiones roscadas: Excel = {total_excel}; modelo 3D = {total_modelo}. "
            f"Diferencia (modelo − Excel): {total_modelo - total_excel:+d}. Revisar los datos.")


def pie_informe_planta(canvas, numero):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#4D9824"))
    canvas.line(15*mm, 14*mm, 195*mm, 14*mm)
    canvas.setFillColor(colors.HexColor("#24451E"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(15*mm, 10.5*mm, "Elaborado por: Juan Navarrete A.")
    canvas.drawRightString(195*mm, 10.5*mm, f"Página {numero}")
    canvas.setFont("Helvetica", 6)
    canvas.drawCentredString(105*mm, 6.5*mm,
        "SERVICIO DE INSPECCIÓN Y EVALUACIÓN DE ACTIVOS FÍSICOS DE ENAP REFINERÍAS S.A.")
    canvas.drawCentredString(105*mm, 3.2*mm, "CONTRATO N° AC 31104857")
    canvas.restoreState()


def generar_pdf(registro, tag, config, estado_diseno, cantidad, origen, registro_operacional=None, imagen_modelo=None, imagen_posterior=None, pagina_inicial=0, informe_planta=False):
    salida = BytesIO()
    doc = SimpleDocTemplate(
        salida, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=17 * mm,
        title=f"Ficha técnica de boquillas - {tag}", author="Control de Intercambiadores",
    )
    navy, teal, pale, line, ink, muted = (
        colors.HexColor("#24451E"), colors.HexColor("#4D9824"), colors.HexColor("#F0F6E9"),
        colors.HexColor("#CAD8BF"), colors.HexColor("#253021"), colors.HexColor("#626E5A"),
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("hx_title", parent=styles["Title"], fontName="Helvetica-Bold",
                                 fontSize=17, leading=20, textColor=colors.white, alignment=TA_LEFT)
    eyebrow = ParagraphStyle("hx_eye", parent=styles["Normal"], fontName="Helvetica-Bold",
                              fontSize=7, leading=9, textColor=colors.HexColor("#FFC321"), spaceAfter=3)
    section_style = ParagraphStyle("hx_section", parent=styles["Heading2"], fontName="Helvetica-Bold",
                                   fontSize=10, leading=13, textColor=navy, spaceBefore=4, spaceAfter=6)
    body = ParagraphStyle("hx_body", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=8, leading=10, textColor=ink)
    small = ParagraphStyle("hx_small", parent=body, fontSize=7, leading=9, textColor=muted)
    cell = ParagraphStyle("hx_cell", parent=body, fontSize=7, leading=8.5)
    cell_center = ParagraphStyle("hx_cell_center", parent=cell, alignment=TA_CENTER)
    cell_header = ParagraphStyle("hx_cell_header", parent=cell_center, fontName="Helvetica-Bold",
                                 textColor=colors.white)

    def p(valor, estilo=cell):
        return Paragraph(escape(str(valor)), estilo)

    def pie(canvas, documento):
        if informe_planta:
            pie_informe_planta(canvas, pagina_inicial + documento.page)
            return
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.line(15 * mm, 12 * mm, 195 * mm, 12 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(muted)
        canvas.drawString(15 * mm, 7.5 * mm, "INGEMARS · CONTROL DE INTERCAMBIADORES · REGISTRO TÉCNICO")
        canvas.drawRightString(195 * mm, 7.5 * mm, f"Página {pagina_inicial + documento.page}")
        canvas.drawString(15 * mm, 3.5 * mm, "Elaborado por: Juan Navarrete A.")
        canvas.restoreState()

    columnas = list(registro.index) if hasattr(registro, "index") else list(registro.keys())
    col_unidad = buscar_columna(columnas, ("UNIDAD DE PROCESO", "UNIDAD", "AREA"), ("UNIDAD", "AREA"))
    unidad = registro[col_unidad] if col_unidad and informado(registro[col_unidad]) else "Sin información"
    unidad_style = ParagraphStyle("hx_unidad", parent=body, textColor=colors.white)
    elementos = []
    def logo_pdf(nombre, ancho, alto):
        ruta = ROOT / nombre
        if not ruta.is_file():
            return p("INGEMARS" if "ingemar" in nombre else "ENAP", section_style)
        logo = Image(str(ruta))
        logo._restrictSize(ancho, alto)
        logo.hAlign = "LEFT" if "ingemar" in nombre else "RIGHT"
        return logo

    logos = Table([[logo_pdf("logoingemar.png", 65 * mm, 22 * mm),
                    logo_pdf("logoenap.png", 25 * mm, 25 * mm)]], colWidths=[140 * mm, 40 * mm])
    logos.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, -1), 2, colors.HexColor("#FFC321")),
    ]))
    elementos += [logos, Spacer(1, 4 * mm)]
    cabecera = Table([
        [Paragraph("REGISTRO DE INSPECCIÓN", eyebrow)],
        [Paragraph(f"Ficha técnica de boquillas · {escape(str(tag))}", title_style)],
        [p(f"UNIDAD: {unidad}", unidad_style)],
    ], colWidths=[180 * mm])
    cabecera.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), navy), ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1), ("TOPPADDING", (0, 1), (-1, 1), 1),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 2), ("TOPPADDING", (0, 2), (-1, 2), 1),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 8),
    ]))
    elementos += [cabecera, Spacer(1, 7 * mm)]

    conexiones = registro_roscas(config, registro)
    estado_roscas = estado_conexiones_roscadas(registro, cantidad, config)
    if estado_roscas == "Sin conexiones roscadas" or sin_roscas_declarado(registro) or (cantidad == 0 and conexiones):
        conflicto = estado_roscas == "Revisar discrepancia"
        destacado_style = ParagraphStyle("hx_sin_roscas", parent=body, fontName="Helvetica-Bold",
            fontSize=13, leading=17, textColor=navy)
        mensaje = "REVISAR · DISCREPANCIA EN CONEXIONES ROSCADAS" if conflicto else "EQUIPO SIN CONEXIONES ROSCADAS"
        detalle = ("El comentario o el total cero no coinciden con las conexiones registradas. Revisar antes de dar por verificada la ausencia de roscas."
            if conflicto else "Ausencia de conexiones roscadas declarada en comentarios de Hoja 1."
            if sin_roscas_declarado(registro) else "Cantidad registrada de conexiones roscadas: 0.")
        destacado = Table([[p(mensaje, destacado_style)], [p(detalle, body)]], colWidths=[180 * mm])
        destacado.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF2CC") if conflicto else pale),
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#C58A18") if conflicto else teal),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elementos += [KeepTogether([destacado, Spacer(1, 5 * mm)])]
    total = cantidad if cantidad is not None else "No disponible"
    total_label_style = ParagraphStyle("hx_total_label", parent=body,
                                      fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=navy)
    total_number_style = ParagraphStyle("hx_total_number", parent=body,
                                       fontName="Helvetica-Bold", fontSize=28 if cantidad is not None else 12,
                                       leading=32 if cantidad is not None else 16,
                                       alignment=TA_CENTER, textColor=colors.white)
    recuadro_total = Table([[p("TOTAL DE CONEXIONES ROSCADAS", total_label_style),
                            p(total, total_number_style)]], colWidths=[140 * mm, 40 * mm])
    recuadro_total.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), pale), ("BACKGROUND", (1, 0), (1, 0), teal),
        ("BOX", (0, 0), (-1, -1), 1.2, teal), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    recuadro_operacion = Table([[p("DATOS OPERACIONALES", total_label_style)]],
                              colWidths=[180 * mm])
    recuadro_operacion.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), pale), ("BOX", (0, 0), (-1, -1), 1.2, teal),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elementos += [recuadro_operacion, Spacer(1, 2 * mm)]
    operacion = datos_operacionales(registro_operacional or {})
    columnas_operacion = list(operacion[0]) if operacion else ["Parámetro"]
    datos_operacion = [[p(k.upper(), cell_header) for k in columnas_operacion]] + [
        [p(fila[k]) for k in columnas_operacion] for fila in operacion
    ]
    if not operacion:
        datos_operacion.append([p("Sin datos operacionales registrados.")])
    tabla_operacion = Table(datos_operacion, colWidths=[180 * mm / len(columnas_operacion)] * len(columnas_operacion), repeatRows=1)
    tabla_operacion.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), teal), ("GRID", (0, 0), (-1, -1), .4, line),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos += [tabla_operacion, Spacer(1, 6 * mm), recuadro_total, Spacer(1, 2 * mm)]
    aviso_roscas = aviso_diferencia_roscas(registro, config)
    if aviso_roscas:
        aviso_style = ParagraphStyle("hx_aviso_roscas", parent=body, textColor=colors.HexColor("#784600"))
        aviso_tabla = Table([[p(aviso_roscas, aviso_style)]], colWidths=[180 * mm])
        aviso_tabla.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF2CC")),
            ("BOX", (0, 0), (-1, -1), .8, colors.HexColor("#C58A18")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ]))
        elementos += [aviso_tabla, Spacer(1, 3 * mm)]
    if config is None and conexiones:
        elementos += [p("Origen: Hoja 1 · columnas H–AC. —: dato no identificado en la descripción.", small),
                      Spacer(1, 2 * mm)]
    if conexiones:
        encabezado = ["BOQUILLA / ORIGEN", "LADO", "MEDIDA", "TIPO", "RATING", "TAG CPLG", "CUERPO"]
        datos_roscas = [[p(x, cell_header) for x in encabezado]] + [
            [p(fila[k], cell_center if k in {"LADO", "MEDIDA", "TIPO", "RATING"} else cell) for k in encabezado] for fila in conexiones
        ]
        tabla_roscas = Table(datos_roscas, repeatRows=1,
                             colWidths=[37*mm, 20*mm, 23*mm, 17*mm, 22*mm, 29*mm, 32*mm])
        tabla_roscas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), teal), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .4, line), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla_roscas)
    else:
        elementos.append(p("No hay conexiones roscadas registradas.", body))
    conjunto = (config or {}).get("assemblyContext", {}).get("lower") or config or {}
    titulo_vistas = "VISTA DEL CONJUNTO" if conjunto.get("stackedEquipment") else "VISTA DEL EQUIPO"
    if conjunto.get("stackedEquipment") and (imagen_modelo or imagen_posterior):
        inferior = conjunto.get("nameplate", "—")
        superior = conjunto["stackedEquipment"]["data"].get("nameplate", "—")
        elementos.append(p(f"Inferior: {inferior} · Superior: {superior}. Boquillas y datos de esta ficha: {tag}.", small))
    if imagen_modelo:
        imagen = Image(BytesIO(imagen_modelo), width=180 * mm, height=78.75 * mm)
        elementos.append(KeepTogether([Spacer(1, 6 * mm),
            Paragraph(titulo_vistas + " · NS (NEAR SIDE)", section_style), imagen]))
    if imagen_posterior:
        imagen = Image(BytesIO(imagen_posterior), width=180 * mm, height=78.75 * mm)
        elementos.append(KeepTogether([Spacer(1, 6 * mm),
            Paragraph(titulo_vistas + " · FS (FAR SIDE)", section_style), imagen]))
    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()


def clave_captura(tag, config):
    return hashlib.sha256(json.dumps([normalizar(tag), config, "report-v44"], sort_keys=True).encode()).hexdigest()[:20]


def decodificar_capturas(captura, clave):
    if not isinstance(captura, dict) or captura.get("action") != "report_capture" or captura.get("capture_key") != clave:
        raise ValueError("La captura no corresponde al equipo solicitado.")
    imagenes = {}
    for campo, prefijo in (("image", "captura_pdf_"), ("rear_image", "captura_posterior_pdf_")):
        imagen = captura.get(campo, "")
        if not (isinstance(imagen, str) and imagen.startswith("data:image/png;base64,") and len(imagen) < 8_000_000):
            raise ValueError("Captura no válida")
        contenido = base64.b64decode(imagen.split(",", 1)[1], validate=True)
        if not contenido.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("PNG no válido")
        imagenes[prefijo + clave] = contenido
    return imagenes


def resumen_informe_planta(equipos):
    total, sin_conteo, detalladas, grupos = 0, 0, 0, {}
    for equipo in equipos:
        if equipo["cantidad"] is None:
            sin_conteo += 1
        else:
            total += equipo["cantidad"]
        for fila in registro_roscas(equipo["config"], equipo["registro"]):
            medida = normalizar_medida_rosca(fila.get("MEDIDA") or "—")
            rating = str(fila.get("RATING") or "—").strip()
            if medida in {"—", "Sin medida"}:
                medida = "Sin identificar"
            if rating == "—":
                rating = "Sin identificar"
            grupos[(medida, rating)] = grupos.get((medida, rating), 0) + 1
            detalladas += 1
    return {"equipos": len(equipos), "total": total, "sin_conteo": sin_conteo,
            "detalladas": detalladas, "distribucion": [(m, r, n) for (m, r), n in sorted(grupos.items())]}


def nombre_planta_informe(codigo):
    clave = re.sub(r"\s+", "", normalizar(codigo))
    nombres = {
        "A0ALQ": "ALQUILACIÓN (Alkylation)",
        "A0CCK": "CRACKING CATALÍTICO",
        "A0LPG3": "Liquefied Petroleum Gas 3",
        "ALPG3": "Liquefied Petroleum Gas 3",
        "A0SHP": "Selective Hydrogenation Process",
        "A0SAR": "Spent Acid Regeneration",
        "A0URA2": "Sulfur Recovery Unit 2",
        "A0DIPE": "Di-Isopropyl Ether",
        "A0HDG": "Hydrodesulfurization of Gasoline",
    }
    return nombres.get(clave, str(codigo))


def preliminares_planta(equipos, planta, inicios):
    from reportlab.platypus import PageBreak
    salida = BytesIO()
    doc = SimpleDocTemplate(salida, pagesize=A4, leftMargin=15*mm, rightMargin=15*mm,
                            topMargin=18*mm, bottomMargin=18*mm)
    verde, oscuro, claro, amarillo = map(colors.HexColor, ("#4D9824", "#24451E", "#F0F6E9", "#FFC321"))
    estilos = getSampleStyleSheet()
    titulo = ParagraphStyle("planta_titulo", parent=estilos["Title"], fontName="Helvetica-Bold",
                            fontSize=28, leading=34, textColor=oscuro, alignment=TA_LEFT)
    subtitulo = ParagraphStyle("planta_sub", parent=titulo, fontSize=20, leading=26)
    cuerpo = ParagraphStyle("planta_cuerpo", parent=estilos["Normal"], fontSize=9, leading=13)
    cabecera = ParagraphStyle("planta_col", parent=cuerpo, fontName="Helvetica-Bold", textColor=colors.white)
    def texto(valor, estilo=cuerpo):
        return Paragraph(escape(str(valor)), estilo)
    def tabla(datos, anchos):
        t = Table([[texto(v, cabecera if i == 0 else cuerpo) for v in fila] for i, fila in enumerate(datos)],
                  colWidths=anchos, repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), verde),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, claro]),
            ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#CAD8BF")),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
        return t
    def pie(canvas, documento):
        canvas.saveState()
        pie_informe_planta(canvas, documento.page)
        if documento.page == 1:
            canvas.setFillColor(amarillo)
            canvas.rect(15*mm, 243*mm, 180*mm, 1.2*mm, fill=1, stroke=0)
        canvas.restoreState()
    logos = []
    for archivo, ancho, alto in (("logoingemar.png", 75*mm, 25*mm), ("logoenap.png", 28*mm, 28*mm)):
        if (ROOT / archivo).is_file():
            logo = Image(str(ROOT / archivo)); logo._restrictSize(ancho, alto); logos.append(logo)
        else:
            logos.append(texto("INGEMARS" if "ingemar" in archivo else "ENAP"))
    logo_tabla = Table([logos], colWidths=[140*mm,40*mm])
    logo_tabla.setStyle(TableStyle([("ALIGN",(1,0),(1,0),"RIGHT"),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    autor_label = ParagraphStyle("autor_label", parent=cuerpo, fontName="Helvetica-Bold",
                                 fontSize=11, leading=15, textColor=oscuro)
    autor_nombre = ParagraphStyle("autor_nombre", parent=cuerpo, fontName="Helvetica-Bold",
                                  fontSize=18, leading=24, textColor=oscuro)
    autor = Table([[texto("ELABORADO POR:", autor_label)],
                   [texto("Juan Navarrete A.", autor_nombre)]], colWidths=[180*mm])
    autor.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),claro),
        ("LINEBEFORE",(0,0),(0,-1),4,verde),
        ("LEFTPADDING",(0,0),(-1,-1),12), ("RIGHTPADDING",(0,0),(-1,-1),12),
        ("TOPPADDING",(0,0),(-1,0),10), ("BOTTOMPADDING",(0,1),(-1,1),12)]))
    elementos = [logo_tabla, Spacer(1,24*mm), texto("INFORME TÉCNICO", cuerpo),
        Spacer(1,5*mm), texto("LEVANTAMIENTO DE CONEXIONES ROSCADAS", titulo),
        Spacer(1,5*mm), texto("Y DATOS OPERACIONALES", subtitulo), Spacer(1,12*mm),
        texto("INTERCAMBIADORES DE CALOR", cuerpo), Spacer(1,9*mm),
        texto("PLANTA / UNIDAD DE PROCESO", cuerpo), texto(planta, subtitulo),
        texto(nombre_planta_informe(planta), subtitulo), Spacer(1,18*mm), autor, PageBreak()]
    resumen = resumen_informe_planta(equipos)
    elementos += [texto("RESUMEN DE LA PLANTA", subtitulo), Spacer(1,7*mm),
        tabla([["INDICADOR", "CANTIDAD"], ["Equipos incluidos", resumen["equipos"]],
               ["Total de conexiones roscadas · conteos disponibles", resumen["total"]],
               ["Conexiones con descripción detallada", resumen["detalladas"]],
               ["Equipos sin conteo disponible", resumen["sin_conteo"]]], [140*mm,40*mm]),
        Spacer(1,9*mm), texto("CONEXIONES POR MEDIDA Y CLASE", subtitulo), Spacer(1,5*mm)]
    if resumen["distribucion"]:
        elementos.append(tabla([["MEDIDA", "CLASE / RATING", "CONEXIONES"]] +
            [list(fila) for fila in resumen["distribucion"]], [65*mm,65*mm,50*mm]))
    else:
        elementos.append(texto("No hay conexiones detalladas para distribuir por medida y clase."))
    elementos += [Spacer(1,5*mm), texto("El total conserva el criterio de la ficha: Excel válido, con respaldo del modelo o de las descripciones. "
        "La distribución cuenta conexiones detalladas del modelo; sin modelo, usa H–AC de Hoja 1. "
        "Los campos desconocidos se agrupan como Sin identificar. Ambos totales pueden diferir si falta detalle o hay discrepancias."),
        PageBreak(), texto("ÍNDICE DE EQUIPOS", subtitulo), Spacer(1,7*mm),
        tabla([["EQUIPO", "CONEXIONES ROSCADAS", "PÁGINA"]] + [[equipo["tag"],
            equipo["cantidad"] if equipo["cantidad"] is not None else "Sin dato", inicios[i]]
            for i, equipo in enumerate(equipos)], [80*mm,65*mm,35*mm])]
    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()


def generar_pdf_planta(equipos, imagenes, planta=None):
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas as pdfcanvas
    if planta is None:
        registro = equipos[0]["registro"] if equipos else {}
        columna = buscar_columna(list(registro), ("UNIDAD DE PROCESO", "UNIDAD", "AREA"), ("UNIDAD", "AREA"))
        planta = str(registro.get(columna, "Planta"))
    fichas = []
    for equipo in equipos:
        clave = equipo["captura_key"]
        pdf = generar_pdf(equipo["registro"], equipo["tag"], equipo["config"], equipo["estado"],
                          equipo["cantidad"], equipo["origen"], registro_operacional=equipo["operacion"],
                          imagen_modelo=imagenes.get("captura_pdf_" + clave),
                          imagen_posterior=imagenes.get("captura_posterior_pdf_" + clave), informe_planta=True)
        fichas.append(PdfReader(BytesIO(pdf)))
    paginas_previas = 3
    for intento in range(5):
        inicios, cursor = [], paginas_previas + 1
        for ficha in fichas:
            inicios.append(cursor)
            cursor += len(ficha.pages)
        previo = PdfReader(BytesIO(preliminares_planta(equipos, planta, inicios)))
        if len(previo.pages) == paginas_previas:
            break
        paginas_previas = len(previo.pages)
    else:
        raise ValueError("No se pudo estabilizar la paginación del índice.")
    writer = PdfWriter()
    for pagina in previo.pages:
        writer.add_page(pagina)
    for equipo, ficha in zip(equipos, fichas):
        inicio = len(writer.pages)
        for pagina in ficha.pages:
            # Reemplaza solo el número de página de cada ficha por el del informe completo.
            sello = BytesIO()
            canvas = pdfcanvas.Canvas(sello, pagesize=A4)
            canvas.setFillColor(colors.white)
            canvas.rect(173*mm,9*mm,24*mm,4*mm,fill=1,stroke=0)
            canvas.setFont("Helvetica",7)
            canvas.setFillColor(colors.HexColor("#626E5A"))
            canvas.drawRightString(195*mm,10.5*mm,f"Página {len(writer.pages)+1}")
            canvas.save()
            pagina.merge_page(PdfReader(BytesIO(sello.getvalue())).pages[0])
            writer.add_page(pagina)
        writer.add_outline_item(equipo["tag"], inicio)
    writer.add_metadata({"/Title": f"Levantamiento de conexiones roscadas y datos operacionales · {planta} · {nombre_planta_informe(planta)}", "/Author": "Juan Navarrete A."})
    salida = BytesIO()
    writer.write(salida)
    writer.close()
    return salida.getvalue()


def generar_zip_fichas(equipos, imagenes):
    salida = BytesIO()
    usados = set()
    with zipfile.ZipFile(salida, "w", compression=zipfile.ZIP_DEFLATED) as archivo:
        for equipo in equipos:
            clave = equipo["captura_key"]
            pdf = generar_pdf(equipo["registro"], equipo["tag"], equipo["config"], equipo["estado"],
                equipo["cantidad"], equipo["origen"], registro_operacional=equipo["operacion"],
                imagen_modelo=imagenes.get("captura_pdf_" + clave),
                imagen_posterior=imagenes.get("captura_posterior_pdf_" + clave))
            nombre = re.sub(r"[^\w.-]+", "_", equipo["tag"]).strip(".") or "Equipo"
            base = f"Ficha_{nombre}"
            nombre_archivo, indice = base + ".pdf", 2
            while nombre_archivo.casefold() in usados:
                nombre_archivo = f"{base}_{indice}.pdf"
                indice += 1
            usados.add(nombre_archivo.casefold())
            archivo.writestr(nombre_archivo, pdf)
    return salida.getvalue()


def informe_por_planta(df, col_unidad, col_equipo, col_roscadas, db, operacionales, estado, incluir_bonete):
    tarea = st.session_state.get("informe_planta_tarea")
    with st.expander("Informe PDF por planta", expanded=bool(tarea or st.session_state.get("informe_planta_resultado"))):
        if not col_unidad:
            st.info("La planilla necesita la columna Unidad de Proceso para preparar un informe por planta.")
            return
        plantas = sorted(v for v in df[col_unidad].unique() if informado(v))
        planta = st.selectbox("Planta / Unidad de proceso", plantas, key="informe_planta_unidad")
        st.caption("Incluye todos los equipos de la planta seleccionada. Los filtros del inventario no limitan este informe.")
        formato = st.selectbox("Archivos a preparar", ["Informe general y PDF individuales (ZIP)",
            "Solo PDF individuales (ZIP)", "Solo informe general"], key="informe_planta_formato")
        st.caption("El ZIP contiene una ficha PDF independiente por equipo, igual que al exportarlos de a uno.")
        con_imagenes = st.checkbox("Incluir vistas NS y FS de los modelos 3D", value=True, key="informe_planta_imagenes")
        if st.button("Preparar informe de la planta", disabled=bool(tarea) or not plantas, key="preparar_planta"):
            equipos = []
            for registro in df[df[col_unidad] == planta].sort_values(col_equipo).to_dict("records"):
                tag = str(registro[col_equipo]).strip()
                if not informado(tag):
                    continue
                config = db.get(normalizar(tag), {}).get("data")
                cantidad, origen = contar_conexiones(registro, col_roscadas, config, incluir_bonete)
                equipos.append({"registro": registro, "tag": tag, "config": config,
                    "estado": estado(tag), "cantidad": cantidad, "origen": origen,
                    "operacion": operacionales.get(normalizar(tag)), "captura_key": clave_captura(tag, config)})
            if not equipos:
                st.warning("No hay equipos válidos en esta planta.")
            else:
                st.session_state.pop("informe_planta_resultado", None)
                st.session_state["informe_planta_tarea"] = {"id": uuid.uuid4().hex, "planta": planta,
                    "equipos": equipos, "con_imagenes": con_imagenes, "omitidas": [], "formato": formato}
                st.rerun()
        if tarea:
            if st.button("Cancelar preparación", key="cancelar_planta"):
                st.session_state.pop("informe_planta_tarea", None)
                st.rerun()
            pendientes = [e for e in tarea["equipos"] if tarea["con_imagenes"] and e["config"] is not None
                and e["captura_key"] not in tarea["omitidas"]
                and ("captura_pdf_" + e["captura_key"] not in st.session_state or
                     "captura_posterior_pdf_" + e["captura_key"] not in st.session_state)]
            total_modelos = sum(e["config"] is not None for e in tarea["equipos"])
            if pendientes:
                equipo = pendientes[0]
                clave = equipo["captura_key"]
                st.progress((total_modelos - len(pendientes)) / max(1, total_modelos),
                            text=f"Preparando vistas de {equipo['tag']} · {len(pendientes)} modelos pendientes")
                st.caption("Mantén esta página abierta. Los modelos se preparan automáticamente uno a uno.")
                if st.button("Continuar sin imágenes de este equipo", key="omitir_captura_" + clave):
                    tarea["omitidas"].append(clave)
                    st.rerun()
                captura = declarar_visor()(initial_data=equipo["config"], readonly=True, ack=None,
                    height=260, capture_key=clave, report_mode=True,
                    key="informe_planta_" + tarea["id"] + clave, default=None)
                if isinstance(captura, dict) and captura.get("capture_key") == clave:
                    if captura.get("action") == "report_capture":
                        try:
                            st.session_state.update(decodificar_capturas(captura, clave))
                            st.rerun()
                        except ValueError as exc:
                            st.warning(str(exc))
                    elif captura.get("action") == "capture_error":
                        st.warning("No se pudo capturar este modelo. Puedes continuar sin sus imágenes.")
                st.stop()
            with st.spinner("Preparando los archivos PDF de la planta…"):
                imagenes = st.session_state if tarea["con_imagenes"] else {}
                try:
                    formato = tarea.get("formato", "Solo informe general")
                    pdf = (generar_pdf_planta(tarea["equipos"], imagenes, planta=tarea["planta"])
                           if formato != "Solo PDF individuales (ZIP)" else None)
                    zip_pdf = (generar_zip_fichas(tarea["equipos"], imagenes)
                               if formato != "Solo informe general" else None)
                except Exception as exc:
                    st.error(f"No se pudo generar el informe de planta: {exc}. Revisa que requirements.txt esté actualizado.")
                    return
                sin_imagen = [e["tag"] for e in tarea["equipos"] if tarea["con_imagenes"] and
                    (e["config"] is None or e["captura_key"] in tarea["omitidas"])]
                st.session_state["informe_planta_resultado"] = {"planta": tarea["planta"], "pdf": pdf, "zip": zip_pdf,
                    "equipos": len(tarea["equipos"]), "sin_imagen": sin_imagen}
                st.session_state.pop("informe_planta_tarea", None)
                st.rerun()
        resultado = st.session_state.get("informe_planta_resultado")
        if resultado:
            st.success(f"Informe de {resultado['planta']} listo: {resultado['equipos']} equipos.")
            if resultado["sin_imagen"]:
                st.caption("Equipos incluidos sin vistas 3D: " + ", ".join(resultado["sin_imagen"]))
            nombre = re.sub(r'[^\w.-]+', '_', resultado["planta"])
            if resultado.get("pdf"):
                st.download_button("Descargar informe de planta · PDF", data=resultado["pdf"],
                    file_name=f"Informe_{nombre}.pdf", mime="application/pdf", key="descargar_planta")
            if resultado.get("zip"):
                st.download_button("Descargar PDF individuales · ZIP", data=resultado["zip"],
                    file_name=f"Fichas_{nombre}.zip", mime="application/zip", key="descargar_fichas_planta")


def main():
    aplicar_diseno()
    st.sidebar.markdown('<div class="hx-brand"><div class="hx-brand-mark">HX</div>'
                        '<div><strong>Control de equipos</strong><small>INSPECCIÓN Y MANTENIMIENTO</small></div></div>',
                        unsafe_allow_html=True)
    st.markdown('''<div class="hx-hero"><div><div class="hx-eyebrow">Gestión de activos / Intercambiadores de calor</div>
    <h1>Control e inspección<br>de intercambiadores</h1>
    <p>Consulta el estado de los equipos, revisa sus conexiones y accede a la documentación técnica y al modelo 3D.</p></div>
    <svg viewBox="0 0 240 140" fill="none" aria-hidden="true">
      <g stroke="#88b2c8" stroke-width="1.5"><rect x="46" y="45" width="141" height="54" rx="4"/>
      <path d="M46 51H30V93H46M187 48H203Q230 72 203 96H187M60 45V99M174 45V99M70 60H164M70 70H164M70 80H164"/>
      <path d="M76 45V25H94V45M141 99V118H159V99M64 99L58 114H85L80 99M164 99L170 114H143"/>
      <path d="M28 41V103M41 41V103M191 41V103" stroke="#40c7b0" stroke-width="3"/>
      <path d="M71 25H99M136 118H164" stroke="#40c7b0" stroke-width="3"/>
      <path d="M15 127H226M16 128V133M225 128V133" stroke-dasharray="3 4" opacity=".45"/></g>
    </svg></div>''', unsafe_allow_html=True)
    st.sidebar.subheader("Filtrar equipos")
    # El editor incrementa esta revisión solo después de verificar una escritura.
    revision = st.session_state.get("design_revision", 0)
    if st.session_state.get("principal_design_revision") != revision:
        cargar_disenos.clear()
        st.session_state["principal_design_revision"] = revision
    if st.sidebar.button("Actualizar datos", use_container_width=True):
        cargar_datos.clear()
        cargar_operacionales.clear()
        cargar_disenos.clear()
    try:
        df = cargar_datos()
    except Exception as exc:
        st.error(f"No se pudo leer {NOMBRE_HOJA}: {exc}")
        st.stop()
    try:
        db, errores = cargar_disenos()
        disenos_disponibles = True
    except Exception as exc:
        db, errores, disenos_disponibles = {}, {}, False
        st.warning(f"No se pudieron consultar los diseños 3D: {exc}. No se marcarán como pendientes.")
    if errores:
        with st.expander(f"Revisar {len(errores)} diseños con datos inválidos"):
            for error in errores.values():
                st.write(error)

    def estado(tag):
        clave = normalizar(tag)
        if not disenos_disponibles:
            return "No disponible"
        if clave in errores:
            return "Revisar datos"
        return "Registrado" if clave in db else "Pendiente"

    col_equipo = buscar_columna(df.columns, ("EQUIPO", "TAG", "TAG EQUIPO"), ("EQUIPO",))
    col_unidad = buscar_columna(df.columns, ("UNIDAD DE PROCESO", "UNIDAD", "AREA"), ("UNIDAD", "AREA"))
    col_status = buscar_columna(df.columns, ("STATUS", "ESTATUS", "ESTADO"), ("STATUS", "ESTATUS"))
    col_tipo_sap = buscar_columna(df.columns, ("TIPO (SAP)", "TIPO SAP", "TIPO DE INTERCAMBIADOR SAP"))
    col_comentario = buscar_columna(df.columns, ("COMENTARIO", "COMENTARIOS"), ("COMENTARIO",))
    col_roscadas = buscar_columna(df.columns, ("CONEXIONES ROSCADAS", "CANTIDAD PLUGS"), ("ROSCAD", "PLUG"))
    col_geo = buscar_columna(df.columns, ("GEORREFERENCIA", "COORDENADAS"), ("GEORREFER", "COORD"))
    col_lat = buscar_columna(df.columns, ("LATITUD", "LAT"))
    col_lon = buscar_columna(df.columns, ("LONGITUD", "LON", "LNG"))
    if not col_equipo:
        st.error("No se encontró una columna EQUIPO o TAG. Revisa los encabezados de Hoja 1.")
        st.stop()
    operacionales, avisos_operacionales = {}, []
    error_operacionales = None
    try:
        filas_operacionales, columna_denominacion = cargar_operacionales()
        operacionales, avisos_operacionales = vincular_operacionales(
            filas_operacionales, df[col_equipo], columna_denominacion)
    except Exception as exc:
        error_operacionales = str(exc)
        st.warning(f"No se pudo leer {HOJA_OPERACION}: {exc}")
    if avisos_operacionales:
        with st.expander(f"Revisar {len(avisos_operacionales)} coincidencias de datos operacionales"):
            for aviso in avisos_operacionales:
                st.write(aviso)

    if col_status:
        df[col_status] = df[col_status].map(lambda v: "SIN INFORMACIÓN" if not informado(v) else v.upper())

    if col_tipo_sap:
        df[col_tipo_sap] = df[col_tipo_sap].map(lambda v: str(v).strip().upper() if informado(v) else "Sin información")
    with st.sidebar.expander("Criterio de conteo"):
        incluir_bonete = st.checkbox("Incluir venteo y drenaje de diseños antiguos", value=True)
        st.caption("Los diseños nuevos ya los incluyen en la lista general. Un total válido en la planilla tiene prioridad.")
    estados_roscas = pd.Series({i: estado_conexiones_roscadas(row,
        contar_conexiones(row, col_roscadas, db.get(normalizar(row[col_equipo]), {}).get("data"), incluir_bonete)[0],
        db.get(normalizar(row[col_equipo]), {}).get("data")) for i, row in df.iterrows()}, dtype=str)
    filtrado = df.copy()
    filtro_roscas = st.sidebar.selectbox("Conexiones roscadas", ["Todos", "Sin conexiones roscadas",
        "Con conexiones roscadas", "Revisar discrepancia", "Sin información"])
    if filtro_roscas != "Todos":
        filtrado = filtrado.loc[estados_roscas.loc[filtrado.index] == filtro_roscas]

    busqueda = st.sidebar.text_input("Buscar equipo", placeholder="TAG, unidad o comentario…").strip()
    if busqueda:
        columnas_busqueda = [c for c in (col_equipo, col_unidad, col_comentario) if c]
        coincidencias = pd.Series(False, index=filtrado.index)
        for c in columnas_busqueda:
            coincidencias |= filtrado[c].str.contains(busqueda, case=False, regex=False, na=False)
        filtrado = filtrado[coincidencias]
    selecciones = []
    for label, col in (("Tipo de intercambiador (SAP)", col_tipo_sap), ("Estatus", col_status), ("Unidad / Área", col_unidad), ("Equipo / TAG", col_equipo)):
        if col:
            opciones = [None] + sorted(filtrado[col].unique())
            elegido = st.sidebar.selectbox(label, opciones, format_func=lambda v: "Todos" if v is None else v)
            selecciones.append(elegido)
            if elegido is not None:
                filtrado = filtrado[filtrado[col] == elegido]
    informe_por_planta(df, col_unidad, col_equipo, col_roscadas, db, operacionales, estado, incluir_bonete)
    cantidades = []
    for _, row in filtrado.iterrows():
        cfg = db.get(normalizar(row[col_equipo]), {}).get("data")
        cantidades.append(contar_conexiones(row, col_roscadas, cfg, incluir_bonete)[0])
    conocidos = [n for n in cantidades if n is not None]
    st.sidebar.divider()
    st.sidebar.caption("Las consultas reflejan los filtros seleccionados. Usa Actualizar datos para volver a consultar la planilla.")
    for nombre in ("logojn.png", "logo.png"):
        if (ROOT / nombre).is_file():
            st.sidebar.image(str(ROOT / nombre), use_container_width=True)
            break

    chequeados = int((filtrado[col_status] == "CHEQUEADO").sum()) if col_status else None
    registrados = int(filtrado[col_equipo].map(normalizar).isin(db).sum()) if disenos_disponibles else None
    indicadores([
        ("Registros filtrados", len(filtrado), f"De {len(df)} registros en la planilla"),
        ("Inspección chequeada", chequeados if chequeados is not None else "—",
         f"{chequeados / len(filtrado):.0%} de los registros filtrados" if col_status and len(filtrado) else "Sin registros evaluables"),
        ("Diseños 3D", registrados if registrados is not None else "—", "Registros filtrados con diseño válido" if disenos_disponibles else "Consulta 3D no disponible"),
        ("Conexiones roscadas", sum(conocidos) if conocidos else "—", f"Conteo conocido en {len(conocidos)} de {len(filtrado)} registros"),
    ])
    sin_roscas = int((estados_roscas.loc[filtrado.index] == "Sin conexiones roscadas").sum())
    st.info(f"Equipos sin conexiones roscadas: {sin_roscas} de {len(filtrado)} registros filtrados. Puedes verlos con el filtro Conexiones roscadas.")
    if df[col_equipo].map(normalizar).duplicated().any():
        st.warning("Hay TAG repetidos en Hoja 1. Los gráficos y totales cuentan filas; revisa duplicados si cada equipo debe ocupar una sola fila.")
    columnas_inventario = [c for c in df.columns if not es_columna_auxiliar(c)]
    tabla, stats = st.tabs(["Inventario de equipos", "Análisis de inspección"])
    registro = None
    with tabla:
        seccion("Inventario de equipos", "Selecciona un registro para consultar su ficha técnica y documentación.", f"{len(filtrado)} registros")
        defaults = list(dict.fromkeys(
            c for c in (col_equipo, col_tipo_sap, col_unidad, col_status, col_roscadas)
            if c and c in columnas_inventario
        ))
        with st.expander("Personalizar columnas"):
            visibles = st.multiselect("Campos de la planilla", columnas_inventario, default=defaults)
            st.caption("Las columnas auxiliares Cantidad, Conn, Conn1, Conn2, etc. se ocultan del inventario.")
        mostrar = filtrado[visibles].copy()
        mostrar.insert(0, "Estado de conexiones roscadas", estados_roscas.loc[filtrado.index])
        mostrar.insert(0, "Diseño 3D", filtrado[col_equipo].map(estado))
        firma = hashlib.sha256(json.dumps([selecciones, visibles, filtrado.index.tolist(), filtrado[col_equipo].tolist()], ensure_ascii=False).encode()).hexdigest()[:16]
        evento = st.dataframe(mostrar, hide_index=True, use_container_width=True,
                              selection_mode="single-row", on_select="rerun", key="tabla_" + firma)
        filas = evento.selection.rows
        if filas and 0 <= filas[0] < len(filtrado):
            registro = filtrado.iloc[filas[0]]
    with stats:
        seccion("Estado de la inspección", "Distribución de los registros según los filtros actuales.")
        if filtrado.empty:
            st.info("No hay registros con estos filtros.")
        else:
            if col_tipo_sap:
                seccion("Resumen por tipo SAP", "Equipos y conexiones roscadas según los filtros actuales.")
                resumen_sap = resumen_tipos_sap(filtrado.to_dict("records"), cantidades, col_tipo_sap)
                st.dataframe(pd.DataFrame(resumen_sap), hide_index=True, use_container_width=True)
                st.caption("Conexiones roscadas suma los conteos disponibles. Los equipos sin conteo se indican aparte; un conteo de cero sí es válido.")
            for panel, col, label in zip(st.columns(2), (col_status, col_unidad), ("Estatus", "Unidad")):
                with panel:
                    if col:
                        conteos = filtrado[col].value_counts().rename_axis(label).reset_index(name="Cantidad")
                        fig = px.bar(conteos, x=label, y="Cantidad", color=label, text="Cantidad",
                                     color_discrete_map=COLORES if col == col_status else None,
                                     color_discrete_sequence=["#0f9385", "#256b91", "#7993aa", "#b59454", "#64748b"])
                        fig.update_layout(showlegend=False, title=f"Registros por {label.lower()}",
                                          yaxis_title="Registros", xaxis_title=None, height=340,
                                          margin=dict(l=12, r=12, t=55, b=24),
                                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                                          font=dict(family="Arial, sans-serif"), bargap=.4)
                        fig.update_traces(textposition="outside", cliponaxis=False)
                        fig.update_yaxes(gridcolor="rgba(128,145,165,.15)", rangemode="tozero")
                        st.plotly_chart(fig, use_container_width=True)

    if registro is None:
        titulo_vacio = "No hay equipos con estos filtros" if filtrado.empty else "Consulta una ficha técnica"
        mensaje_vacio = "Ajusta la búsqueda o los filtros de la barra lateral." if filtrado.empty else "Selecciona una fila del inventario para ver sus conexiones, documentos y ubicación."
        st.markdown(f'<div class="hx-empty"><strong>{titulo_vacio}</strong><span>{mensaje_vacio}</span></div>', unsafe_allow_html=True)

    if registro is not None:
        tag = str(registro[col_equipo]).strip()
        config = db.get(normalizar(tag), {}).get("data")
        cantidad, origen = contar_conexiones(registro, col_roscadas, config, incluir_bonete)
        aviso_roscas = aviso_diferencia_roscas(registro, config)
        if aviso_roscas:
            st.warning(aviso_roscas)

        captura_key = hashlib.sha256(json.dumps([normalizar(tag), config, "report-v44"], sort_keys=True).encode()).hexdigest()[:20]
        imagen_modelo = st.session_state.get("captura_pdf_" + captura_key)
        imagen_posterior = st.session_state.get("captura_posterior_pdf_" + captura_key)

        st.divider()
        unidad = str(registro[col_unidad]) if col_unidad else "Unidad no registrada"
        estatus = str(registro[col_status]) if col_status else "Estado no registrado"
        st.markdown(f'<div class="hx-detail"><div class="hx-eyebrow">Ficha técnica / Equipo seleccionado</div>'
                    f'<h2>{escape(tag)}</h2><div class="hx-detail-meta"><span>{escape(unidad)}</span>'
                    f'<span class="hx-pill">{escape(estatus)}</span>'
                    f'<span class="hx-pill">3D · {escape(estado(tag))}</span></div></div>', unsafe_allow_html=True)
        clasificacion_roscas = estado_conexiones_roscadas(registro, cantidad, config)
        if clasificacion_roscas == "Sin conexiones roscadas":
            st.success("EQUIPO SIN CONEXIONES ROSCADAS · " + ("Declarado en los comentarios de Hoja 1." if sin_roscas_declarado(registro) else "Cantidad registrada: 0."))
        elif clasificacion_roscas == "Revisar discrepancia":
            st.warning("Revisar: el comentario sin conexiones roscadas o el total cero contradice las conexiones registradas.")
        detalles, enlaces = st.columns([2, 1])
        with detalles:
            seccion("Información del equipo", "Datos registrados en la planilla de inspección.")
            resumen = {c: registro[c] for c in (col_equipo, col_unidad, col_status, col_comentario) if c}
            st.table(pd.DataFrame(resumen.items(), columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            seccion("Datos operacionales", "Temperaturas IN/OUT, presión y producto por circuito.")
            registro_operacional = operacionales.get(normalizar(tag))
            if registro_operacional is None:
                st.caption("Datos operacionales no disponibles." if error_operacionales else
                           "Sin una coincidencia única en Datos Operacionales para este equipo.")
            operacion = datos_operacionales(registro_operacional or {})
            if operacion:
                if "Inner pipe" in operacion[0] or "Outer pipe" in operacion[0]:
                    st.caption("Intercambiador horquilla · Inner pipe / Outer pipe")
                st.table(pd.DataFrame(operacion).set_index("Parámetro"))
            else:
                st.info("Sin datos operacionales registrados.")
            with st.expander("Todos los datos técnicos de la planilla"):
                datos_visibles = datos_tecnicos(registro, registro_operacional)
                st.table(pd.DataFrame(datos_visibles, columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            seccion("Registro de roscas", "Conexiones roscadas y su boquilla de origen.")
            boquillas = registro_roscas(config, registro)
            st.caption("Origen: modelo 3D guardado." if config is not None else
                       "Origen: Hoja 1, columnas H–AC. Los campos no identificados se muestran con —.")
            if boquillas:
                st.dataframe(pd.DataFrame(boquillas), hide_index=True, use_container_width=True)
            else:
                st.info("Sin conexiones roscadas registradas.")
            if config is None and celdas_roscas_planilla(registro):
                with st.expander("Ver descripciones originales de las conexiones"):
                    st.table(pd.DataFrame(celdas_roscas_planilla(registro), columns=["Columna", "Descripción"]))
            with st.expander("Comparación Excel / modelo 3D", expanded=False):
                if config is None:
                    st.info("Este equipo no tiene un modelo 3D válido para comparar. Los datos del Excel siguen disponibles.")
                else:
                    roscas_excel = filas_roscas_planilla(registro)
                    roscas_modelo = filas_roscas(config)
                    total_declarado = cantidad_entera(registro[col_roscadas]) if col_roscadas else None
                    for panel, titulo, valor in zip(st.columns(3),
                            ("Total declarado Excel", "Conexiones descritas H–AC", "Conexiones del modelo 3D"),
                            (total_declarado if total_declarado is not None else "Sin dato", len(roscas_excel), len(roscas_modelo))):
                        panel.metric(titulo, valor)
                    if len(roscas_excel) != len(roscas_modelo) or (
                            total_declarado is not None and total_declarado != len(roscas_modelo)) or (
                            total_declarado is not None and total_declarado != len(roscas_excel)):
                        st.warning("Las cantidades no coinciden. Revisa el total declarado, las descripciones del Excel y el modelo 3D.")
                    elif total_declarado is None:
                        st.info("La cantidad de descripciones coincide con el modelo. Falta un total declarado válido en Excel.")
                    else:
                        st.success("Las tres cantidades coinciden.")
                    comparacion = comparar_roscas(roscas_excel, roscas_modelo)
                    pendientes = sum(f["RESULTADO"] != "Coincide" for f in comparacion)
                    if pendientes:
                        st.warning(f"{pendientes} resultados requieren revisión por diferencias, datos incompletos o conexiones sin pareja.")
                    elif comparacion:
                        st.success("Todas las conexiones comparadas coinciden en sus datos.")
                    else:
                        st.info("No hay conexiones roscadas descritas en ninguna de las dos fuentes.")
                    if comparacion:
                        st.dataframe(pd.DataFrame(comparacion), hide_index=True, use_container_width=True)
                    with st.expander("Ver ambas fuentes y descripciones originales"):
                        st.write("Hoja 1 · H–AC")
                        st.dataframe(pd.DataFrame(roscas_excel), hide_index=True, use_container_width=True)
                        st.write("Modelo 3D guardado")
                        st.dataframe(pd.DataFrame(roscas_modelo), hide_index=True, use_container_width=True)
                        st.table(pd.DataFrame(celdas_roscas_planilla(registro), columns=["Columna", "Texto original"]))
                    st.caption("El cruce usa primero TAG CPLG y luego origen/lado. Las coincidencias ambiguas y los campos vacíos requieren revisión; no se emparejan por orden. Se comparan las conexiones roscadas, no todas las boquillas bridadas o SW.")
            abrir, copiar = st.columns(2)
            with abrir:
                if st.button("Abrir editor 3D", type="primary", disabled=not informado(tag),
                             use_container_width=True):
                    ir_editor(tag)
            with copiar:
                if st.button("Usar como plantilla", disabled=config is None,
                             help="Copia el modelo para crear otro TAG sin modificar este equipo.",
                             use_container_width=True):
                    ir_editor(tag, como_plantilla=True)
        with enlaces:
            seccion("Documentación", "Recursos y evidencia del equipo.")
            st.metric("Conexiones roscadas", cantidad if cantidad is not None else "No disponible")
            st.caption(origen)
            st.link_button("Abrir carpeta del proyecto", GDRIVE_FOLDER_URL, use_container_width=True)
            termino = tag if informado(tag) else (registro[col_unidad] if col_unidad else "")
            if informado(termino):
                url = "https://drive.google.com/drive/u/0/search?q=" + urllib.parse.quote(str(termino), safe="")
                st.link_button(f"Buscar {termino} en Drive", url, use_container_width=True)
                st.caption("La búsqueda abarca tu Drive; el botón anterior abre la carpeta del proyecto.")
            try:
                pdf = generar_pdf(registro, tag, config, estado(tag), cantidad, origen,
                                  registro_operacional=operacionales.get(normalizar(tag)),
                                  imagen_modelo=imagen_modelo, imagen_posterior=imagen_posterior)
                nombre = re.sub(r'[^\w.-]+', '_', tag)[:100] or "equipo"
                st.download_button("Descargar ficha técnica · PDF", data=pdf, file_name=f"Ficha_{nombre}.pdf",
                                   mime="application/pdf", use_container_width=True)
                st.caption("Incluye los datos operacionales, el registro de roscas y el total de conexiones roscadas.")
            except Exception as exc:
                st.error(f"No se pudo generar el PDF: {exc}")
            if config and imagen_modelo is None:
                st.caption("La vista para el PDF se prepara al cargar el modelo 3D de abajo. Si no aparece, recarga la página.")
            st.divider()
            foto = st.file_uploader("Evidencia fotográfica", type=["png", "jpg", "jpeg"],
                                    key="foto_" + hashlib.sha256(normalizar(tag).encode()).hexdigest()[:16])
            st.caption("Vista temporal: la fotografía no se guarda en Drive ni se incorpora al PDF.")
            if foto is not None:
                st.image(foto, caption=f"Equipo {tag}", use_container_width=True)
            coords = extraer_coordenadas(registro[col_geo]) if col_geo else None
            if coords is None and col_lat and col_lon:
                coords = extraer_coordenadas(f"{registro[col_lat]};{registro[col_lon]}")
            if coords:
                lat, lon = coords
                st.link_button("Abrir ubicación en Google Maps", f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")
                st.map(pd.DataFrame([{"lat": lat, "lon": lon}]), zoom=15)

    # La vista 3D solo se crea después de una selección explícita en la tabla.
    if registro is not None:
        st.divider()
        seccion("Modelo del intercambiador", "Explora la geometría y las conexiones del equipo seleccionado.",
                "VISTA 3D · SOLO LECTURA")
        clave = normalizar(registro[col_equipo])
        if not disenos_disponibles:
            st.warning("Vista previa no disponible hasta recuperar la lectura de Diseño3D.")
        elif clave in errores:
            st.warning(errores[clave])
        elif clave not in db:
            st.info("El equipo seleccionado todavía no tiene un diseño 3D guardado.")
        elif not (ROOT / "visor_3d" / "index.html").is_file():
            st.error("Falta visor_3d/index.html en el repositorio.")
        else:
            cfg = db[clave]["data"]
            digest = hashlib.sha256(json.dumps([clave, cfg, "report-v44"], sort_keys=True).encode()).hexdigest()[:20]
            captura = declarar_visor()(initial_data=cfg, readonly=True, ack=None, height=650,
                                      capture_key=digest, key="preview_" + digest, default=None)
            if (isinstance(captura, dict) and captura.get("action") == "report_capture"
                    and captura.get("capture_key") == digest
                    and "captura_pdf_" + digest not in st.session_state):
                try:
                    imagenes = {}
                    for campo, prefijo in (("image", "captura_pdf_"), ("rear_image", "captura_posterior_pdf_")):
                        imagen = captura.get(campo, "")
                        if not (isinstance(imagen, str) and imagen.startswith("data:image/png;base64,")
                                and len(imagen) < 8_000_000):
                            raise ValueError("Captura no válida")
                        contenido = base64.b64decode(imagen.split(",", 1)[1], validate=True)
                        if not contenido.startswith(b"\x89PNG\r\n\x1a\n"):
                            raise ValueError("PNG no válido")
                        imagenes[prefijo + digest] = contenido
                    st.session_state.update(imagenes)
                    st.rerun()
                except ValueError:
                    st.warning("No se pudieron preparar las vistas del modelo para el PDF.")


if __name__ == "__main__":
    main()
