import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- PERSISTENCIA DE DATOS (ARCHIVO LOCAL) ---
DB_FILE = "datos_logistica.json"

def cargar_datos():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"usuarios": {}, "flota": [], "guias": []}

def guardar_datos(datos):
    with open(DB_FILE, "w") as f:
        json.dump(datos, f)

# Inicializar datos en la sesión
if 'data' not in st.session_state:
    st.session_state.data = cargar_datos()

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Sistema Logístico Global", layout="wide")

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 LOGÍSTICA GLOBAL")
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador"])

# --- VISTA: TRANSPORTISTA ---
if perfil == "Transportista":
    st.title("🏢 Panel de Empresa")
    
    empresa_id = st.text_input("Nombre de su Empresa").strip().lower()
    
    if empresa_id:
        # Registro si no existe
        if empresa_id not in st.session_state.data["usuarios"]:
            st.warning(f"La empresa '{empresa_id}' no está registrada.")
            with st.form("registro_form"):
                nueva_clave = st.text_input("Defina su Contraseña", type="password")
                nuevo_correo = st.text_input("Correo electrónico de contacto")
                if st.form_submit_button("Finalizar Registro"):
                    st.session_state.data["usuarios"][empresa_id] = {"clave": nueva_clave, "correo": nuevo_correo}
                    guardar_datos(st.session_state.data)
                    st.success("Empresa registrada. Ahora ingrese su clave abajo.")
                    st.rerun()
        else:
            # Login directo
            if f"auth_{empresa_id}" not in st.session_state:
                clave_login = st.text_input("Ingrese su Contraseña", type="password")
                if st.button("Entrar"):
                    if clave_login == st.session_state.data["usuarios"][empresa_id]["clave"]:
                        st.session_state[f"auth_{empresa_id}"] = True
                        st.rerun()
                    else:
                        st.error("Contraseña incorrecta")
            
            # Panel ya autenticado
            if st.session_state.get(f"auth_{empresa_id}", False):
                st.success(f"Sesión activa: {empresa_id.upper()}")
                tab1, tab2 = st.tabs(["🚛 Gestión de Flota", "📊 Ver Excel"])
                
                with tab1:
                    st.subheader("Registrar Camión")
                    pat = st.text_input("Patente (Ej: ABCD12)").upper()
                    if st.button("Añadir a mi Flota"):
                        if pat:
                            st.session_state.data["flota"].append({"empresa": empresa_id, "patente": pat})
                            guardar_datos(st.session_state.data)
                            st.success(f"Patente {pat} guardada correctamente.")
                
                with tab2:
                    mis_guias = [g for g in st.session_state.data["guias"] if g['empresa'] == empresa_id]
                    if mis_guias:
                        df = pd.DataFrame(mis_guias)
                        st.dataframe(df)
                    else:
                        st.info("No hay guías registradas aún.")
                
                if st.button("Cerrar Sesión"):
                    del st.session_state[f"auth_{empresa_id}"]
                    st.rerun()

# --- VISTA: CONDUCTOR ---
elif perfil == "Conductor":
    st.title("🚛 Enviar Guía")
    patente_ingresada = st.text_input("Ingrese Patente del Camión").upper()
    
    if patente_ingresada:
        # Buscar a qué empresa pertenece la patente en la base de datos guardada
        registro = next((f for f in st.session_state.data["flota"] if f["patente"] == patente_ingresada), None)
        
        if registro:
            st.info(f"Camión detectado de la empresa: {registro['empresa'].upper()}")
            foto = st.file_uploader("Capturar Foto de la Guía", type=["jpg", "png", "jpeg"])
            
            if st.button("Subir Guía Ahora"):
                if foto:
                    nueva_guia = {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "empresa": registro["empresa"],
                        "patente": patente_ingresada
                    }
                    st.session_state.data["guias"].append(nueva_guia)
                    guardar_datos(st.session_state.data)
                    st.success("✅ Guía enviada con éxito. Puede cerrar la página.")
                else:
                    st.error("Por favor, suba la foto antes de enviar.")
        else:
            st.error("⚠️ Esta patente no está registrada por ninguna empresa. Contacte a su jefe.")

# --- VISTA: ADMINISTRADOR (MAESTRO) ---
elif perfil == "Administrador":
    st.title("🛡️ Panel Maestro")
    clave_m = st.text_input("Clave Maestra", type="password")
    
    if clave_m == "linares2026": # Cambia esto a tu gusto
        tab_a, tab_b = st.tabs(["Empresas", "Estadísticas"])
        with tab_a:
            st.json(st.session_state.data["usuarios"])
        with tab_b:
            df_flota = pd.DataFrame(st.session_state.data["flota"])
            if not df_flota.empty:
                st.write(df_flota['empresa'].value_counts())
