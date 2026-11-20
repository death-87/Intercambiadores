"""Herramientas de inspección integradas dentro de Jndigital."""
from pathlib import Path
import runpy
import streamlit as st
from portal import ir_inicio
from inspecciones.configuracion import google_configurado

ROOT = Path(__file__).resolve().parent
HERRAMIENTAS = {
    "Informe de inspección visual": "pages/2_Informe_Visual.py",
    "Informe de equipos / intercambiadores": "pages/3_Intercambiadores.py",
    "Checklist de inspección visual": "pages/4_Checklist_IV.py",
    "Checklist de piping": "pages/Checklist Piping.py",
    "Panel de actividades de inspectores": "app.py",
}


def mostrar_informes():
    st.markdown('<style>' + (ROOT.parent / 'assets' / 'inspecciones.css').read_text() + '</style>', unsafe_allow_html=True)
    st.button("← Inicio de Jndigital", key="jn_informes_inicio", on_click=ir_inicio)
    st.markdown('''<header class="jn-report-header"><div class="jn-report-brand"><b>jn<span>.</span></b><div><strong>Jndigital</strong><small>GESTIÓN DE INSPECCIÓN Y MANTENIMIENTO</small></div></div><div class="jn-report-category">SOLUCIONES / INFORMES DE INSPECCIÓN</div></header>''', unsafe_allow_html=True)
    herramienta = st.selectbox("Herramienta de inspección", list(HERRAMIENTAS), key="jn_inspecciones_herramienta")
    from inspecciones.acceso import USUARIOS_SISTEMA
    autenticado = st.session_state.get('autenticado') and st.session_state.get('usuario_actual') in USUARIOS_SISTEMA
    if not autenticado:
        st.markdown('<style>[data-testid="stSidebar"],[data-testid="stHeader"],[data-testid="collapsedControl"]{display:none}</style>', unsafe_allow_html=True)
        st.markdown('''<div class="jn-access-intro"><h2>Tu espacio de inspección.</h2><p>Inicia sesión con tu cuenta habitual de inspector. Los permisos se mantienen para consultar y registrar información.</p></div>''', unsafe_allow_html=True)
        from inspecciones.acceso import validar_usuario
        with st.form('jn_inspecciones_login'):
            usuario = st.text_input('Usuario', key='jn_inspecciones_login_usuario').strip().lower()
            password = st.text_input('Contraseña', type='password', key='jn_inspecciones_login_password')
            ingresar = st.form_submit_button('Ingresar a Informes de Inspección', type='primary')
        if ingresar:
            if validar_usuario(usuario, password):
                datos = USUARIOS_SISTEMA[usuario]
                st.session_state.update(autenticado=True, usuario_actual=usuario, rol_actual=datos['rol'], nombre_usuario=datos['nombre'])
                st.rerun()
            else:
                st.error('Usuario o contraseña incorrectos.')
        return
    st.sidebar.markdown('**Jndigital · Inspección**')
    st.sidebar.caption('Sesión: ' + str(st.session_state.get('nombre_usuario', 'Inspector')))
    if herramienta != "Panel de actividades de inspectores" and st.sidebar.button('Cerrar sesión', key='jn_inspecciones_logout'):
        for key in ('autenticado','usuario_actual','rol_actual','nombre_usuario'):
            st.session_state.pop(key, None)
        st.rerun()
    if not google_configurado():
        st.info('Puedes preparar y descargar informes con datos manuales. Para consultar equipos, informes guardados o fotografías de Drive, falta conectar Google en Render.')
        with st.expander('Conectar los datos actuales de Informes de Inspección'):
            st.write('En la configuración de inspectores.streamlit.app, abre Secrets. Copia directamente su contenido a una variable privada de Render llamada INSPECCIONES_SECRETS_TOML. No lo pegues en el chat ni en GitHub.')
            st.caption('También se admite INSPECCIONES_GOOGLE_CREDENTIALS_JSON con las credenciales JSON de la misma cuenta de servicio. Conserva los permisos y las hojas actuales.')
        if herramienta == "Panel de actividades de inspectores":
            st.warning('El panel de actividades requiere conectar la planilla antes de continuar.')
            return
    runpy.run_path(str(ROOT / HERRAMIENTAS[herramienta]), run_name='__inspecciones_herramienta__')
