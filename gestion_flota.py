import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Sistema Logístico Maule", layout="centered")

# --- PERSISTENCIA DE DATOS Y SEGURIDAD ---
# Nota: Para permanencia total tras cerrar el navegador, se recomienda conectar SQL.
if 'admin_password' not in st.session_state:
    st.session_state['admin_password'] = "linares2026"  # Clave inicial[span_2](start_span)[span_2](end_span)
if 'security_answer' not in st.session_state:
    st.session_state['security_answer'] = "linares" # Respuesta para recuperar cuenta[span_3](start_span)[span_3](end_span)
if 'db_flota' not in st.session_state:
    st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state:
    st.session_state.db_guias = []

# --- MENU LATERAL ---
st.sidebar.title("🚚 ACCESO AL SISTEMA")
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador (Dueño)"])

# --- VISTA INICIO ---
if perfil == "Inicio":
    st.title("Sistema de Gestión de Carga")
    st.write("Bienvenido. Seleccione su perfil para continuar.")

# --- VISTA TRANSPORTISTA ---
elif perfil == "Transportista":
    st.title("🏢 Panel del Transportista")
    emp = st.text_input("Nombre de la Empresa")
    clv = st.text_input("Clave de Empresa", type="password")
    
    if st.button("Ingresar"):
        st.session_state['sesion_activa'] = emp
        st.success(f"Sesión iniciada: {emp}")

    if st.session_state.get('sesion_activa') == emp:
        t1, t2 = st.tabs(["➕ Registrar Equipo", "📋 Mis Guías"])
        with t1:
            pat = st.text_input("Patente").upper()
            con = st.text_input("Nombre Chofer")
            if st.button("Guardar"):
                st.session_state.db_flota.append({"empresa": emp, "patente": pat, "conductor": con})
                st.success("Camión registrado.")
        with t2:
            mis_g = [g for g in st.session_state.db_guias if g['empresa'] == emp]
            if mis_g: st.dataframe(pd.DataFrame(mis_g))

# --- VISTA CONDUCTOR ---
elif perfil == "Conductor":
    st.title("📸 Reporte de Entrega")
    loc = streamlit_js_eval(data_of='get_location', key='get_loc')
    
    nom = st.text_input("Nombre del Chofer")
    pat_c = st.text_input("Patente del Camión").upper()
    foto = st.file_uploader("Sacar foto a la Guía", type=['jpg', 'png', 'jpeg'])
    
    if st.button("Enviar Guía y GPS"):
        if nom and pat_c and foto and loc:
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            emp_p = next((i['empresa'] for i in st.session_state.db_flota if i['patente'] == pat_c), "Independiente")
            
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp_p, "conductor": nom, "patente": pat_c,
                "gps": f"https://www.google.com/maps?q={lat},{lon}"
            })
            st.balloons()
            st.success("✅ Guía enviada con éxito.")
        else:
            st.error("Error: Asegúrese de subir la foto y permitir el GPS.")

# --- VISTA ADMINISTRADOR (DUEÑO) CON GESTIÓN DE CLAVES ---
elif perfil == "Administrador (Dueño)":
    st.title("💎 Panel Maestro")

    if not st.session_state.get('admin_auth'):
        tab_log, tab_rec = st.tabs(["🔒 Ingresar", "🔑 Recuperar Clave"])
        
        with tab_log:
            p_in = st.text_input("Contraseña Maestra", type="password")
            if st.button("Acceder"):
                if p_in == st.session_state['admin_password']:
                    st.session_state['admin_auth'] = True
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta.")
        
        with tab_rec:
            st.write("Pregunta: ¿Cuál es su ciudad de origen?")
            resp = st.text_input("Respuesta de seguridad")
            if st.button("Ver mi Clave"):
                if resp.lower() == st.session_state['security_answer']:
                    st.info(f"Su clave es: {st.session_state['admin_password']}")
                else:
                    st.error("Respuesta incorrecta.")
    
    else:
        # PANEL YA AUTENTICADO
        m1, m2, m3 = st.tabs(["📊 Reporte Global", "⚙️ Cambiar Clave", "🚪 Salir"])
        
        with m1:
            if st.session_state.db_flota:
                df = pd.DataFrame(st.session_state.db_flota)
                st.write("### Camiones por Transportista")
                st.table(df['empresa'].value_counts())
                st.write("### Listado Total")
                st.dataframe(df)
            else:
                st.info("No hay datos aún.")

        with m2:
            st.subheader("Configurar Nueva Contraseña")
            old_p = st.text_input("Clave Actual", type="password")
            new_p = st.text_input("Nueva Clave", type="password")
            if st.button("Actualizar Ahora"):
                if old_p == st.session_state['admin_password']:
                    st.session_state['admin_password'] = new_p
                    st.success("✅ Clave cambiada exitosamente.")
                else:
                    st.error("La clave actual no coincide.")

        with m3:
            if st.button("Cerrar Sesión Segura"):
                st.session_state['admin_auth'] = False
                st.rerun()
