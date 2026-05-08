import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

# 1. Base de Datos con Separación por Empresa
conn = sqlite3.connect('logistica_nacional_segura.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS reportes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id TEXT, fecha TEXT, 
                   chofer TEXT, patente TEXT, detalle TEXT, foto BLOB, ubicacion TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS empresas 
                  (codigo TEXT PRIMARY KEY, nombre TEXT)''')
conn.commit()

st.set_page_config(page_title="Logística Pro Chile", layout="wide")

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 Panel de Control")
rol = st.sidebar.radio("Seleccione su Rol:", ["👨‍✈️ Chofer (En Ruta)", "🏢 Administración (Dueños)"])

# --- VISTA DEL CHOFER ---
if rol == "👨‍✈️ Chofer (En Ruta)":
    st.title("Sistema de Registro para Conductores")
    
    with st.form("form_chofer", clear_on_submit=True):
        st.subheader("📝 Datos del Viaje")
        # Primero los datos, luego la cámara
        nombre_chofer = st.text_input("Nombre Completo del Conductor")
        patente = st.text_input("Patente del Camión").upper()
        codigo_empresa = st.text_input("Código de su Empresa (Entregado por su jefe)")
        
        st.markdown("---")
        st.subheader("📸 Documentación")
        foto = st.camera_input("Fotografiar Guía de Despacho (Cámara Trasera)")
        
        detalle = st.text_area("Notas / Detalles de la Carga")
        
        if st.form_submit_button("🚀 ENVIAR REPORTE"):
            if nombre_chofer and patente and codigo_empresa and foto:
                fecha_ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                # Simulamos GPS (Coordenadas de Linares o ruta)
                gps = "-35.8406, -71.5932" 
                
                cursor.execute("""INSERT INTO reportes (empresa_id, fecha, chofer, patente, detalle, foto, ubicacion) 
                               VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                               (codigo_empresa, fecha_ahora, nombre_chofer, patente, detalle, foto.getvalue(), gps))
                conn.commit()
                st.success(f"✅ Reporte enviado para la empresa {codigo_empresa}")
                st.balloons()
            else:
                st.error("⚠️ Error: Debe completar todos los datos y tomar la foto.")

# --- VISTA DEL DUEÑO (CON CLAVE DE EMPRESA) ---
else:
    st.title("🔒 Acceso a Administración")
    clave_acceso = st.text_input("Ingrese su Código de Empresa para ver reportes", type="password")
    
    if clave_acceso:
        st.success(f"Panel de Control: Empresa {clave_acceso}")
        tab1, tab2 = st.tabs(["📊 Reportes y Excel", "📍 Ubicación GPS"])
        
        with tab1:
            # Solo filtramos los datos de ESA empresa
            query = "SELECT fecha, chofer, patente, detalle, ubicacion FROM reportes WHERE empresa_id = ?"
            df = pd.read_sql_query(query, conn, params=(clave_acceso,))
            
            if not df.empty:
                st.subheader("Historial de Viajes Registrados")
                st.dataframe(df, use_container_width=True)
                
                # Botón de Excel Directo
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Cobranza_Mes')
                
                st.download_button(
                    label="📥 DESCARGAR EXCEL PARA COBRANZA",
                    data=output.getvalue(),
                    file_name=f"reporte_{clave_acceso}_{datetime.now().strftime('%m_%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.info("No hay viajes registrados para este código de empresa.")
        
        with tab2:
            st.subheader("Mapa de Últimos Movimientos")
            if not df.empty:
                st.write("Coordenadas registradas de los últimos servicios:")
                st.table(df[['patente', 'ubicacion']])
                st.info("Aquí se integrará el mapa visual en el siguiente paso.")
