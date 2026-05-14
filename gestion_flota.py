import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- BASE DE DATOS (PERSISTENCIA REAL) ---
def init_db():
    conn = sqlite3.connect('logistica_v4.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla de Empresas (Transportistas)
    c.execute('''CREATE TABLE IF NOT EXISTS empresas 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT UNIQUE, pin TEXT)''')
    # Tabla de Flota (Patente vinculada a Empresa)
    c.execute('''CREATE TABLE IF NOT EXISTS flota 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, patente TEXT UNIQUE, conductor TEXT)''')
    # Tabla de Registros (Viajes y Guías)
    c.execute('''CREATE TABLE IF NOT EXISTS registros 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id INTEGER, patente TEXT, conductor TEXT, fecha TEXT)''')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- MANEJO DE SESIÓN ---
if 'auth_id' not in st.session_state: st.session_state.auth_id = None
if 'auth_tipo' not in st.session_state: st.session_state.auth_tipo = None

# PIN MAESTRO DEL DUEÑO (TÚ)
PIN_MAESTRO = "998877"

# --- SIDEBAR PROFESIONAL ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    st.divider()
    menu = st.selectbox("Seleccione Perfil", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    st.divider()
    if st.session_state.auth_id:
        if st.button("Cerrar Sesión"):
            st.session_state.auth_id = None
            st.rerun()

# --- PANTALLA INICIAL ---
if menu == "Inicio":
    st.header("Bienvenido a LOGÍSTICA GLOBAL")
    st.image("https://images.unsplash.com/photo-1519003722824-194d4455a60c?auto=format&fit=crop&w=1200&q=80")
    st.info("Plataforma centralizada de transporte. Use el menú lateral para ingresar.")

# --- PERFIL CONDUCTOR: SOLO PATENTE ---
elif menu == "Conductor":
    st.header("📲 Acceso de Conductor")
    pat = st.text_input("Ingrese la Patente del Camión").strip().upper()
    if pat:
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente = ?", (pat,))
        res = c.fetchone()
        if res:
            st.success(f"✅ Bienvenido, {res[0]}")
            with st.form("envio_guia"):
                foto = st.file_uploader("Subir foto de la Guía", type=['jpg','png','jpeg'])
                if st.form_submit_button("FINALIZAR VIAJE Y ENVIAR"):
                    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                    c.execute("INSERT INTO registros (empresa_id, patente, conductor, fecha) VALUES (?,?,?,?)", 
                              (res[1], pat, res[0], fecha))
                    conn.commit()
                    st.balloons()
                    st.success("Información enviada con éxito al transportista.")
        else:
            st.error("❌ Patente no registrada. Contacte a su transportista.")

# --- PERFIL TRANSPORTISTA: GESTIÓN Y PIN ---
elif menu == "Transportista":
    if not st.session_state.auth_id:
        t1, t2 = st.tabs(["Ingresar", "Registrar Empresa"])
        with t1:
            em = st.text_input("Email de la Empresa")
            pi = st.text_input("PIN de Acceso", type="password")
            if st.button("Entrar al Panel"):
                c.execute("SELECT id, nombre FROM empresas WHERE email=? AND pin=?", (em, pi))
                u = c.fetchone()
                if u:
                    st.session_state.auth_id = u[0]
                    st.session_state.empresa_nombre = u[1]
                    st.rerun()
                else: st.error("Email o PIN incorrectos.")
        with t2:
            n_e = st.text_input("Nombre de su Empresa")
            e_e = st.text_input("Email Corporativo")
            p_e = st.text_input("Cree un PIN (4-6 números)", type="password")
            if st.button("Crear mi Cuenta"):
                try:
                    c.execute("INSERT INTO empresas (nombre, email, pin) VALUES (?,?,?)", (n_e, e_e, p_e))
                    conn.commit()
                    st.success("Cuenta creada con éxito. Ahora puede Ingresar.")
                except: st.error("Este email ya está en uso.")
    else:
        st.header(f"🏢 Panel: {st.session_state.empresa_nombre}")
        tab_f, tab_r = st.tabs(["📋 Gestionar Flota", "📊 Reporte de Guías"])
        
        with tab_f:
            with st.form("reg_camion"):
                st.subheader("Inscribir nuevo camión")
                p_c = st.text_input("Patente").strip().upper()
                n_c = st.text_input("Nombre del Conductor")
                if st.form_submit_button("REGISTRAR EN SISTEMA"):
                    try:
                        c.execute("INSERT INTO flota (empresa_id, patente, conductor) VALUES (?,?,?)", 
                                  (st.session_state.auth_id, p_c, n_c))
                        conn.commit()
                        st.success("Camión y conductor registrados.")
                    except: st.error("Esa patente ya existe en el sistema.")
            
            st.write("#### Sus Camiones Registrados")
            df_flota = pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={st.session_state.auth_id}", conn)
            st.table(df_flota)

        with tab_r:
            st.subheader("Historial de Guías Recibidas")
            df_reg = pd.read_sql(f"SELECT fecha, patente, conductor FROM registros WHERE empresa_id={st.session_state.auth_id}", conn)
            st.dataframe(df_reg)
            if not df_reg.empty:
                csv = df_reg.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar Reporte Excel", csv, "reporte_logistica.csv", "text/csv")

# --- PERFIL DUEÑO: ACCESO TOTAL ---
elif menu == "Dueño App":
    st.header("🔑 Control Maestro")
    p_m = st.text_input("PIN Secreto del Dueño", type="password")
    if p_m == PIN_MAESTRO:
        st.success("Acceso total concedido.")
        df_e = pd.read_sql("SELECT * FROM empresas", conn)
        st.write(f"Total Empresas: {len(df_e)}")
        for i, r in df_e.iterrows():
            with st.expander(f"EMPRESA: {r['nombre']} (ID: {r['id']})"):
                st.write(f"**Email:** {r['email']} | **PIN:** {r['pin']}")
                st.write("**Camiones Inscritos:**")
                st.dataframe(pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={r['id']}", conn))
                st.write("**Viajes Realizados:**")
                st.dataframe(pd.read_sql(f"SELECT fecha, patente, conductor FROM registros WHERE empresa_id={r['id']}", conn))
    elif p_m: st.error("PIN Maestro incorrecto.")
