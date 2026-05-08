import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from io import BytesIO

# 1. Base de Datos Integral
conn = sqlite3.connect('logistica_nacional_v6.db', check_same_thread=False)
cursor = conn.cursor()
# Tabla de Viajes
cursor.execute('''CREATE TABLE IF NOT EXISTS reportes 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, empresa_id TEXT, fecha TEXT, 
                   conductor TEXT, patente TEXT, detalle TEXT, foto BLOB, gps TEXT)''')
# Tabla de Empresas (Aquí es donde se "crean")
cursor.execute('''CREATE TABLE IF NOT EXISTS empresas 
                  (pin TEXT PRIMARY KEY, nombre TEXT, ciudad TEXT)''')
conn.commit()

st.set_page_config(page_title="Logística Pro Chile", layout="wide")

# --- MENÚ LATERAL PROFESIONAL ---
st.sidebar.title("🎮 Centro de Control")
rol = st.sidebar.radio("Seleccione Perfil:", 
                       ["🚚 Conductor en Ruta", "📊 Administrador de Flota", "🔑 Configuración Master"])

# --- MODULO 3: CONFIGURACIÓN MASTER (Para que tú crees las empresas) ---
if rol == "🔑 Configuración Master":
    st.title("Creación de Nuevos Clientes")
    st.info("Aquí es donde tú registras a las empresas antes de entregarles el servicio.")
    
    with st.form("crear_empresa"):
        nom_emp = st.text_input("Nombre de la Empresa (ej: Transportes Cáceres)")
        pin_emp = st.text_input("Asignar PIN de Acceso (4 o 6 dígitos)")
        ciu_emp = st.text_input("Ciudad Base")
        if st.form_submit_button("✅ REGISTRAR EMPRESA CLIENTE"):
            if nom_emp and pin_emp:
                try:
                    cursor.execute("INSERT INTO empresas VALUES (?, ?, ?)", (pin_emp, nom_emp, ciu_emp))
                    conn.commit()
                    st.success(f"Empresa '{nom_emp}' creada. Ya pueden usar el PIN: {pin_emp}")
                except:
                    st.error("Ese PIN ya está en uso. Elige otro.")

# --- MODULO 1: VISTA DEL CONDUCTOR ---
elif rol == "🚚 Conductor en Ruta":
    st.title("Registro de Movimiento")
    
    with st.form("form_conductor", clear_on_submit=True):
        st.subheader("📝 Datos del Servicio")
        nom_cond = st.text_input("Nombre del Conductor")
        pat_camion = st.text_input("Patente del Camión").upper()
        pin_verif = st.text_input("Código de Empresa", help="Solicite el código a su central")
        
        st.markdown("---")
        st.subheader("📸 Documentación")
        foto_g = st.camera_input("Fotografiar Guía")
        det_carga = st.text_area("Observaciones del Viaje")
        
        if st.form_submit_button("🚀 FINALIZAR Y ENVIAR"):
            # Verificamos si el PIN existe
            cursor.execute("SELECT nombre FROM empresas WHERE pin = ?", (pin_verif,))
            empresa_existe = cursor.fetchone()
            
            if empresa_existe and foto_g:
                ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
                loc_gps = "-35.8406, -71.5932" # GPS simulado activo
                cursor.execute("""INSERT INTO reportes (empresa_id, fecha, conductor, patente, detalle, foto, gps) 
                               VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                               (pin_verif, ahora, nom_cond, pat_camion, det_carga, foto_g.getvalue(), loc_gps))
                conn.commit()
                st.success(f"Enviado a central: {empresa_existe[0]}")
                st.balloons()
            else:
                st.error("PIN de empresa inválido o falta fotografía.")

# --- MODULO 2: VISTA DEL ADMINISTRADOR ---
else:
    st.title("🔒 Acceso Administración")
    pin_ingreso = st.text_input("Ingrese PIN de Empresa", type="password")
    
    if pin_ingreso:
        cursor.execute("SELECT nombre FROM empresas WHERE pin = ?", (pin_ingreso,))
        datos_emp = cursor.fetchone()
        
        if datos_emp:
            st.success(f"🏢 Panel Profesional: {datos_emp[0]}")
            
            t1, t2 = st.tabs(["📊 Reportes y Excel", "📍 Geolocalización"])
            
            with t1:
                query = "SELECT fecha, conductor, patente, detalle, gps FROM reportes WHERE empresa_id = ?"
                df = pd.read_sql_query(query, conn, params=(pin_ingreso,))
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    # Excel
                    out = BytesIO()
                    with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
                        df.to_excel(wr, index=False, sheet_name='Viajes')
                    st.download_button("📥 DESCARGAR REPORTE MENSUAL (EXCEL)", out.getvalue(), f"reporte_{datos_emp[0]}.xlsx")
                else:
                    st.info("Sin registros para esta flota.")
            
            with t2:
                st.subheader("Seguimiento de Rutas")
                st.write("Última ubicación capturada por cada conductor:")
                if not df.empty:
                    st.table(df[['conductor', 'patente', 'gps']])
        else:
            st.error("PIN no reconocido en el sistema nacional.")
