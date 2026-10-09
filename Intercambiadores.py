"""Página principal. Ejecutar: streamlit run Intercambiadores.py (Python 3.10 o posterior)."""
from pathlib import Path
from io import BytesIO, StringIO
from datetime import datetime
import hashlib
import json
import math
import re
import unicodedata
import urllib.parse
import uuid
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
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from visor_3d import declarar_visor

st.set_page_config(page_title="Control de Intercambiadores de Calor", layout="wide")
ROOT = Path(__file__).resolve().parent
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"
HOJA_3D = "Diseño3D"
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


def buscar_columna(columnas, exactas, fragmentos=()):
    for nombre in exactas:
        for col in columnas:
            if normalizar(col) == nombre:
                return col
    return next((c for c in columnas if any(x in normalizar(c) for x in fragmentos)), None)


def leer_csv(hoja):
    response = requests.get(
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq",
        params={"tqx": "out:csv", "sheet": hoja, "nc": uuid.uuid4().hex}, timeout=25,
    )
    response.raise_for_status()
    if response.text.lstrip().startswith("<"):
        raise ValueError("Google devolvió HTML en lugar de CSV. Revisa permisos y nombre de la hoja.")
    return pd.read_csv(StringIO(response.text), dtype=str, keep_default_na=False)


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


def validar_diseno(data):
    if not isinstance(data, dict) or not isinstance(data.get("nozzles"), list):
        raise ValueError("se esperaba un objeto con una lista nozzles")
    if data.get("model", "A") not in ("A", "B", "C", "D", "E"):
        raise ValueError("modelo desconocido")
    dimensions = data.get("dimensions", {})
    if not isinstance(dimensions, dict):
        raise ValueError("dimensions debe ser un objeto")
    limits = {
        "shellLength": (0.5, 7.0), "reducerLength": (0.2, 2.0),
        "channelLength": (0.2, 2.0), "bonnetLength": (0.2, 2.0),
        "shellDiameter": (0.2, 2.0), "channelDiameter": (0.2, 2.0),
        "bonnetDiameter": (0.2, 2.0),
    }
    for field, value in dimensions.items():
        if field not in limits:
            continue
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError(f"{field} debe ser numérico")
        low, high = limits[field]
        if not low <= value <= high:
            raise ValueError(f"{field} fuera de rango")
    for field in ("nameplate", "vent", "drain"):
        if field in data and not isinstance(data[field], str):
            raise ValueError(f"{field} debe ser texto")
    if data.get("nameplateSide", "front") not in {"front", "rear"}:
        raise ValueError("cara del nameplate inválida")
    for n in data["nozzles"]:
        if not isinstance(n, dict):
            raise ValueError("boquilla inválida")
        idx = n.get("diaIndex")
        if type(idx) is not int or not 0 <= idx < len(DIAMETROS):
            raise ValueError("diaIndex fuera de la tabla de diámetros")
        if n.get("bodyPart") not in {"shell", "transition", "channel", "bonnet", "bonnetLeft"}:
            raise ValueError("cuerpo de boquilla inválido")
        if n.get("connectionType", "flanged") not in {"flanged", "threaded"}:
            raise ValueError("tipo de conexión inválido")
        if n.get("service", "process") not in {"process", "vent", "drain"}:
            raise ValueError("servicio de conexión inválido")
        if n.get("face", "RF") not in {"RF", "FF"}:
            raise ValueError("cara de brida inválida")
        if n.get("pos") not in {"superior", "inferior", "front", "rear"}:
            raise ValueError("posición de boquilla inválida")
        x = n.get("valX")
        if type(x) not in (int, float) or not math.isfinite(x):
            raise ValueError("posición X inválida")
        angle = n.get("angleDeg")
        if angle is not None and (
            type(angle) not in (int, float) or not math.isfinite(angle)
            or not 0 <= angle < 360
        ):
            raise ValueError("ángulo perimetral fuera de rango")
        neck_length = n.get("neckLength")
        if neck_length is not None and (
            type(neck_length) not in (int, float) or not math.isfinite(neck_length)
            or not 0.10 <= neck_length <= 1.50
        ):
            raise ValueError("largo visual del niple fuera de rango")
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
    return db, errores


