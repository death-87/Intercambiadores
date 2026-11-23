"""Portada y navegación de Jndigital, independientes de los módulos técnicos."""
from html import escape
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
SOLUCIONES = (
    ("01", "Intercambiadores", "Información técnica, modelos 3D e informes de conexiones roscadas en un mismo espacio.", "Equipos · Modelos 3D · PDF", "disponible"),
    ("02", "Informes de Inspección", "Creación de informes y organización de los antecedentes de cada inspección.", "Informes · Antecedentes · Revisiones", "disponible"),
    ("03", "Reparaciones Temporales", "Seguimiento de reparaciones temporales y sus antecedentes técnicos.", "Reparaciones · Seguimiento · Registros", "disponible"),
    ("04", "Piping e isométricos", "Arma líneas con cañerías, válvulas, codos, tees, reductores y bridas del catálogo de equipos.", "Diseño 3D · Isométricos · Materiales", "disponible"),
)
ENLACES_SOLUCIONES = {
    "03": "https://reparacionestemp.streamlit.app/",
}



def ir_solucion():
    st.session_state["jn_section"] = "intercambiadores"
    st.query_params["solucion"] = "intercambiadores"


def ir_informes():
    st.session_state["jn_section"] = "informes"
    st.query_params["solucion"] = "informes"


def ir_piping():
    st.session_state["jn_section"] = "piping"
    st.query_params["solucion"] = "piping"


def ir_inicio():
    st.session_state["jn_section"] = "inicio"
    if "solucion" in st.query_params:
        del st.query_params["solucion"]


