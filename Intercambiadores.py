import os
import re
import json
import unicodedata
import urllib.parse
import pandas as pd
import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
from fpdf import FPDF

# -----------------------------------------------------------------------------
# NAVEGACIÓN SEGURA Y CARGA DE MÓDULOS (SOPORTE PARA MAYÚSCULAS/TILDES)
# -----------------------------------------------------------------------------
def ir_a_diseno():
    paginas_posibles = [
        "pages/diseno.py",
        "pages/Diseño.py",
        "pages/diseño.py",
        "pages/Diseno.py"
    ]
    for pag in paginas_posibles:
        try:
            st.switch_page(pag)
            return
        except Exception:
            continue
    st.error("❌ No se encontró el archivo de diseño en la carpeta 'pages/'. Revisa que esté subido a GitHub como 'pages/diseno.py' o 'pages/Diseño.py'.")

# Intentar importar el motor SVG probando distintas combinaciones de nombre de archivo
generate_modular_exchanger_svg = None
for mod_path in ["pages.diseno", "pages.Diseño", "pages.diseño", "pages.Diseno"]:
    try:
        import importlib
        mod = importlib.import_module(mod_path)
        generate_modular_exchanger_svg = getattr(mod, "generate_modular_exchanger_svg", None)
        if generate_modular_exchanger_svg:
            break
    except Exception:
        continue

# Configuración de página de Streamlit
st.set_page_config(page_title="Control de Intercambiadores de Calor", layout="wide")

