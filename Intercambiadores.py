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
        pdf.multi_cell(0, 5.5, texto_pdf(texto), new_x="LMARGIN", new_y="NEXT")

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
    return bytes(pdf.output())


def main():
    if (ROOT / "franja.jpg").is_file():
        st.image(str(ROOT / "franja.jpg"), use_container_width=True)
    st.title("🔥 Consulta e Inspección de Intercambiadores de Calor")
    st.sidebar.header("🎯 Búsqueda e Inspección")
    # El editor incrementa esta revisión solo después de verificar una escritura.
    revision = st.session_state.get("design_revision", 0)
    if st.session_state.get("principal_design_revision") != revision:
        cargar_disenos.clear()
        st.session_state["principal_design_revision"] = revision
    if st.sidebar.button("🔄 Actualizar datos", use_container_width=True):
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
            return "⚠️ No disponible"
        if clave in errores:
            return "⚠️ Revisar datos"
        return "✅ Creado" if clave in db else "❌ Pendiente"

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
    selecciones = []
    for label, col in (("Estatus", col_status), ("Unidad / Área", col_unidad), ("Equipo / TAG", col_equipo)):
        if col:
            opciones = [None] + sorted(filtrado[col].unique())
            elegido = st.sidebar.selectbox(label, opciones, format_func=lambda v: "Todos" if v is None else v)
            selecciones.append(elegido)
            if elegido is not None:
                filtrado = filtrado[filtrado[col] == elegido]
    incluir_bonete = st.sidebar.checkbox("Contar venteo y drenaje del bonete", value=True)
    st.sidebar.caption("Aplica al cálculo desde el diseño. Un total válido en la planilla tiene prioridad y se usa sin sumarle conexiones.")
    cantidades = []
    for _, row in filtrado.iterrows():
        cfg = db.get(normalizar(row[col_equipo]), {}).get("data")
        cantidades.append(contar_conexiones(row, col_roscadas, cfg, incluir_bonete)[0])
    conocidos = [n for n in cantidades if n is not None]
    st.sidebar.metric("Conexiones roscadas registradas", sum(conocidos) if conocidos else "Sin datos")
    st.sidebar.caption(f"Cantidad disponible en {len(conocidos)} de {len(filtrado)} registros filtrados. Los desconocidos no se cuentan como cero.")
    for nombre in ("logojn.png", "logo.png"):
        if (ROOT / nombre).is_file():
            st.sidebar.image(str(ROOT / nombre), use_container_width=True)
            break

    st.write(f"**Registros encontrados:** {len(filtrado)} de {len(df)}")
    if df[col_equipo].map(normalizar).duplicated().any():
        st.warning("Hay TAG repetidos en Hoja 1. Los gráficos y totales cuentan filas; revisa duplicados si cada equipo debe ocupar una sola fila.")
    tabla, stats = st.tabs(["📊 Vista General de Equipos", "📈 Estadísticas"])
    registro = None
    with tabla:
        defaults = list(dict.fromkeys(c for c in (col_equipo, col_unidad, col_status, col_roscadas) if c))
        with st.expander("Columnas visibles"):
            visibles = st.multiselect("Campos de la planilla", list(df.columns), default=defaults)
        mostrar = filtrado[visibles].copy()
        mostrar.insert(0, "🖼️ Estado 3D / Diseño", filtrado[col_equipo].map(estado))
        st.caption("Selecciona una fila para abrir su ficha técnica.")
        firma = hashlib.sha256(json.dumps([selecciones, visibles, filtrado.index.tolist(), filtrado[col_equipo].tolist()], ensure_ascii=False).encode()).hexdigest()[:16]
        evento = st.dataframe(mostrar, hide_index=True, use_container_width=True,
                              selection_mode="single-row", on_select="rerun", key="tabla_" + firma)
        filas = evento.selection.rows
        if filas and 0 <= filas[0] < len(filtrado):
            registro = filtrado.iloc[filas[0]]
        elif len(filtrado) == 1:
            registro = filtrado.iloc[0]
    with stats:
        if filtrado.empty:
            st.info("No hay registros con estos filtros.")
        else:
            for panel, col, label in zip(st.columns(2), (col_status, col_unidad), ("Estatus", "Unidad")):
                with panel:
                    if col:
                        conteos = filtrado[col].value_counts().rename_axis(label).reset_index(name="Cantidad")
                        fig = px.bar(conteos, x=label, y="Cantidad", color=label, text="Cantidad",
                                     color_discrete_map=COLORES if col == col_status else None)
                        fig.update_layout(showlegend=False, yaxis_title="Registros")
                        st.plotly_chart(fig, use_container_width=True)

    if registro is not None:
        tag = str(registro[col_equipo]).strip()
        config = db.get(normalizar(tag), {}).get("data")
        cantidad, origen = contar_conexiones(registro, col_roscadas, config, incluir_bonete)
        st.divider()
        st.subheader(f"📋 Ficha Técnica - {tag}")
        detalles, enlaces = st.columns([2, 1])
        with detalles:
            resumen = {c: registro[c] for c in (col_equipo, col_unidad, col_status, col_comentario) if c}
            st.table(pd.DataFrame(resumen.items(), columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            with st.expander("Todos los datos técnicos de la planilla"):
                st.table(pd.DataFrame(registro.items(), columns=["Parámetro", "Detalle"]).set_index("Parámetro"))
            st.markdown("#### NOZZLE SCHEDULE")
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
            st.write(estado(tag))
            if st.button("🛠️ Ir a Editor 3D", type="primary", disabled=not informado(tag)):
                ir_editor(tag)
        with enlaces:
            st.metric("Conexiones roscadas", cantidad if cantidad is not None else "No disponible")
            st.caption(origen)
            st.link_button("📁 Abrir carpeta de documentación", GDRIVE_FOLDER_URL, use_container_width=True)
            termino = tag if informado(tag) else (registro[col_unidad] if col_unidad else "")
            if informado(termino):
                url = "https://drive.google.com/drive/u/0/search?q=" + urllib.parse.quote(str(termino), safe="")
                st.link_button(f"🔎 Buscar {termino} en Drive", url, use_container_width=True)
                st.caption("La búsqueda abarca tu Drive; el botón anterior abre la carpeta del proyecto.")
            try:
                pdf = generar_pdf(registro, tag, config, estado(tag), cantidad, origen)
                nombre = re.sub(r'[^\w.-]+', '_', tag)[:100] or "equipo"
                st.download_button("📄 Descargar ficha PDF", data=pdf, file_name=f"Ficha_{nombre}.pdf",
                                   mime="application/pdf", use_container_width=True)
            except Exception as exc:
                st.error(f"No se pudo generar el PDF: {exc}. Instala fpdf2 según requirements.txt.")
            foto = st.file_uploader("Fotografía del equipo", type=["png", "jpg", "jpeg"],
                                    key="foto_" + hashlib.sha256(normalizar(tag).encode()).hexdigest()[:16])
            st.caption("Vista temporal: la fotografía no se guarda en Drive ni se incorpora al PDF.")
            if foto is not None:
                st.image(foto, caption=f"Equipo {tag}", use_container_width=True)
            coords = extraer_coordenadas(registro[col_geo]) if col_geo else None
            if coords is None and col_lat and col_lon:
                coords = extraer_coordenadas(f"{registro[col_lat]};{registro[col_lon]}")
            if coords:
                lat, lon = coords
                st.link_button("🗺️ Abrir en Google Maps", f"https://www.google.com/maps/search/?api=1&query={lat},{lon}")
                st.map(pd.DataFrame([{"lat": lat, "lon": lon}]), zoom=15)

    st.divider()
    st.subheader("🔍 Vista previa 3D — solo lectura")
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
