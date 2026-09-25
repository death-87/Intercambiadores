"""Página principal. Ejecutar: streamlit run app.py (Python 3.10 o posterior)."""
from pathlib import Path
from io import StringIO
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
from fpdf import FPDF
from visor_3d import declarar_visor

st.set_page_config(page_title="Control de Intercambiadores de Calor", layout="wide")
ROOT = Path(__file__).resolve().parent
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"
HOJA_3D = "Diseño3D"
GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/10hv3MlaXaL4rZkQrssnROAX18ms_31rc"
DIAMETROS = ['1/2"', '3/4"', '1"', '1 1/2"', '2"', '3"', '4"', '6"', '8"', '10"', '12"']
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
    for field in ("nameplate", "vent", "drain"):
        if field in data and not isinstance(data[field], str):
            raise ValueError(f"{field} debe ser texto")
    for n in data["nozzles"]:
        if not isinstance(n, dict):
            raise ValueError("boquilla inválida")
        idx = n.get("diaIndex")
        if type(idx) is not int or not 0 <= idx < len(DIAMETROS):
            raise ValueError("diaIndex fuera de la tabla de diámetros")
        if n.get("bodyPart") not in {"shell", "channel", "bonnet"}:
            raise ValueError("cuerpo de boquilla inválido")
        if n.get("pos") not in {"superior", "inferior"}:
            raise ValueError("posición de boquilla inválida")
        x = n.get("valX")
        if type(x) not in (int, float) or not math.isfinite(x):
            raise ValueError("posición X inválida")
        for field in ("hasNS", "hasFS"):
            if field in n and not isinstance(n[field], bool):
                raise ValueError(f"{field} debe ser booleano")
        for field in ("tagName", "rating", "tagNS", "tagFS"):
            if field in n and not isinstance(n[field], str):
                raise ValueError(f"{field} debe ser texto")
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


