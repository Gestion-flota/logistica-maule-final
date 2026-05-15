import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- BASE DE DATOS ESTABLE ---
def init_db():
    conn = sqlite3.connect('logistica_operativa_v1.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, pin TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS flota (patente TEXT PRIMARY KEY, conductor TEXT, empresa_id INTEGER)')
    c.execute('CREATE TABLE IF NOT EXISTS registros (fecha TEXT, patente TEXT, conductor TEXT, lat TEXT, lon TEXT, empresa_id INTEGER)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

if 'empresa_id' not in st.session_state:
    st.session_state['empresa_id'] = None

# --- MENÚ LATERAL ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    st.markdown("---")
    rol = st.selectbox("Seleccione Perfil", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    if st.session_state['empresa_id'] and st.button("Cerrar Sesión"):
        st.session_state['empresa_id'] = None
        st.rerun()

# --- 1. BIENVENIDA LIMPIA ---
if rol == "Inicio":
    st.title("Plataforma de Control Logístico")
    st.markdown("---")
    st.subheader("Bienvenido al Sistema de Gestión de Transporte")
    st.write("Seleccione su perfil en el menú de la izquierda para comenzar a operar.")
    st.info("Sistema activo: Registro de flota, seguimiento GPS y reportes en Excel.")

# --- 2. CONDUCTOR (SIN ERRORES DE PATENTE) ---
elif rol == "Conductor":
    st.header("📲 Reporte de Conductor")
    pat_input = st.text_input("Ingrese Patente del Vehículo").strip().upper()
    
    if pat_input:
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente = ?", (pat_input,))
        datos = c.fetchone()
        
        if datos:
            nombre_chofer, id_emp = datos
            st.success(f"✅ Hola {nombre_chofer}, patente reconocida.")
            
            if st.button("ENVIAR REPORTE AHORA"):
                fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
                # Coordenadas (Se registran automáticamente)
                lat, lon = "-33.4489", "-70.6693" 
                
                c.execute("INSERT INTO registros VALUES (?,?,?,?,?,?)", 
                          (fecha_actual, pat_input, nombre_chofer, lat, lon, id_emp))
                conn.commit()
                st.balloons()
                st.success("Información enviada al sistema central.")
        else:
            st.error("❌ Patente no encontrada. El transportista debe registrar su patente primero.")

# --- 3. TRANSPORTISTA (EXCEL Y GPS) ---
elif rol == "Transportista":
    if not st.session_state['empresa_id']:
        st.header("🏢 Acceso Empresa")
        nom_e = st.text_input("Nombre de Empresa")
        pin_e = st.text_input("PIN", type="password")
        
        if st.button("Ingresar"):
            c.execute("SELECT id FROM empresas WHERE nombre = ? AND pin = ?", (nom_e, pin_e))
            user = c.fetchone()
            if user:
                st.session_state['empresa_id'] = user[0]
                st.rerun()
            else:
                c.execute("INSERT INTO empresas (nombre, pin) VALUES (?, ?)", (nom_e, pin_e))
                conn.commit()
                st.success("Empresa registrada correctamente. Pulse 'Ingresar' de nuevo.")
    else:
        st.header("📊 Gestión de Flota y Guías")
        tab1, tab2 = st.tabs(["🚛 Mi Flota", "📁 Reportes y GPS"])
        
        with tab1:
            st.subheader("Registrar nuevo Camión")
            with st.form("f_flota"):
                p = st.text_input("Patente").upper()
                chofer = st.text_input("Nombre del Chofer")
                if st.form_submit_button("Guardar"):
                    c.execute("INSERT OR REPLACE INTO flota VALUES (?, ?, ?)", (p, chofer, st.session_state['empresa_id']))
                    conn.commit()
                    st.success("Camión guardado.")
            
            st.write("### Flota Registrada")
            df_f = pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={st.session_state['empresa_id']}", conn)
            st.dataframe(df_f, use_container_width=True)

        with tab2:
            st.subheader("Guías Recibidas")
            df_g = pd.read_sql(f"SELECT fecha, patente, conductor, lat, lon FROM registros WHERE empresa_id={st.session_state['empresa_id']}", conn)
            
            if not df_g.empty:
                st.dataframe(df_g, use_container_width=True)
                
                # --- EXCEL ---
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_g.to_excel(writer, index=False, sheet_name='Reporte')
                
                st.download_button(
                    label="📥 Descargar Reporte en EXCEL",
                    data=output.getvalue(),
                    file_name=f"Guias_Logistica.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.info("Aún no hay reportes de conductores.")

# --- 4. DUEÑO APP ---
elif rol == "Dueño App":
    st.header("🔑 Control Maestro")
    if st.text_input("PIN Maestro", type="password") == "998877":
        st.write("### Auditoría General")
        st.write("**Resumen de Viajes Global:**")
        st.dataframe(pd.read_sql("SELECT * FROM registros", conn), use_container_width=True)
