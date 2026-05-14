import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN PROFESIONAL ---
st.set_page_config(page_title="LOGÍSTICA GLOBAL", layout="wide")

# --- ESTILO PARA EVITAR PANTALLA NEGRA VACÍA ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f5f5;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A BASE DE DATOS (Persistencia Garantizada) ---
conn = sqlite3.connect('logistica_global_v2.db', check_same_thread=False)
c = conn.cursor()

# Creación de tablas (si no existen)
c.execute('CREATE TABLE IF NOT EXISTS transportistas (id INTEGER PRIMARY KEY, nombre TEXT, pin TEXT, email TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS flota (id INTEGER PRIMARY KEY, id_transp INTEGER, patente TEXT, conductor TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS guias (id INTEGER PRIMARY KEY, id_transp INTEGER, patente TEXT, conductor TEXT, fecha TEXT, foto_path TEXT)')
conn.commit()

# --- LÓGICA DE ACCESO ---
PIN_MAESTRO_DUENO = "9999" # Cambia esto a tu PIN secreto

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.title("🚛 LOGÍSTICA GLOBAL")
    st.subheader("Panel de Navegación")
    rol = st.selectbox("Seleccione su Perfil", ["Inicio", "Dueño de la App", "Transportista", "Conductor"])
    st.divider()
    st.info("Plataforma de Control de Transporte Terrestre")

# --- CONTENIDO PRINCIPAL ---

if rol == "Inicio":
    # Esto elimina la pantalla negra al entrar
    st.header("Bienvenido a la Plataforma LOGÍSTICA GLOBAL")
    st.markdown("""
    ### Sistema Centralizado de Gestión de Flotas
    Por favor, seleccione su tipo de acceso en el menú de la izquierda para comenzar a operar:
    *   **Transportistas:** Gestione su flota, conductores y descargue reportes.
    *   **Conductores:** Suba sus guías de despacho al finalizar sus viajes.
    """)
    # Imagen de transporte real (Camión profesional)
    st.image("https://images.unsplash.com/photo-1519003722824-194d4455a60c?ixlib=rb-1.2.1&auto=format&fit=crop&w=1350&q=80", caption="Gestión de transporte eficiente")

elif rol == "Dueño de la App":
    st.header("🔑 Acceso Maestro")
    pin_admin = st.text_input("Ingrese su PIN Único", type="password")
    if pin_admin == PIN_MAESTRO_DUENO:
        st.success("Acceso total a la base de datos concedido.")
        # Aquí puedes ver TODO sin filtros
        todas_las_guias = pd.read_sql("SELECT * FROM guias", conn)
        st.write("### Historial Global de Viajes")
        st.dataframe(todas_las_guias)
    elif pin_admin:
        st.error("PIN incorrecto. Acceso denegado.")

elif rol == "Transportista":
    st.header("🏢 Panel de Administración de Transporte")
    
    # Sistema de PIN para el Transportista
    with st.expander("Identificación de Transportista", expanded=True):
        email_t = st.text_input("Correo electrónico")
        pin_t = st.text_input("PIN de Empresa", type="password")
        
        # Simulación de login (En producción usarías validación contra la tabla 'transportistas')
        if st.button("Ingresar al Sistema"):
            st.session_state['login_ok'] = True
            st.success("Sesión iniciada.")

    if st.session_state.get('login_ok'):
        tab1, tab2, tab3 = st.tabs(["Registrar Flota", "Monitoreo de Guías", "Descarga Excel"])
        
        with tab1:
            st.subheader("Alta de Equipos y Conductores")
            col1, col2 = st.columns(2)
            with col1:
                n_patente = st.text_input("Patente del Camión").upper()
            with col2:
                n_conductor = st.text_input("Nombre Completo del Conductor")
            
            if st.button("Guardar en mi Flota"):
                if n_patente and n_conductor:
                    c.execute("INSERT INTO flota (id_transp, patente, conductor) VALUES (1, ?, ?)", (n_patente, n_conductor))
                    conn.commit()
                    st.success(f"Registrado: {n_conductor} asignado a {n_patente}")
        
        with tab2:
            st.subheader("Guías Recibidas")
            guias_df = pd.read_sql("SELECT patente, conductor, fecha FROM guias", conn)
            st.table(guias_df)

        with tab3:
            st.subheader("Exportar Datos")
            if st.button("Generar reporte para Excel"):
                csv = guias_df.to_csv(index=False).encode('utf-8')
                st.download_button("Descargar Archivo .CSV", csv, "reporte_logistica.csv", "text/csv")

elif rol == "Conductor":
    st.header("🚚 Registro de Finalización de Viaje")
    patente_c = st.text_input("Ingrese la Patente del Camión").upper()
    
    if patente_c:
        # Buscamos quién es el conductor según la patente ingresada
        c.execute("SELECT conductor FROM flota WHERE patente=?", (patente_c,))
        res = c.fetchone()
        
        if res:
            nombre_chofer = res[0]
            st.info(f"Conductor identificado: **{nombre_chofer}**")
            foto = st.file_uploader("Subir foto de la Guía de Despacho", type=['jpg', 'png', 'jpeg'])
            
            if st.button("Enviar Guía"):
                if foto:
                    fecha_ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                    c.execute("INSERT INTO guias (id_transp, patente, conductor, fecha) VALUES (1, ?, ?, ?)", 
                              (patente_c, nombre_chofer, fecha_ahora))
                    conn.commit()
                    st.success("Guía enviada con éxito. Puede cerrar la aplicación.")
                else:
                    st.warning("Debe subir la foto para finalizar.")
        else:
            st.error("Esta patente no está registrada por su transportista.")
