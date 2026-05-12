import streamlit as st
import pandas as pd
from datetime import datetime
import io

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Logística Maule Pro", layout="wide")

# Inicialización de bases de datos
if 'admin_password' not in st.session_state: st.session_state['admin_password'] = "linares2026"
if 'admin_auth' not in st.session_state: st.session_state['admin_auth'] = False
if 'db_flota' not in st.session_state: st.session_state.db_flota = [] 
if 'db_guias' not in st.session_state: st.session_state.db_guias = []

# --- MENÚ LATERAL ---
st.sidebar.title("🚚 SISTEMA LOGÍSTICO")
perfil = st.sidebar.selectbox("Seleccione Perfil", ["Inicio", "Transportista", "Conductor", "Administrador de la App"])

# --- VISTA: TRANSPORTISTA ---
if perfil == "Transportista":
    st.title("🏢 Panel de Gestión para Transportistas")
    empresa_nom = st.text_input("Nombre de su Empresa", placeholder="Ej: Transportes Cáceres")
    
    if empresa_nom:
        t1, t2 = st.tabs(["🚛 Registrar Camiones", "📋 Ver y Descargar Guías"])
        
        with t1:
            col_a, col_b = st.columns(2)
            with col_a:
                pat = st.text_input("Patente").upper()
                chofer = st.text_input("Nombre Chofer habitual")
            if st.button("Registrar en mi Flota"):
                st.session_state.db_flota.append({"empresa": empresa_nom, "patente": pat, "conductor": chofer})
                st.success(f"Unidad {pat} añadida con éxito.")

        with t2:
            st.subheader(f"Historial de Guías - {empresa_nom}")
            # Filtramos solo las guías de esta empresa
            mis_guias = [g for g in st.session_state.db_guias if g['empresa'].lower() == empresa_nom.lower()]
            
            if mis_guias:
                df = pd.DataFrame(mis_guias)
                # Mostramos la tabla (sin la columna de la imagen para que sea limpia)
                st.dataframe(df.drop(columns=['foto_archivo'], errors='ignore'))
                
                # --- BOTÓN DESCARGAR EXCEL ---
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.drop(columns=['foto_archivo'], errors='ignore').to_excel(writer, index=False, sheet_name='Guias')
                st.download_button(
                    label="📥 Descargar Reporte en Excel",
                    data=output.getvalue(),
                    file_name=f"reporte_{empresa_nom}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                # --- VER FOTOS DE GUÍAS ---
                st.write("---")
                st.write("### 📸 Revisar Documentos Digitales")
                idx_guia = st.number_input("Ingrese el número de fila para ver la foto:", min_value=0, max_value=len(mis_guias)-1, step=1)
                if st.button("Mostrar Foto de la Guía"):
                    guia_sel = mis_guias[idx_guia]
                    if guia_sel['foto_archivo']:
                        st.image(guia_sel['foto_archivo'], caption=f"Guía Patente {guia_sel['patente']}")
            else:
                st.info("No hay guías registradas para esta empresa todavía.")

# --- VISTA: CONDUCTOR ---
elif perfil == "Conductor":
    st.title("🚛 Envío de Documentación (Chofer)")
    c1, c2 = st.columns(2)
    with c1:
        nombre_c = st.text_input("Su Nombre completo")
        patente_c = st.text_input("Patente del Camión").upper()
    with c2:
        archivo = st.file_uploader("Capturar Foto de la Guía", type=['jpg', 'png', 'jpeg'])
    
    if st.button("🚀 Enviar Guía al Sistema"):
        if nombre_c and patente_c and archivo:
            # Buscamos la empresa automáticamente
            emp_pertenece = next((f['empresa'] for f in st.session_state.db_flota if f['patente'] == patente_c), "Empresa no registrada")
            
            nueva_guia = {
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "empresa": emp_pertenece,
                "conductor": nombre_c,
                "patente": patente_c,
                "ubicacion": "Maule, Chile", # Aquí se podría integrar GPS real más adelante
                "foto_archivo": archivo.read()
            }
            st.session_state.db_guias.append(nueva_guia)
            st.balloons()
            st.success("✅ Guía enviada. El dueño de la empresa ya puede verla.")
        else:
            st.error("Faltan datos o la foto de la guía.")

# --- VISTA: ADMINISTRADOR (BLOQUEADO) ---
elif perfil == "Administrador de la App":
    st.title("🛡️ Panel Maestro")
    if not st.session_state['admin_auth']:
        clave = st.text_input("Clave de Acceso", type="password")
        if st.button("Entrar"):
            if clave == st.session_state['admin_password']:
                st.session_state['admin_auth'] = True
                st.rerun()
    else:
        st.write("Resumen total del sistema")
        if st.session_state.db_guias:
            st.dataframe(pd.DataFrame(st.session_state.db_guias).drop(columns=['foto_archivo']))
        if st.button("Cerrar Sesión"):
            st.session_state['admin_auth'] = False
            st.rerun()

elif perfil == "Inicio":
    st.title("Sistema de Gestión de Fletes")
    st.write("Bienvenido. Use el menú lateral para operar.")
