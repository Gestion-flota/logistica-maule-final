import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE IMPACTO ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- ESTILO LIMPIO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #007bff; color: white; }
    .main { background-color: #f8f9fa; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS PERSISTENTE (Simulación con Cache para Pruebas Rápidas) ---
# NOTA: Para que sea 100% permanente, conectaremos tu Google Sheet en el siguiente paso.
if 'db_flota' not in st.session_state:
    st.session_state['db_flota'] = pd.DataFrame(columns=["patente", "conductor"])
if 'db_guias' not in st.session_state:
    st.session_state['db_guias'] = pd.DataFrame(columns=["fecha", "patente", "conductor"])

# --- NAVEGACIÓN LATERAL ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    rol = st.selectbox("Acceso de Usuario", ["Inicio", "Transportista", "Conductor", "Dueño de la App"])
    st.divider()
    st.write("v2.0 - Sistema Profesional")

# --- LÓGICA DE PANTALLAS ---

if rol == "Inicio":
    st.header("Bienvenido a la Plataforma LOGÍSTICA GLOBAL")
    st.write("Gestión centralizada de transporte terrestre. Seleccione su perfil en el menú izquierdo.")
    st.image("https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1200&q=80")

elif rol == "Transportista":
    st.header("🏢 Panel de Administración")
    tab1, tab2 = st.tabs(["Registrar Equipo", "Reporte de Guías"])
    
    with tab1:
        with st.form("alta_equipo"):
            pat = st.text_input("Patente del Camión").strip().upper()
            nom = st.text_input("Nombre del Conductor").strip()
            if st.form_submit_button("GUARDAR EN SISTEMA"):
                if pat and nom:
                    nueva_fila = pd.DataFrame({"patente": [pat], "conductor": [nom]})
                    st.session_state['db_flota'] = pd.concat([st.session_state['db_flota'], nueva_fila]).drop_duplicates('patente')
                    st.success(f"Registrado: {nom} ({pat})")
                else: st.error("Complete todos los campos")

    with tab2:
        st.write("### Guías Recibidas")
        st.dataframe(st.session_state['db_guias'])
        csv = st.session_state['db_guias'].to_csv(index=False).encode('utf-8')
        st.download_button("DESCARGAR EXCEL", csv, "reporte_logistica.csv", "text/csv")

elif rol == "Conductor":
    st.header("🚚 Finalizar Viaje")
    p_ingreso = st.text_input("Ingrese Patente del Camión").strip().upper()
    
    if p_ingreso:
        # Búsqueda en la base de datos
        match = st.session_state['db_flota'][st.session_state['db_flota']['patente'] == p_ingreso]
        
        if not match.empty:
            nombre_c = match.iloc[0]['conductor']
            st.success(f"✅ Conductor: {nombre_c}")
            archivo = st.file_uploader("Subir foto de la Guía", type=['jpg', 'png', 'jpeg'])
            if st.button("ENVIAR GUÍA AHORA"):
                if archivo:
                    nueva_guia = pd.DataFrame({
                        "fecha": [datetime.now().strftime("%d/%m/%Y %H:%M")],
                        "patente": [p_ingreso],
                        "conductor": [nombre_c]
                    })
                    st.session_state['db_guias'] = pd.concat([st.session_state['db_guias'], nueva_guia])
                    st.balloons()
                    st.success("Información enviada con éxito.")
                else: st.warning("Suba la foto antes de enviar.")
        else:
            st.error("Patente no registrada. Contacte a su transportista.")

elif rol == "Dueño de la App":
    st.header("🔑 Acceso Maestro")
    pin = st.text_input("PIN Único", type="password")
    if pin == "9999":
        st.write("### Base de Datos Global")
        st.write("Flota Registrada:", st.session_state['db_flota'])
        st.write("Guías Enviadas:", st.session_state['db_guias'])
