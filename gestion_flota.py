import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

# 1. Base de Datos Centralizada
conn = sqlite3.connect('logistica_integral_v5.db', check_same_thread=False)
cursor = conn.cursor()
# Tabla para los reportes de viajes
cursor.execute('''CREATE TABLE IF NOT EXISTS reportes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, patente TEXT, detalle TEXT, foto BLOB)''')
# Tabla para los equipos de la empresa
cursor.execute('''CREATE TABLE IF NOT EXISTS equipos 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, patente TEXT, modelo TEXT, dueño TEXT)''')
conn.commit()

st.set_page_config(page_title="Logística Pro", layout="wide")

# --- MENÚ LATERAL (Aquí es donde entran los dueños) ---
st.sidebar.title("🎮 Panel de Control")
opcion = st.sidebar.radio("Ir a:", ["🚛 Registro de Chofer", "🏢 Administración (Dueños)"])

# --- MODULO 1: VISTA DEL CHOFER ---
if opcion == "🚛 Registro de Chofer":
    st.title("🚚 Sistema de Control de Cargas")
    st.markdown("##### Registro de Movimientos para Conductores")
    
    with st.form("registro_nacional", clear_on_submit=True):
        foto = st.camera_input("📸 Fotografiar Guía de Despacho")
        patente = st.text_input("Patente del Camión").upper()
        detalle = st.text_area("Detalles de la Carga / Observaciones")
        
        if st.form_submit_button("🚀 ENVIAR REPORTE"):
            if patente and detalle and foto:
                fecha_ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                cursor.execute("INSERT INTO reportes (fecha, patente, detalle, foto) VALUES (?, ?, ?, ?)", 
                               (fecha_ahora, patente, detalle, foto.getvalue()))
                conn.commit()
                st.success("Reporte enviado correctamente.")
            else:
                st.error("Complete todos los campos y la foto.")

# --- MODULO 2: VISTA DEL DUEÑO (ADMINISTRACIÓN) ---
else:
    st.title("🏢 Panel de Administración")
    
    tab1, tab2 = st.tabs(["📋 Ver Reportes de Viajes", "🚜 Gestionar Equipos"])
    
    with tab1:
        st.subheader("Historial de Guías y Cobranzas")
        df_viajes = pd.read_sql_query("SELECT fecha as 'Fecha', patente as 'Camión', detalle as 'Detalle' FROM reportes", conn)
        if not df_viajes.empty:
            st.dataframe(df_viajes, use_container_width=True)
            # Botón Excel aquí
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_viajes.to_excel(writer, index=False)
            st.download_button("📥 Descargar Excel de Cobranza", output.getvalue(), "reporte.xlsx")
        else:
            st.info("No hay viajes registrados aún.")

    with tab2:
        st.subheader("Registrar Nuevo Equipo / Camión")
        with st.form("registro_equipos"):
            nueva_patente = st.text_input("Patente del Equipo").upper()
            modelo = st.text_input("Modelo (ej: Mercedes GLE 250)")
            dueño_equipo = st.text_input("Nombre del Propietario / Empresa")
            
            if st.form_submit_button("💾 Guardar Equipo"):
                if nueva_patente and dueño_equipo:
                    cursor.execute("INSERT INTO equipos (patente, modelo, dueño) VALUES (?, ?, ?)", 
                                   (nueva_patente, modelo, dueño_equipo))
                    conn.commit()
                    st.success(f"Equipo {nueva_patente} registrado con éxito.")
                
        # Mostrar lista de equipos registrados
        st.markdown("---")
        st.write("### Equipos en Flota")
        df_equipos = pd.read_sql_query("SELECT patente as 'Patente', modelo as 'Modelo', dueño as 'Dueño' FROM equipos", conn)
        st.table(df_equipos)
