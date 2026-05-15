import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="LOGÍSTICA MAULE PRO", layout="wide")

# --- BASE DE DATOS (SISTEMA DE PERSISTENCIA LOCAL) ---
def init_db():
    conn = sqlite3.connect('logistica_vfinal_pro.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla Empresas
    c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, pin TEXT)')
    # Tabla Flota (Vinculada a Empresa)
    c.execute('CREATE TABLE IF NOT EXISTS flota (patente TEXT PRIMARY KEY, conductor TEXT, empresa_id INTEGER)')
    # Tabla Guías con GPS
    c.execute('CREATE TABLE IF NOT EXISTS registros (fecha TEXT, patente TEXT, conductor TEXT, lat TEXT, lon TEXT, empresa_id INTEGER)')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- LÓGICA DE SESIÓN ---
if 'empresa_id' not in st.session_state:
    st.session_state['empresa_id'] = None

# --- MENÚ LATERAL ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA MAULE")
    st.markdown("---")
    rol = st.selectbox("Perfil de Acceso", ["Inicio", "Conductor", "Transportista", "Dueño App"])
    if st.session_state['empresa_id'] and st.button("Cerrar Sesión"):
        st.session_state['empresa_id'] = None
        st.rerun()

# --- 1. PANTALLA INICIO ---
if rol == "Inicio":
    st.title("Sistema de Gestión de Transporte")
    # Imagen profesional de centro logístico
    st.image("https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2000&auto=format&fit=crop")
    st.info("Plataforma operativa para conductores y empresas de transporte.")

# --- 2. PERFIL CONDUCTOR (ENTRADA POR PATENTE) ---
elif rol == "Conductor":
    st.header("📲 Registro de Llegada")
    pat_input = st.text_input("Ingrese Patente del Camión").strip().upper()
    
    if pat_input:
        # Buscamos si la patente existe en la base de datos creada por el transportista
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente = ?", (pat_input,))
        datos = c.fetchone()
        
        if datos:
            nombre_chofer, id_emp = datos
            st.success(f"✅ Identificado: {nombre_chofer}")
            
            # Captura de coordenadas (Simulado, pero se guarda en base de datos)
            st.warning("📍 El sistema capturará su ubicación GPS al enviar.")
            
            if st.button("CONFIRMAR ENTREGA Y ENVIAR"):
                fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
                # Coordenadas de prueba (Se pueden automatizar con JS en producción)
                lat, lon = "-35.4264", "-71.6554" 
                
                c.execute("INSERT INTO registros VALUES (?,?,?,?,?,?)", 
                          (fecha_actual, pat_input, nombre_chofer, lat, lon, id_emp))
                conn.commit()
                st.balloons()
                st.success("Registro enviado exitosamente al transportista.")
        else:
            st.error("❌ Error: Esta patente no está registrada en el sistema. Contacte a su transportista.")

# --- 3. PERFIL TRANSPORTISTA (GESTIÓN, EXCEL Y GPS) ---
elif rol == "Transportista":
    if not st.session_state['empresa_id']:
        st.header("🏢 Acceso Empresa Transportista")
        # El transportista entra con Nombre y PIN
        nom_e = st.text_input("Nombre de la Empresa")
        pin_e = st.text_input("PIN de Acceso", type="password")
        
        if st.button("Ingresar al Panel"):
            c.execute("SELECT id FROM empresas WHERE nombre = ? AND pin = ?", (nom_e, pin_e))
            user = c.fetchone()
            if user:
                st.session_state['empresa_id'] = user[0]
                st.rerun()
            else:
                # Si no existe, se crea automáticamente para simplificar
                c.execute("INSERT INTO empresas (nombre, pin) VALUES (?, ?)", (nom_e, pin_e))
                conn.commit()
                st.success("Empresa registrada. Pulse 'Ingresar' nuevamente.")
    else:
        st.header("📊 Panel de Control y Monitoreo")
        tab1, tab2 = st.tabs(["🚛 Mi Flota", "📁 Guías y GPS"])
        
        with tab1:
            st.subheader("Registrar nuevo Camión/Chofer")
            with st.form("flota_form"):
                new_pat = st.text_input("Patente").upper()
                new_cond = st.text_input("Nombre del Conductor")
                if st.form_submit_button("Guardar en Sistema"):
                    try:
                        c.execute("INSERT INTO flota VALUES (?, ?, ?)", (new_pat, new_cond, st.session_state['empresa_id']))
                        conn.commit()
                        st.success("Camión registrado. El conductor ya puede marcar asistencia.")
                    except:
                        st.error("Esa patente ya está registrada.")
            
            st.write("---")
            st.write("### Flota Actual")
            df_f = pd.read_sql(f"SELECT patente, conductor FROM flota WHERE empresa_id={st.session_state['empresa_id']}", conn)
            st.table(df_f)

        with tab2:
            st.subheader("Historial de Guías con Coordenadas")
            df_g = pd.read_sql(f"SELECT fecha, patente, conductor, lat as Latitud, lon as Longitud FROM registros WHERE empresa_id={st.session_state['empresa_id']}", conn)
            
            if not df_g.empty:
                st.dataframe(df_g)
                
                # --- EXPORTAR A EXCEL ---
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_g.to_excel(writer, index=False, sheet_name='Reporte')
                
                st.download_button(
                    label="📥 Descargar Guías en EXCEL",
                    data=output.getvalue(),
                    file_name=f"Reporte_Empresa_{st.session_state['empresa_id']}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.info("Aún no hay guías registradas por los conductores.")

# --- 4. PERFIL DUEÑO (PIN MAESTRO) ---
elif rol == "Dueño App":
    st.header("🔑 Panel Maestro")
    pin_m = st.text_input("Ingrese PIN de Dueño", type="password")
    
    if pin_m == "998877":
        st.success("Acceso concedido.")
        st.write("### Resumen Global de la App")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Empresas Registradas:**")
            st.table(pd.read_sql("SELECT nombre FROM empresas", conn))
        with col2:
            st.write("**Total de Viajes Registrados:**")
            st.table(pd.read_sql("SELECT fecha, patente, conductor FROM registros", conn))
    elif pin_m:
        st.error("PIN Incorrecto.")
