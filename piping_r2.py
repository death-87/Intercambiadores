"""Private R2 storage for the single authorized Piping owner."""
import hashlib
import json
import re
import uuid
from contextlib import closing
from urllib.parse import quote, unquote

import boto3
import streamlit as st
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from piping_core import validar_piping

MAX_BYTES = 32_000_000
PREFIX = "designs/"
REQUIRED = ("account_id", "bucket", "access_key_id", "secret_access_key", "owner_email")


def _client(config):
    return boto3.client(
        "s3",
        endpoint_url=f"https://{config['account_id']}.r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id=config["access_key_id"],
        aws_secret_access_key=config["secret_access_key"],
        config=Config(
            connect_timeout=5, read_timeout=30,
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )


def guardar_proyecto(config, event_id, name, design):
    if not isinstance(event_id, str) or not 1 <= len(event_id) <= 100:
        raise ValueError("Identificador de guardado inválido.")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120:
        raise ValueError("Escribe un nombre de hasta 120 caracteres.")
    name = name.strip()
    payload = json.dumps(design, ensure_ascii=False, allow_nan=False).encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise ValueError("El diseño supera 32 MB.")
    digest = hashlib.sha256(event_id.encode() + b"\x00" + payload).hexdigest()
    key = f"{PREFIX}{quote(name, safe='')}/{digest}.json"
    try:
        with closing(_client(config)) as client:
            try:
                client.put_object(
                    Bucket=config["bucket"], Key=key, Body=payload,
                    ContentType="application/json", IfNoneMatch="*",
                    Metadata={"save-digest": digest},
                )
            except ClientError as error:
                if error.response.get("ResponseMetadata", {}).get("HTTPStatusCode") != 412:
                    raise
                existing = client.head_object(Bucket=config["bucket"], Key=key)
                if existing.get("Metadata", {}).get("save-digest") != digest:
                    raise ValueError("Ya existe un archivo con ese identificador.") from error
    except (BotoCoreError, ClientError) as error:
        raise ValueError("No se pudo confirmar el guardado en R2.") from error
    return {"id": key, "name": name}


def mostrar_cuenta():
    try:
        config = st.secrets.get("piping_r2", {})
    except (FileNotFoundError, st.errors.StreamlitSecretNotFoundError):
        config = {}
    ready = all(isinstance(config.get(key), str) and config[key].strip() for key in REQUIRED)
    ready = ready and bool(re.fullmatch(r"[a-f0-9]{32}", config["account_id"]))
    logged_in = ready and st.user.is_logged_in
    owner = logged_in and st.user.get("email_verified") is True and (
        st.user.get("email", "").strip().casefold() == config["owner_email"].strip().casefold()
    )
    with st.expander("Cuenta de Piping · Mis diseños"):
        if not owner:
            st.caption("Modo invitado. Puedes diseñar, descargar el JSON y volver a importarlo.")
            if ready and not logged_in and st.button("Entrar como propietario"):
                st.login()
            if logged_in:
                st.caption("Esta cuenta no tiene acceso al guardado privado.")
                if st.button("Cerrar sesión"):
                    st.logout()
            return {}, False

        if st.button("Cerrar sesión de propietario"):
            st.session_state.clear()
            st.logout()
        if st.button("Actualizar lista de diseños"):
            st.session_state.pop("jn_r2_projects", None)
        try:
            if "jn_r2_projects" not in st.session_state:
                with closing(_client(config)) as client:
                    pages = client.get_paginator("list_objects_v2").paginate(
                        Bucket=config["bucket"], Prefix=PREFIX,
                    )
                    objects = [
                        (item["Key"], item["LastModified"])
                        for page in pages for item in page.get("Contents", [])
                        if re.fullmatch(r"designs/[^/]+/[a-f0-9]{64}\.json", item["Key"])
                    ]
                st.session_state["jn_r2_projects"] = sorted(
                    objects, key=lambda item: item[1], reverse=True,
                )
            projects = dict(st.session_state["jn_r2_projects"])
            selected = st.selectbox(
                "Diseños privados", list(projects), index=None,
                format_func=lambda key: (
                    f"{unquote(key.split('/')[1])} · "
                    f"{projects[key]:%Y-%m-%d %H:%M} UTC · {key.split('/')[-1][:8]}"
                ),
            )
            if st.button("Abrir diseño de la nube", disabled=selected is None):
                with closing(_client(config)) as client:
                    response = client.get_object(Bucket=config["bucket"], Key=selected)
                    with closing(response["Body"]) as body:
                        raw = body.read(MAX_BYTES + 1)
                if len(raw) > MAX_BYTES:
                    raise ValueError("El diseño supera 32 MB.")
                design = validar_piping(json.loads(raw))
                st.session_state["jn_piping_design"] = design
                st.session_state["jn_piping_load_token"] = uuid.uuid4().hex
                st.session_state["jn_piping_imported"] = True
        except (BotoCoreError, ClientError, ValueError, TypeError, KeyError):
            st.error("No se pudieron consultar o abrir los diseños de R2.")
    return config, True
