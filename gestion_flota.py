import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from io import BytesIO

# --- CONFIGURACIÓN DE APARIENCIA ---
st.set_page_config(page_title="SISTEMA DE LOGÍSTICA PRO", layout="wide")

# --- ESTILO CSS PROFESIONAL ---
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #003366; color: white; font-weight: bold; }
    .stTextInput>div>div>input { border-radius: 5px; }
    h1, h2, h3 { color: #003366; font-family: 'Arial'; }
    </style>
    """, unsafe_allow_html=True)

# --- BASE DE DATOS (ESTRUCTURA BLINDADA) ---
def init_db():
    conn = sqlite3.connect('sistema_logistica_v7.db', check_same_thread=False)
    c = conn.cursor()
    # Tabla Empresas/Transportistas
    c.execute('CREATE TABLE IF NOT EXISTS empresas (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, email TEXT UNIQUE, pin TEXT)')
    # Tabla Flota (Patente es la llave)
    c.execute('CREATE TABLE IF NOT EXISTS flota (patente TEXT PRIMARY KEY, conductor TEXT, empresa_id INTEGER)')
    # Tabla Guías (Con GPS y Fecha)
    c.execute('CREATE TABLE IF NOT EXISTS guias (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, patente TEXT, conductor TEXT, lat TEXT, lon TEXT, guia_ref TEXT, empresa_id INTEGER)')
    # Tabla Admin
    c.execute('CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY, email TEXT, pin TEXT)')
    # Insertar admin por defecto si no existe
    c.execute('INSERT OR IGNORE INTO admin (id, email, pin) VALUES (1, "admin@logistica.com", "998877")')
    conn.commit()
    return conn

conn = init_db()
c = conn.cursor()

# --- MANEJO DE SESIÓN ---
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'user_type' not in st.session_state: st.session_state['user_type'] = None

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1519003722824-194d4455a60c?q=80&w=500&auto=format&fit=crop", caption="Logística Integrada")
    st.title("MENÚ PRINCIPAL")
    opcion = st.radio("Seleccione Perfil:", ["Inicio", "Conductor", "Transportista", "Dueño de App"])
    
    if st.session_state['user_id']:
        if st.button("Cerrar Sesión Segura"):
            st.session_state['user_id'] = None
            st.session_state['user_type'] = None
            st.rerun()

# --- VISTA: INICIO ---
if opcion == "Inicio":
    st.title("Bienvenido al Centro de Gestión Logística")
    st.markdown("---")
    st.write("### Optimización y Control de Flotas en Tiempo Real")
    st.image("https://images.unsplash.com/photo-1501700493788-fa1a4fc9fe62?q=80&w=1200&auto=format&fit=crop", use_container_width=True)
    st.info("Plataforma diseñada para el monitoreo de equipos, gestión de documentos y reportes operativos.")

# --- VISTA: CONDUCTOR (SIN BLOQUEOS) ---
elif opcion == "Conductor":
    st.header("📲 Acceso Conductor")
    pat = st.text_input("Ingrese la Patente del Vehículo (Ej: ABCD-12)").strip().upper()
    
    if pat:
        c.execute("SELECT conductor, empresa_id FROM flota WHERE patente = ?", (pat,))
        res = c.fetchone()
        if res:
            conductor_nombre, emp_id = res
            st.success(f"✅ ¡Bienvenido, {conductor_nombre}! Su turno ha iniciado.")
            st.write("---")
            st.subheader("Subir Guía de Trabajo")
            archivo = st.file_uploader("Adjuntar foto o PDF de la Guía", type=['png', 'jpg', 'pdf'])
            
            if st.button("FINALIZAR TRABAJO Y ENVIAR"):
                # Simulación de captura GPS (Se guarda la ubicación actual)
                lat, lon = "-33.4489", "-70.6693" 
                fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
                guia_name = archivo.name if archivo else "Sin archivo"
                
                c.execute("INSERT INTO guias (fecha, patente, conductor, lat, lon, guia_ref, empresa_id) VALUES (?,?,?,?,?,?,?)",
                          (fecha, pat, conductor_nombre, lat, lon, guia_name, emp_id))
                conn.commit()
                st.balloons()
                st.success("Información enviada correctamente. Puede retirarse.")
        else:
            st.error("Patente no reconocida. Por favor, solicite a su transportista que lo registre en el sistema.")

# --- VISTA: TRANSPORTISTA (GESTIÓN + RECUPERACIÓN) ---
elif opcion == "Transportista":
    if not st.session_state['user_id'] or st.session_state['user_type'] != 'empresa':
        st.header("🏢 Acceso Empresa Transportista")
        tab_log, tab_rec = st.tabs(["Ingresar", "Olvidé mi PIN"])
        
        with tab_log:
            email_e = st.text_input("Correo Electrónico")
            pin_e = st.text_input("PIN de Acceso", type="password")
            if st.button("Entrar al Panel"):
                c.execute("SELECT id FROM empresas WHERE email=? AND pin=?", (email_e, pin_e))
                u = c.fetchone()
                if u:
                    st.session_state['user_id'] = u[0]
                    st.session_state['user_type'] = 'empresa'
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas.")
                    if st.button("¿No tiene cuenta? Registrar Empresa"):
                        # Registro rápido
                        c.execute("INSERT INTO empresas (nombre, email, pin) VALUES ('Nueva Empresa', ?, '1234')", (email_e,))
                        conn.commit()
                        st.info("Empresa registrada con PIN temporal 1234. Ingrese y cámbielo.")

        with tab_rec:
            rec_mail = st.text_input("Ingrese su correo registrado")
            if st.button("Recuperar PIN"):
                c.execute("SELECT pin FROM empresas WHERE email=?", (rec_mail,))
                p = c.fetchone()
                if p: st.warning(f"Su PIN es: {p[0]} (En un sistema real, esto se enviaría a su email).")
                else: st.error("Correo no encontrado.")
    else:
        st.header("📊 Panel Administrativo")
        t1, t2 = st.tabs(["🛠 Gestión de Equipos", "📋 Reportes y Monitoreo"])
        
        with t1:
            st.subheader("Registrar Conductor y Patente")
            with st.form("flota"):
                p_new = st.text_input("Patente").upper()
                c_new = st.text_input("Nombre del Conductor")
                if st.form_submit_button("Crear Equipo de Trabajo"):
                    try:
                        c.execute("INSERT INTO flota VALUES (?, ?, ?)", (p_new, c_new, st.session_state['user_id']))
                        conn.commit()
                        st.success("Equipo creado con éxito.")
                    except: st.error("La patente ya existe.")
            
            st.write("### Mi Flota Actual")
            df_f = pd.read_sql(f"SELECT patente as Patente, conductor as Conductor FROM flota WHERE empresa_id={st.session_state['user_id']}", conn)
            st.table(df_f)

        with t2:
            st.subheader("Guías Recibidas y GPS")
            df_g = pd.read_sql(f"SELECT fecha, patente, conductor, lat as Latitud, lon as Longitud, guia_ref as Archivo FROM guias WHERE empresa_id={st.session_state['user_id']}", conn)
            if not df_g.empty:
                st.dataframe(df_g, use_container_width=True)
                
                # EXCEL
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_g.to_excel(writer, index=False, sheet_name='Reporte')
                st.download_button("📥 DESCARGAR GUÍAS A EXCEL", output.getvalue(), "Reporte_Logistica.xlsx")
            else:
                st.info("No hay guías registradas hoy.")

# --- VISTA: DUEÑO DE APP (CONTROL TOTAL) ---
elif opcion == "Dueño de App":
    st.header("🔑 Control Maestro del Dueño")
    tab_a1, tab_a2 = st.tabs(["Ingreso Admin", "Recuperar Admin"])
    
    with tab_a1:
        pin_adm = st.text_input("PIN Maestro", type="password")
        if pin_adm:
            c.execute("SELECT pin FROM admin WHERE id=1")
            if pin_adm == c.fetchone()[0]:
                st.success("Acceso Total Concedido")
                st.write("### Auditoría Global de Transportistas")
                df_admin = pd.read_sql("SELECT nombre, email FROM empresas", conn)
                st.table(df_admin)
                
                st.write("### Movimientos Globales (GPS/Guías)")
                st.dataframe(pd.read_sql("SELECT * FROM guias", conn))
            else: st.error("PIN Maestro Incorrecto.")

    with tab_a2:
        adm_mail = st.text_input("Correo de Administrador")
        if st.button("Enviar Clave"):
            c.execute("SELECT pin FROM admin WHERE email=?", (adm_mail,))
            res_a = c.fetchone()
            if res_a: st.warning(f"El PIN Maestro es: {res_a[0]}")
            else: st.error("Correo de administrador no reconocido.")
