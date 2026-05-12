import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval # Para el GPS real

st.set_page_config(page_title="Sistema Logístico Real", layout="centered")

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
    if st.button("Ingresar"):
        st.session_state['login_exitoso'] = emp

    if 'login_exitoso' in st.session_state:
        t1, t2 = st.tabs(["➕ Registrar Equipo", "📋 Ver Guías Recibidas"])
        with t1:
            p = st.text_input("Patente").upper()
            c = st.text_input("Nombre Conductor")
            if st.button("Guardar"):
                st.session_state.db_flota.append({"empresa": emp, "patente": p, "conductor": c})
                st.success("Registrado")
        with t2:
            mis_guias = [g for g in st.session_state.db_guias if g['empresa'] == emp]
            if mis_guias: st.dataframe(pd.DataFrame(mis_guias))

# --- VISTA CONDUCTOR (CON GPS REAL) ---
elif perfil == "Conductor":
    st.title("📸 Finalizar Viaje")
    
    # 📍 CAPTURA DE GPS AUTOMÁTICA
    loc = streamlit_js_eval(data_of='get_location', key='get_loc')
    
    nom = st.text_input("Su Nombre")
    pat = st.text_input("Patente").upper()
    
    # El botón 'Upload' abrirá la cámara en celulares
    archivo = st.file_uploader("Presione para sacar foto a la Guía", type=['jpg', 'jpeg', 'png'])
    
    if st.button("ENVIAR Y TERMINAR"):
        if nom and pat and archivo and loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            
            # Buscamos empresa
            emp_p = next((i['empresa'] for i in st.session_state.db_flota if i['patente'] == pat), "Independiente")
            
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp_p,
                "conductor": nom,
                "patente": pat,
                "ubicacion": f"Lat: {lat}, Lon: {lon}",
                "google_maps": f"https://www.google.com/maps?q={lat},{lon}"
            })
            st.success("✅ Guía y GPS enviados correctamente.")
        elif not loc:
            st.error("⚠️ Debe permitir el acceso al GPS en su celular para continuar.")
        else:
            st.error("Complete todos los datos.")

# --- VISTA DUEÑO APP ---
elif perfil == "Dueño App":
    st.title("💎 Vista Global")
    if st.session_state.db_flota:
        st.write("### Resumen de Camiones por Empresa")
        st.table(pd.DataFrame(st.session_state.db_flota)['empresa'].value_counts())
    else:
        st.info("No hay datos.")
