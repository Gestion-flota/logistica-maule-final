import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Logística Maule Segura", layout="wide")

# Inicialización de bases de datos en memoria
if 'admin_password' not in st.session_state: st.session_state['admin_password'] = "linares2026"
if 'admin_auth' not in st.session_state: st.session_state['admin_auth'] = False
if 'db_usuarios' not in st.session_state: st.session_state.db_usuarios = {} # {nombre_empresa: {'clave': p, 'correo': c}}
if 'db_flota' not in st.session_state: st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state: st.session_state.db_guias = []

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 SISTEMA LOGÍSTICO")
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])

# --- VISTA: TRANSPORTISTA (CON CLAVE INDIVIDUAL) ---
if perfil == "Transportista":
    st.title("🏢 Acceso Privado para Transportistas")
    empresa_nom = st.text_input("Nombre de la Empresa").strip().lower()
    
    if empresa_nom:
        # Registro si la empresa es nueva
        if empresa_nom not in st.session_state.db_usuarios:
            st.warning(f"La empresa '{empresa_nom}' no está registrada.")
            with st.expander("Registrar mi empresa ahora"):
                nueva_clave = st.text_input("Defina su clave privada", type="password")
                correo = st.text_input("Correo electrónico de recuperación")
                if st.button("Crear Cuenta"):
                    st.session_state.db_usuarios[empresa_nom] = {'clave': nueva_clave, 'correo': correo}
                    st.success("Cuenta creada. Ahora ingrese su clave arriba.")
        
        # Login si la empresa ya existe
        else:
            pass_input = st.text_input("Ingrese su clave privada", type="password")
            if st.button("Entrar al Panel"):
                if pass_input == st.session_state.db_usuarios[empresa_nom]['clave']:
                    st.session_state[f'auth_{empresa_nom}'] = True
                else:
                    st.error("Clave incorrecta.")

            # Opción de recuperación
            with st.expander("¿Olvidó su clave?"):
                st.info(f"Se enviará un código al correo: {st.session_state.db_usuarios[empresa_nom]['correo']}")
                if st.button("Recuperar por Correo"):
                    st.success("Instrucciones enviadas (Simulado)")

        # PANEL UNA VEZ AUTENTICADO
        if st.session_state.get(f'auth_{empresa_nom}', False):
            st.success(f"Bienvenido, {empresa_nom.upper()}")
            t1, t2, t3 = st.tabs(["🚛 Gestión de Flota", "📋 Historial de Guías", "🚪 Salir"])
            
            with t1:
                pat = st.text_input("Nueva Patente").upper()
                chofer = st.text_input("Nombre del Chofer")
                if st.button("Registrar Camión"):
                    st.session_state.db_flota.append({"empresa": empresa_nom, "patente": pat, "conductor": chofer})
                    st.success("Camión registrado.")

            with t2:
                mis_guias = [g for g in st.session_state.db_guias if g['empresa'] == empresa_nom]
                if mis_guias:
                    df = pd.DataFrame(mis_guias)
                    st.dataframe(df.drop(columns=['foto_archivo']))
                    
                    # Excel con xlsxwriter
                    output = io.BytesIO()
                    try:
                        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                            df.drop(columns=['foto_archivo']).to_excel(writer, index=False)
                        st.download_button("📥 Descargar Reporte Excel", output.getvalue(), f"{empresa_nom}.xlsx")
                    except:
                        st.error("Error: Ejecuta 'pip install xlsxwriter' en tu terminal.")

                    st.write("### 📸 Ver Foto de Guía")
                    idx = st.number_input("Número de fila:", 0, len(mis_guias)-1, 0)
                    if st.button("Visualizar"):
                        st.image(mis_guias[idx]['foto_archivo'])
                else:
                    st.info("Aún no tienes guías enviadas por tus conductores.")

            with t3:
                if st.button("Cerrar Sesión Privada"):
                    st.session_state[f'auth_{empresa_nom}'] = False
                    st.rerun()

# --- VISTA: CONDUCTOR (ACCESO LIBRE) ---
elif perfil == "Conductor":
    st.title("🚛 Envío de Guía")
    patente_c = st.text_input("Patente del Camión").upper()
    archivo = st.file_uploader("Subir foto de Guía", type=['jpg', 'jpeg', 'png'])
    
    if st.button("Enviar Guía"):
        if patente_c and archivo:
            # Buscar empresa a la que pertenece la patente
            emp = next((f['empresa'] for f in st.session_state.db_flota if f['patente'] == patente_c), "Independiente")
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp,
                "patente": patente_c,
                "foto_archivo": archivo.read()
            })
            st.success(f"Guía enviada a {emp}. ¡Buen viaje!")

# --- VISTA: ADMINISTRADOR (TU PANEL) ---
elif perfil == "Administrador de la App":
    st.title("🛡️ Panel Maestro")
    if not st.session_state['admin_auth']:
        adm_pass = st.text_input("Clave Maestra", type="password")
        if st.button("Acceder"):
            if adm_pass == st.session_state['admin_password']:
                st.session_state['admin_auth'] = True
                st.rerun()
    else:
        st.write("### Control Total de Usuarios")
        st.write(st.session_state.db_usuarios) # Aquí puedes ver todas las claves si alguien la olvida
        if st.button("Cerrar Sesión"):
            st.session_state['admin_auth'] = False
            st.rerun()