# Estilizado global para tablas compactas y legibles
st.markdown("""
    <style>
    [data-testid="stTable"] {
        width: fit-content !important;
        max-width: 100% !important;
        margin-top: 5px;
    }
    [data-testid="stTable"] table {
        width: auto !important;
    }
    [data-testid="stTable"] th {
        font-size: 11px !important;
        padding: 6px 12px !important;
        font-weight: 700 !important;
        white-space: nowrap !important;
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
    }
    [data-testid="stTable"] td {
        font-size: 11px !important;
        padding: 5px 12px !important;
        white-space: nowrap !important;
        line-height: 1.2 !important;
        border: 1px solid #334155 !important;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CABECERA VISUAL
# -----------------------------------------------------------------------------
if os.path.exists("franja.jpg"):
    st.image("franja.jpg", use_container_width=True)

st.title("🔥 Consulta e Inspección de Intercambiadores de Calor")
st.markdown("---")

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE GOOGLE SHEETS
# -----------------------------------------------------------------------------
SHEET_ID = "1lhpb211bqPyDAxxnBFgKaN7nY-WImR961xJ3mrIGYZ4"
NOMBRE_HOJA = "Hoja 1"

GDRIVE_FOLDER_URL = "https://drive.google.com/drive/folders/1zGSlDQu5o9waFqm211P344MAqxCC8AAK"

MAPA_COLORES_ESTATUS = {
    "CHEQUEADO": "#28a745",        # Verde
    "NO CHEQUEADO": "#dc3545",     # Rojo
    "SIN INFORMACIÓN": "#6c757d"   # Gris
}

# -----------------------------------------------------------------------------
# CLASE Y FUNCIONES AUXILIARES PARA PDF Y TEXTO
# -----------------------------------------------------------------------------
class PDFCustom(FPDF):
    def footer(self):
        self.set_y(-18)
        logo_path = None
        for posible in ["logojn.png", "logojn.npg", "logo.png"]:
            if os.path.exists(posible):
                logo_path = posible
                break
        
        if logo_path:
            try:
                self.image(logo_path, x=170, y=self.get_y(), w=25)
            except Exception:
                pass

def normalizar_texto(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    nfkd_form = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).lower().strip()

def sanitizar_para_pdf(texto):
    if not isinstance(texto, str):
        texto = str(texto)
    return texto.encode('latin-1', 'replace').decode('latin-1')

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

def generar_link_gdrive(termino_busqueda):
    busqueda_encoded = urllib.parse.quote(str(termino_busqueda))
    return f"https://drive.google.com/drive/u/0/search?q={busqueda_encoded}"

def extraer_coordenadas(coordenadas):
    if pd.isna(coordenadas) or str(coordenadas).strip() in ['Sin información', 'nan', '']:
        return None, None
    numeros = re.findall(r'-?\d+[\.,]\d+', str(coordenadas))
    if len(numeros) >= 2:
        lat = numeros[0].replace(',', '.')
        lon = numeros[1].replace(',', '.')
        return lat, lon
    return None, None

def generar_pdf_equipo(val_equipo, val_unidad, valor_status, datos_mostrar, color_hex, titulo_doc, config_equipo=None):
    pdf = PDFCustom()
    pdf.set_auto_page_break(auto=True, margin=22)
    pdf.add_page()
    rgb = hex_to_rgb(color_hex)
    
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 7, sanitizar_para_pdf(titulo_doc), ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 10)
    txt_equipo_unidad = f"EQUIPO: {sanitizar_para_pdf(val_equipo)}    |    UNIDAD DE PROCESO: {sanitizar_para_pdf(val_unidad)}"
    pdf.cell(0, 5, txt_equipo_unidad, ln=True, align="C")
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*rgb)
    pdf.cell(0, 5, f"Estatus Actual: {sanitizar_para_pdf(valor_status)}", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(3)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Ficha Tecnica del Intercambiador", ln=True)
    pdf.ln(1)
    
    items_filtrados = [(str(k), str(v)) for k, v in datos_mostrar.items() if str(v).strip() != ""]
    
    ancho_columna = 93
    pdf.set_draw_color(*rgb)
    
    for i in range(0, len(items_filtrados), 2):
        k1, v1 = items_filtrados[i]
        k1_c = sanitizar_para_pdf(k1)
        v1_c = sanitizar_para_pdf(v1)
        
        if i + 1 < len(items_filtrados):
            k2, v2 = items_filtrados[i+1]
            k2_c = sanitizar_para_pdf(k2)
            v2_c = sanitizar_para_pdf(v2)
        else:
            k2_c, v2_c = "", ""
            
        lineas_v1 = max(1, int(len(v1_c) / 50) + 1)
        lineas_v2 = max(1, int(len(v2_c) / 50) + 1) if k2_c else 1
        max_lineas = max(lineas_v1, lineas_v2)
        
        altura_valor = max_lineas * 4.5 + 2
        
        if pdf.get_y() + altura_valor + 20 > 270:
            pdf.add_page()
            
        x_inicio = pdf.get_x()
        
        pdf.set_font("Arial", "B", 7.5)
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(ancho_columna, 4.5, f"  {k1_c}", border="TRL", fill=True)
        pdf.cell(4, 4.5, "", border=0)
        
        if k2_c:
            pdf.cell(ancho_columna, 4.5, f"  {k2_c}", border="TRL", fill=True, ln=True)
        else:
            pdf.cell(ancho_columna, 4.5, "", border=0, ln=True)
            
        y_despues_titulos = pdf.get_y()
        
        pdf.set_xy(x_inicio, y_despues_titulos)
        pdf.set_font("Arial", "", 8)
        pdf.multi_cell(ancho_columna, 4.5, f"  {v1_c}", border="BRL")
        y_fin_izq = pdf.get_y()
        
        if k2_c:
            pdf.set_xy(x_inicio + ancho_columna + 4, y_despues_titulos)
            pdf.set_font("Arial", "", 8)
            pdf.multi_cell(ancho_columna, 4.5, f"  {v2_c}", border="BRL")
            y_fin_der = pdf.get_y()
            max_y = max(y_fin_izq, y_fin_der)
        else:
            max_y = y_fin_izq
            
        pdf.set_xy(x_inicio, max_y + 1)

    if config_equipo and generate_modular_exchanger_svg:
        try:
            import cairosvg
            svg_code = generate_modular_exchanger_svg(config_equipo)
            png_temp = f"temp_pdf_{sanitizar_para_pdf(val_equipo)}.png"
            cairosvg.svg2png(bytestring=svg_code.encode('utf-8'), write_to=png_temp)
            
            if pdf.get_y() + 85 > 270:
                pdf.add_page()
            pdf.ln(5)
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 5, "Plano Esquematico del Equipo", ln=True)
            pdf.ln(2)
            pdf.image(png_temp, x=15, w=180)
            if os.path.exists(png_temp):
                os.remove(png_temp)
        except Exception:
            pass
        
    pdf.set_draw_color(0, 0, 0)
    
    pdf_out = pdf.output()
    if isinstance(pdf_out, str):
        return pdf_out.encode('latin-1')
    return bytes(pdf_out)

# -----------------------------------------------------------------------------
# CARGA AUTOMÁTICA DE DATOS
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def cargar_datos(sheet_id, nombre_hoja):
    nombre_hoja_encoded = urllib.parse.quote(nombre_hoja)
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_hoja_encoded}"
    
    data = pd.read_csv(sheet_url)
    
    columnas = []
    conteo_columnas = {}
    for col in data.columns:
        col_clean = " ".join(str(col).split())
        if col_clean in conteo_columnas:
            conteo_columnas[col_clean] += 1
            columnas.append(f"{col_clean} ({conteo_columnas[col_clean]})")
        else:
            conteo_columnas[col_clean] = 1
            columnas.append(col_clean)
            
    data.columns = columnas
    data = data.fillna("Sin información")
    data = data.astype(str)
    
    for col in data.columns:
        if 'STATUS' in col.upper() or 'ESTATUS' in col.upper():
            data[col] = data[col].str.strip().str.upper()
            data[col] = data[col].replace({'NAN': 'SIN INFORMACIÓN', '': 'SIN INFORMACIÓN'})
            
    return data

try:
    df = cargar_datos(SHEET_ID, NOMBRE_HOJA)
except Exception as e:
    st.error(f"❌ Error al conectar con Google Sheets: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# RECONOCIMIENTO DE COLUMNAS CLAVE
# -----------------------------------------------------------------------------
col_unidad = next((c for c in df.columns if 'UNIDAD' in c.upper()), None)
col_equipo = next((c for c in df.columns if 'EQUIPO' in c.upper()), None)
col_status = next((c for c in df.columns if 'STATUS' in c.upper() or 'ESTATUS' in c.upper()), None)
col_comentario = next((c for c in df.columns if 'COMENTARIO' in c.upper()), None)
col_geo = next((c for c in df.columns if 'GEORREFERENCIA' in c.upper() or 'LAT' in c.upper() or 'COORD' in c.upper()), None)

# -----------------------------------------------------------------------------
# BARRA LATERAL: FILTROS
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Búsqueda e Inspección")
df_filtrado = df.copy()

if col_status:
    estados = ["Todos"] + sorted([x for x in df[col_status].unique() if x not in ["SIN INFORMACIÓN", "Sin información"]])
    status_sel = st.sidebar.selectbox("⚡ Filtrar por Estatus:", estados)
    if status_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_status] == status_sel]

if col_unidad:
    unidades = ["Todas"] + sorted([x for x in df_filtrado[col_unidad].unique() if x not in ["Sin información", "SIN INFORMACIÓN"]])
    unidad_sel = st.sidebar.selectbox("🏢 Unidad de Proceso:", unidades)
    if unidad_sel != "Todas":
        df_filtrado = df_filtrado[df_filtrado[col_unidad] == unidad_sel]

if col_equipo:
    equipos = ["Todos"] + sorted([x for x in df_filtrado[col_equipo].unique() if x not in ["Sin información", "SIN INFORMACIÓN"]])
    equipo_sel = st.sidebar.selectbox("🔥 Seleccionar Equipo / Tag:", equipos)
    if equipo_sel != "Todos":
        df_filtrado = df_filtrado[df_filtrado[col_equipo] == equipo_sel]

st.sidebar.markdown("---")
for logo in ["logojn.png", "logojn.npg", "logo.png"]:
    if os.path.exists(logo):
        st.sidebar.image(logo, use_container_width=True)
        break

# -----------------------------------------------------------------------------
# VISTA PRINCIPAL
# -----------------------------------------------------------------------------
st.markdown(f"**Registros encontrados:** `{len(df_filtrado)}` de `{len(df)}` totales.")

pestana_tabla, pestana_stats = st.tabs(["📊 Vista General de Equipos", "📈 Panel General y Estadísticas"])

registro_seleccionado = None

with pestana_tabla:
    st.caption("💡 Haz clic en cualquier fila para abrir inmediatamente la Ficha Técnica del Intercambiador.")
    
    evento_tabla = st.dataframe(
        df_filtrado, 
        use_container_width=True, 
        selection_mode="single-row", 
        on_select="rerun"
    )

    if evento_tabla and "selection" in evento_tabla and "rows" in evento_tabla["selection"]:
        filas_seleccionadas = evento_tabla["selection"]["rows"]
        if len(filas_seleccionadas) > 0:
            indice_fila = filas_seleccionadas[0]
            registro_seleccionado = df_filtrado.iloc[indice_fila]

with pestana_stats:
    st.subheader("📊 Análisis Gráfico de Intercambiadores")
    
    if len(df_filtrado) == 0:
        st.warning("No hay datos disponibles para graficar con los filtros aplicados.")
    else:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("##### 📉 Estado de Inspección (STATUS)")
            if col_status:
                df_status_counts = df_filtrado[col_status].value_counts().reset_index()
                df_status_counts.columns = ['Estatus', 'Cantidad']
                fig_status = px.bar(
                    df_status_counts, 
                    x='Estatus', 
                    y='Cantidad', 
                    color='Estatus', 
                    color_discrete_map=MAPA_COLORES_ESTATUS, 
                    text='Cantidad'
                )
                fig_status.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total Equipos")
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No se encontró la columna de Status para graficar.")
                
        with col_g2:
            st.markdown("##### 🏢 Equipos por Unidad de Proceso")
            if col_unidad:
                df_unidad_counts = df_filtrado[col_unidad].value_counts().reset_index()
                df_unidad_counts.columns = ['Unidad', 'Cantidad']
                fig_unidad = px.bar(df_unidad_counts, x='Unidad', y='Cantidad', text='Cantidad')
                fig_unidad.update_layout(showlegend=False, xaxis_title="", yaxis_title="Total Equipos")
                st.plotly_chart(fig_unidad, use_container_width=True)
            else:
                st.info("No se encontró la columna de Unidad de Proceso para graficar.")

# -----------------------------------------------------------------------------
# DETALLE / FICHA TÉCNICA DEL INTERCAMBIADOR
# -----------------------------------------------------------------------------
if (registro_seleccionado is not None) or (len(df_filtrado) == 1):
    registro = registro_seleccionado if registro_seleccionado is not None else df_filtrado.iloc[0]
    
    st.markdown("---")
    
    col_detalles, col_enlaces = st.columns([2, 1])

    with col_detalles:
        val_equipo = registro[col_equipo] if col_equipo else "Detalle"
        val_unidad = registro[col_unidad] if col_unidad else "Sin unidad"
        val_equipo_clean = str(val_equipo).strip()
        
        st.subheader(f"📋 Ficha Técnica - Equipo {val_equipo}")
        
        # 1. FICHA TÉCNICA FILTRADA (Únicamente Unidad de Proceso, Equipo y Comentario)
        datos_ficha_reducida = {}
        for k, v in registro.items():
            k_upper = str(k).upper()
            if 'UNIDAD' in k_upper and 'Unidad de Proceso' not in datos_ficha_reducida:
                datos_ficha_reducida['Unidad de Proceso'] = v
            elif 'EQUIPO' in k_upper and 'Equipo' not in datos_ficha_reducida:
                datos_ficha_reducida['Equipo'] = v
            elif 'COMENTARIO' in k_upper and 'Comentario' not in datos_ficha_reducida:
                datos_ficha_reducida['Comentario'] = v
        
        df_ficha = pd.DataFrame(list(datos_ficha_reducida.items()), columns=['Parámetro', 'Detalle'])
        st.table(df_ficha.style.hide(axis='index'))

        # Cargar archivo JSON de configuración del equipo si existe
        archivo_json = f"config_{val_equipo_clean}.json"
        config_equipo = None
        if os.path.exists(archivo_json):
            try:
                with open(archivo_json, "r", encoding="utf-8") as f:
                    config_equipo = json.load(f)
            except Exception:
                config_equipo = None

        st.markdown("### 📐 Plano Esquemático de Boquillas")
        if config_equipo and generate_modular_exchanger_svg:
            # Dibujo visual SVG
            svg_code = generate_modular_exchanger_svg(config_equipo)
            components.html(
                f'<div style="background:#ffffff; border:1px solid #cbd5e1; border-radius:8px; padding:10px; width:100%; height:100%; box-sizing:border-box; display:flex; justify-content:center; align-items:center;">{svg_code}</div>', 
                height=480
            )
            
            # 2. TABLA NOZZLE SCHEDULE DEBAJO DEL ESQUEMA
            st.markdown(f"#### 📋 NOZZLE SCHEDULE - {val_equipo_clean}")
            
            table_rows = []
            global_aux_rating = config_equipo.get("equipment", {}).get("aux_rating", "6000#")

            for noz in config_equipo.get("nozzles", []):
                auxs = noz.get("auxiliaries", [])
                aux_parts = [f"{aux.get('size', '')} {aux.get('position', '')}" for aux in auxs]
                aux_combined = "  ".join(aux_parts) if aux_parts else ""

                size_desc = str(noz.get("size", "")).strip()
                rating_desc = str(noz.get("rating", "")).strip()
                type_desc = str(noz.get("type", "")).strip()
                
                rating_type = f"{rating_desc} {type_desc}".strip()
                if size_desc and rating_type:
                    desc_full = f"{size_desc} - {rating_type}"
                else:
                    desc_full = size_desc or rating_type

                table_rows.append({
                    "MK": noz.get("tag", ""),
                    "QT": 1,
                    "DESCRIPTION": desc_full,
                    "PROCESS": noz.get("service", "INLET"),
                    "AUXILIARIES": aux_combined
                })

            table_rows.append({
                "MK": "", "QT": "", "DESCRIPTION": "", "PROCESS": "", "AUXILIARIES": f"{global_aux_rating} CPLGS."
            })

            df_nozzles = pd.DataFrame(table_rows)
            st.table(df_nozzles.style.hide(axis='index'))

            col_plan1, col_plan2 = st.columns([3, 1])
            with col_plan1:
                st.success(f"✅ Plano esquemático y tabla de boquillas cargados para **{val_equipo_clean}**.")
            with col_plan2:
                if st.button("✏️ Editar Plano Esquemático"):
                    st.session_state["tag_para_diseño"] = val_equipo_clean
                    ir_a_diseno()
        else:
            st.info(f"ℹ️ El equipo **{val_equipo_clean}** aún no tiene un plano esquemático guardado.")
            if st.button(f"🛠️ Diseñar Plano Esquemático para {val_equipo_clean}", type="primary"):
                st.session_state["tag_para_diseño"] = val_equipo_clean
                ir_a_diseno()

    with col_enlaces:
        color_principal = "#005ce6"
        valor_status = "SIN INFORMACIÓN"
        if col_status and registro[col_status] not in ['Sin información', 'SIN INFORMACIÓN']:
            valor_status = registro[col_status].strip().upper()
            color_principal = MAPA_COLORES_ESTATUS.get(valor_status, "#005ce6")
            
        st.markdown(f"""
        <div style="background: transparent; padding: 12px; border-radius: 8px; text-align: center; border: 2px solid {color_principal}; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 12px; color: #666; font-weight: bold; text-transform: uppercase;">Estatus del Equipo</p>
            <h3 style="margin: 4px 0 0 0; font-size: 22px; color: {color_principal}; line-height: 1.1;">{valor_status}</h3>
        </div>
        """, unsafe_allow_html=True)
            
        st.subheader("📁 Accesos Rápidos y Evidencia")
        
        termino_busqueda = val_equipo if val_equipo not in ["Sin información", "SIN INFORMACIÓN"] else val_unidad
            
        if termino_busqueda and termino_busqueda not in ["Sin información", "SIN INFORMACIÓN"]:
            url_gdrive = generar_link_gdrive(termino_busqueda)
            st.link_button(
                label=f"📂 Buscar Planos/Docs de '{termino_busqueda}' en Drive", 
                url=url_gdrive, 
                use_container_width=True
            )
            st.write("") 

        titulo_doc = f"Intercambiador {val_equipo} ({val_unidad})"
        pdf_bytes = generar_pdf_equipo(val_equipo, val_unidad, valor_status, datos_ficha_reducida, color_principal, titulo_doc, config_equipo=config_equipo)
        
        st.download_button(
            label="📄 Descargar Ficha PDF para Terreno",
            data=pdf_bytes,
            file_name=f"Ficha_Intercambiador_{val_equipo}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.write("")

        st.markdown("🖼️ **Evidencia / Fotografía de Inspección**")
        foto_subida = st.file_uploader("Sube o arrastra la imagen del equipo:", type=["png", "jpg", "jpeg"], key="visor_foto")
        
        if foto_subida is not None:
            st.image(foto_subida, caption=f"Evidencia - Equipo {val_equipo}", use_container_width=True)

        if col_geo and registro[col_geo] not in ['Sin información', 'SIN INFORMACIÓN']:
            lat, lon = extraer_coordenadas(registro[col_geo])
            if lat and lon:
                st.markdown("---")
                url_maps = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
                st.link_button(
                    label="🗺️ Abrir Ubicación en Google Maps", 
                    url=url_maps, 
                    use_container_width=True
                )
                mapa_html = f"""
                <iframe 
                    width="100%" 
                    height="300" 
                    frameborder="0" 
                    scrolling="no" 
                    marginheight="0" 
                    marginwidth="0" 
                    src="https://maps.google.com/maps?q={lat},{lon}&hl=es&z=16&output=embed"
                    style="border-radius: 8px; border: 1px solid #ddd; margin-top: 10px;">
                </iframe>
                """
                st.markdown(mapa_html, unsafe_allow_html=True)
