import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURACIÓN INICIAL ---
st.set_page_config(page_title="Logística Maule PRO", layout="wide")

# Bases de datos temporales (Se mantienen mientras la app esté corriendo)
if 'db_usuarios' not in st.session_state: st.session_state.db_usuarios = {} 
if 'db_flota' not in st.session_state: st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state: st.session_state.db_guias = []
if 'admin_pass' not in st.session_state: st.session_state.admin_pass = "linares2026"
if 'admin_auth' not in st.session_state: st.session_state.admin_auth = False

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 MENÚ PRINCIPAL")
perfil = st.sidebar.selectbox("Seleccione su Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])

# --- VISTA: INICIO ---
if perfil == "Inicio":
    st.title("🚛 Sistema Logístico Maule")
    st.info("Bienvenido. Use el menú lateral para ingresar según su rol.")
    st.write("---")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Para Empresas")
        st.write("Registre su flota y controle sus guías de despacho con reportes en Excel.")
    with c2:
        st.subheader("Para Choferes")
        st.write("Envíe fotos de sus guías al instante desde cualquier lugar.")

# --- VISTA: TRANSPORTISTA ---
elif perfil == "Transportista":
    st.title("🏢 Panel de Transportes")
    empresa_nom = st.text_input("Nombre de su Empresa").strip().lower()
    
    if empresa_nom:
        if empresa_nom not in st.session_state.db_usuarios:
            st.warning(f"La empresa '{empresa_nom}' no está registrada.")
            with st.expander("📝 Registrar mi empresa"):
                p1 = st.text_input("Defina su Contraseña", type="password")
                m1 = st.text_input("Correo de contacto")
                if st.button("Crear Cuenta"):
                    st.session_state.db_usuarios[empresa_nom] = {'clave': p1, 'correo': m1}
                    st.success("Cuenta creada. Ahora ingrese su clave arriba.")
        else:
            pass_check = st.text_input("Contraseña de Acceso", type="password")
            if st.button("🔓 Entrar"):
                if pass_check == st.session_state.db_usuarios[empresa_nom]['clave']:
                    st.session_state[f'active_{empresa_nom}'] = True
                else:
                    st.error("Clave incorrecta.")
            
            with st.expander("🆘 Olvidé mi contraseña"):
                correo_val = st.text_input("Ingrese su correo registrado")
                if correo_val == st.session_state.db_usuarios[empresa_nom]['correo']:
                    st.success("Correo verificado.")
                    nueva_p = st.text_input("Nueva contraseña", type="password")
                    if st.button("Cambiar y Entrar"):
                        st.session_state.db_usuarios[empresa_nom]['clave'] = nueva_p
                        st.session_state[f'active_{empresa_nom}'] = True
                        st.rerun()

        if st.session_state.get(f'active_{empresa_nom}', False):
            st.success(f"Sesión iniciada: {empresa_nom.upper()}")
            t1, t2, t3 = st.tabs(["📊 Historial de Guías", "🚛 Gestionar Flota", "🚪 Salir"])
            
            with t1:
                mis_g = [g for g in st.session_state.db_guias if g['empresa'] == empresa_nom]
                if mis_g:
                    df = pd.DataFrame(mis_g)
                    st.dataframe(df.drop(columns=['foto']))
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df.drop(columns=['foto']).to_excel(writer, index=False)
                    st.download_button("📥 Bajar Excel", output.getvalue(), f"{empresa_nom}.xlsx")
                else:
                    st.info("No hay guías registradas.")

            with t2:
                p_cam = st.text_input("Patente").upper()
                chofer = st.text_input("Nombre Chofer")
                if st.button("Registrar Camión"):
                    st.session_state.db_flota.append({"empresa": empresa_nom, "patente": p_cam, "conductor": chofer})
                    st.success("Añadido.")

            with t3:
                if st.button("Cerrar Sesión"):
                    st.session_state[f'active_{empresa_nom}'] = False
                    st.rerun()

# --- VISTA: CONDUCTOR ---
elif perfil == "Conductor":
    st.title("🚛 Envío de Guía")
    pat_c = st.text_input("Patente del Camión").upper()
    archivo = st.file_uploader("Foto de la Guía", type=['jpg', 'png'])
    if st.button("🚀 Enviar a mi Empresa"):
        if pat_c and archivo:
            emp = next((f['empresa'] for f in st.session_state.db_flota if f['patente'] == pat_c), "Independiente")
            st.session_state.db_guias.append({
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp,
                "patente": pat_c,
                "foto": archivo.read()
            })
            st.success(f"Guía enviada a {emp}.")

# --- VISTA: ADMINISTRADOR (TU PANEL) ---
elif perfil == "Administrador de la App":
    st.title("🛡️ Panel Maestro de Control")
    if not st.session_state.admin_auth:
        c_adm = st.text_input("Clave Maestra", type="password")
        if st.button("Entrar"):
            if c_adm == st.session_state.admin_pass:
                st.session_state.admin_auth = True
                st.rerun()
    else:
        # AQUÍ ES DONDE VES TODO
        tab1, tab2 = st.tabs(["👥 Usuarios y Claves", "🚛 Inventario de Flotas"])
        
        with tab1:
            st.write("### Transportistas Registrados")
            if st.session_state.db_usuarios:
                for emp, info in st.session_state.db_usuarios.items():
                    st.info(f"EMPRESA: **{emp.upper()}** | CLAVE: **{info['clave']}** | CORREO: {info['correo']}")
            else:
                st.write("No hay usuarios aún.")

        with tab2:
            st.write("### Camiones por Transportista")
            if st.session_state.db_flota:
                df_adm = pd.DataFrame(st.session_state.db_flota)
                # Resumen rápido
                st.write("**Total de camiones en el sistema:**", len(df_adm))
                st.table(df_adm)
            else:
                st.write("No hay camiones registrados.")
        
        if st.button("Cerrar Sesión de Administrador"):
            st.session_state.admin_auth = False
            st.rerun()
