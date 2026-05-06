import streamlit as st
import sqlite3
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Gestión de Flota Maule", layout="wide")

# --- BASE DE DATOS BLINDADA (v10) ---
def inicializar_db():
    conn = sqlite3.connect('entrega_final_v10.db', check_same_thread=False)
    cursor = conn.cursor()
    # Tabla de Empresas
    cursor.execute('CREATE TABLE IF NOT EXISTS empresas (id TEXT PRIMARY KEY, nombre TEXT, clave TEXT)')
    # Tabla de Choferes
    cursor.execute('CREATE TABLE IF NOT EXISTS choferes (rut TEXT PRIMARY KEY, nombre TEXT, pin TEXT, id_empresa TEXT)')
    # Tabla de Rutas con FOTO
    cursor.execute('''CREATE TABLE IF NOT EXISTS rutas 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, chofer_rut TEXT, 
                       patente TEXT, guias TEXT, id_empresa TEXT, foto_guia BLOB)''')
    conn.commit()
    return conn, cursor

conn, cursor = inicializar_db()

# --- ESTADO DE SESIÓN ---
if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False
if 'chofer_auth' not in st.session_state: st.session_state.chofer_auth = False

# --- BARRA LATERAL ---
st.sidebar.title("🚛 Menú Principal")
opcion = st.sidebar.radio("Seleccione:", ["Portal Conductor", "Panel Administrador", "Registrar Nueva Empresa"])

# --- 1. REGISTRAR EMPRESA ---
if opcion == "Registrar Nueva Empresa":
    st.header("🏗️ Registro de Empresa Cliente")
    with st.form("registro_emp"):
        n = st.text_input("Nombre de la Empresa")
        i = st.text_input("ID de Acceso (ej: arm1)").lower().strip()
        c = st.text_input("Clave Maestra", type="password")
        if st.form_submit_button("Crear Plataforma"):
            if n and i and c:
                try:
                    cursor.execute("INSERT INTO empresas VALUES (?,?,?)", (i, n, c))
                    conn.commit()
                    st.success(f"✅ Empresa '{n}' creada. ID: {i}")
                except: st.error("❌ El ID ya existe.")
            else: st.warning("Complete todos los campos.")

# --- 2. PANEL ADMINISTRADOR ---
elif opcion == "Panel Administrador":
    if not st.session_state.admin_auth:
        st.header("🔑 Acceso Dueño")
        user_admin = st.text_input("ID Empresa")
        pass_admin = st.text_input("Contraseña", type="password")
        if st.button("Ingresar al Panel"):
            res = cursor.execute("SELECT nombre FROM empresas WHERE id=? AND clave=?", (user_admin, pass_admin)).fetchone()
            if res:
                st.session_state.admin_auth = True
                st.session_state.emp_id = user_admin
                st.rerun()
            else: st.error("❌ Credenciales incorrectas.")
    else:
        st.header(f"📊 Panel de Control: {st.session_state.emp_id.upper()}")
        if st.button("Cerrar Sesión"): st.session_state.admin_auth = False; st.rerun()
        
        tab1, tab2 = st.tabs(["👤 Gestión de Choferes", "📋 Reportes con Foto"])
        
        with tab1:
            st.subheader("Registrar Conductor Nuevo")
            with st.form("add_chofer"):
                c_nom = st.text_input("Nombre Completo")
                c_rut = st.text_input("RUT (sin puntos)")
                c_pin = st.text_input("PIN de 4 dígitos")
                if st.form_submit_button("Dar de Alta"):
                    try:
                        cursor.execute("INSERT INTO choferes VALUES (?,?,?,?)", (c_rut, c_nom, c_pin, st.session_state.emp_id))
                        conn.commit()
                        st.success(f"✅ {c_nom} registrado.")
                    except: st.error("❌ El RUT ya está registrado.")
        
        with tab2:
            st.subheader("Historial de Rutas y Guías")
            reportes = cursor.execute("""SELECT r.fecha, c.nombre, r.patente, r.guias, r.foto_guia 
                                      FROM rutas r JOIN choferes c ON r.chofer_rut = c.rut 
                                      WHERE r.id_empresa=? ORDER BY r.id DESC""", (st.session_state.emp_id,)).fetchall()
            for r in reportes:
                with st.expander(f"📅 {r[0]} | Chofer: {r[1]} | Patente: {r[2]}"):
                    st.write(f"**Guías:** {r[3]}")
                    if r[4]: st.image(r[4], caption="Foto de la Guía")

# --- 3. PORTAL CONDUCTOR (CORRECCIÓN DE CÁMARA) ---
elif opcion == "Portal Conductor":
    if not st.session_state.chofer_auth:
        st.header("🚚 Portal de Conductores")
        c_id_e = st.text_input("ID Empresa")
        c_rut = st.text_input("Tu RUT")
        c_pin = st.text_input("Tu PIN", type="password")
        if st.button("Validar Datos"):
            res = cursor.execute("SELECT nombre FROM choferes WHERE rut=? AND pin=? AND id_empresa=?", (c_rut, c_pin, c_id_e)).fetchone()
            if res:
                st.session_state.chofer_auth = True
                st.session_state.chofer_nom = res[0]
                st.session_state.chofer_rut = c_rut
                st.session_state.chofer_emp = c_id_e
                st.rerun()
            else: st.error("❌ No reconocido. Revisa ID Empresa, RUT o PIN.")
    else:
        st.subheader(f"Bienvenido, {st.session_state.chofer_nom}")
        if st.button("Cambiar Usuario / Salir"): st.session_state.chofer_auth = False; st.rerun()
        
        st.divider()
        st.info("📷 **PASO 1:** Toma la foto de la guía primero.")
        # LA CÁMARA ESTÁ FUERA DEL FORMULARIO PARA EVITAR QUE SE OCULTE
        foto = st.camera_input("Capturar Guía de Despacho")
        
        st.divider()
        st.info("✍️ **PASO 2:** Completa los datos del camión.")
        with st.form("envio_final", clear_on_submit=True):
            pat = st.text_input("Patente del Camión")
            gui = st.text_area("Detalle de las Guías")
            
            if st.form_submit_button("🚀 ENVIAR REPORTE AL DUEÑO"):
                if pat and gui and foto:
                    cursor.execute("INSERT INTO rutas (fecha, chofer_rut, patente, guias, id_empresa, foto_guia) VALUES (?,?,?,?,?,?)",
                                   (datetime.now().strftime("%d/%m/%Y %H:%M"), st.session_state.chofer_rut, pat, gui, st.session_state.chofer_emp, foto.getvalue()))
                    conn.commit()
                    st.balloons()
                    st.success("¡Reporte enviado con éxito!")
                else:
                    st.error("⚠️ Debes tomar la foto Y completar los campos de texto.")