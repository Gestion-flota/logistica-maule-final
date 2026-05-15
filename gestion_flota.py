import streamlit as st
import pandas as pd
import sqlite3
import os
from datetime import datetime
import random

# ==========================================
# 1. CONFIGURACIÓN DE ALMACENAMIENTO SEGURO
# ==========================================
DB_FILE = "sistema_flota.db"
CARPETA_IMAGENES = "guias_guardadas"

if not os.path.exists(CARPETA_IMAGENES):
    os.makedirs(CARPETA_IMAGENES)

st.set_page_config(page_title="Gestión Administrativa de Flota", layout="wide")

# ==========================================
# 2. MOTOR DE BASE DE DATOS (ESTRUCTURA RELACIONAL)
# ==========================================
def inicializar_base_datos():
    """Crea las tablas asegurando que la información quede blindada."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # TABLA 1: Transportistas (Dueños de flotas)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transportistas (
                pin TEXT PRIMARY KEY,
                empresa TEXT NOT NULL
            )
        ''')
        
        # TABLA 2: Conductores (Ligados a la patente y al PIN del transportista dueño)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conductores (
                patente TEXT PRIMARY KEY,
                nombre TEXT NOT NULL,
                transportista_pin TEXT NOT NULL,
                FOREIGN KEY(transportista_pin) REFERENCES transportistas(pin)
            )
        ''')
        
        # TABLA 3: Reportes de Guías y GPS (Historial permanente)
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
        cursor.execute("SELECT nombre, transportista_pin FROM conductores WHERE patente = ?", (patente.upper().strip(),))
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
# 3. INTERFAZ GRÁFICA PROFESIONAL
# ==========================================
st.title("🚚 Sistema Autónomo de Gestión de Flotas y Guías")

rol = st.sidebar.radio("Seleccione el módulo de ingreso:", ["Conductor", "Transportista", "Panel Administrador (Tú)"])

# ------------------------------------------
# MÓDULO 1: CONDUCTOR (ENTRADA RÁPIDA POR PATENTE)
# ------------------------------------------
if rol == "Conductor":
    st.header("📲 Acceso Conductores")
    patente_input = st.text_input("Ingrese la patente del camión para iniciar viaje:", max_chars=7).upper().strip()
    
    if patente_input:
        datos_chofer = obtener_conductor_por_patente(patente_input)
        
        if datos_chofer:
            st.success(f"👋 ¡Hola {datos_chofer['nombre']}! Conductor asignado al camión [{patente_input}].")
            st.subheader("Reporte de Viaje Actual")
            
            foto_guia = st.file_uploader("Capture o cargue la foto de la Guía de Despacho:", type=["jpg", "jpeg", "png"])
            
            if foto_guia is not None:
                # Simulación GPS centrada en zona de operación chilena
                lat_gps = -33.44 + random.uniform(-0.08, 0.08)
                lon_gps = -70.66 + random.uniform(-0.08, 0.08)
                
                if st.button("Finalizar Reporte y Guardar de Forma Segura"):
                    guardar_reporte_viaje(patente_input, datos_chofer['nombre'], lat_gps, lon_gps, foto_guia, datos_chofer['transportista_pin'])
                    st.balloons()
                    st.success("✅ Guía y ubicación respaldadas en la base de datos del transportista.")
        else:
            st.error("❌ Esta patente no se encuentra registrada en ninguna flota activa.")

# ------------------------------------------
# MÓDULO 2: TRANSPORTISTA (EL PROTAGONISTA)
# ------------------------------------------
elif rol == "Transportista":
    st.header("📊 Panel Privado del Transportista")
    
    # Sistema de Doble Opción para Comodidad: Ingresar o Registrarse por única vez
    modo_acceso = st.radio("¿Qué desea hacer?", ["Tengo un PIN creado", "Soy nuevo y quiero crear mi PIN"], horizontal=True)
    
    if modo_acceso == "Soy nuevo y quiero crear mi PIN":
        st.subheader("🔑 Registro Único de Transportista")
        nueva_empresa = st.text_input("Nombre de su Empresa de Transportes:")
        nuevo_pin = st.text_input("Asigne su PIN Secreto (Memorícelo):", type="password")
        
        if st.button("Crear mi cuenta permanente"):
            if nueva_empresa and nuevo_pin:
                if registrar_transportista(nueva_empresa, nuevo_pin):
                    st.success(f"🎉 ¡Empresa '{nueva_empresa}' registrada con éxito! Ahora cambie a la opción 'Tengo un PIN creado' para operar.")
                else:
                    st.error("Este PIN ya está en uso por otro transportista. Use uno diferente.")
            else:
                st.warning("Debe rellenar ambos campos.")
                
    elif modo_acceso == "Tengo un PIN creado":
        pin_ingreso = st.text_input("Ingrese su PIN de Seguridad para ingresar a su flota:", type="password")
        
        if pin_ingreso:
            nombre_empresa = verificar_transportista(pin_ingreso)
            
            if nombre_empresa:
                st.success(f"🔒 Conectado con éxito a: **{nombre_empresa}**")
                
                menu_tab = st.tabs(["🚛 Mi Flota (Crear Camiones)", "📋 Mis Reportes Diarios", "🗺️ Mapa Satelital GPS"])
                
                # Pestaña 1: Creación a escala de sus 20 o 30 camiones
                with menu_tab[0]:
                    st.subheader("➕ Añadir Camión y Conductor a mi Flota")
                    c1, c2 = st.columns(2)
                    with c1:
                        nom_chofer = st.text_input("Nombre del Conductor:")
                    with c2:
                        pat_chofer = st.text_input("Patente del Camión (Ej: ABCD12):", max_chars=7).upper().strip()
                        
                    if st.button("Habilitar en mi Flota"):
                        if nom_chofer and pat_chofer:
                            if registrar_conductor(nom_chofer, pat_chofer, pin_ingreso):
                                st.success(f"Vehículo [{pat_chofer}] agregado a {nombre_empresa}.")
                            else:
                                st.error("Esta patente ya está asignada a un camión del sistema.")
                        else:
                            st.warning("Complete ambos datos.")
                            
                    st.write("---")
                    st.subheader("Mis Camiones Habilitados")
                    df_camiones = obtener_conductores_por_transportista(pin_ingreso)
                    st.dataframe(df_camiones, use_container_width=True, hide_index=True)
                
                # Pestaña 2: Reportes Diarios, Descargas e Inspección de fotos
                with menu_tab[1]:
                    st.subheader("📋 Historial Incorruptible de Guías Recibidas")
                    df_rep = obtener_reportes_por_transportista(pin_ingreso)
                    
                    if not df_rep.empty:
                        st.dataframe(df_rep[["id", "fecha", "patente", "conductor", "lat", "lon", "guia_ref"]], use_container_width=True, hide_index=True)
                        
                        # Descarga Excel directa a la carpeta que el transportista elija en su PC
                        csv_data = df_rep.to_csv(index=False).encode('utf-8-sig')
                        st.download_button(
                            label="📥 Guardar Reporte en Excel (.csv)",
                            data=csv_data,
                            file_name=f"Reporte_{nombre_empresa.replace(' ', '_')}.csv",
                            mime="text/csv"
                        )
                        
                        st.write("---")
                        st.subheader("🔍 Escáner / Visor de Documentos")
                        id_sel = st.selectbox("Seleccione ID del Reporte para abrir la Guía:", df_rep["id"].unique())
                        
                        info_fila = df_rep[df_rep["id"] == id_sel].iloc[0]
                        ruta_foto = os.path.join(CARPETA_IMAGENES, info_fila["guia_ref"])
                        
                        if os.path.exists(ruta_foto):
                            st.image(ruta_foto, caption=f"Guía Escaneada - Camión {info_fila['patente']} ({info_fila['conductor']})", width=550)
                        else:
                            st.error("El archivo de imagen no está disponible en el servidor local.")
                    else:
                        st.info("Su flota aún no registra guías reportadas el día de hoy.")
                        
                # Pestaña 3: Mapa GPS
                with menu_tab[2]:
                    st.subheader("🗺️ Monitoreo de Flota por Coordenadas")
                    df_rep = obtener_reportes_por_transportista(pin_ingreso)
                    if not df_rep.empty:
                        st.map(df_rep[['lat', 'lon']].dropna())
                    else:
                        st.info("Sin ubicaciones registradas el día de hoy.")
            else:
                st.error("❌ PIN no registrado. Si es primera vez, cree un PIN en la opción de arriba.")

# ------------------------------------------
# MÓDULO 3: PANEL ADMINISTRADOR (TÚ COMO DUEÑO)
# ------------------------------------------
elif rol == "Panel Administrador (Tú)":
    st.header("🛠️ Métricas de Administración de la Aplicación")
    st.write("Privacidad activa: No tienes acceso a ver las fotos ni rutas privadas de los clientes, solo la escala del negocio.")
    
    with sqlite3.connect(DB_FILE) as conn:
        tx_totales = conn.execute("SELECT COUNT(*) FROM transportistas").fetchone()[0]
        camiones_totales = conn.execute("SELECT COUNT(*) FROM conductores").fetchone()[0]
        
        # Query para ver cuántos camiones tiene cada transportista
        df_admin = pd.read_sql_query('''
            SELECT t.empresa as 'Empresa Transportista', COUNT(c.patente) as 'Cantidad de Camiones Activos'
            FROM transportistas t
            LEFT JOIN conductores c ON t.pin = c.transportista_pin
            GROUP BY t.pin
        ''', conn)
        
    c1, c2 = st.columns(2)
    c1.metric(label="Clientes Transportistas Usando la App", value=tx_totales)
    c2.metric(label="Total de Camiones Operando a Nivel Global", value=camiones_totales)
    
    st.write("### Desglose de Uso por Cliente")
    st.dataframe(df_admin, use_container_width=True, hide_index=True)
