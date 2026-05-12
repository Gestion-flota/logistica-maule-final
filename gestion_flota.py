import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="Sistema Logístico Seguro", layout="centered")

# --- BASE DE DATOS ---
if 'db_flota' not in st.session_state:
    st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state:
    st.session_state.db_guias = []

# --- MENU LATERAL ---
st.sidebar.title("🚚 ACCESO")
perfil = st.sidebar.selectbox("¿Quién ingresa?", ["Seleccione...", "Transportista", "Conductor", "Dueño App"])

# --- VISTA TRANSPORTISTA ---
if perfil == "Transportista":
    st.title("🏢 Panel del Transportista")
    emp = st.text_input("Nombre de su Empresa")
    clv = st.text_input("Contraseña Empresa", type="password")
    
    if st.button("Ingresar"):
        st.session_state['login_empresa'] = emp
        st.success(f"Sesión iniciada: {emp}")

    if 'login_empresa' in st.session_state and st.session_state['login_empresa'] == emp:
        t1, t2 = st.tabs(["➕ Registrar Equipo", "📋 Ver mis Guías"])
        with t1:
            p = st.text_input("Patente").upper()
            c = st.text_input("Nombre Conductor")
            if st.button("Guardar Equipo"):
                st.session_state.db_flota.append({"empresa": emp, "patente": p, "conductor": c})
                st.success("Registrado en su flota.")
        with t2:
            mis_g = [g for g in st.session_state.db_guias if g['empresa'] == emp]
            if mis_g: st.dataframe(pd.DataFrame(mis_g))

# --- VISTA CONDUCTOR ---
elif perfil == "Conductor":
    st.title("📸 Subir Guía (Chofer)")
    loc = streamlit_js_eval(data_of='get_location', key='get_loc')
    
    nom = st.text_input("Su Nombre")
    pat = st.text_input("Patente").upper()
    archivo = st.file_uploader("Sacar Foto a Guía", type=['jpg', 'png', 'jpeg'])
    
    if st.button("Finalizar Viaje"):
        if nom and pat and archivo and loc:
            lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
            emp_p = next((i['empresa'] for i in st.session_state.db_flota if i['patente'] == pat), "Independiente")
            
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp_p, "conductor": nom, "patente": pat,
                "gps": f"https://www.google.com/maps?q={lat},{lon}"
            })
            st.success("✅ Datos enviados.")
        else:
            st.error("Faltan datos o GPS.")

# --- VISTA DUEÑO APP (CON CLAVE DE ACCESO) ---
elif perfil == "Dueño App":
    st.title("💎 Panel Maestro")
    
    # Bloqueo de seguridad
    password_master = st.text_input("Ingrese Clave de Administrador", type="password")
    
    if password_master == "tu_clave_secreta_aqui": # <--- CAMBIA ESTA CLAVE
        st.success("Acceso Autorizado")
        
        if st.session_state.db_flota:
            df_flota = pd.DataFrame(st.session_state.db_flota)
            
            st.write("### 📊 Resumen de Camiones por Empresa")
            resumen = df_flota['empresa'].value_counts()
            st.table(resumen)
            
            st.write("### 🚛 Detalle Global de la Flota")
            st.dataframe(df_flota)
            
            if st.session_state.db_guias:
                st.write("### 📑 Todas las Guías Subidas")
                st.dataframe(pd.DataFrame(st.session_state.db_guias))
        else:
            st.info("Aún no hay transportistas con equipos registrados.")
    
    elif password_master != "":
        st.error("❌ Clave incorrecta. Acceso denegado.")
