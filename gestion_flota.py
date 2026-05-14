import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA PROFESIONAL ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide", initial_sidebar_state="expanded")

# --- BASE DE DATOS LOCAL (PERSISTENCIA TOTAL) ---
def init_db():
    conn = sqlite3.connect('logistica_global_vFinal.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT UNIQUE, pin TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, patente TEXT UNIQUE, conductor TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS guias (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, patente TEXT, conductor TEXT, fecha TEXT)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- ESTADO DE SESIÓN ---
if 'empresa_id' not in st.session_state:
    st.session_state['empresa_id'] = None

# PIN MAESTRO DUEÑO
PIN_MAESTRO = "998877"

# --- SIDEBAR PROFESIONAL ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    st.markdown("---")
    rol = st.selectbox("Perfil de Acceso", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    st.markdown("---")
    if st.session_state['empresa_id']:
        if st.button("Cerrar Sesión"):
            st.session_state['empresa_id'] = None
            st.rerun()

# --- LÓGICA DE PANTALLAS ---

if rol == "Inicio":
    # --- PANTALLA DE INICIO PROFESIONAL ---
    st.title("Sistema Central de Logística Terrestre")
    st.markdown("---")
    
    # NUEVA IMAGEN PROFESIONAL DE TRANSPORTE GLOBAl
    # Esta imagen ha sido generada para reflejar la logística y el profesionalismo
    st.image("https://r.jina.ai/https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80", 
             caption="Centro Operativo Logística Global - Conectando el Maule con el mundo.")
    
    st.info("Plataforma de gestión de transporte profesional. Use el menú lateral para ingresar.")

elif rol == "Conductor":
    st.header("📲 Acceso Conductor")
    pat = st.text_input("Ingrese la Patente").strip().upper()
    if pat:
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente = ?", (pat,))
        res = c.fetchone()
        if res:
            st.success(f"✅ Bienvenido, {res[0]}")
            foto = st.file_uploader("Subir foto de Guía", type=['jpg','png','jpeg'])
            if st.button("ENVIAR REPORTE DE VIAJE"):
                if foto:
                    fecha_n = datetime.now().strftime("%d/%m/%Y %H:%M")
                    c.execute("INSERT INTO guias (empresa_id, patente, conductor, fecha) VALUES (?,?,?,?)", (res[1], pat, res[0], fecha_n))
                    conn.commit()
                    st.balloons()
                    st.success("Información enviada correctamente.")
        else: st.error("❌ Patente no registrada.")

elif rol == "Transportista":
    if not st.session_state['empresa_id']:
        st.header("🏢 Ingreso Empresa")
        t1, t2 = st.tabs(["Ingresar", "Registrar Empresa"])
        with t1:
            em = st.text_input("Email Corporativo")
            pi = st.text_input("PIN de Acceso", type="password")
            if st.button("Entrar al Panel"):
                c.execute("SELECT id, nombre FROM empresas WHERE email=? AND pin=?", (em, pi))
                u = c.fetchone()
                if u:
                    st.session_state['empresa_id'] = u[0]
                    st.session_state['empresa_nombre'] = u[1]
                    st.rerun()
                else: st.error("Email o PIN incorrectos.")
        with t2:
            n_e = st.text_input("Nombre de Empresa")
            e_e = st.text_input("Email Nuevo")
            p_e = st.text_input("Crear PIN (4-6 números)", type="password")
            if st.button("Crear mi Cuenta"):
                try:
                    c.execute("INSERT INTO empresas (nombre, email, pin) VALUES (?,?,?)", (n_e, e_e, p_e))
                    conn.commit()
                    st.success("Cuenta creada. Ahora puede Ingresar.")
                except: st.error("Email ya registrado.")
    else:
        st.header(f"🏢 Panel: {st.session_state['empresa_nombre']}")
        t_f, t_r = st.tabs(["📋 Gestionar Flota", "📊 Reporte de Guías"])
        with t_f:
            with st.form("reg_flota"):
                p = st.text_input("Patente").strip().upper()
                c_c = st.text_input("Nombre Conductor")
                if st.form_submit_button("GUARDAR EN FLOTA"):
                    if p and c_c:
                        c.execute("INSERT OR REPLACE INTO flota (empresa_id, patente, conductor) VALUES (?,?,?)", (st.session_state['empresa_id'], p, c_c))
                        conn.commit()
                        st.success(f"Registrado: {c_c}")
            st.dataframe(pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={st.session_state['empresa_id']}", conn))
        with t_r:
            st.dataframe(pd.read_sql(f"SELECT fecha, patente, conductor FROM guias WHERE empresa_id={st.session_state['empresa_id']}", conn))

elif rol == "Dueño App":
    if st.text_input("PIN Maestro", type="password") == PIN_MAESTRO:
        st.header("🔑 Control Maestro")
        df_e = pd.read_sql("SELECT * FROM empresas", conn)
        st.write(f"Empresas Totales: {len(df_e)}")
        for i, r in df_e.iterrows():
            with st.expander(f"EMPRESA: {r['nombre']} (ID: {r['id']})"):
                st.write("**Flota Registrada:**")
                st.dataframe(pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={r['id']}", conn))
                st.write("**Viajes Realizados:**")
                st.dataframe(pd.read_sql(f"SELECT fecha, patente, conductor FROM guias WHERE empresa_id={r['id']}", conn))
