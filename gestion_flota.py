import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Logístico Maule", layout="centered")

# Inicialización de claves y datos (Persistencia en sesión)
if 'admin_password' not in st.session_state:
    st.session_state['admin_password'] = "linares2026[span_2](start_span)"[span_2](end_span)
if 'security_answer' not in st.session_state:
    st.session_state['security_answer'] = "linares[span_3](start_span)"[span_3](end_span)
if 'admin_auth' not in st.session_state:
    st.session_state['admin_auth'] = False[span_4](start_span)[span_4](end_span)

if 'db_flota' not in st.session_state:
    st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state:
    st.session_state.db_guias = []

# --- MENU LATERAL ---
st.sidebar.title("🚚 ACCESO")
# Cambiado a "Administrador de la App" como pediste
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])[span_5](start_span)[span_5](end_span)

# --- VISTA ADMINISTRADOR DE LA APP (EL BLOQUEO TOTAL) ---
if perfil == "Administrador de la App":
    st.title("🛡️ Acceso Restringido: Administrador")

    # Si NO está autenticado, solo mostramos el cuadro de contraseña
    if not st.session_state['admin_auth']:
        col1, col2 = st.columns([2,1])
        with col1:
            pwd_input = st.text_input("Ingrese su Clave Maestra para ver el Panel", type="password")[span_6](start_span)[span_6](end_span)
            if st.button("Validar Acceso"):
                if pwd_input == st.session_state['admin_password']:
                    st.session_state['admin_auth'] = True
                    st.rerun()[span_7](start_span)[span_7](end_span)
                else:
                    st.error("Clave incorrecta. Acceso denegado.")[span_8](start_span)[span_8](end_span)
        
        with col2:
            st.write("---")
            # Opción de recuperación oculta en un expander para que no estorbe
            with st.expander("¿Olvidó su clave?"):
                resp = st.text_input("Ciudad de origen")[span_9](start_span)[span_9](end_span)
                if st.button("Revelar Clave"):
                    if resp.lower() == st.session_state['security_answer']:
                        st.info(f"Su clave es: {st.session_state['admin_password']}")[span_10](start_span)[span_10](end_span)
    
    # SI YA ESTÁ AUTENTICADO, recién mostramos el Panel Maestro
    else:
        st.success("Sesión de Administrador Activa")
        m1, m2, m3 = st.tabs(["📊 Reporte Global", "⚙️ Configuración de Seguridad", "🚪 Cerrar Sesión"])[span_11](start_span)[span_11](end_span)
        
        with m1:
            st.header("Resumen de Camiones y Guías")
            if st.session_state.db_flota:
                st.dataframe(pd.DataFrame(st.session_state.db_flota))[span_12](start_span)[span_12](end_span)
            else:
                st.info("No hay registros de transporte aún.")

        with m2:
            st.subheader("Cambiar Clave de Administrador")
            st.warning("Solo tú puedes cambiar esta clave. Una vez cambiada, la anterior dejará de funcionar.")[span_13](start_span)[span_13](end_span)
            old_p = st.text_input("Clave Actual", type="password")[span_14](start_span)[span_14](end_span)
            new_p = st.text_input("Nueva Clave", type="password")[span_15](start_span)[span_15](end_span)
            if st.button("Guardar Nueva Clave"):
                if old_p == st.session_state['admin_password']:
                    st.session_state['admin_password'] = new_p[span_16](start_span)[span_16](end_span)
                    st.success("Clave actualizada correctamente.")
                else:
                    st.error("La clave actual no es correcta.")

        with m3:
            if st.button("Finalizar Sesión"):
                st.session_state['admin_auth'] = False[span_17](start_span)[span_17](end_span)
                st.rerun()

# --- VISTAS PÚBLICAS (NO CAMBIAN) ---
elif perfil == "Transportista":
    st.title("🏢 Sección Transportistas")
    st.info("Aquí los transportistas solo ven sus propios datos.")
    # (Aquí va tu código de registro de flota que ya teníamos)

elif perfil == "Conductor":
    st.title("🚛 Sección Conductores")
    st.info("Aquí los conductores solo suben sus guías y GPS.")
    # (Aquí va tu código de subida de guías que ya teníamos)
