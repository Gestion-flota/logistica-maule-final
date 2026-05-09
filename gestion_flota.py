import streamlit as st
import pandas as pd
from io import BytesIO
from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import Optional

# --- BASE DE DATOS ---
class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    codigo_acceso: str = Field(unique=True)
    pin: str
    nombre_empresa: str
    rol: str # 'admin_general', 'transportista', 'conductor'

class Equipo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    empresa: str
    conductor: str
    patente: str = Field(unique=True)
    pin_conductor: str
    detalle: str
    gps: str = "Pendiente"

sqlite_url = "sqlite:///plataforma_final.db"
engine = create_engine(sqlite_url)
SQLModel.metadata.create_all(engine)

# Crear tu acceso de dueño (CÁMBIALO AQUÍ SI QUIERES)
with Session(engine) as session:
    if not session.exec(select(Usuario).where(Usuario.rol == "admin_general")).first():
        session.add(Usuario(codigo_acceso="dueño123", pin="2024", nombre_empresa="SaaS Master", rol="admin_general"))
        session.commit()

st.set_page_config(page_title="Gestión de Flota Pro", layout="wide")
if 'auth' not in st.session_state: st.session_state.auth = None

# --- LOGIN ÚNICO ---
def login():
    st.title("🚚 Portal Logístico")
    st.info("Ingrese su Código/Patente y PIN")
    with st.form("login"):
        user_in = st.text_input("Usuario / Patente")
        pin_in = st.text_input("PIN", type="password")
        if st.form_submit_button("Entrar"):
            with Session(engine) as session:
                # 1. Buscar en Usuarios (Dueño o Empresario)
                u = session.exec(select(Usuario).where(Usuario.codigo_acceso == user_in, Usuario.pin == pin_in)).first()
                if u:
                    st.session_state.auth = {"data": u, "tipo": u.rol}
                    st.rerun()
                # 2. Buscar en Equipos (Conductores)
                c = session.exec(select(Equipo).where(Equipo.patente == user_in, Equipo.pin_conductor == pin_in)).first()
                if c:
                    st.session_state.auth = {"data": c, "tipo": "conductor"}
                    st.rerun()
                st.error("Acceso denegado.")

# --- PANEL DUEÑO (TÚ) ---
def panel_dueño():
    st.header("💎 Administración Global")
    with st.expander("➕ Crear Nueva Empresa Cliente"):
        with st.form("c_emp"):
            n = st.text_input("Nombre Empresa")
            c = st.text_input("Código Acceso")
            p = st.text_input("PIN")
            if st.form_submit_button("Dar de Alta"):
                with Session(engine) as session:
                    session.add(Usuario(codigo_acceso=c, pin=p, nombre_empresa=n, rol="transportista"))
                    session.commit()
                st.success("Empresa creada.")

# --- PANEL TRANSPORTISTA (EMPRESARIO) ---
def panel_transportista():
    emp = st.session_state.auth["data"].nombre_empresa
    st.header(f"🏢 Gestión de Flota: {emp}")
    tab1, tab2 = st.tabs(["📋 Mi Flota", "➕ Registrar Conductor"])
    
    with tab2:
        with st.form("add"):
            c1, c2, c3 = st.columns(3)
            cond = c1.text_input("Nombre Chofer")
            pat = c2.text_input("Patente")
            p_c = c3.text_input("PIN para Chofer (4 dígitos)")
            det = st.text_area("Detalles de Ruta")
            if st.form_submit_button("Registrar Equipo"):
                with Session(engine) as session:
                    session.add(Equipo(empresa=emp, conductor=cond, patente=pat, pin_conductor=p_c, detalle=det))
                    session.commit()
                st.success("Registrado.")

# --- PANEL CONDUCTOR (SIMPLIFICADO) ---
def panel_conductor():
    datos = st.session_state.auth["data"]
    st.title("🚛 Modo Conductor")
    st.header(f"Bienvenido, {datos.conductor}")
    st.subheader(f"Camión: {datos.patente}")
    st.info(f"**Tu Ruta/Carga:** {datos.detalle}")
    if st.button("📍 Compartir mi ubicación actual"):
        st.success("Ubicación enviada al sistema (Simulado)")

# --- LÓGICA DE NAVEGACIÓN ---
if st.session_state.auth:
    if st.sidebar.button("Salir"):
        st.session_state.auth = None
        st.rerun()
    
    tipo = st.session_state.auth["tipo"]
    if tipo == "admin_general": panel_dueño()
    elif tipo == "transportista": panel_transportista()
    elif tipo == "conductor": panel_conductor()
else:
    login()