def filas_boquillas(config):
    filas = []
    for n in config.get("nozzles", []):
        auxiliares = []
        for side in ("NS", "FS"):
            if n.get("has" + side, False):
                auxiliares.append(f"{n.get('tag' + side) or 'Medida no registrada'} {side}")
        filas.append({
            "MK": n.get("tagName") or "Sin TAG", "QT": 1,
            "DIÁMETRO": DIAMETROS[n["diaIndex"]],
            "RATING": n.get("rating") or "Sin información",
            "CUERPO": n["bodyPart"].upper(), "POSICIÓN": n["pos"],
            "AUXILIARES": " | ".join(auxiliares) or "Sin auxiliares",
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
    n = sum(int(noz.get("hasNS", False)) + int(noz.get("hasFS", False))
            for noz in config.get("nozzles", []))
    if incluir_bonete:
        # En este esquema, una medida informada representa una conexión presente.
        n += int(informado(config.get("vent", ""))) + int(informado(config.get("drain", "")))
    return n, "Calculado del diseño: NS/FS" + (" + venteo/drenaje" if incluir_bonete else "")


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


def ir_editor(tag):
    for nombre in ("diseno.py", "Diseño.py", "diseño.py", "Diseno.py", "editor_3d.py"):
        destino = ROOT / "pages" / nombre
        if destino.is_file():
            st.session_state["tag_para_diseño"] = str(tag).strip()
            st.switch_page(str(destino))
            return
    st.error("No se encontró la página del editor dentro de pages/.")


def texto_pdf(texto):
    return str(texto).encode("latin-1", "replace").decode("latin-1")


class PDFCustom(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Página {self.page_no()}", align="C")


def generar_pdf(registro, tag, config, estado_diseno, cantidad, origen):
    pdf = PDFCustom()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()

    def linea(texto, bold=False, size=9):
        pdf.set_font("Helvetica", "B" if bold else "", size)
        # API compartida por PyFPDF y fpdf2: restablecer X explícitamente.
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(0, 5.5, texto_pdf(texto), align="L")
        pdf.set_x(pdf.l_margin)

    linea(f"Ficha técnica - {tag}", True, 16)
    linea(f"Generado: {datetime.now():%Y-%m-%d %H:%M} (hora del servidor)")
    pdf.ln(3)
    for k, v in registro.items():
        if informado(v):
            linea(f"{k}: {v}")
    pdf.ln(4)
    linea("Conexiones roscadas", True, 12)
    linea(f"Total: {cantidad if cantidad is not None else 'No disponible'}. {origen}.")
    pdf.ln(4)
    linea("NOZZLE SCHEDULE", True, 12)
    if config is None:
        linea(estado_diseno)
    else:
        filas = filas_boquillas(config)
        if not filas:
            linea("Sin boquillas registradas.")
        for fila in filas:
            pdf.ln(2)
            linea(f"{fila['MK']} | Cantidad: 1 | {fila['DIÁMETRO']} | {fila['RATING']}", True)
            linea(f"Cuerpo: {fila['CUERPO']} | Posición: {fila['POSICIÓN']}")
            linea(f"Auxiliares: {fila['AUXILIARES']}")
        pdf.ln(3)
        linea(f"Venteo bonete: {config.get('vent') or 'Sin medida registrada'}")
        linea(f"Drenaje bonete: {config.get('drain') or 'Sin medida registrada'}")
    salida = pdf.output(dest="S")
    # PyFPDF devuelve str con bytes latin-1; fpdf2 devuelve bytearray.
    return salida.encode("latin-1") if isinstance(salida, str) else bytes(salida)


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
        incluir_bonete = st.checkbox("Incluir venteo y drenaje del bonete", value=True)
        st.caption("Aplica al cálculo desde el diseño. Un total válido en la planilla tiene prioridad y se usa sin sumarle conexiones.")
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
    tabla, stats = st.tabs(["Inventario de equipos", "Análisis de inspección"])
    registro = None
    with tabla:
        seccion("Inventario de equipos", "Selecciona un registro para consultar su ficha técnica y documentación.", f"{len(filtrado)} registros")
        defaults = list(dict.fromkeys(c for c in (col_equipo, col_unidad, col_status, col_roscadas) if c))
        with st.expander("Personalizar columnas"):
            visibles = st.multiselect("Campos de la planilla", list(df.columns), default=defaults)
        mostrar = filtrado[visibles].copy()
        mostrar.insert(0, "Diseño 3D", filtrado[col_equipo].map(estado))
        firma = hashlib.sha256(json.dumps([selecciones, visibles, filtrado.index.tolist(), filtrado[col_equipo].tolist()], ensure_ascii=False).encode()).hexdigest()[:16]
        evento = st.dataframe(mostrar, hide_index=True, use_container_width=True,
                              selection_mode="single-row", on_select="rerun", key="tabla_" + firma)
        filas = evento.selection.rows
        if filas and 0 <= filas[0] < len(filtrado):
            registro = filtrado.iloc[filas[0]]
        elif len(filtrado) == 1:
            registro = filtrado.iloc[0]
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
                st.table(pd.DataFrame(registro.items(), columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            seccion("Conexiones y boquillas", "Nozzle schedule del diseño guardado.")
            if config is None:
                st.info(estado(tag) + ": no hay una configuración válida disponible para mostrar boquillas.")
            else:
                boquillas = filas_boquillas(config)
                if boquillas:
                    st.dataframe(pd.DataFrame(boquillas), hide_index=True, use_container_width=True)
                else:
                    st.info("Sin boquillas registradas.")
                st.write(f"**Venteo bonete:** {config.get('vent') or 'Sin medida registrada'}")
                st.write(f"**Drenaje bonete:** {config.get('drain') or 'Sin medida registrada'}")
            if st.button("Abrir editor 3D", type="primary", disabled=not informado(tag), use_container_width=True):
                ir_editor(tag)
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

    st.divider()
    seccion("Modelo del intercambiador", "Explora la geometría y las conexiones del diseño guardado.", "VISTA 3D · SOLO LECTURA")
    if not disenos_disponibles:
        st.warning("Vista previa no disponible hasta recuperar la lectura de Diseño3D.")
    elif not db:
        st.info("No hay diseños válidos disponibles." if errores else "Todavía no hay diseños guardados.")
    elif not (ROOT / "visor_3d" / "index.html").is_file():
        st.error("Falta visor_3d/index.html en el repositorio.")
    else:
        claves = sorted(db, key=lambda k: db[k]["tag"])
        preferido = normalizar(registro[col_equipo]) if registro is not None else None
        ss = st.session_state
        if ss.get("preview_3d_select") not in claves:
            ss["preview_3d_select"] = preferido if preferido in db else claves[0]
        if preferido != ss.get("preview_ficha_anterior"):
            ss["preview_ficha_anterior"] = preferido
            if preferido in db:
                ss["preview_3d_select"] = preferido
        clave = st.selectbox("Equipo guardado", claves, format_func=lambda k: db[k]["tag"], key="preview_3d_select")
        cfg = db[clave]["data"]
        digest = hashlib.sha256(json.dumps([clave, cfg], sort_keys=True).encode()).hexdigest()[:20]
        declarar_visor()(initial_data=cfg, readonly=True, ack=None, height=650,
                         key="preview_" + digest, default=None)


if __name__ == "__main__":
    main()
