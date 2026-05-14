import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS (Persistencia Total) ---
# Esto asegura que la patente que anota el transportista quede grabada para siempre
conn = st.connection("gsheets", type=GSheetsConnection)

def obtener_datos(tabla):
    return conn.read(worksheet=tabla)

def guardar_dato(tabla, nuevo_df):
    df_existente = obtener_datos(tabla)
    df_final = pd.concat([df_existente, nuevo_df], ignore_index=True)
    conn.update(worksheet=tabla, data=df_final)

# --- ESTILO ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #1f4e79; color: white; height: 3em; }
    .main { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    rol = st.selectbox("Perfil de Acceso", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    st.divider()
    st.write("**Estado:** Conectado a Base de Datos")

# --- LÓGICA DE PANTALLAS ---

if rol == "Inicio":
    st.header("Bienvenido a LOGÍSTICA GLOBAL")
    st.image("https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1200&q=80")
    st.info("Plataforma de gestión de transporte. Los datos registrados aquí son permanentes.")

elif rol == "Conductor":
    st.header("📲 Reporte de Conductor")
    pat_ingreso = st.text_input("Ingrese la Patente").strip().upper()
    
    if pat_ingreso:
        # Buscamos en la hoja de Google directamente
        df_flota = obtener_datos("Flota")
        match = df_flota[df_flota['patente'] == pat_ingreso]
        
        if not match.empty:
            nombre_c = match.iloc[0]['conductor']
            st.success(f"✅ Bienvenido, {nombre_c}")
            archivo = st.file_uploader("Subir foto de Guía", type=['jpg', 'png', 'jpeg'])
            if st.button("ENVIAR REPORTE FINAL"):
                if archivo:
                    nueva_guia = pd.DataFrame({
                        "fecha": [datetime.now().strftime("%d/%m/%Y %H:%M")],
                        "patente": [pat_ingreso],
                        "conductor": [nombre_c]
                    })
                    guardar_dato("Guias", nueva_guia)
                    st.balloons()
                    st.success("Información enviada con éxito.")
                else: st.warning("Por favor, suba la foto de la guía.")
        else:
            st.error("❌ Patente NO registrada en el sistema. Avise a su transportista.")

elif rol == "Transportista":
    st.header("🏢 Panel Administrativo")
    t1, t2 = st.tabs(["Inscribir Camión", "Ver Reportes"])
    
    with t1:
        with st.form("registro_flota"):
            p = st.text_input("Patente del Equipo").strip().upper()
            n = st.text_input("Nombre del Conductor").strip()
            if st.form_submit_button("REGISTRAR"):
                if p and n:
                    nuevo_registro = pd.DataFrame({"patente": [p], "conductor": [n]})
                    guardar_dato("Flota", nuevo_registro)
                    st.success(f"Guardado: {n} en {p}")
                else: st.error("Complete ambos campos.")

    with t2:
        st.write("### Historial de Guías")
        df_guias = obtener_datos("Guias")
        st.dataframe(df_guias)

elif rol == "Dueño App":
    st.header("🔑 Control Maestro")
    pin = st.text_input("PIN Maestro", type="password")
    if pin == "998877":
        st.write("### Auditoría Total")
        st.write("**Empresas y Flota:**")
        st.dataframe(obtener_datos("Flota"))
        st.write("**Todos los Viajes:**")
        st.dataframe(obtener_datos("Guias"))
