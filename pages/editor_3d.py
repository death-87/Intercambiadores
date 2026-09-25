from pathlib import Path
from copy import deepcopy
from io import StringIO
import json
import time
import uuid
import sys
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Editor 3D de Equipos", layout="wide")
WEBAPP_URL = 'https://script.google.com/macros/s/AKfycbxPmdGXS7i61XrwRDWc9rRJAceBByb4AmXt1Fzyrbuf2sEvvWMTuOw1iltTdXJ2mfhdSQ/exec'
SHEET_ID = '1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4'
HOJA_3D = 'Diseño3D'
plantilla_blanco = {'nameplate': '', 'vent': '3/4"', 'drain': '3/4"', 'nozzles': [{'tagName': 'S1', 'diaIndex': 6, 'rating': '300#', 'bodyPart': 'shell', 'pos': 'superior', 'valX': -1.5, 'hasNS': True, 'tagNS': '3/4"', 'hasFS': True, 'tagFS': '1"'}, {'tagName': 'S2', 'diaIndex': 6, 'rating': '300#', 'bodyPart': 'shell', 'pos': 'inferior', 'valX': 1.5, 'hasNS': True, 'tagNS': '3/4"', 'hasFS': True, 'tagFS': '1"'}, {'tagName': 'T1', 'diaIndex': 8, 'rating': '300#', 'bodyPart': 'channel', 'pos': 'superior', 'valX': -2.9775, 'hasNS': True, 'tagNS': '1"', 'hasFS': True, 'tagFS': '1"'}, {'tagName': 'T2', 'diaIndex': 8, 'rating': '300#', 'bodyPart': 'channel', 'pos': 'inferior', 'valX': -2.9775, 'hasNS': True, 'tagNS': '1"', 'hasFS': True, 'tagFS': '1"'}]}
NEW = "-- NUEVO EQUIPO (En blanco) --"
ss = st.session_state


def cargar_db():
    response = requests.get(
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq",
        params={"tqx": "out:csv", "sheet": HOJA_3D, "nc": uuid.uuid4().hex},
        timeout=25,
    )
    response.raise_for_status()
    if response.text.lstrip().startswith("<"):
        raise ValueError("Sheets no devolvió un CSV. Revisa los permisos de lectura.")
    df = pd.read_csv(StringIO(response.text), dtype=str, keep_default_na=False)
    if len(df.columns) < 2:
        raise ValueError("La hoja debe tener columnas TAG y datos JSON, con encabezados.")
    db = {}
    for _, row in df.iterrows():
        tag, raw = row.iloc[0].strip(), row.iloc[1].strip()
        if not tag or not raw:
            continue
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("nozzles"), list):
            raise ValueError(f"Datos inválidos para el equipo {tag}.")
        db[tag] = data
    return db


def guardar_db(tag, data):
    response = requests.post(WEBAPP_URL, json={
        "tag": tag, "datos": json.dumps(data, ensure_ascii=False)
    }, timeout=30)
    response.raise_for_status()
    # Un HTTP 200 no demuestra que Apps Script haya escrito la fila.
    for attempt in range(3):
        fresh = cargar_db()
        if fresh.get(tag) == data:
            return fresh
        if attempt < 2:
            time.sleep(1)
    raise ValueError("No se pudo confirmar el contenido en Sheets. La escritura puede haberse realizado; revisa la hoja antes de reintentar.")


st.title("🛠️ Editor 3D de Intercambiadores de Calor")
if "ex_db" not in ss:
    try:
        ss.ex_db = cargar_db()
    except Exception as exc:
        st.error(f"No se pudo cargar Diseño3D: {exc}")
        st.stop()
if "ex_drafts" not in ss:
    ss.ex_drafts = {}
    ss.ex_seen = {}
    ss.ex_ack = None

options = [NEW] + sorted(ss.ex_db)
if "ex_select" not in ss:
    initial = st.query_params.get("equipo")
    ss.ex_select = initial if initial in ss.ex_db else NEW
selected = st.selectbox("Seleccionar equipo para editar:", options, key="ex_select")
if selected == NEW:
    if "equipo" in st.query_params:
        del st.query_params["equipo"]
else:
    st.query_params["equipo"] = selected

if ss.get("ex_loaded") != selected:
    ss.ex_loaded = selected
    ss.ex_generation = uuid.uuid4().hex
    ss.ex_ack = None
if selected not in ss.ex_drafts:
    ss.ex_drafts[selected] = deepcopy(ss.ex_db.get(selected, plantilla_blanco))
    if selected != NEW and not ss.ex_drafts[selected].get("nameplate"):
        ss.ex_drafts[selected]["nameplate"] = selected

st.caption("Edita el TAG y guarda desde el panel del visor. Cambiar el TAG guarda bajo ese nombre; no elimina la fila anterior.")
viewer_path = Path(__file__).resolve().parent.parent / "visor_3d"
if not (viewer_path / "index.html").is_file():
    st.error(f"No se encontró {viewer_path / 'index.html'}")
    st.stop()
project_root = str(viewer_path.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from visor_3d import declarar_visor

viewer = declarar_visor()
result = viewer(initial_data=ss.ex_drafts[selected], ack=ss.ex_ack,
                key="viewer_" + ss.ex_generation, default=None)
if isinstance(result, dict) and result.get("event_id") != ss.ex_seen.get(ss.ex_generation):
    event_id = result.get("event_id")
    data = result.get("data")
    if event_id and isinstance(data, dict) and isinstance(data.get("nozzles"), list):
        ss.ex_seen[ss.ex_generation] = event_id
        ss.ex_drafts[selected] = deepcopy(data)
        if result.get("action") == "save":
            tag = str(data.get("nameplate", "")).strip()
            try:
                if not tag:
                    raise ValueError("Debes ingresar el TAG del equipo.")
                data["nameplate"] = tag
                with st.spinner("Guardando y verificando en Sheets..."):
                    ss.ex_db = guardar_db(tag, data)
                ss.ex_drafts[tag] = deepcopy(data)
                message = f"✅ Equipo '{tag}' guardado y verificado en Sheets."
            except Exception as exc:
                message = f"❌ Guardado no confirmado: {exc}"
            ss.ex_ack = {"event_id": event_id, "message": message}
            st.rerun()