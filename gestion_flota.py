import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

# 1. Base de Datos Nacional (Guarda Datos, Fotos y Ubicación)
conn = sqlite3.connect('logistica_nacional_v4.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS reportes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   fecha TEXT, patente TEXT, detalle TEXT, 
                   foto BLOB, latitud TEXT, longitud TEXT)''')
conn.commit()

st.set_page_config(page_title="Gestión de Cargas", layout="wide")
st.title("🚚 Sistema de Control de Cargas y Logística")
st.markdown("##### Registro de Movimientos para Transportistas")

# 2. Formulario para el Conductor
with st.form("registro_nacional", clear_on_submit=True):
    st.subheader("📸 Captura de Guía de Despacho")
    st.info("Al presionar el botón de abajo, use la cámara trasera para fotografiar el documento.")
    
    # Cámara integrada
    foto = st.camera_input("Fotografiar Documento")
    
    col1, col2 = st.columns(2)
    with col1:
        patente = st.text_input("Patente del Camión").upper()
    with col2:
        # Coordenadas por defecto (Linares) para evitar errores de permisos GPS
        lat, lon = "-35.8406", "-71.5932" 
    
    detalle = st.text_area("Detalles de la Carga / Observaciones")
    
    boton = st.form_submit_button("🚀 ENVIAR REPORTE AL SISTEMA")
    
    if boton:
        if patente and detalle and foto:
            fecha_ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
            # Procesar foto para guardarla
            img_bytes = foto.getvalue()
            
            cursor.execute("""INSERT INTO reportes (fecha, patente, detalle, foto, latitud, longitud) 
                           VALUES (?, ?, ?, ?, ?, ?)""", 
                           (fecha_ahora, patente, detalle, img_bytes, lat, lon))
            conn.commit()
            st.success(f"✅ ¡Éxito! El reporte de la patente {patente} ha sido guardado.")
            st.balloons()
        else:
            st.error("⚠️ Falta información: Debe tomar la foto, escribir la patente y el detalle.")

# 3. Panel para los Dueños de Empresa (Control de Cobranza)
st.markdown("---")
st.subheader("📊 Historial de Servicios y Descarga de Planilla")

# Consultamos los datos (sin la foto para que la tabla sea rápida)
df = pd.read_sql_query("SELECT fecha as 'Fecha', patente as 'Camión', detalle as 'Detalle Guías' FROM reportes", conn)

if not df.empty:
    st.dataframe(df, use_container_width=True)
    
    # Generador de Excel automático
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Reporte_Cobranza')
    
    st.download_button(
        label="📥 DESCARGAR EXCEL PARA COBRANZA",
        data=output.getvalue(),
        file_name=f"reporte_logistica_{datetime.now().strftime('%d_%m')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.write("Aún no hay registros en el sistema nacional.")
