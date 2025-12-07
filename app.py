import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN IMPORTANTE ---
# Pon aquí el nombre EXACTO de tu archivo de Google Sheets
NOMBRE_HOJA = "Base de Datos LeClub"  

# --- CONEXIÓN ---
@st.cache_resource
def conectar_google_sheets():
    """
    Conecta con Google Sheets usando los secretos configurados en Streamlit Cloud.
    """
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Manejo de errores si no están configurados los secretos
    if "gcp_service_account" not in st.secrets:
        st.error("⚠️ Falta configurar los secretos (Secrets) en Streamlit Cloud.")
        st.stop()

    # Cargar credenciales desde st.secrets
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    
    return gspread.authorize(credentials)

# --- FUNCIONES ---

def guardar_datos(datos):
    try:
        client = conectar_google_sheets()
        
        # Intentamos abrir la hoja
        try:
            sheet = client.open(NOMBRE_HOJA).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            st.error(f"❌ No encuentro la hoja '{NOMBRE_HOJA}'. Asegúrate de haberla compartido con el email del servicio.")
            return False

        # Añadir fecha
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fila_completa = [fecha_hora] + datos
        
        sheet.append_row(fila_completa)
        return True
        
    except Exception as e:
        st.error(f"Error técnico: {e}")
        return False

def leer_datos():
    try:
        client = conectar_google_sheets()
        sheet = client.open(NOMBRE_HOJA).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

# --- INTERFAZ (Tu Formulario) ---

st.title("Registro de Modelos - Le Club")
st.markdown("---")

with st.form("formulario_registro"):
    col1, col2 = st.columns(2)
    with col1:
        nombre = st.text_input("Nombre Completo")
        telefono = st.text_input("Teléfono / WhatsApp")
    with col2:
        email = st.text_input("Correo Electrónico")
        categoria = st.selectbox("Categoría", ["Nuevo Ingreso", "Profesional", "Elite", "Master"])
    
    notas = st.text_area("Notas adicionales")
    
    submitted = st.form_submit_button("💾 Guardar Registro", use_container_width=True)
    
    if submitted:
        if nombre and email:
            st.info("Guardando datos...")
            # Aquí definimos qué guardamos y en qué orden
            datos = [nombre, email, telefono, categoria, notas]
            
            if guardar_datos(datos):
                st.success(f"¡Excelente! {nombre} ha sido registrad@ correctamente.")
                st.balloons()
            else:
                st.error("No se pudo guardar. Revisa la conexión.")
        else:
            st.warning("⚠️ El nombre y el correo son obligatorios.")

# --- VISUALIZADOR (Solo para admin) ---
st.markdown("---")
with st.expander("🔐 Ver Base de Datos (Admin)"):
    pass_admin = st.text_input("Contraseña de admin", type="password")
    if pass_admin == "admin123": # Puedes cambiar esto por una contraseña real
        df = leer_datos()
        if not df.empty:
            st.dataframe(df)
            st.caption(f"Total de registros: {len(df)}")
        else:
            st.info("La base de datos está vacía o no se pudo leer.")
