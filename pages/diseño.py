"""Página Streamlit para editar y guardar el modelo 3D."""
from pathlib import Path
from copy import deepcopy
from io import StringIO
import json
import time
import uuid
import sys
import unicodedata
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Editor 3D de Equipos", layout="wide")
WEBAPP_URL = 'https://script.google.com/macros/s/AKfycbxPmdGXS7i61XrwRDWc9rRJAceBByb4AmXt1Fzyrbuf2sEvvWMTuOw1iltTdXJ2mfhdSQ/exec'
SHEET_ID = '1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4'
HOJA_3D = 'Diseño3D'
plantilla_blanco = {
    "model": "A",
    "dimensions": {
        "shellLength": 4.275, "reducerLength": 0.9, "channelLength": 1.20,
        "bonnetLength": 0.80, "shellDiameter": 1.098,
        "channelDiameter": 1.098, "bonnetDiameter": 1.098,
        "modelALengthsEnabled": True,
    },
    "nameplate": "", "nameplateSide": "front", "vent": "", "drain": "",
    "nozzles": [
        {"tagName": "S1", "service": "process", "diaIndex": 6, "connectionType": "flanged", "rating": "300#", "flangeType": "WN", "face": "RF", "bodyPart": "shell",
         "pos": "superior", "valX": -1.5, "hasNS": True, "sizeNS": '3/4"',
         "tagNS": "", "hasFS": True, "sizeFS": '1"', "tagFS": ""},
        {"tagName": "S2", "service": "process", "diaIndex": 6, "connectionType": "flanged", "rating": "300#", "flangeType": "WN", "face": "RF", "bodyPart": "shell",
         "pos": "inferior", "valX": 1.5, "hasNS": True, "sizeNS": '3/4"',
         "tagNS": "", "hasFS": True, "sizeFS": '1"', "tagFS": ""},
        {"tagName": "T1", "service": "process", "diaIndex": 8, "connectionType": "flanged", "rating": "300#", "flangeType": "WN", "face": "RF", "bodyPart": "channel",
         "pos": "superior", "valX": -2.9775, "hasNS": True, "sizeNS": '1"',
         "tagNS": "", "hasFS": True, "sizeFS": '1"', "tagFS": ""},
        {"tagName": "T2", "service": "process", "diaIndex": 8, "connectionType": "flanged", "rating": "300#", "flangeType": "WN", "face": "RF", "bodyPart": "channel",
         "pos": "inferior", "valX": -2.9775, "hasNS": True, "sizeNS": '1"',
         "tagNS": "", "hasFS": True, "sizeFS": '1"', "tagFS": ""},
        {"tagName": "VENT", "service": "vent", "diaIndex": 1, "connectionType": "threaded", "rating": "3000#", "flangeType": "WN", "face": "RF", "bodyPart": "bonnet",
         "pos": "superior", "valX": 2.50, "hasNS": False, "sizeNS": "", "tagNS": "", "hasFS": False, "sizeFS": "", "tagFS": ""},
        {"tagName": "DRAIN", "service": "drain", "diaIndex": 1, "connectionType": "threaded", "rating": "3000#", "flangeType": "WN", "face": "RF", "bodyPart": "bonnet",
         "pos": "inferior", "valX": 2.50, "hasNS": False, "sizeNS": "", "tagNS": "", "hasFS": False, "sizeFS": "", "tagFS": ""},
    ],
}
NEW = "-- NUEVO EQUIPO (En blanco) --"
ss = st.session_state


def normalizar_tag(value):
    value = unicodedata.normalize("NFKD", str(value).strip())
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).upper().split())


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
        if normalizar_tag(tag) == "__CONFIG_INFORMES__":
            continue
        if not tag or not raw:
            continue
        data = json.loads(raw)
        if not isinstance(data, dict) or not isinstance(data.get("nozzles"), list):
            raise ValueError(f"Datos inválidos para el equipo {tag}.")
        db[tag] = data
    # El superior es seleccionable por su TAG, pero ambos niveles conservan
    # una única fuente de verdad: el diseño completo del conjunto.
    conjuntos = list(db.items())
    propietarios = {}
    for owner, data in conjuntos:
        if data.get("stackedEquipment", {}).get("sameEquipment"):
            continue
        upper = data.get("stackedEquipment", {}).get("data", {})
        upper_tag = str(upper.get("nameplate", "")).strip()
        if not upper_tag:
            continue
        key = normalizar_tag(upper_tag)
        if key == normalizar_tag(owner) or key in propietarios:
            raise ValueError(f"TAG superior duplicado en conjuntos: {upper_tag}")
        propietarios[key] = owner
        for existing in list(db):
            if normalizar_tag(existing) == key:
                del db[existing]
        db[upper_tag] = data
    return db


