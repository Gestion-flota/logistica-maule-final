import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Logística Maule", layout="centered")

# --- INICIALIZACIÓN DE SEGURIDAD ---
if 'admin_password' not in st.session_state:
    st.session_state['admin_password'] = "linares2026"
if 'security_answer' not in st.session_state:
    st.session_state['security_answer'] = "linares"
if 'admin_auth' not in st.session_state:
    st.session_state['admin_auth'] = False

if 'db_flota' not in st.session_state:
    st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state:
    st.session_state.db_guias = []

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 ACCESO")
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])

# --- VISTA: INICIO ---
if perfil == "Inicio":
    st.title("Bienvenido al Sistema Logístico")
    st.write("Seleccione su perfil en el menú de la izquierda.")

# --- VISTA: ADMINISTRADOR (BLOQUEADO) ---
elif perfil == "Administrador de la App":
    st.title("🛡️ Panel Privado del Administrador")

    if not st.session_state['admin_auth']:
        col1, col2 = st.columns([2,1])
        with col1:
            pwd_input = st.text_input("Ingrese Clave Maestra", type="password")
            if st.button("Entrar al Panel"):
                if pwd_input == st.session_state['admin_password']:
                    st.session_state['admin_auth'] = True
                    st.rerun()
                else:
                    st.error("Clave incorrecta.")
        
        with col2:
            with st.expander("¿Olvidó su clave?"):
                resp = st.text_input("Ciudad de origen")
                if st.button("Recuperar"):
                    if resp.lower() == st.session_state['security_answer']:
                        st.info(f"Su clave es: {st.session_state['admin_password']}")
    else:
        # CONTENIDO EXCLUSIVO DEL DUEÑO
        m1, m2, m3 = st.tabs(["📊 Reporte Global", "⚙️ Configuración", "🚪 Salir"])
        
        with m1:
            st.header("Control de Flota y Guías")
            if st.session_state.db_flota:
                st.write("### Unidades Registradas")
                st.dataframe(pd.DataFrame(st.session_state.db_flota))
            if st.session_state.db_guias:
                st.write("### Guías Recibidas")
                st.dataframe(pd.DataFrame(st.session_state.db_guias))
            if not st.session_state.db_flota and not st.session_state.db_guias:
                st.info("No hay datos registrados todavía.")

        with m2:
            st.subheader("Seguridad del Panel")
            nueva_p = st.text_input("Definir Nueva Clave", type="password")
            if st.button("Cambiar Clave Ahora"):
                st.session_state['admin_password'] = nueva_p
                st.success("Clave cambiada con éxito.")

        with m3:
            if st.button("Cerrar Sesión"):
                st.session_state['admin_auth'] = False
                st.rerun()

# --- VISTA: TRANSPORTISTA ---
elif perfil == "Transportista":
    st.title("🏢 Registro de Transportistas")
    empresa = st.text_input("Nombre Empresa")
    if empresa:
        t1, t2 = st.tabs(["Registrar Camión", "Ver mis Guías"])
        with t1:
            pat = st.text_input("Patente").upper()
            chofer = st.text_input("Nombre Chofer")
            if st.button("Guardar en Flota"):
                st.session_state.db_flota.append({"empresa": empresa, "patente": pat, "conductor": chofer})
                st.success(f"Patente {pat} registrada.")
        with t2:
            mis_guias = [g for g in st.session_state.db_guias if g['empresa'] == empresa]
            if mis_guias: st.dataframe(pd.DataFrame(mis_guias))
            else: st.info("No tienes guías subidas aún.")

# --- VISTA: CONDUCTOR ---
elif perfil == "Conductor":
    st.title("🚛 Envío de Guía (Chofer)")
    nombre_c = st.text_input("Su Nombre")
    patente_c = st.text_input("Patente del Camión").upper()
    archivo = st.file_uploader("Subir foto de Guía", type=['jpg', 'jpeg', 'png'])
    
    if st.button("Finalizar y Enviar"):
        if nombre_c and patente_c and archivo:
            # Buscamos a qué empresa pertenece esa patente
            emp_pertenece = next((f['empresa'] for f in st.session_state.db_flota if f['patente'] == patente_c), "Independiente")
            
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp_pertenece,
                "conductor": nombre_c,
                "patente": patente_c
            })
            st.success("✅ Guía enviada correctamente.")
        else:
            st.error("Por favor complete los datos y suba la foto.")
