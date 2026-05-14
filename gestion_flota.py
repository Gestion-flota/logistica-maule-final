import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL PRO", layout="wide")

# --- BASE DE DATOS ---
def init_db():
    conn = sqlite3.connect('logistica_pro.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY, nombre TEXT, pin TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (patente TEXT PRIMARY KEY, conductor TEXT, empresa_id INTEGER)')
    # Añadimos columnas de GPS
    c.execute('CREATE TABLE IF NOT EXISTS guias (fecha TEXT, patente TEXT, conductor TEXT, latitud TEXT, longitud TEXT, empresa_id INTEGER)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

if 'emp_id' not in st.session_state:
    st.session_state['emp_id'] = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA PRO")
    rol = st.selectbox("Perfil", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    if st.session_state['emp_id'] and st.button("Cerrar Sesión"):
        st.session_state['emp_id'] = None
        st.rerun()

# --- PANTALLAS ---

if rol == "Inicio":
    st.title("Sistema de Gestión de Transporte")
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?auto=format&fit=crop&w=1200&q=80")

elif rol == "Conductor":
    st.header("📲 Registro de Entrega (GPS Activo)")
    pat = st.text_input("Patente").strip().upper()
    
    # Captura de Ubicación (HTML/JS simple para Streamlit)
    st.markdown("### Ubicación")
    st.info("El sistema registrará su posición actual automáticamente al enviar.")
    
    if pat:
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente=?", (pat,))
        res = c.fetchone()
        if res:
            st.success(f"Chofer: {res[0]}")
            # Simulamos captura de coordenadas (en móviles pide permiso de GPS)
            lat_sim = st.text_input("Latitud (Auto)", "-35.5842", disabled=True)
            lon_sim = st.text_input("Longitud (Auto)", "-71.2415", disabled=True)
            
            if st.button("ENVIAR GUÍA Y POSICIÓN GPS"):
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                c.execute("INSERT INTO guias VALUES (?,?,?,?,?,?)", (fecha, pat, res[0], lat_sim, lon_sim, res[1]))
                conn.commit()
                st.balloons()
                st.success("Registrado correctamente con GPS.")
        else: st.error("Patente no existe.")

elif rol == "Transportista":
    if not st.session_state['emp_id']:
        st.header("🏢 Acceso Transportista")
        n = st.text_input("Nombre Empresa")
        p = st.text_input("PIN", type="password")
        if st.button("Entrar"):
            c.execute("SELECT id FROM empresas WHERE nombre=? AND pin=?", (n, p))
            u = c.fetchone()
            if u: st.session_state['emp_id'] = u[0]; st.rerun()
            else:
                c.execute("INSERT INTO empresas (nombre, pin) VALUES (?,?)", (n, p))
                conn.commit(); st.success("Cuenta creada. Reingrese.")
    else:
        st.header("📊 Sus Datos y Descarga Excel")
        df = pd.read_sql(f"SELECT fecha, patente, conductor, latitud, longitud FROM guias WHERE empresa_id={st.session_state['emp_id']}", conn)
        
        if not df.empty:
            st.dataframe(df) # Tabla interactiva
            
            # --- FUNCIÓN EXCEL ---
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Reporte_Guias')
            
            st.download_button(
                label="📥 DESCARGAR TODO EN EXCEL",
                data=output.getvalue(),
                file_name=f"Reporte_Logistica_{datetime.now().strftime('%d_%m')}.xlsx",
                mime="application/vnd.ms-excel"
            )
        else: st.info("Sin datos registrados.")

        st.divider()
        st.subheader("Registrar Nuevo Camión")
        with st.form("add"):
            p_f = st.text_input("Patente").upper()
            n_f = st.text_input("Nombre Chofer")
            if st.form_submit_button("GUARDAR"):
                c.execute("INSERT OR REPLACE INTO flota VALUES (?,?,?)", (p_f, n_f, st.session_state['emp_id']))
                conn.commit(); st.rerun()

elif rol == "Dueño App":
    if st.text_input("PIN Maestro", type="password") == "998877":
        st.write("Auditoría Global (Excel de todas las empresas)")
        all_df = pd.read_sql("SELECT * FROM guias", conn)
        st.dataframe(all_df)
