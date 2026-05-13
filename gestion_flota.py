import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Logística Maule Sistema", layout="wide")

# Bases de datos temporales
if 'db_usuarios' not in st.session_state: st.session_state.db_usuarios = {} 
if 'db_flota' not in st.session_state: st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state: st.session_state.db_guias = []
if 'admin_pass' not in st.session_state: st.session_state.admin_pass = "linares2026"
if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 SISTEMA LOGÍSTICO")
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])

# --- VISTA: INICIO ---
if perfil == "Inicio":
    st.title("🚛 Bienvenido al Sistema Logístico")
    st.info("Seleccione su perfil para comenzar a trabajar.")

# --- VISTA: TRANSPORTISTA (RECUPERADA Y MEJORADA) ---
elif perfil == "Transportista":
    st.title("🏢 Panel de Control - Empresa")
    empresa_nom = st.text_input("Nombre de la Empresa").strip().lower()
    
    if empresa_nom:
        # Si no existe, se registra
        if empresa_nom not in st.session_state.db_usuarios:
            st.warning(f"La empresa '{empresa_nom}' no está registrada.")
            with st.expander("📝 Registrar mi empresa ahora"):
                p1 = st.text_input("Defina su Clave", type="password")
                m1 = st.text_input("Correo electrónico")
                if st.button("Finalizar Registro"):
                    st.session_state.db_usuarios[empresa_nom] = {'clave': p1, 'correo': m1}
                    st.success("Registrado. Ingrese su clave arriba.")
        else:
            # Login obligatorio
            pass_check = st.text_input("Contraseña", type="password")
            if st.button("Entrar al Sistema"):
                if pass_check == st.session_state.db_usuarios[empresa_nom]['clave']:
                    st.session_state[f'active_{empresa_nom}'] = True
                else:
                    st.error("Clave incorrecta.")
            
            # Recuperación
            with st.expander("🆘 Olvidé mi clave"):
                c_val = st.text_input("Correo registrado")
                if c_val == st.session_state.db_usuarios[empresa_nom]['correo']:
                    st.info(f"Su clave es: {st.session_state.db_usuarios[empresa_nom]['clave']}")

        # CONTENIDO QUE HABÍAMOS PERDIDO (Excel y Flota)
        if st.session_state.get(f'active_{empresa_nom}', False):
            st.divider()
            st.success(f"Empresa: {empresa_nom.upper()}")
            t1, t2, t3 = st.tabs(["📊 Historial de Guías", "🚛 Mi Flota", "🚪 Salir"])
            
            with t1:
                mis_g = [g for g in st.session_state.db_guias if g['empresa'] == empresa_nom]
                if mis_g:
                    df = pd.DataFrame(mis_g)
                    st.dataframe(df.drop(columns=['foto'], errors='ignore'))
                    
                    # El botón de Excel que faltaba
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.drop(columns=['foto'], errors='ignore').to_excel(writer, index=False)
                    st.download_button("📥 Descargar Reporte Excel", output.getvalue(), f"guias_{empresa_nom}.xlsx")
                else:
                    st.info("No hay guías para mostrar.")

            with t2:
                # AQUÍ EL TRANSPORTISTA CREA AL CONDUCTOR
                st.subheader("Registrar Nuevo Camión y Conductor")
                pat_n = st.text_input("Patente (Ej: AB1234)").upper()
                con_n = st.text_input("Nombre del Conductor")
                if st.button("Guardar en Flota"):
                    st.session_state.db_flota.append({"empresa": empresa_nom, "patente": pat_n, "conductor": con_n})
                    st.success(f"Camión {pat_n} registrado correctamente.")

            with t3:
                if st.button("Cerrar Sesión"):
                    st.session_state[f'active_{empresa_nom}'] = False
                    st.rerun()

# --- VISTA: CONDUCTOR (ACCESO LIBRE) ---
elif perfil == "Conductor":
    st.title("🚛 Envío de Guía de Despacho")
    pat_c = st.text_input("Patente del Camión").upper()
    archivo = st.file_uploader("Foto de la Guía", type=['jpg', 'png', 'jpeg'])
    
    if st.button("Enviar Guía"):
        if pat_c and archivo:
            # Buscar a qué empresa pertenece la patente automáticamente
            emp = next((f['empresa'] for f in st.session_state.db_flota if f['patente'] == pat_c), "Independiente")
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp,
                "patente": pat_c,
                "foto": archivo.read()
            })
            st.success(f"Guía enviada con éxito a {emp}.")

# --- VISTA: ADMINISTRADOR (TU PANEL PARA VER TODO) ---
elif perfil == "Administrador de la App":
    st.title("🛡️ Panel Maestro")
    c_maestra = st.text_input("Clave Maestra", type="password")
    
    if c_maestra == st.session_state.admin_pass:
        st.session_state.admin_auth = True
        tab_a, tab_b = st.tabs(["👥 Usuarios", "🚛 Flotas Globales"])
        
        with tab_a:
            st.write("### Claves de Empresas")
            st.json(st.session_state.db_usuarios)
            
        with tab_b:
            st.write("### Todos los Camiones Registrados")
            if st.session_state.db_flota:
                st.table(pd.DataFrame(st.session_state.db_flota))
            else:
                st.info("No hay camiones en la base de datos.")
    elif c_maestra != "":
        st.error("Clave maestra incorrecta.")
