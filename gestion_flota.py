import streamlit as st
import pandas as pd
from io import BytesIO

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Portal de Gestión de Flota", layout="wide")

# --- SIMULACIÓN DE BASE DE DATOS ---
if 'usuarios' not in st.session_state:
    st.session_state.usuarios = {
        "admin_general": {"clave": "1234", "rol": "super_admin", "empresa": "SaaS Owner"},
        "caceres_admin": {"clave": "5566", "rol": "transportista", "empresa": "Transportes Cáceres"},
        "arm_admin": {"clave": "7788", "rol": "transportista", "empresa": "ARM Logística"}
    }

if 'datos_flota' not in st.session_state:
    st.session_state.datos_flota = pd.DataFrame([
        {"empresa": "Transportes Cáceres", "conductor": "Juan Perez", "patente": "AB-CD-12", "detalle": "Ruta Norte", "gps": "-35.8406, -71.5932"},
        {"empresa": "ARM Logística", "conductor": "Andres Retamal", "patente": "TKHL92", "detalle": "Entrega Local", "gps": "-35.8406, -71.5932"}
    ])

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
    st.session_state.usuario_actual = None

# --- INTERFAZ DE LOGIN ---
def login():
    st.title("🚚 Sistema de Gestión de Flota")
    st.info("Ingresa con tu código de empresa y PIN")
    with st.form("login_form"):
        user = st.text_input("Usuario (Código de acceso)")
        password = st.text_input("PIN", type="password")
        submit = st.form_submit_button("Ingresar al Panel")
        
        if submit:
            if user in st.session_state.usuarios and st.session_state.usuarios[user]["clave"] == password:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = st.session_state.usuarios[user]
                st.rerun()
            else:
                st.error("Código o PIN incorrecto")

# --- PANEL DEL DUEÑO (TU VISTA) ---
def panel_super_admin():
    st.header("📊 Panel de Control Global (Dueño de App)")
    st.write("Resumen de facturación y uso de equipos.")
    
    resumen = st.session_state.datos_flota.groupby('empresa').size().reset_index(name='Cantidad de Equipos')
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Uso por Empresa")
        st.table(resumen)
    with col2:
        st.metric("Total Camiones en Plataforma", len(st.session_state.datos_flota))

# --- PANEL DEL TRANSPORTISTA ---
def panel_transportista(empresa_nombre):
    st.header(f"🏢 Panel Profesional: {empresa_nombre}")
    
    # Filtro de seguridad: solo ve lo suyo
    datos_propios = st.session_state.datos_flota[st.session_state.datos_flota['empresa'] == empresa_nombre]
    
    tab1, tab2, tab3 = st.tabs(["📋 Reportes y Excel", "📍 Geolocalización", "➕ Nuevo Equipo"])
    
    with tab1:
        st.subheader("Datos de la Flota")
        st.dataframe(datos_propios, use_container_width=True)
        
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            datos_propios.to_excel(writer, index=False, sheet_name='Reporte')
        
        st.download_button(
            label="📥 Descargar Reporte Excel",
            data=output.getvalue(),
            file_name=f"reporte_{empresa_nombre}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tab2:
        st.subheader("Mapa de Equipos")
        st.write("Ubicaciones registradas:")
        st.table(datos_propios[['conductor', 'patente', 'gps']])

    with tab3:
        st.subheader("Registrar nuevo equipo/viaje")
        with st.form("nuevo_equipo"):
            c1, c2 = st.columns(2)
            cond = c1.text_input("Nombre Conductor")
            pat = c2.text_input("Patente")
            det = st.text_area("Detalles")
            
            if st.form_submit_button("Guardar"):
                nuevo = {"empresa": empresa_nombre, "conductor": cond, "patente": pat, "detalle": det, "gps": "Cargando..."}
                st.session_state.datos_flota = pd.concat([st.session_state.datos_flota, pd.DataFrame([nuevo])], ignore_index=True)
                st.success("Registrado!")
                st.rerun()

# --- LÓGICA PRINCIPAL ---
if not st.session_state.autenticado:
    login()
else:
    st.sidebar.write(f"Empresa: **{st.session_state.usuario_actual['empresa']}**")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    if st.session_state.usuario_actual["rol"] == "super_admin":
        panel_super_admin()
    else:
        panel_transportista(st.session_state.usuario_actual["empresa"])