def mostrar_inicio():
    """Devuelve True si se mostró la portada; el módulo no debe cargar datos aún."""
    section = st.session_state.get("jn_section", st.query_params.get("solucion", "inicio"))
    if section == "piping":
        from piping import mostrar_piping
        mostrar_piping()
        return True
    if section == "informes":
        from inspecciones import mostrar_informes
        mostrar_informes()
        return True
    if section == "intercambiadores":
        st.button("← Inicio de Jndigital", key="jn_back_home", on_click=ir_inicio, use_container_width=True)
        st.sidebar.markdown('<div class="jn-module-label">SOLUCIÓN / INTERCAMBIADORES</div><style>[data-testid="stSidebarNav"]{display:none}.jn-module-label{font-size:10px;letter-spacing:.12em;color:#64748b;margin:12px 0}</style>', unsafe_allow_html=True)
        return False

    st.markdown('<style>' + (ROOT / "assets" / "portal.css").read_text(encoding="utf-8") + '</style>', unsafe_allow_html=True)
    with st.container(key="jn_topbar"):
        brand, links, access = st.columns([4, 4, 2], vertical_alignment="center")
        with brand:
            st.markdown('<div class="jn-brand"><span class="jn-monogram">jn<span>●</span></span><div><b>Jndigital<span class="jn-brand-dot">.</span></b><small>SOLUCIONES PARA LA GESTIÓN TÉCNICA</small></div></div>', unsafe_allow_html=True)
        with links:
            st.markdown('<nav class="jn-nav" aria-label="Secciones de inicio"><a href="#soluciones">Soluciones</a><a href="#enfoque">Servicios</a></nav>', unsafe_allow_html=True)
        with access:
            st.markdown('<a class="jn-access-link" href="#soluciones">Acceder a herramientas ↗</a>', unsafe_allow_html=True)

    with st.container(key="jn_hero"):
        left, right = st.columns([1.18, 1], gap="large", vertical_alignment="center")
        with left:
            st.markdown('''<div class="jn-hero-copy"><div class="jn-kicker"><span></span> INGENIERÍA + SOLUCIONES DIGITALES</div>
            <h1>Tecnología para<br>inspeccionar <em>mejor.</em></h1>
            <p>Conecta la información de tus equipos con las decisiones de cada día. Herramientas para la inspección, los informes y la gestión del mantenimiento.</p></div>''', unsafe_allow_html=True)
            st.markdown('<a class="jn-primary-link" href="#soluciones">Explorar soluciones →</a>', unsafe_allow_html=True)
            st.markdown('<div class="jn-hero-note"><span class="jn-status-dot"></span> Equipos, informes y seguimiento técnico</div>', unsafe_allow_html=True)
        with right:
            st.markdown('''<div class="jn-visual" role="img" aria-label="Esquema de un intercambiador y su flujo de información técnica">
            <div class="jn-visual-top"><span>INFORMACIÓN QUE COBRA FORMA</span><span class="jn-cross">+</span></div>
            <svg class="jn-machine" viewBox="0 0 520 300" fill="none" aria-hidden="true">
              <defs><linearGradient id="jn-metal" x1="100" y1="90" x2="300" y2="230" gradientUnits="userSpaceOnUse"><stop stop-color="#35596b"/><stop offset=".5" stop-color="#173746"/><stop offset="1" stop-color="#0e2835"/></linearGradient></defs>
              <g stroke="#244353" stroke-width="1"><path d="M0 100H520M0 150H520M0 200H520M0 250H520M60 0V300M160 0V300M260 0V300M360 0V300M460 0V300"/></g>
              <path d="M91 183L155 216L413 132L347 101Z" fill="#081c27" opacity=".7"/>
              <path d="M136 141L351 82L393 111L178 173Z" fill="#295162" stroke="#83afbf"/>
              <path d="M178 173L393 111V175L178 237Z" fill="url(#jn-metal)" stroke="#83afbf"/>
              <path d="M136 141V205L178 237V173Z" fill="#3b6171" stroke="#a1c3cd"/>
              <path d="M143 142V207M151 148V212M168 166V229M184 171V234M371 117V181M380 114V178" stroke="#aac8d0" stroke-width="2"/>
              <path d="M208 155V218M223 151V214M238 147V210M253 143V206M268 139V202M283 135V198M298 131V194M313 127V190M328 123V186" stroke="#467082"/>
              <path d="M211 122V80L231 74V116M316 196V237L338 230V190" fill="#315d6b" stroke="#9ac1cc"/>
              <path d="M206 80L226 73L237 77L216 84ZM311 235L333 228L344 232L322 239Z" fill="#20cab1" stroke="#6fe4d4"/>
              <path d="M212 225V250L228 258L245 253V216M334 190V218L350 227L367 222V181" stroke="#83afbf" stroke-width="2"/>
              <path d="M232 74V44H325M338 230V263H430M141 163H82V110H39" stroke="#20cab1" stroke-dasharray="4 5"/>
              <circle cx="232" cy="74" r="5" fill="#20cab1"/><circle cx="338" cy="230" r="5" fill="#20cab1"/><circle cx="141" cy="163" r="5" fill="#20cab1"/>
              <text x="333" y="48" fill="#93b4c3" font-size="11" font-family="sans-serif">DATOS TÉCNICOS</text><text x="344" y="282" fill="#93b4c3" font-size="11" font-family="sans-serif">MODELO 3D</text><text x="25" y="98" fill="#93b4c3" font-size="11" font-family="sans-serif">INSPECCIÓN</text>
            </svg><div class="jn-visual-bottom"><span>REGISTRO</span><i>→</i><span>VISUALIZACIÓN</span><i>→</i><span>INFORME</span></div></div>''', unsafe_allow_html=True)

    st.markdown('''<div class="jn-value-strip"><span>UNA BASE TÉCNICA, MÁS POSIBILIDADES</span><b>Información organizada</b><i>＋</i><b>Visualización de equipos</b><i>＋</i><b>Informes claros</b></div>''', unsafe_allow_html=True)
    st.markdown('''<section id="soluciones" class="jn-section-heading"><div><div class="jn-eyebrow">ELIGE TU ESPACIO DE TRABAJO</div><h2>Soluciones que avanzan contigo<span>.</span></h2></div><p>Comienza con las herramientas disponibles.<br>Un punto de acceso a tus aplicaciones técnicas.</p></section>''', unsafe_allow_html=True)
    with st.container(key="jn_solutions"):
        columns = st.columns(4, gap="medium")
        for column, (number, title, description, detail, status) in zip(columns, SOLUCIONES):
            with column, st.container(key="jn_solution_" + number, border=True):
                available = status == "disponible"
                state = {"disponible":"Disponible", "por_conectar":"Por conectar", "proximamente":"Próximamente"}[status]
                badge = "jn-badge active" if available else "jn-badge"
                st.markdown(f'''<article class="jn-solution"><div class="jn-card-top"><span class="jn-card-number">{number}</span><span class="{badge}">{state}</span></div><h3>{escape(title)}</h3><p>{escape(description)}</p><div class="jn-card-detail">{escape(detail)}</div></article>''', unsafe_allow_html=True)
                if number in ENLACES_SOLUCIONES:
                    st.link_button("Abrir herramienta ↗", ENLACES_SOLUCIONES[number], use_container_width=True)
                    st.markdown('<div class="jn-external-note">Se abre en una pestaña nueva</div>', unsafe_allow_html=True)
                else:
                    st.button("Abrir solución ↗" if available else "En preparación", key="jn_open_" + number, disabled=not available, on_click=(ir_informes if number == "02" else ir_piping if number == "04" else ir_solucion) if available else None, use_container_width=True, type="primary" if available else "secondary")

    st.markdown('''<section id="enfoque" class="jn-approach"><div><div class="jn-eyebrow">NUESTROS SERVICIOS DIGITALES</div><h2>Menos dispersión.<br>Más criterio técnico.</h2><p>Un portal pensado para acompañar el trabajo de terreno y la preparación de información técnica.</p></div><div class="jn-steps"><div><span>01</span><section><h3>Organiza</h3><p>Consulta equipos, antecedentes y datos operacionales.</p></section></div><div><span>02</span><section><h3>Visualiza</h3><p>Revisa modelos 3D y ubica las conexiones del equipo.</p></section></div><div><span>03</span><section><h3>Documenta</h3><p>Genera fichas e informes con la información disponible.</p></section></div></div></section>''', unsafe_allow_html=True)
    with st.container(key="jn_bottom_cta"):
        copy, button = st.columns([3, 1], vertical_alignment="center")
        with copy:
            st.markdown('<div class="jn-bottom-copy"><h3>Tu próximo trabajo comienza aquí.</h3><p>Encuentra la herramienta para tus equipos, inspecciones e informes.</p></div>', unsafe_allow_html=True)
        with button:
            st.markdown('<a class="jn-access-link" href="#soluciones">Ver herramientas →</a>', unsafe_allow_html=True)
    st.markdown('<footer class="jn-footer"><b>Jndigital<span>.</span></b><p>Gestión de Inspección y Mantenimiento</p><a href="#soluciones">Explorar soluciones ↑</a></footer>', unsafe_allow_html=True)
    return True