def tag_registro(data):
    apilado = data.get("stackedEquipment", {})
    return str((apilado.get("equipmentTag") or data.get("nameplate", ""))
               if apilado.get("sameEquipment") else data.get("nameplate", "")).strip()


def resolver_tag_guardado(tag, db):
    """Reutiliza el nombre guardado para actualizar el mismo registro."""
    solicitado = str(tag).strip()
    coincidencias = [k for k in db if normalizar_tag(k) == normalizar_tag(solicitado)]
    if len(coincidencias) > 1:
        raise ValueError(f"Hay varios registros equivalentes a '{solicitado}'. Corrige los TAG duplicados.")
    return coincidencias[0] if coincidencias else solicitado


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

def preparar_copia_desde(origen):
    """Callback: se ejecuta antes del rerun y puede cambiar el widget ex_select."""
    copia = deepcopy(ss.ex_drafts[origen])
    copia["nameplate"] = ""
    ss.ex_drafts[NEW] = copia
    ss.ex_template_source = origen
    ss.ex_select = NEW
    ss.ex_loaded = None


# La página principal puede abrir un equipo o copiarlo como plantilla. La copia
# comienza como un borrador sin TAG y nunca escribe sobre el equipo de origen.
template_requested = ss.get("tag_para_plantilla")
if template_requested:
    try:
        ss.ex_db = cargar_db()
    except Exception as exc:
        st.error(f"No se pudo actualizar Diseño3D antes de copiar {template_requested}: {exc}")
        st.stop()
    coincidencias = [k for k in ss.ex_db if normalizar_tag(k) == normalizar_tag(template_requested)]
    if len(coincidencias) != 1:
        st.error(f"No se encontró un único diseño válido para usar como plantilla: {template_requested}.")
        st.stop()
    origen = coincidencias[0]
    copia = deepcopy(ss.ex_db[origen])
    copia["nameplate"] = ""
    ss.ex_drafts[NEW] = copia
    ss.ex_select = NEW
    ss.ex_loaded = None
    ss.ex_template_source = origen
    ss.pop("tag_para_plantilla", None)
    ss.pop("tag_para_diseño", None)

# La página principal entrega el TAG por sesión; switch_page puede limpiar la URL.
requested = ss.get("tag_para_diseño")
if requested:
    try:
        ss.ex_db = cargar_db()
    except Exception as exc:
        st.error(f"No se pudo actualizar Diseño3D antes de abrir {requested}: {exc}")
        st.stop()
    coincidencias = [k for k in ss.ex_db if normalizar_tag(k) == normalizar_tag(requested)]
    if len(coincidencias) > 1:
        st.error(f"Hay varios TAG equivalentes a {requested} en Diseño3D. Corrige el duplicado.")
        st.stop()
    if coincidencias:
        ss.ex_select = coincidencias[0]
    else:
        # Conservar otro borrador nuevo por TAG antes de abrir el solicitado.
        previous = ss.ex_drafts.get(NEW)
        if previous and previous.get("nameplate"):
            ss.ex_drafts["draft:" + normalizar_tag(previous["nameplate"])] = deepcopy(previous)
        ss.ex_select = NEW
        draft_key = "draft:" + normalizar_tag(requested)
        ss.ex_drafts[NEW] = deepcopy(ss.ex_drafts.get(draft_key, plantilla_blanco))
        ss.ex_drafts[NEW]["nameplate"] = str(requested).strip()
    ss.ex_loaded = None
    ss.pop("tag_para_diseño", None)

options = [NEW] + sorted(ss.ex_db)
pending_selection = ss.pop("ex_select_pending", None)
if pending_selection in options:
    ss.ex_select = pending_selection
