import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- BASE DE DATOS (MECANISMO DE SEGURIDAD) ---
def init_db():
    conn = sqlite3.connect('logistica_sistema.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla de Empresas/Transportistas
    c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY, nombre TEXT, pin TEXT)')
    # Tabla de Flota
    c.execute('CREATE TABLE IF NOT EXISTS flota (patente TEXT PRIMARY KEY, conductor TEXT, empresa_id INTEGER)')
    # Tabla de Guías
    c.execute('CREATE TABLE IF NOT EXISTS guias (fecha TEXT, patente TEXT, conductor TEXT, empresa_id INTEGER)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ESTADO DE SESIÓN ---
if 'empresa_id' not in st.session_state:
    st.session_state['empresa_id'] = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    opcion = st.selectbox("Perfil de Usuario", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    if st.session_state['empresa_id'] and st.button("Cerrar Sesión"):
        st.session_state['empresa_id'] = None
        st.rerun()

# --- PANTALLAS ---

if opcion == "Inicio":
    st.header("Plataforma de Control Logístico")
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80")
    st.info("Seleccione su perfil para ingresar al sistema.")

elif opcion == "Conductor":
    st.header("📲 Acceso Conductor")
    p_ingreso = st.text_input("Ingrese la Patente del Camión").strip().upper()
    if p_ingreso:
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente = ?", (p_ingreso,))
        res = c.fetchone()
        if res:
            nombre_c, emp_id = res
            st.success(f"✅ Bienvenido, {nombre_c}")
            foto = st.file_uploader("Subir foto de Guía", type=['jpg','png','jpeg'])
            if st.button("ENVIAR REPORTE"):
                if foto:
                    fecha_n = datetime.now().strftime("%d/%m/%Y %H:%M")
                    c.execute("INSERT INTO guias VALUES (?,?,?,?)", (fecha_n, p_ingreso, nombre_c, emp_id))
                    conn.commit()
                    st.balloons()
                    st.success("Información enviada correctamente.")
                else: st.warning("Suba la foto antes de enviar.")
        else: st.error("❌ Patente no encontrada. Su transportista debe registrarlo primero.")

elif opcion == "Transportista":
    if not st.session_state['empresa_id']:
        st.header("🏢 Ingreso Empresa")
        # Para la prueba, si no hay empresas, permitimos crear una rápido
        nombre_e = st.text_input("Nombre de Empresa")
        pin_e = st.text_input("PIN de Acceso", type="password")
        if st.button("Entrar / Registrar"):
            c.execute("SELECT id FROM empresas WHERE nombre = ? AND pin = ?", (nombre_e, pin_e))
            emp = c.fetchone()
            if emp:
                st.session_state['empresa_id'] = emp[0]
                st.rerun()
            else:
                c.execute("INSERT INTO empresas (nombre, pin) VALUES (?,?)", (nombre_e, pin_e))
                conn.commit()
                st.success("Empresa registrada. Pulse entrar nuevamente.")
    else:
        st.header(f"Panel Administrativo")
        t1, t2 = st.tabs(["📋 Registro de Flota", "📊 Reporte de Guías"])
        with t1:
            with st.form("reg_flota"):
                pat = st.text_input("Patente").strip().upper()
                nom = st.text_input("Nombre del Conductor")
                if st.form_submit_button("GUARDAR EN FLOTA"):
                    if pat and nom:
                        c.execute("INSERT OR REPLACE INTO flota VALUES (?,?,?)", (pat, nom, st.session_state['empresa_id']))
                        conn.commit()
                        st.success(f"Registrado: {nom}")
            st.write("### Su Flota Actual")
            st.dataframe(pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={st.session_state['empresa_id']}", conn))
        with t2:
            st.write("### Guías Recibidas")
            st.dataframe(pd.read_sql(f"SELECT fecha, patente, conductor FROM guias WHERE empresa_id={st.session_state['empresa_id']}", conn))

elif opcion == "Dueño App":
    st.header("🔑 Control Maestro")
    if st.text_input("PIN Maestro", type="password") == "998877":
        st.write("### Auditoría Global")
        st.write("Empresas:")
        st.dataframe(pd.read_sql("SELECT * FROM empresas", conn))
        st.write("Flota Global:")
        st.dataframe(pd.read_sql("SELECT * FROM flota", conn))
        st.write("Viajes Totales:")
        st.dataframe(pd.read_sql("SELECT * FROM guias", conn))
