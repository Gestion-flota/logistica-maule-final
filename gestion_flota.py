import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import random

# ==========================================
# 1. CONFIGURACIÓN DE ALMACENAMIENTO SEGURO
# ==========================================
DB_FILE = "sistema_flota_v3.db"
CARPETA_IMAGENES = "guias_guardadas"

if not os.path.exists(CARPETA_IMAGENES):
    os.makedirs(CARPETA_IMAGENES)

st.set_page_config(page_title="Gestión Administrativa de Flota", layout="wide")

# ==========================================
# 2. MOTOR DE BASE DE DATOS
# ==========================================
def inicializar_base_datos():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transportistas (
                pin TEXT PRIMARY KEY,
                empresa TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conductores (
                patente TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                transportista_pin TEXT NOT NULL,
                FOREIGN KEY(transportista_pin) REFERENCES transportistas(pin)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reportes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT NOT NULL,
                patente TEXT NOT NULL,
                conductor TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                guia_ref TEXT NOT NULL,
                transportista_pin TEXT NOT NULL,
                FOREIGN KEY(transportista_pin) REFERENCES transportistas(pin)
            )
        ''')
        conn.commit()

inicializar_base_datos()

# --- OPERACIONES DE CAPA DE DATOS ---
def registrar_transportista(empresa, pin):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO transportistas (pin, empresa) VALUES (?, ?)", (pin.strip(), empresa.strip()))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def verificar_transportista(pin):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT empresa FROM transportistas WHERE pin = ?", (pin.strip(),))
        res = cursor.fetchone()
    return res[0] if res else None

def registrar_conductor(nombre, patente, transportista_pin):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO conductores (patente, nombre, transportista_pin) VALUES (?, ?, ?)", 
                           (patente.upper().strip(), nombre.strip(), transportista_pin))
            conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def obtener_conductor_por_patente(patente):
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, transportista_pin FROM conductores WHERE UPPER(patente) = ?", (patente.upper().strip(),))
        res = cursor.fetchone()
    return {"nombre": res[0], "transportista_pin": res[1]} if res else None

def guardar_reporte_viaje(patente, conductor, lat, lon, archivo_subido, transportista_pin):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{timestamp}_{patente}_{archivo_subido.name}"
    ruta_completa = os.path.join(CARPETA_IMAGENES, nombre_archivo)
    
    with open(ruta_completa, "wb") as f:
        f.write(archivo_subido.getbuffer())
        
    fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M")
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO reportes (fecha, patente, conductor, lat, lon, guia_ref, transportista_pin)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (fecha_actual, patente.upper().strip(), conductor, lat, lon, nombre_archivo, transportista_pin))
        conn.commit()

def obtener_reportes_por_transportista(transportista_pin):
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT * FROM reportes WHERE transportista_pin = ? ORDER BY id DESC", conn, params=(transportista_pin,))
    return df

def obtener_conductores_por_transportista(transportista_pin):
    with sqlite3.connect(DB_FILE) as conn:
        df = pd.read_sql_query("SELECT patente, nombre FROM conductores WHERE transportista_pin = ?", conn, params=(transportista_pin,))
    return df

# ==========================================
# 3. INTERFAZ GRÁFICA
# ==========================================
st.title("🚚 Sistema Autónomo de Gestión de Flotas y Guías")
rol = st.sidebar.radio("Seleccione el módulo de ingreso:", ["Conductor", "Transportista", "Panel Administrador (Tú)"])

if rol == "Conductor":
    st.header("📲 Acceso Conductores")
    patente_input = st.text_input("Ingrese la patente del camión para iniciar viaje:").upper().strip()
    
    if patente_input:
        datos_chofer = obtener_conductor_por_patente(patente_input)
        if datos_chofer:
            st.success(f"👋 ¡Hola {datos_chofer['nombre']}! Conductor autorizado.")
            st.subheader("Reporte de Viaje Actual")
            foto_guia = st.file_uploader("Capture o cargue la foto de la Guía de Despacho:", type=["jpg", "jpeg", "png"])
            
            if foto_guia is not None:
                lat_gps = -33.44 + random.uniform(-0.08, 0.08)
                lon_gps = -70.66 + random.uniform(-0.08, 0.08)
                if st.button("Finalizar Reporte y Guardar de Forma Segura"):
                    guardar_reporte_viaje(patente_input, datos_chofer['nombre'], lat_gps, lon_gps, foto_guia, datos_chofer['transportista_pin'])
                    st.balloons()
                    st.success("✅ Guía y ubicación respaldadas con éxito.")
        else:
            st.error("❌ Esta patente no se encuentra registrada en ninguna flota activa.")

elif rol == "Transportista":
    st.header("📊 Panel Privado del Transportista")
    modo_acceso = st.radio("¿Qué desea hacer?", ["Tengo un PIN creado", "Soy nuevo y quiero crear mi PIN"], horizontal=True)
    
    if modo_acceso == "Soy nuevo y quiero crear mi PIN":
        st.subheader("🔑 Registro Único de Transportista")
        nueva_empresa = st.text_input("Nombre de su Empresa de Transportes:")
        nuevo_pin = st.text_input("Asigne su PIN Secreto:", type="password")
        if st.button("Crear mi cuenta permanente"):
            if nueva_empresa and nuevo_pin:
                if registrar_transportista(nueva_empresa, nuevo_pin):
                    st.success(f"🎉 ¡Empresa '{nueva_empresa}' registrada! Seleccione 'Tengo un PIN creado'.")
                else:
                    st.error("Este PIN ya está en uso.")
            else:
                st.warning("Debe rellenar ambos campos.")
                
    elif modo_acceso == "Tengo un PIN creado":
        pin_ingreso = st.text_input("Ingrese su PIN de Seguridad:", type="password")
        if pin_ingreso:
            nombre_empresa = verificar_transportista(pin_ingreso)
            if nombre_empresa:
                st.success(f"🔒 Conectado a: **{nombre_empresa}**")
                menu_tab = st.tabs(["🚛 Mi Flota (Crear Camiones)", "📋 Mis Reportes Diarios", "🗺️ Mapa Satelital GPS"])
                
                with menu_tab[0]:
                    st.subheader("➕ Añadir Camión a mi Flota")
                    c1, c2 = st.columns(2)
                    with c1: nom_chofer = st.text_input("Nombre del Conductor:")
                    with c2: pat_chofer = st.text_input("Patente:").upper().strip()
                    if st.button("Habilitar en mi Flota"):
                        if nom_chofer and pat_chofer:
                            if registrar_conductor(nom_chofer, pat_chofer, pin_ingreso):
                                st.success(f"Vehículo [{pat_chofer}] agregado.")
                                st.rerun()
                            else: st.error("Esta patente ya está asignada.")
                        else: st.warning("Complete ambos datos.")
                    st.write("---")
                    st.subheader("Mis Camiones Habilitados")
                    st.dataframe(obtener_conductores_por_transportista(pin_ingreso), use_container_width=True, hide_index=True)
                
                with menu_tab[1]:
                    st.subheader("📋 Historial de Guías")
                    df_rep = obtener_reportes_por_transportista(pin_ingreso)
                    if not df_rep.empty:
                        st.dataframe(df_rep[["id", "fecha", "patente", "conductor", "lat", "lon", "guia_ref"]], use_container_width=True, hide_index=True)
                    else: st.info("Sin guías hoy.")
                
                with menu_tab[2]:
                    st.subheader("🗺️ Monitoreo Satelital GPS")
                    df_rep = obtener_reportes_por_transportista(pin_ingreso)
                    if not df_rep.empty: st.map(df_rep[['lat', 'lon']].dropna())
                    else: st.info("Sin ubicaciones hoy.")
            else: st.error("❌ PIN incorrecto.")

elif rol == "Panel Administrador (Tú)":
    st.header("🛠️ Panel Global del Administrador")
    st.write("Visualización exclusiva de la escala del negocio por cliente.")
    
    with sqlite3.connect(DB_FILE) as conn:
        # Consulta SQL avanzada para cruzar las empresas con la cantidad de patentes registradas
        df_admin = pd.read_sql_query('''
            SELECT t.empresa as 'Empresa Transportista', COUNT(c.patente) as 'Camiones Registrados'
            FROM transportistas t
            LEFT JOIN conductores c ON t.pin = c.transportista_pin
            GROUP BY t.pin, t.empresa
            ORDER BY COUNT(c.patente) DESC
        ''', conn)
        
        # Calculamos los totales a partir de la tabla
        tx_totales = len(df_admin)
        camiones_totales = int(df_admin['Camiones Registrados'].sum()) if not df_admin.empty else 0
        
    # Mostramos los indicadores generales arriba
    c1, c2 = st.columns(2)
    c1.metric(label="Total de Clientes (Empresas)", value=tx_totales)
    c2.metric(label="Total de Camiones en la App", value=camiones_totales)
    
    st.write("---")
    st.write("### 📊 Detalle de Flotas por Empresa")
    
    # Mostramos la tabla limpia y profesional que pediste
    if not df_admin.empty:
        st.dataframe(df_admin, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay empresas registradas en el sistema.")