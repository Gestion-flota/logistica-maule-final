import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- BASE DE DATOS (Manejador de errores integrado) ---
def init_db():
    try:
        conn = sqlite3.connect('logistica_v8_estable.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT UNIQUE, pin TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS flota (patente TEXT PRIMARY KEY, conductor TEXT, empresa_id INTEGER)')
        c.execute('CREATE TABLE IF NOT EXISTS guias (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, patente TEXT, conductor TEXT, lat TEXT, lon TEXT, guia_ref TEXT, empresa_id INTEGER)')
        conn.commit()
        return conn
    except Exception as e:
        st.error(f"Error crítico de base de datos: {e}")
        return None

conn = init_db()

# SESIÓN
if 'emp_id' not in st.session_state: st.session_state['emp_id'] = None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=500&auto=format&fit=crop", caption="Gestión Profesional")
    st.title("LOGÍSTICA GLOBAL")
    rol = st.selectbox("Seleccione su Perfil", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    if st.session_state['emp_id'] and st.button("Cerrar Sesión"):
        st.session_state['emp_id'] = None
        st.rerun()

# --- VISTA INICIO ---
if rol == "Inicio":
    st.title("Sistema Central de Transporte")
    st.markdown("---")
    st.write("### Bienvenido al centro operativo.")
    st.image("https://images.unsplash.com/photo-1519003722824-194d4455a60c?q=80&w=1200&auto=format&fit=crop", use_container_width=True)

# --- VISTA CONDUCTOR ---
elif rol == "Conductor":
    st.header("📲 Reporte de Entrega")
    pat = st.text_input("Ingrese Patente").strip().upper()
    if pat:
        c = conn.cursor()
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente=?", (pat,))
        res = c.fetchone()
        if res:
            st.success(f"Conductor: {res[0]}")
            arc = st.file_uploader("Subir Guía (Imagen/PDF)")
            if st.button("ENVIAR AHORA"):
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                lat, lon = "-33.44", "-70.66" # GPS
                nom_arc = arc.name if arc else "Sin documento"
                c.execute("INSERT INTO guias (fecha, patente, conductor, lat, lon, guia_ref, empresa_id) VALUES (?,?,?,?,?,?,?)",
                          (fecha, pat, res[0], lat, lon, nom_arc, res[1]))
                conn.commit()
                st.balloons()
                st.success("Información enviada.")
        else: st.warning("Patente no registrada por el transportista.")

# --- VISTA TRANSPORTISTA (Donde estaba el error) ---
elif rol == "Transportista":
    if not st.session_state['emp_id']:
        st.header("🏢 Acceso Empresa")
        tab_log, tab_reg = st.tabs(["Ingresar", "Registrar Empresa Nueva"])
        
        with tab_log:
            e_mail = st.text_input("Email")
            e_pin = st.text_input("PIN", type="password")
            if st.button("Entrar"):
                c = conn.cursor()
                c.execute("SELECT id FROM empresas WHERE email=? AND pin=?", (e_mail, e_pin))
                u = c.fetchone()
                if u: 
                    st.session_state['emp_id'] = u[0]
                    st.rerun()
                else: st.error("Email o PIN incorrecto.")

        with tab_reg:
            st.subheader("Formulario de Registro")
            r_nom = st.text_input("Nombre de Empresa")
            r_mail = st.text_input("Email de Registro")
            r_pin = st.text_input("Crear PIN", type="password")
            if st.button("Crear Perfil"):
                if r_nom and r_mail and r_pin:
                    try:
                        c = conn.cursor()
                        c.execute("INSERT INTO empresas (nombre, email, pin) VALUES (?,?,?)", (r_nom, r_mail, r_pin))
                        conn.commit()
                        st.success("Perfil creado exitosamente. Ahora puede ingresar en la pestaña 'Ingresar'.")
                    except sqlite3.IntegrityError:
                        st.error("Error: Este correo ya está registrado.")
                    except Exception as e:
                        st.error(f"Error inesperado: {e}")
                else:
                    st.warning("Por favor complete todos los campos.")
    else:
        st.header("📊 Gestión Administrativa")
        t1, t2 = st.tabs(["🚛 Mi Flota", "📁 Reportes Excel"])
        with t1:
            with st.form("f"):
                p_f = st.text_input("Patente").upper()
                c_f = st.text_input("Nombre Chofer")
                if st.form_submit_button("Guardar"):
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO flota VALUES (?,?,?)", (p_f, c_f, st.session_state['emp_id']))
                    conn.commit(); st.success("Registrado.")
            st.table(pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={st.session_state['emp_id']}", conn))
        
        with t2:
            df = pd.read_sql(f"SELECT fecha, patente, conductor, lat, lon, guia_ref FROM guias WHERE empresa_id={st.session_state['emp_id']}", conn)
            if not df.empty:
                st.dataframe(df)
                out = BytesIO()
                with pd.ExcelWriter(out, engine='xlsxwriter') as wr: df.to_excel(wr, index=False)
                st.download_button("📥 DESCARGAR EXCEL", out.getvalue(), "Reporte.xlsx")

# --- VISTA DUEÑO ---
elif rol == "Dueño App":
    if st.text_input("PIN Maestro", type="password") == "998877":
        st.write("### Control Maestro")
        st.dataframe(pd.read_sql("SELECT * FROM guias", conn))
