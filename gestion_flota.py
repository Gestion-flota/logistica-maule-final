import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from PIL import Image

# --- CONFIGURACIÓN E IMÁGENES ---
st.set_page_config(page_title="SISTEMA LOGÍSTICA GLOBAL", layout="wide")

# Función para simular imágenes de transporte terrestre
# 

# --- BASE DE DATOS (Persistencia Total) ---
conn = sqlite3.connect('logistica_v1.db', check_same_thread=False)
c = conn.cursor()

# Creamos las tablas necesarias
c.execute('''CREATE TABLE IF NOT EXISTS transportistas 
             (id INTEGER PRIMARY KEY, nombre TEXT, pin TEXT, email TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS flota 
             (id INTEGER PRIMARY KEY, id_transp INTEGER, patente TEXT, conductor TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS guias 
             (id INTEGER PRIMARY KEY, id_transp INTEGER, patente TEXT, conductor TEXT, fecha TEXT, foto BLOB)''')
conn.commit()

# --- FUNCIONES DE SEGURIDAD ---
PIN_DUEÑO = "9999" # Tu pin único

def login_transportista(email, pin):
    c.execute("SELECT id, nombre FROM transportistas WHERE email=? AND pin=?", (email, pin))
    return c.fetchone()

# --- INTERFAZ - SIDEBAR (Solución a Pantalla Negra) ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    st.markdown("---")
    rol = st.selectbox("Acceso de Usuario", ["Seleccione...", "Dueño App", "Transportista", "Conductor"])
    st.markdown("---")
    st.image("https://img.freepik.com/vector-gratis/ilustracion-concepto-logistica-transporte_114360-1246.jpg")

# --- LÓGICA POR ROL ---

if rol == "Dueño App":
    st.header("🔑 Panel de Control Maestro")
    pin_check = st.text_input("Ingrese PIN Maestro", type="password")
    if pin_check == PIN_DUEÑO:
        st.success("Acceso Total Concedido")
        tab1, tab2 = st.tabs(["Todos los Viajes", "Gestión de Transportistas"])
        with tab1:
            all_data = pd.read_sql("SELECT * FROM guias", conn)
            st.dataframe(all_data)
        with tab2:
            st.write("Aquí puedes auditar a cada empresa registrada.")
    elif pin_check:
        st.error("PIN Incorrecto")

elif rol == "Transportista":
    st.header("🏢 Panel Administrativo de Transporte")
    menu_t = st.tabs(["Ingresar/Recuperar", "Mi Flota", "Monitoreo y Guías"])
    
    with menu_t[0]:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Entrar")
            mail = st.text_input("Email Corporativo")
            pin_t = st.text_input("PIN de Acceso", type="password")
            if st.button("Iniciar Sesión"):
                user = login_transportista(mail, pin_t)
                if user:
                    st.session_state['user_id'] = user[0]
                    st.success(f"Bienvenido {user[1]}")
                else: st.error("Datos incorrectos")
        with col2:
            st.subheader("¿Olvidó su PIN?")
            st.button("Recuperar por Email")

    with menu_t[1]:
        if 'user_id' in st.session_state:
            st.subheader("Registro de Equipos")
            patente = st.text_input("Patente del Camión")
            chofer = st.text_input("Nombre del Conductor")
            if st.button("Asignar Equipo"):
                c.execute("INSERT INTO flota (id_transp, patente, conductor) VALUES (?,?,?)", 
                          (st.session_state['user_id'], patente.upper(), chofer))
                conn.commit()
                st.info("Camión y Conductor vinculados correctamente.")
        else: st.warning("Inicie sesión para gestionar flota.")

    with menu_t[2]:
        if 'user_id' in st.session_state:
            st.subheader("Descarga de Datos (Excel)")
            # Aquí se filtran solo las guías de ESTE transportista
            data_t = pd.read_sql(f"SELECT * FROM guias WHERE id_transp={st.session_state['user_id']}", conn)
            st.dataframe(data_t)
            # Botón para Excel
            csv = data_t.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar Reporte Excel (CSV)", csv, "reporte_viajes.csv", "text/csv")

elif rol == "Conductor":
    st.header("🚚 Reporte de Conductor")
    pat_cond = st.text_input("Ingrese Patente del Vehículo").upper()
    
    if pat_cond:
        # El conductor pone su patente y el sistema le dice quién es
        c.execute("SELECT conductor, id_transp FROM flota WHERE patente=?", (pat_cond,))
        res = c.fetchone()
        if res:
            st.success(f"Hola **{res[0]}**. Al terminar su viaje, suba la foto de la guía.")
            foto_guia = st.file_uploader("Capturar o Subir Foto de Guía", type=['jpg', 'png', 'pdf'])
            if st.button("Finalizar Viaje y Enviar"):
                if foto_guia:
                    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    c.execute("INSERT INTO guias (id_transp, patente, conductor, fecha) VALUES (?,?,?,?)",
                              (res[1], pat_cond, res[0], fecha_hoy))
                    conn.commit()
                    st.balloons()
                    st.success("Información enviada al transportista.")
        else:
            st.error("Patente no encontrada. El transportista debe registrarlo primero.")
