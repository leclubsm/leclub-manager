import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
from fpdf import FPDF
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import uuid
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Le Club Manager", layout="wide", page_icon="💎")

# --- CONEXIÓN GOOGLE SHEETS ---
# Nombre de tu archivo en Drive y ruta de credenciales
SHEET_NAME = "Base de Datos LeClub"
CREDENTIALS_FILE = "credentials.json"

@st.cache_resource
def conectar_google_sheets():
    """Conecta con Google Sheets y devuelve el objeto Spreadsheet."""
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME)
    except Exception as e:
        st.error(f"❌ Error conectando a Google Sheets: {e}")
        return None

def obtener_o_crear_pestana(sh, nombre_pestana):
    """Busca una pestaña, si no existe la crea."""
    try:
        return sh.worksheet(nombre_pestana)
    except gspread.WorksheetNotFound:
        return sh.add_worksheet(title=nombre_pestana, rows=100, cols=20)

# --- ESTILOS CSS "CYBER DARK PRO" ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Roboto', sans-serif; }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { background-color: #111111; border-right: 1px solid #333; }
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] p { color: #FFFFFF !important; }
    
    /* TEXTOS */
    h1, h2, h3, h4 { color: #FFFFFF !important; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 0 10px rgba(0, 242, 255, 0.4); }
    p, label { color: #CCCCCC !important; }
    
    /* KPI CARDS */
    div[data-testid="stMetric"] { background-color: #1A1C24; border: 1px solid #333; border-left: 4px solid #00F2FF; padding: 10px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
    div[data-testid="stMetricValue"] { color: #00F2FF !important; font-size: 24px !important; font-weight: 700 !important; }
    div[data-testid="stMetricLabel"] { color: #BBBBBB !important; font-size: 14px !important; }

    /* TARJETAS PERSONALIZADAS */
    .cyber-card { background: linear-gradient(145deg, #1A1C24, #14161B); border: 1px solid #333; box-shadow: 0 0 15px rgba(0, 242, 255, 0.05); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 15px; }
    .glow { border: 1px solid #00F2FF; box-shadow: 0 0 15px rgba(0, 242, 255, 0.2); }
    .gold-glow { border: 1px solid #FFD700; box-shadow: 0 0 15px rgba(255, 215, 0, 0.2); }
    
    /* TABLA OCUPACIÓN */
    .occupancy-table { width: 100%; border-collapse: separate; border-spacing: 5px; margin-top: 20px; }
    .occupancy-table th { background-color: #00F2FF; color: black; padding: 15px; text-align: center; font-weight: bold; font-size: 1.1em; border-radius: 5px; }
    .occupancy-table td { border: 1px solid #444; padding: 20px; text-align: center; background-color: #1e1e1e; width: 33%; vertical-align: middle; border-radius: 8px; transition: 0.3s; }
    .occupancy-table td:hover { background-color: #252525; border-color: #00F2FF; }
    
    .model-badge { background-color: #111; border-left: 4px solid #D500F9; padding: 10px; border-radius: 5px; text-align: left; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
    .model-name { color: white; font-weight: bold; display: block; font-size: 1.1em; }
    .model-meta { color: #888; font-size: 0.8em; }
    
    .free-slot { color: #4CAF50; font-weight: bold; letter-spacing: 1px; border: 1px dashed #4CAF50; padding: 5px 10px; border-radius: 15px; background: rgba(76, 175, 80, 0.1); }
    
    /* BOTONES */
    .stButton>button { background: transparent; color: #00F2FF; border: 1px solid #00F2FF; border-radius: 4px; font-weight: 600; text-transform: uppercase; width: 100%; }
    .stButton>button:hover { background: #00F2FF; color: #000; box-shadow: 0 0 15px rgba(0, 242, 255, 0.6); }
    </style>
    """, unsafe_allow_html=True)

# --- ARCHIVOS Y CONSTANTES ---
LOGO_FILE = "Black logo - no background.png"
META_SEMANAL_USD = 4200
PORCENTAJE_SATELITE = 80
PORCENTAJE_PLANTA = 60
VALOR_TOKEN_DEFECTO = 0.05
TASA_RETEFUENTE = 0.04
PASSWORD_ADMIN = "admin123"

PLATAFORMAS_MAESTRAS = ["Chaturbate", "Stripchat", "BongaCams", "CamSoda", "StreamMate", "Flirt4Free", "LiveJasmin", "Cams.com", "Xlovecam", "Cherry.tv", "Livestrip"]
PLATAFORMAS_DOLAR_DIRECTO = ["Flirt4Free", "StreamMate", "LiveJasmin", "Cams.com", "Cherry.tv", "Xlovecam", "Livestrip"]
TURNOS = ["Mañana", "Tarde", "Noche", "Satelite"]
CATEGORIAS_GASTOS = ["Adelanto Modelo", "Nómina Staff", "Arriendo", "Servicios", "Aseo/Cafetería", "Mantenimiento", "Publicidad", "Incentivos", "Otro"]

# --- GESTIÓN DE DATOS (CLOUD) ---
def cargar_datos_cloud():
    """Descarga datos de Google Sheets. Si las pestañas no existen, devuelve DFs vacíos."""
    sh = conectar_google_sheets()
    if not sh: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), {}
    
    # 1. Producción
    try:
        ws = sh.worksheet("Produccion")
        df = pd.DataFrame(ws.get_all_records())
        if not df.empty and 'Fecha' in df.columns: df['Fecha'] = pd.to_datetime(df['Fecha'])
    except: df = pd.DataFrame(columns=['Fecha', 'Nickname', 'Nombre_Real', 'Documento', 'Tipo_Modelo', 'Pagina', 'Tokens', 'Valor_Token', 'TRM_Registro', 'Total_USD'])

    # 2. Asistencia
    try:
        ws = sh.worksheet("Asistencia")
        df_a = pd.DataFrame(ws.get_all_records())
        if not df_a.empty and 'Fecha' in df_a.columns: df_a['Fecha'] = pd.to_datetime(df_a['Fecha'])
    except: df_a = pd.DataFrame(columns=['Fecha', 'Nickname', 'Estado', 'Observacion', 'Turno'])

    # 3. Gastos
    cols_gastos = ['ID', 'Fecha', 'Categoria', 'Descripcion', 'Monto', 'Modelo_Relacionado', 'Responsable', 'Es_Prestamo', 'Cuotas_Totales', 'Cuotas_Pagadas', 'Saldo_Pendiente']
    try:
        ws = sh.worksheet("Gastos")
        df_g = pd.DataFrame(ws.get_all_records())
        if not df_g.empty and 'Fecha' in df_g.columns: 
            df_g['Fecha'] = pd.to_datetime(df_g['Fecha'])
            for c in cols_gastos: 
                if c not in df_g.columns: df_g[c] = 0
    except: df_g = pd.DataFrame(columns=cols_gastos)

    # 4. Configuración (JSON en una celda o columnas)
    # Para simplificar en Sheets, usaremos columnas: Nickname, ConfigJSON
    mods = {}
    try:
        ws = sh.worksheet("Configuracion")
        records = ws.get_all_records()
        for r in records:
            try: mods[r['Nickname']] = json.loads(r['Data'])
            except: pass
    except: pass

    return df, df_a, df_g, mods

def guardar_todo_cloud():
    """Sube los DataFrames actuales a Google Sheets."""
    sh = conectar_google_sheets()
    if not sh: return
    
    with st.spinner("☁️ Sincronizando con Google Drive..."):
        # Helper para subir DF
        def subir_df(pestana, df):
            ws = obtener_o_crear_pestana(sh, pestana)
            ws.clear()
            if not df.empty:
                # Convertir fechas a string para serialización JSON
                df_save = df.copy()
                if 'Fecha' in df_save.columns: df_save['Fecha'] = df_save['Fecha'].astype(str)
                ws.update([df_save.columns.values.tolist()] + df_save.values.tolist())
            else:
                # Si está vacío, al menos poner cabeceras
                ws.update([df.columns.values.tolist()])

        subir_df("Produccion", st.session_state.data)
        subir_df("Asistencia", st.session_state.asistencia)
        subir_df("Gastos", st.session_state.gastos)
        
        # Guardar configuración
        ws_conf = obtener_o_crear_pestana(sh, "Configuracion")
        ws_conf.clear()
        ws_conf.update([['Nickname', 'Data']] + [[k, json.dumps(v)] for k, v in st.session_state.db_modelos.items()])

# Inicializar Estado
if 'data' not in st.session_state:
    df, asis, gas, mods = cargar_datos_cloud()
    st.session_state.data = df
    st.session_state.asistencia = asis
    st.session_state.gastos = gas
    st.session_state.db_modelos = mods

# --- HELPERS (Funciones originales) ---
def get_quincena_dates(fecha_ref):
    if fecha_ref.day <= 15:
        q_act_ini = fecha_ref.replace(day=1)
        q_act_fin = fecha_ref.replace(day=15)
        nom_act = f"Q1 {fecha_ref.strftime('%b')}"
        q_prev_fin = fecha_ref.replace(day=1) - timedelta(days=1)
        q_prev_ini = q_prev_fin.replace(day=16)
        nom_prev = f"Q2 {q_prev_fin.strftime('%b')}"
        return q_act_ini, q_act_fin, nom_act, q_prev_ini, q_prev_fin, nom_prev
    else:
        next_m = fecha_ref.replace(day=28) + timedelta(days=4)
        q_act_fin = next_m - timedelta(days=next_m.day)
        q_act_ini = fecha_ref.replace(day=16)
        nom_act = f"Q2 {fecha_ref.strftime('%b')}"
        q_prev_ini = fecha_ref.replace(day=1)
        q_prev_fin = fecha_ref.replace(day=15)
        nom_prev = f"Q1 {fecha_ref.strftime('%b')}"
        return q_act_ini, q_act_fin, nom_act, q_prev_ini, q_prev_fin, nom_prev

def generar_recibo_pdf(datos_modelo, f_ini, f_fin, neto, detalles, desglose, trm):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(LOGO_FILE): pdf.image(LOGO_FILE, x=10, y=8, w=45); pdf.ln(25)
    else: pdf.ln(10)
    pdf.set_font("Arial", 'B', 14); pdf.cell(0, 10, "COMPROBANTE DE PAGO", 1, 1, 'C'); pdf.ln(5)
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, "INFORMACIÓN", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 6, f"Modelo: {datos_modelo['nombre_real']}", 1); pdf.cell(95, 6, f"Doc: {datos_modelo['documento']}", 1, 1)
    pdf.cell(95, 6, f"Nick: {datos_modelo['nickname']}", 1); pdf.cell(95, 6, f"Tipo: {datos_modelo['tipo']} ({detalles['porcentaje']}%)", 1, 1)
    pdf.cell(190, 6, f"Periodo: {f_ini.strftime('%d/%m')} al {f_fin.strftime('%d/%m')} | TRM Pago: ${trm:,.0f}", 1, 1); pdf.ln(3)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, "DETALLE PLATAFORMAS (USD)", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 9)
    for p, v in desglose.items():
        if v > 0: pdf.cell(140, 6, p, 1); pdf.cell(50, 6, f"$ {v:,.2f}", 1, 1, 'R')
    pdf.set_font("Arial", 'B', 9); pdf.cell(140, 6, "TOTAL USD", 1); pdf.cell(50, 6, f"$ {detalles['ingresos']:,.2f}", 1, 1, 'R'); pdf.ln(3)
    pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, "LIQUIDACIÓN FINAL (COP)", 1, 1, 'L', True)
    pdf.set_font("Arial", '', 10)
    pdf.cell(140, 6, "Bruto (USD * TRM)", 1); pdf.cell(50, 6, f"$ {detalles['ingresos_brutos_cop']:,.0f}", 1, 1, 'R')
    pdf.cell(140, 6, f"Ganancia ({detalles['porcentaje']}%)", 1); pdf.cell(50, 6, f"$ {detalles['ganancia_base']:,.0f}", 1, 1, 'R')
    pdf.cell(140, 6, "Retefuente (4%)", 1); pdf.cell(50, 6, f"- $ {detalles['retefuente']:,.0f}", 1, 1, 'R')
    pdf.cell(140, 6, "Deducciones / Abonos", 1); pdf.cell(50, 6, f"- $ {detalles['deducciones']:,.0f}", 1, 1, 'R')
    pdf.set_fill_color(220, 255, 220)
    pdf.set_font("Arial", 'B', 12); pdf.cell(140, 10, "NETO A PAGAR", 1); pdf.cell(50, 10, f"$ {neto:,.0f}", 1, 1, 'R', True)
    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ ---
st.sidebar.title("💎 LE CLUB")
if os.path.exists(LOGO_FILE): st.sidebar.image(LOGO_FILE)
else: st.sidebar.markdown("### MANAGER V2.0")

st.sidebar.write("---")
# Botón de recarga manual para forzar actualización desde la nube
if st.sidebar.button("🔄 Actualizar Datos Nube"):
    st.cache_resource.clear()
    df, asis, gas, mods = cargar_datos_cloud()
    st.session_state.data = df
    st.session_state.asistencia = asis
    st.session_state.gastos = gas
    st.session_state.db_modelos = mods
    st.success("Datos actualizados desde Drive")

menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📊 Dashboard", "🛏️ Habitaciones (Cupos)", "📝 Registro Diario", "📅 Asistencia", "💸 Caja & Gastos", "💰 Nómina (Admin)", "👤 Detalles", "⚙️ Configuración"])

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 TABLERO DE CONTROL")
    today = pd.Timestamp(date.today())
    q_ini, q_fin, q_nom, q_prev_ini, q_prev_fin, q_prev_nom = get_quincena_dates(today)
    
    df = st.session_state.data.copy()
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_act = df[(df['Fecha'] >= q_ini) & (df['Fecha'] <= q_fin)]
        df_prev = df[(df['Fecha'] >= q_prev_ini) & (df['Fecha'] <= q_prev_fin)]
        total_act = df_act['Total_USD'].sum()
        if not df_act.empty:
            top_model_row = df_act.groupby('Nickname')['Total_USD'].sum()
            top_model_name = top_model_row.idxmax() if not top_model_row.empty else "N/A"
            top_model_val = top_model_row.max() if not top_model_row.empty else 0
        else: top_model_name = "N/A"; top_model_val = 0
    else: df_act = pd.DataFrame(); total_act = 0; top_model_name = "N/A"; top_model_val = 0

    df_att = st.session_state.asistencia.copy()
    if not df_att.empty:
        df_att['Fecha'] = pd.to_datetime(df_att['Fecha'])
        df_att['Fecha_Date'] = df_att['Fecha'].dt.date
        def es_falta(estado): return "falta" in str(estado).lower() or "sin excusa" in str(estado).lower() or "❌" in str(estado).lower()
        faltas_hoy = df_att[(df_att['Fecha_Date'] == today.date()) & (df_att['Estado'].apply(es_falta))].shape[0]
        faltas_q_act = df_att[(df_att['Fecha_Date'] >= q_ini.date()) & (df_att['Fecha_Date'] <= q_fin.date()) & (df_att['Estado'].apply(es_falta))].shape[0]
        faltas_q_prev = df_att[(df_att['Fecha_Date'] >= q_prev_ini.date()) & (df_att['Fecha_Date'] <= q_prev_fin.date()) & (df_att['Estado'].apply(es_falta))].shape[0]
    else: faltas_hoy = 0; faltas_q_act = 0; faltas_q_prev = 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.markdown(f"<div class='cyber-card glow'><h3 style='margin:0;color:#fff'>PRODUCCIÓN</h3><h2 style='color:#00f2ff;margin:5px 0'>$ {total_act:,.0f}</h2><p>{q_nom}</p></div>", unsafe_allow_html=True)
    with c2: 
        delta = faltas_q_act - faltas_q_prev
        st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>FALTAS (Q)</h3><h2 style='color:#fff;margin:5px 0'>{faltas_q_act}</h2><p style='color:{'#f00' if delta>0 else '#0f0'}'>{delta:+d} vs Ant</p></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='cyber-card gold-glow'><h3 style='margin:0;color:#FFD700'>👑 TOP MODEL</h3><h2 style='color:#fff;margin:5px 0'>{top_model_name}</h2><p>$ {top_model_val:,.0f} USD</p></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>FALTAS HOY</h3><h2 style='color:#fff;margin:5px 0'>{faltas_hoy}</h2><p>Del día</p></div>", unsafe_allow_html=True)
    
    meta_global = sum([d.get('meta_quincenal', 0) for d in st.session_state.db_modelos.values()])
    avance_global = (total_act / meta_global * 100) if meta_global > 0 else 0
    with c5: st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>META</h3><h2 style='color:#fff;margin:5px 0'>{avance_global:.1f}%</h2><p>DE ${meta_global:,.0f}</p></div>", unsafe_allow_html=True)

    g1, g2 = st.columns([1, 1])
    with g1:
        st.subheader("🌐 PLATAFORMAS")
        if not df_act.empty:
            pl = df_act.groupby('Pagina')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False)
            figp = px.bar(pl, x='Pagina', y='Total_USD', text_auto='.0f', color='Total_USD', color_continuous_scale=['#222', '#D500F9'])
            figp.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0,r=0,t=0,b=0), coloraxis_showscale=False)
            st.plotly_chart(figp, use_container_width=True)
    with g2:
        st.subheader("🏆 RANKING")
        if not df_act.empty:
            rk = df_act.groupby('Nickname')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=True)
            figr = px.bar(rk, x='Total_USD', y='Nickname', orientation='h', text_auto='.0f')
            figr.update_traces(marker_color='#00F2FF')
            figr.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0,r=0,t=0,b=0), xaxis_title="USD", yaxis_title="")
            st.plotly_chart(figr, use_container_width=True)

# --- 2. HABITACIONES ---
elif menu == "🛏️ Habitaciones (Cupos)":
    st.title("🛏️ MAPA DE OCUPACIÓN")
    html = """<table class="occupancy-table"><thead><tr><th style="width:10%;">HAB</th><th>🌅 MAÑANA</th><th>☀️ TARDE</th><th>🌙 NOCHE</th></tr></thead><tbody>"""
    for r in range(1, 6):
        html += f"<tr><td style='font-size:1.5em; font-weight:bold; color:#00F2FF;'>{r}</td>"
        for turno in ["Mañana", "Tarde", "Noche"]:
            ocupante = None
            for nick, data in st.session_state.db_modelos.items():
                if data.get('habitacion') == r and data.get('turno') == turno:
                    ocupante = nick; break
            if ocupante: html += f"<td><div class='model-badge'><span class='model-name'>{ocupante}</span><span class='model-meta'>Asignada</span></div></td>"
            else: html += f"<td><span class='free-slot'>🟢 LIBRE</span></td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)

# --- 3. REGISTRO ---
elif menu == "📝 Registro Diario":
    st.title("📝 PRODUCCIÓN")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        if len(st.session_state.db_modelos)>0:
            fr = st.date_input("Fecha", date.today(), key="dr")
            ns = st.selectbox("Modelo", sorted(list(st.session_state.db_modelos.keys())), key="ns")
            dt = st.session_state.db_modelos[ns]
            pl = dt.get('plataformas', [])
            st.markdown(f"<div style='background:#222;padding:10px;border-left:3px solid #00f2ff'><h4>{dt['nombre_real']}</h4><small>{dt.get('turno','-')} | {dt['tipo']}</small></div>", unsafe_allow_html=True)
            if pl:
                with st.form("fp"):
                    ip = {}
                    for p in pl:
                        st.markdown(f"**{p}**")
                        ca, cb = st.columns(2)
                        if p in PLATAFORMAS_DOLAR_DIRECTO:
                            v = ca.number_input("USD", 0.0, step=1.0, key=f"u{p}{ns}")
                            ip[p] = {'t':'usd', 'v':v}
                        else:
                            tk = ca.number_input("Tokens", 0, step=1, key=f"t{p}{ns}")
                            pr = cb.number_input("Precio", value=VALOR_TOKEN_DEFECTO, format="%.3f", key=f"p{p}{ns}")
                            ip[p] = {'t':'tok', 'v':tk, 'p':pr}
                    if st.form_submit_button("GUARDAR EN NUBE"):
                        rg = []
                        for p, d in ip.items():
                            if d['v']>0:
                                u = d['v'] if d['t']=='usd' else d['v']*d['p']
                                rg.append({'Fecha':pd.to_datetime(fr), 'Nickname':ns, 'Nombre_Real':dt['nombre_real'], 'Documento':dt['documento'], 'Tipo_Modelo':dt['tipo'], 'Pagina':p, 'Tokens':d['v'] if d['t']=='tok' else 0, 'Valor_Token':d['p'] if d['t']=='tok' else 0, 'TRM_Registro':0, 'Total_USD':u})
                        if rg:
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(rg)], ignore_index=True)
                            guardar_todo_cloud(); st.success("✅ Guardado en Drive"); st.rerun()
    with c2:
        st.subheader("EDICIÓN RÁPIDA")
        if not st.session_state.data.empty:
            df_edit = st.data_editor(st.session_state.data.sort_values('Fecha', ascending=False), num_rows="dynamic", key="me", height=600)
            if st.button("💾 SINCRONIZAR CAMBIOS"):
                st.session_state.data = df_edit
                guardar_todo_cloud()
                st.success("Base de datos actualizada")

# --- 4. ASISTENCIA ---
elif menu == "📅 Asistencia":
    st.title("📅 ASISTENCIA")
    c1, c2 = st.columns([2, 1])
    with c1:
        fa = st.date_input("Fecha", date.today(), key="da")
        for tr in TURNOS:
            ms = [k for k, v in st.session_state.db_modelos.items() if v.get('turno')==tr]
            if ms:
                with st.expander(f"TURNO {tr.upper()}", expanded=True):
                    with st.form(f"f_{tr}"):
                        rh = {}
                        for n in sorted(ms):
                            ca, cb = st.columns([2, 2])
                            with ca:
                                st.markdown(f"**{n}**")
                                stt = st.radio(f"s_{n}", ["✅ Asistió", "⚠️ Excusa", "❌ Falta"], horizontal=True, label_visibility="collapsed")
                            with cb: obs = st.text_input("Nota", key=f"o_{n}", label_visibility="collapsed")
                            rh[n] = {'e':stt, 'o':obs}
                        if st.form_submit_button("GUARDAR"):
                            nvs = [{'Fecha':pd.to_datetime(fa), 'Nickname':n, 'Estado':d['e'], 'Observacion':d['o'], 'Turno':tr} for n, d in rh.items()]
                            dfa = st.session_state.asistencia
                            st.session_state.asistencia = pd.concat([dfa[~((dfa['Fecha'].dt.date==fa)&(dfa['Turno']==tr))], pd.DataFrame(nvs)], ignore_index=True)
                            guardar_todo_cloud(); st.success("✅ Asistencia Guardada"); st.rerun()
    with c2:
        st.subheader("Historial")
        if not st.session_state.asistencia.empty:
            sh = st.session_state.asistencia.sort_values('Fecha', ascending=False).head(15)
            sh['Fecha'] = sh['Fecha'].dt.date
            st.dataframe(sh[['Fecha', 'Nickname', 'Estado']], use_container_width=True, hide_index=True)

# --- 5. CAJA Y GASTOS ---
elif menu == "💸 Caja & Gastos":
    st.title("💸 CAJA MENOR")
    with st.form("fg"):
        c1, c2, c3 = st.columns(3)
        fg = c1.date_input("Fecha", date.today())
        cg = c2.selectbox("Categoría", CATEGORIAS_GASTOS)
        mg = c3.number_input("Monto", step=5000)
        ds = st.text_input("Detalle")
        es_p = False; mr = None; cu = 1
        if cg == "Adelanto Modelo":
            es_p = True
            ca, cb = st.columns(2)
            mr = ca.selectbox("Modelo", sorted(list(st.session_state.db_modelos.keys())))
            cu = cb.number_input("Cuotas", 1, 12, 1)
        if st.form_submit_button("REGISTRAR GASTO"):
            ng = {"ID":str(uuid.uuid4())[:8], "Fecha":pd.to_datetime(fg), "Categoria":cg, "Descripcion":ds, "Monto":mg, "Modelo_Relacionado":mr if mr else "", "Es_Prestamo":es_p, "Cuotas_Totales":cu, "Cuotas_Pagadas":0, "Saldo_Pendiente":mg}
            st.session_state.gastos = pd.concat([st.session_state.gastos, pd.DataFrame([ng])], ignore_index=True)
            guardar_todo_cloud(); st.success("Gasto registrado"); st.rerun()
    
    if not st.session_state.gastos.empty:
        st.dataframe(st.session_state.gastos, use_container_width=True)

# --- 6. NÓMINA (ADMIN) ---
elif menu == "💰 Nómina (Admin)":
    st.title("🔐 ZONA SEGURA: NÓMINA")
    pwd = st.text_input("Contraseña", type="password")
    if pwd == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        today = date.today()
        qi, qf, _, _, _, _ = get_quincena_dates(pd.Timestamp(today))
        c1, c2, c3 = st.columns(3)
        g_ini = c1.date_input("Inicio", qi); g_fin = c2.date_input("Fin", qf); g_trm = c3.number_input("TRM PAGO", 4100)
        
        st.divider()
        c1, c2 = st.columns([1, 2])
        with c1:
            np = st.selectbox("Modelo", sorted(list(st.session_state.db_modelos.keys())))
            cuota_sugerida = 0
            if not st.session_state.gastos.empty:
                gas = st.session_state.gastos
                prests = gas[(gas['Es_Prestamo'] == True) & (gas['Modelo_Relacionado'] == np) & (gas['Saldo_Pendiente'] > 0)]
                for ix, row in prests.iterrows(): cuota_sugerida += row['Monto']/row['Cuotas_Totales']
            if cuota_sugerida > 0: st.warning(f"⚠️ DEBE CUOTA: ${cuota_sugerida:,.0f}")
            
            if st.button("COBRAR CUOTAS"):
                for ix, row in prests.iterrows():
                    st.session_state.gastos.at[ix, 'Cuotas_Pagadas'] += 1
                    st.session_state.gastos.at[ix, 'Saldo_Pendiente'] -= (row['Monto']/row['Cuotas_Totales'])
                guardar_todo_cloud(); st.success("Cobro registrado"); st.rerun()
                
            ded = st.number_input("Deducciones", value=float(cuota_sugerida), step=10000.0)
            dm = st.session_state.db_modelos[np]
            prc = PORCENTAJE_SATELITE if dm['tipo'] == "Satelite" else st.slider("% Planta", 40, 80, PORCENTAJE_PLANTA)
        
        with c2:
            if not st.session_state.data.empty:
                msk = (st.session_state.data['Nickname']==np) & (st.session_state.data['Fecha'].dt.date>=g_ini) & (st.session_state.data['Fecha'].dt.date<=g_fin)
                dff = st.session_state.data.loc[msk]
                if not dff.empty:
                    usd = dff['Total_USD'].sum(); cop = usd*g_trm; bas = cop*(prc/100); ret = bas*TASA_RETEFUENTE; net = bas-ret-ded
                    st.markdown(f"<div class='cyber-card glow'><h1 style='color:#00f2ff;margin:0'>$ {net:,.0f}</h1><p>A PAGAR NETO</p></div>", unsafe_allow_html=True)
                    ds = dff.groupby('Pagina')['Total_USD'].sum().to_dict()
                    dtl = {'ingresos':usd, 'ingresos_brutos_cop':cop, 'porcentaje':prc, 'ganancia_base':bas, 'retefuente':ret, 'deducciones':ded}
                    if st.button("🖨️ PDF"):
                        inf = dm.copy(); inf['nickname'] = np
                        b = generar_recibo_pdf(inf, g_ini, g_fin, net, dtl, ds, g_trm)
                        st.download_button("Descargar Recibo", b, file_name=f"Pago_{np}.pdf")

# --- 7. CONFIGURACIÓN ---
elif menu == "⚙️ Configuración":
    st.title("⚙️ ADMIN MODELOS")
    t1, t2 = st.tabs(["Editar", "Crear"])
    with t1:
        if st.session_state.db_modelos:
            md = st.selectbox("Editar", sorted(list(st.session_state.db_modelos.keys())))
            d = st.session_state.db_modelos[md]
            with st.form("ed"):
                nm = st.text_input("Nombre", d['nombre_real']); dc = st.text_input("Doc", d['documento'])
                mt = st.number_input("Meta", value=d.get('meta_quincenal', 0))
                pl = st.multiselect("Plataformas", PLATAFORMAS_MAESTRAS, default=d.get('plataformas', []))
                tp = st.radio("Tipo", ["Planta", "Satelite"], index=0 if d['tipo']=="Planta" else 1)
                tn = st.selectbox("Turno", TURNOS, index=TURNOS.index(d.get('turno','Mañana')) if d.get('turno') in TURNOS else 0)
                rm = st.number_input("Habitación", 0, 5, d.get('habitacion', 0))
                if st.form_submit_button("ACTUALIZAR"):
                    st.session_state.db_modelos[md] = {"nombre_real": nm, "documento": dc, "tipo": tp, "turno": tn, "plataformas": pl, "meta_quincenal": mt, "habitacion": rm}
                    guardar_todo_cloud(); st.success("Modelo actualizada"); st.rerun()
    with t2:
        with st.form("nw"):
            nk = st.text_input("Nickname"); nm = st.text_input("Nombre Real")
            if st.form_submit_button("CREAR MODELO"):
                if nk:
                    st.session_state.db_modelos[nk] = {"nombre_real": nm, "documento": "", "tipo": "Planta", "turno": "Mañana", "plataformas": [], "meta_quincenal": 2000, "habitacion": 0}
                    guardar_todo_cloud(); st.success("Modelo creada"); st.rerun()