if "ex_select" not in ss:
    initial = st.query_params.get("equipo")
    ss.ex_select = initial if initial in ss.ex_db else NEW
selected = st.selectbox("Seleccionar equipo para editar:", options, key="ex_select")
if selected != NEW and ss.get("ex_template_source"):
    ss.pop("ex_template_source", None)
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

if selected != NEW:
    st.button(
        "📋 Crear equipo nuevo usando este formato",
        help="Copia modelo, dimensiones y boquillas; el equipo actual queda intacto.",
        use_container_width=True,
        on_click=preparar_copia_desde,
        args=(selected,),
    )

if selected == NEW and ss.get("ex_template_source"):
    st.info(f"Plantilla copiada desde '{ss.ex_template_source}'. Escribe el TAG de destino: si ya existe, su diseño se reemplazará; si no existe, se creará un registro nuevo.")
else:
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
# La raíz del JSON es siempre el inferior. La selección del editor viaja
# separadamente para que abrir el TAG superior no active el equipo inferior.
editor_data = deepcopy(ss.ex_drafts[selected])
editor_data["_editorSelection"] = {
    "tag": selected if selected != NEW else "",
    "token": ss.ex_generation,
}
result = viewer(initial_data=editor_data, ack=ss.ex_ack, stack_models=ss.ex_db,
                selected_tag=editor_data["_editorSelection"]["tag"], selection_token=ss.ex_generation,
                draft_key=selected,
                key="viewer_" + ss.ex_generation, default=None)
if isinstance(result, dict) and result.get("event_id") != ss.ex_seen.get(ss.ex_generation):
    event_id = result.get("event_id")
    data = result.get("data")
    if event_id and isinstance(data, dict) and isinstance(data.get("nozzles"), list):
        ss.ex_seen[ss.ex_generation] = event_id
        ss.ex_drafts[selected] = deepcopy(data)
        # Los dos accesos al conjunto comparten también el borrador actual.
        owner_tag = tag_registro(data)
        upper_tag = str(data.get("stackedEquipment", {}).get("data", {}).get("nameplate", "")).strip()
        if upper_tag:
            for alias in ((owner_tag,) if data.get("stackedEquipment", {}).get("sameEquipment") else (owner_tag, upper_tag)):
                if alias in ss.ex_db:
                    ss.ex_drafts[alias] = deepcopy(data)
        if result.get("action") == "save":
            tag = tag_registro(data)
            try:
                if not tag:
                    raise ValueError("Debes ingresar el TAG del equipo.")
                tag = resolver_tag_guardado(tag, ss.ex_db)
                if data.get("stackedEquipment", {}).get("sameEquipment"):
                    data["stackedEquipment"]["equipmentTag"] = tag
                else:
                    data["nameplate"] = tag
                with st.spinner("Guardando y verificando en Sheets..."):
                    ss.ex_db = guardar_db(tag, data)
                ss.ex_drafts[tag] = deepcopy(data)
                upper_tag = str(data.get("stackedEquipment", {}).get("data", {}).get("nameplate", "")).strip()
                ss.ex_select_pending = upper_tag if not data.get("stackedEquipment", {}).get("sameEquipment") and upper_tag and normalizar_tag(selected) == normalizar_tag(upper_tag) else tag
                if upper_tag and not data.get("stackedEquipment", {}).get("sameEquipment"):
                    ss.ex_drafts[upper_tag] = deepcopy(data)
                ss.ex_loaded = None
                ss.pop("ex_template_source", None)
                ss.design_revision = ss.get("design_revision", 0) + 1
                message = (f"✅ Equipo '{tag}' guardado con ambos niveles y todas sus conexiones." if data.get("stackedEquipment", {}).get("sameEquipment") else f"✅ Conjunto '{tag}' / '{upper_tag}' guardado; cada TAG conserva sus propias boquillas." if upper_tag else f"✅ Equipo '{tag}' guardado y verificado en Sheets.")
            except Exception as exc:
                message = f"❌ Guardado no confirmado: {exc}"
            ss.ex_ack = {"event_id": event_id, "message": message}
            st.rerun()