def nombre_cuerpo(valor):
    return {
        "shell": "SHELL", "transition": "TRANSICIÓN", "channel": "CHANNEL",
        "bonnet": "BONETE DERECHO", "bonnetLeft": "BONETE IZQUIERDO",
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
        servicio = {"process": "PROCESO", "vent": "VENTEO", "drain": "DRENAJE"}.get(
            n.get("service", "process"), "PROCESO")
        posicion = {"superior": "SUPERIOR", "inferior": "INFERIOR",
                    "front": "FRENTE", "rear": "POSTERIOR"}.get(n.get("pos"), n.get("pos", ""))
        filas.append({
            "MK": n.get("tagName") or "Sin TAG", "QT": 1,
            "SERVICIO": servicio,
            "DIÁMETRO": DIAMETROS[n["diaIndex"]],
            "RATING": n.get("rating") or ("3000#" if roscada else "Sin información"),
            "TIPO": tipo,
            "CUERPO": nombre_cuerpo(n["bodyPart"]), "POSICIÓN": posicion,
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


def contar_conexiones(registro, col_roscadas, config, incluir_bonete):
    n = cantidad_entera(registro[col_roscadas]) if col_roscadas else None
    if n is not None:
        return n, "Total declarado en planilla"
    if config is None:
        return None, "Sin cantidad válida ni diseño disponible"
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


def generar_pdf(registro, tag, config, estado_diseno, cantidad, origen):
    salida = BytesIO()
    doc = SimpleDocTemplate(
        salida, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=14 * mm, bottomMargin=17 * mm,
        title=f"Ficha de conexiones roscadas - {tag}", author="Control de Intercambiadores",
    )
    navy, teal, pale, line, ink, muted = (
        colors.HexColor("#173247"), colors.HexColor("#0F9385"), colors.HexColor("#E8F4F2"),
        colors.HexColor("#C9D5DE"), colors.HexColor("#1F2D38"), colors.HexColor("#647585"),
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("hx_title", parent=styles["Title"], fontName="Helvetica-Bold",
                                 fontSize=17, leading=20, textColor=colors.white, alignment=TA_LEFT)
    eyebrow = ParagraphStyle("hx_eye", parent=styles["Normal"], fontName="Helvetica-Bold",
                              fontSize=7, leading=9, textColor=colors.HexColor("#7FE0D1"), spaceAfter=3)
    section_style = ParagraphStyle("hx_section", parent=styles["Heading2"], fontName="Helvetica-Bold",
                                   fontSize=10, leading=13, textColor=navy, spaceBefore=4, spaceAfter=6)
    body = ParagraphStyle("hx_body", parent=styles["BodyText"], fontName="Helvetica",
                          fontSize=8, leading=10, textColor=ink)
    small = ParagraphStyle("hx_small", parent=body, fontSize=7, leading=9, textColor=muted)
    cell = ParagraphStyle("hx_cell", parent=body, fontSize=7, leading=8.5)
    cell_center = ParagraphStyle("hx_cell_center", parent=cell, alignment=TA_CENTER)
    cell_header = ParagraphStyle("hx_cell_header", parent=cell_center, fontName="Helvetica-Bold",
                                 textColor=colors.white)
    status_text = ParagraphStyle("hx_status", parent=body, fontName="Helvetica-Bold",
                                 textColor=colors.white)

    def p(valor, estilo=cell):
        return Paragraph(escape(str(valor)), estilo)

    def pie(canvas, documento):
        canvas.saveState()
        canvas.setStrokeColor(line)
        canvas.line(15 * mm, 12 * mm, 195 * mm, 12 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(muted)
        canvas.drawString(15 * mm, 7.5 * mm, "CONTROL DE INTERCAMBIADORES · REGISTRO TÉCNICO")
        canvas.drawRightString(195 * mm, 7.5 * mm, f"Página {documento.page}")
        canvas.restoreState()

    elementos = []
    cabecera = Table([
        [Paragraph("REGISTRO DE INSPECCIÓN", eyebrow)],
        [Paragraph(f"Conexiones roscadas · {escape(str(tag))}", title_style)],
        [p(f"Emitido {datetime.now():%d-%m-%Y %H:%M} · hora del servidor", small)],
    ], colWidths=[180 * mm])
    cabecera.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), navy), ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10), ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 1), ("TOPPADDING", (0, 1), (-1, 1), 1),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 2), ("TOPPADDING", (0, 2), (-1, 2), 1),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 8),
    ]))
    elementos += [cabecera, Spacer(1, 7 * mm)]

    columnas = list(registro.index) if hasattr(registro, "index") else list(registro.keys())
    col_unidad = buscar_columna(columnas, ("UNIDAD DE PROCESO", "UNIDAD", "AREA"), ("UNIDAD", "AREA"))
    col_estado = buscar_columna(columnas, ("STATUS", "ESTATUS", "ESTADO"), ("STATUS", "ESTATUS"))
    unidad = registro[col_unidad] if col_unidad and informado(registro[col_unidad]) else "Sin información"
    estado = registro[col_estado] if col_estado and informado(registro[col_estado]) else "Sin información"
    modelo = config.get("model", "A") if config else "Sin diseño"
    datos = [
        [p("EQUIPO", small), p("UNIDAD / ÁREA", small), p("ESTADO", small), p("MODELO 3D", small)],
        [p(tag, body), p(unidad, body), p(estado, body), p(modelo, body)],
    ]
    tabla_datos = Table(datos, colWidths=[45 * mm] * 4)
    tabla_datos.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFF3F6")),
        ("GRID", (0, 0), (-1, -1), .45, line), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos += [tabla_datos, Spacer(1, 6 * mm)]

    filas = filas_boquillas(config) if config else []
    conexiones = []
    if config:
        for n in config.get("nozzles", []):
            posicion = {"superior": "SUPERIOR", "inferior": "INFERIOR",
                        "front": "FRENTE", "rear": "POSTERIOR"}.get(n.get("pos"), n.get("pos", ""))
            if n.get("connectionType", "flanged") == "threaded":
                servicio = {"process": "DIRECTA", "vent": "VENTEO", "drain": "DRENAJE"}.get(
                    n.get("service", "process"), "DIRECTA")
                conexiones.append([
                    n.get("tagName") or "Sin TAG", servicio,
                    f"{DIAMETROS[n['diaIndex']]} · {n.get('rating') or '3000#'}",
                    "—", nombre_cuerpo(n.get("bodyPart")), posicion,
                ])
                continue
            for lado in ("NS", "FS"):
                if n.get("has" + lado, False):
                    legacy = ("size" + lado) not in n
                    medida = (n.get("tag" + lado) if legacy else n.get("size" + lado)) or "Sin medida"
                    tag_plug = "" if legacy else (n.get("tag" + lado) or "")
                    rating_plug = n.get("rating" + lado) or "3000#"
                    conexiones.append([
                        n.get("tagName") or "Sin TAG", lado,
                        f"{medida} · {rating_plug}", tag_plug or "—",
                        nombre_cuerpo(n.get("bodyPart")), posicion,
                    ])
        servicios = {n.get("service") for n in config.get("nozzles", [])}
        for servicio, campo in (("VENTEO", "vent"), ("DRENAJE", "drain")):
            if campo not in servicios and informado(config.get(campo, "")):
                conexiones.append(["LEGACY", servicio, config.get(campo), "—", "BONNET", "—"])
    detectadas = len(conexiones)
    if cantidad is None:
        verificacion, estado_color = "SIN TOTAL DECLARADO", colors.HexColor("#A26918")
    elif cantidad == detectadas:
        verificacion, estado_color = "COINCIDENTE", teal
    else:
        verificacion, estado_color = f"REVISAR · DIFERENCIA {cantidad - detectadas:+d}", colors.HexColor("#B54A4A")
    resumen = Table([
        [p("TOTAL DECLARADO", small), p("IDENTIFICADAS EN 3D", small), p("VERIFICACIÓN", small)],
        [p(cantidad if cantidad is not None else "—", body), p(detectadas, body), p(verificacion, status_text)],
        [p(origen, small), p("Lista 3D + conexiones NS/FS", small), p(estado_diseno, small)],
    ], colWidths=[60 * mm] * 3)
    resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), pale), ("BOX", (0, 0), (-1, -1), .8, teal),
        ("INNERGRID", (0, 0), (-1, -1), .35, line), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BACKGROUND", (2, 1), (2, 1), estado_color), ("TEXTCOLOR", (2, 1), (2, 1), colors.white),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elementos += [Paragraph("CONTROL DE CONEXIONES ROSCADAS", section_style), resumen, Spacer(1, 6 * mm)]

    elementos.append(Paragraph("NOZZLE SCHEDULE", section_style))
    if filas:
        encabezado = ["MK", "SERVICIO", "QT", "DIÁMETRO", "TIPO / RATING", "CUERPO", "POSICIÓN", "NS", "FS"]
        datos_nozzle = [[p(x, cell_header) for x in encabezado]] + [
            [p(
                f"{fila['TIPO']} · {fila['RATING']}" if k == "TIPO / RATING" else fila[k],
                cell_center if k in {"SERVICIO", "QT", "DIÁMETRO", "TIPO / RATING", "NS", "FS"} else cell,
            ) for k in encabezado]
            for fila in filas
        ]
        tabla_nozzle = Table(datos_nozzle, repeatRows=1,
                             colWidths=[17*mm, 20*mm, 8*mm, 18*mm, 25*mm, 20*mm, 22*mm, 25*mm, 25*mm])
        tabla_nozzle.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), navy), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .4, line), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F8FA")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla_nozzle)
    else:
        elementos.append(p("No hay boquillas registradas en el diseño.", body))
    elementos += [Spacer(1, 6 * mm), Paragraph("REGISTRO DE ROSCAS", section_style)]
    if conexiones:
        encabezado = ["BOQUILLA / ORIGEN", "LADO", "MEDIDA / CLASE", "TAG PLUG", "CUERPO", "POSICIÓN"]
        datos_roscas = [[p(x, cell_header) for x in encabezado]] + [
            [p(x, cell_center if i in (1, 2, 3) else cell) for i, x in enumerate(fila)] for fila in conexiones
        ]
        tabla_roscas = Table(datos_roscas, repeatRows=1,
                             colWidths=[35*mm, 18*mm, 31*mm, 30*mm, 34*mm, 32*mm])
        tabla_roscas.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), teal), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), .4, line), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, pale]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elementos.append(tabla_roscas)
    else:
        elementos.append(p("No hay conexiones roscadas identificadas en el diseño 3D.", body))
    elementos += [Spacer(1, 5 * mm), p(
        "Criterio: venteo y drenaje forman parte del mismo listado de boquillas y pueden ubicarse en cualquier componente. "
        "Las dimensiones longitudinales de los componentes se excluyen de esta ficha.", small)]
    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return salida.getvalue()


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
    col_comentario = buscar_columna(df.columns, ("COMENTARIO", "COMENTARIOS"), ("COMENTARIO",))
    col_roscadas = buscar_columna(df.columns, ("CONEXIONES ROSCADAS", "CANTIDAD PLUGS"), ("ROSCAD", "PLUG"))
    col_geo = buscar_columna(df.columns, ("GEORREFERENCIA", "COORDENADAS"), ("GEORREFER", "COORD"))
    col_lat = buscar_columna(df.columns, ("LATITUD", "LAT"))
    col_lon = buscar_columna(df.columns, ("LONGITUD", "LON", "LNG"))
    if not col_equipo:
        st.error("No se encontró una columna EQUIPO o TAG. Revisa los encabezados de Hoja 1.")
        st.stop()
    if col_status:
        df[col_status] = df[col_status].map(lambda v: "SIN INFORMACIÓN" if not informado(v) else v.upper())

    filtrado = df.copy()
    busqueda = st.sidebar.text_input("Buscar equipo", placeholder="TAG, unidad o comentario…").strip()
    if busqueda:
        columnas_busqueda = [c for c in (col_equipo, col_unidad, col_comentario) if c]
        coincidencias = pd.Series(False, index=filtrado.index)
        for c in columnas_busqueda:
            coincidencias |= filtrado[c].str.contains(busqueda, case=False, regex=False, na=False)
        filtrado = filtrado[coincidencias]
    selecciones = []
    for label, col in (("Estatus", col_status), ("Unidad / Área", col_unidad), ("Equipo / TAG", col_equipo)):
        if col:
            opciones = [None] + sorted(filtrado[col].unique())
            elegido = st.sidebar.selectbox(label, opciones, format_func=lambda v: "Todos" if v is None else v)
            selecciones.append(elegido)
            if elegido is not None:
                filtrado = filtrado[filtrado[col] == elegido]
    with st.sidebar.expander("Criterio de conteo"):
        incluir_bonete = st.checkbox("Incluir venteo y drenaje de diseños antiguos", value=True)
        st.caption("Los diseños nuevos ya los incluyen en la lista general. Un total válido en la planilla tiene prioridad.")
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
    if df[col_equipo].map(normalizar).duplicated().any():
        st.warning("Hay TAG repetidos en Hoja 1. Los gráficos y totales cuentan filas; revisa duplicados si cada equipo debe ocupar una sola fila.")
    columnas_inventario = [c for c in df.columns if not es_columna_conn(c)]
    tabla, stats = st.tabs(["Inventario de equipos", "Análisis de inspección"])
    registro = None
    with tabla:
        seccion("Inventario de equipos", "Selecciona un registro para consultar su ficha técnica y documentación.", f"{len(filtrado)} registros")
        defaults = list(dict.fromkeys(
            c for c in (col_equipo, col_unidad, col_status, col_roscadas)
            if c and c in columnas_inventario
        ))
        with st.expander("Personalizar columnas"):
            visibles = st.multiselect("Campos de la planilla", columnas_inventario, default=defaults)
            st.caption("Las columnas auxiliares Conn, Conn1, Conn2, etc. se ocultan del inventario.")
        mostrar = filtrado[visibles].copy()
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
        st.divider()
        unidad = str(registro[col_unidad]) if col_unidad else "Unidad no registrada"
        estatus = str(registro[col_status]) if col_status else "Estado no registrado"
        st.markdown(f'<div class="hx-detail"><div class="hx-eyebrow">Ficha técnica / Equipo seleccionado</div>'
                    f'<h2>{escape(tag)}</h2><div class="hx-detail-meta"><span>{escape(unidad)}</span>'
                    f'<span class="hx-pill">{escape(estatus)}</span>'
                    f'<span class="hx-pill">3D · {escape(estado(tag))}</span></div></div>', unsafe_allow_html=True)
        detalles, enlaces = st.columns([2, 1])
        with detalles:
            seccion("Información del equipo", "Datos registrados en la planilla de inspección.")
            resumen = {c: registro[c] for c in (col_equipo, col_unidad, col_status, col_comentario) if c}
            st.table(pd.DataFrame(resumen.items(), columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            with st.expander("Todos los datos técnicos de la planilla"):
                datos_visibles = [(k, v) for k, v in registro.items() if not es_columna_conn(k)]
                st.table(pd.DataFrame(datos_visibles, columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            seccion("Conexiones y boquillas", "Nozzle schedule del diseño guardado.")
            if config is None:
                st.info(estado(tag) + ": no hay una configuración válida disponible para mostrar boquillas.")
            else:
                st.caption(f"Modelo del intercambiador: {config.get('model', 'A')}")
                dims = config.get("dimensions", {})
                modelo = config.get("model", "A")
                largos = [f"Shell {dims.get('shellLength', 4.5 if modelo == 'B' else 4.275):.2f} m"]
                if modelo == "B":
                    largos.append(f"Transición {dims.get('reducerLength', 0.9):.2f} m")
                if modelo in {"D", "E"}:
                    largo_bonete = dims.get("bonnetLength", 0.80)
                    largos.extend([f"Bonete izquierdo {largo_bonete:.2f} m",
                                   f"Bonete derecho {largo_bonete:.2f} m"])
                else:
                    largos.extend([
                        f"Channel {dims.get('channelLength', 0.65 if modelo == 'B' else 1.20):.2f} m",
                        f"Bonete {dims.get('bonnetLength', 0.40 if modelo == 'B' else 0.80):.2f} m",
                    ])
                st.caption("Largos: " + " · ".join(largos))
                boquillas = filas_boquillas(config)
                if boquillas:
                    st.dataframe(pd.DataFrame(boquillas), hide_index=True, use_container_width=True)
                else:
                    st.info("Sin boquillas registradas.")
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
                pdf = generar_pdf(registro, tag, config, estado(tag), cantidad, origen)
                nombre = re.sub(r'[^\w.-]+', '_', tag)[:100] or "equipo"
                st.download_button("Descargar ficha técnica · PDF", data=pdf, file_name=f"Ficha_{nombre}.pdf",
                                   mime="application/pdf", use_container_width=True)
            except Exception as exc:
                st.error(f"No se pudo generar el PDF: {exc}")
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
            digest = hashlib.sha256(json.dumps([clave, cfg], sort_keys=True).encode()).hexdigest()[:20]
            declarar_visor()(initial_data=cfg, readonly=True, ack=None, height=650,
                             key="preview_" + digest, default=None)


if __name__ == "__main__":
    main()
