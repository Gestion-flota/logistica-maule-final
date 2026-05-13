import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Logística Maule v3", layout="wide")

# Bases de datos temporales
if 'db_usuarios' not in st.session_state: st.session_state.db_usuarios = {} 
if 'db_flota' not in st.session_state: st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state: st.session_state.db_guias = []
if 'admin_pass' not in st.session_state: st.session_state.admin_pass = "linares2026"
if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 MENÚ PRINCIPAL")
perfil = st.sidebar.selectbox("Seleccione su Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])

# --- VISTA: INICIO (PANTALLA NO NEGRA) ---
if perfil == "Inicio":
    st.title("🚛 Sistema de Gestión Logística Maule")
    st.info("Bienvenido al centro de control. Por favor, seleccione su rol en el menú de la izquierda para comenzar.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Transportistas")
        st.write("Gestione su flota, revise sus guías y descargue reportes en Excel.")
    with col2:
        st.subheader("Conductores")
        st.write("Envíe fotos de sus guías de despacho de forma rápida y segura.")
    with col3:
        st.subheader("Administración")
        st.write("Control total de usuarios y seguridad del sistema.")

# --- VISTA: TRANSPORTISTA (SEGURIDAD REFORZADA) ---
elif perfil == "Transportista":
    st.title("🏢 Panel Privado de Transportes")
    
    empresa_nom = st.text_input("Ingrese el nombre de su Empresa").strip().lower()
    
    if empresa_nom:
        if empresa_nom not in st.session_state.db_usuarios:
            st.warning(f"La empresa '{empresa_nom}' no está registrada en el sistema.")
            with st.expander("📝 Registrar mi empresa ahora"):
                p1 = st.text_input("Defina su Contraseña Privada", type="password")
                m1 = st.text_input("Correo electrónico (para recuperación)")
                if st.button("Finalizar Registro"):
                    st.session_state.db_usuarios[empresa_nom] = {'clave': p1, 'correo': m1}
                    st.success("✅ Empresa registrada. Ahora puede ingresar con su clave.")
        else:
            # Pantalla de Login obligatoria
            pass_check = st.text_input("Contraseña de Empresa", type="password")
            col_login, col_recup = st.columns([1, 2])
            
            with col_login:
                if st.button("🔐 Entrar al Panel"):
                    if pass_check == st.session_state.db_usuarios[empresa_nom]['clave']:
                        st.session_state[f'active_{empresa_nom}'] = True
                    else:
                        st.error("Contraseña incorrecta.")
            
            with col_recup:
                with st.expander("¿Olvidó su clave?"):
                    st.write(f"Se enviará un enlace al correo: **{st.session_state.db_usuarios[empresa_nom]['correo']}**")
                    if st.button("Enviar recuperación"):
                        st.info("Simulación: Correo de recuperación enviado.")

        # CONTENIDO EXCLUSIVO
        if st.session_state.get(f'active_{empresa_nom}', False):
            st.divider()
            st.success(f"Sesión Activa: {empresa_nom.upper()}")
            menu_t = st.tabs(["📊 Mis Guías", "🚛 Mi Flota", "⚙️ Ajustes", "🚪 Salir"])
            
            with menu_t[0]: # Guías
                mis_g = [g for g in st.session_state.db_guias if g['empresa'] == empresa_nom]
                if mis_g:
                    df = pd.DataFrame(mis_g)
                    st.dataframe(df.drop(columns=['foto']))
                    # Botón de Excel
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.drop(columns=['foto']).to_excel(writer, index=False)
                    st.download_button("📥 Descargar Reporte Excel", output.getvalue(), f"reporte_{empresa_nom}.xlsx")
                else:
                    st.info("No hay guías enviadas aún.")

            with menu_t[1]: # Flota
                p_camion = st.text_input("Patente").upper()
                n_chofer = st.text_input("Nombre Chofer")
                if st.button("Añadir a Flota"):
                    st.session_state.db_flota.append({"empresa": empresa_nom, "patente": p_camion, "conductor": n_chofer})
                    st.success("Camión añadido.")

            with menu_t[2]: # Ajustes / Cambio de Clave
                st.subheader("Cambiar mi Contraseña")
                nueva = st.text_input("Nueva Clave", type="password")
                if st.button("Actualizar Clave"):
                    st.session_state.db_usuarios[empresa_nom]['clave'] = nueva
                    st.success("Contraseña actualizada con éxito.")

            with menu_t[3]:
                if st.button("Cerrar Sesión"):
                    st.session_state[f'active_{empresa_nom}'] = False
                    st.rerun()

# --- VISTA: ADMINISTRADOR (CON PREGUNTA DE SEGURIDAD) ---
elif perfil == "Administrador de la App":
    st.title("🛡️ Panel Maestro de Control")
    
    if not st.session_state.admin_auth:
        c_maestra = st.text_input("Clave Maestra", type="password")
        if st.button("Acceder"):
            if c_maestra == st.session_state.admin_pass:
                st.session_state.admin_auth = True
                st.rerun()
            else:
                st.error("Error de acceso.")
        
        with st.expander("🆘 Olvidé mi Clave Maestra"):
            st.write("Responda su pregunta de seguridad:")
            pregunta = st.text_input("¿Cuál es su ciudad de nacimiento?")
            if st.button("Validar"):
                if pregunta.lower() == "linares": # RESPUESTA SECRETA
                    st.info(f"Su clave maestra es: {st.session_state.admin_pass}")
    else:
        st.write("### Gestión Global de Usuarios")
        st.write(st.session_state.db_usuarios)
        if st.button("Resetear todo el Sistema"):
            st.session_state.db_usuarios = {}
            st.warning("Se han borrado todos los usuarios.")
        
        if st.button("Cerrar Sesión"):
            st.session_state.admin_auth = False
            st.rerun()

# --- VISTA: CONDUCTOR ---
elif perfil == "Conductor":
    st.title("🚛 Envío de Guía de Despacho")
    pat = st.text_input("Patente del Camión").upper()
    foto = st.file_uploader("Subir foto", type=['jpg', 'png'])
    if st.button("Enviar Datos"):
        if pat and foto:
            # Buscar empresa
            emp = next((f['empresa'] for f in st.session_state.db_flota if f['patente'] == pat), "Sin Empresa")
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp,
                "patente": pat,
                "foto": foto.read()
            })
            st.success("Guía enviada correctamente.")
