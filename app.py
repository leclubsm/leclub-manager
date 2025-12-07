import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta, datetime
from fpdf import FPDF
import os
import json
import uuid
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Le Club Manager", layout="wide", page_icon="💎")

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

# --- ARCHIVOS ---
FILE_DATA = "base_datos_produccion.csv"
FILE_ASISTENCIA = "base_datos_asistencia.csv"
FILE_GASTOS = "base_datos_gastos.csv"
FILE_CONFIG = "configuracion_modelos.json"
LOGO_FILE = "Black logo - no background.png"

# --- CONSTANTES ---
META_SEMANAL_USD = 4200
PORCENTAJE_SATELITE = 80
PORCENTAJE_PLANTA = 60
VALOR_TOKEN_DEFECTO = 0.05
TASA_RETEFUENTE = 0.04
PASSWORD_ADMIN = "admin123"

PLATAFORMAS_MAESTRAS = ["Chaturbate", "Stripchat", "BongaCams", "CamSoda", "StreamMate", "Flirt4Free", "LiveJasmin", "Cams.com", "Xlovecam", "Cherry.tv", "Livestrip"]
PLATAFORMAS_DOLAR_DIRECTO = ["Flirt4Free", "StreamMate", "LiveJasmin", "Cams.com", "Cherry.tv", "Xlovecam", "Livestrip"]
TURNOS = ["Mañana", "Tarde", "Noche", "Satelite"]
HORARIOS = {
    "Mañana": "06:00 AM - 02:00 PM",
    "Tarde": "02:00 PM - 10:00 PM",
    "Noche": "10:00 PM - 06:00 AM"
}
CATEGORIAS_GASTOS = ["Adelanto Modelo", "Nómina Staff", "Arriendo", "Servicios", "Aseo/Cafetería", "Mantenimiento", "Publicidad", "Incentivos", "Otro"]

# --- CARGA DE DATOS ---
def cargar_datos():
    if os.path.exists(FILE_DATA):
        try: df = pd.read_csv(FILE_DATA); df['Fecha'] = pd.to_datetime(df['Fecha'])
        except: df = pd.DataFrame(columns=['Fecha', 'Nickname', 'Nombre_Real', 'Documento', 'Tipo_Modelo', 'Pagina', 'Tokens', 'Valor_Token', 'TRM_Registro', 'Total_USD'])
    else: df = pd.DataFrame(columns=['Fecha', 'Nickname', 'Nombre_Real', 'Documento', 'Tipo_Modelo', 'Pagina', 'Tokens', 'Valor_Token', 'TRM_Registro', 'Total_USD'])
    
    if os.path.exists(FILE_ASISTENCIA):
        try: df_a = pd.read_csv(FILE_ASISTENCIA); df_a['Fecha'] = pd.to_datetime(df_a['Fecha'])
        except: df_a = pd.DataFrame(columns=['Fecha', 'Nickname', 'Estado', 'Observacion', 'Turno'])
    else: df_a = pd.DataFrame(columns=['Fecha', 'Nickname', 'Estado', 'Observacion', 'Turno'])

    cols_gastos = ['ID', 'Fecha', 'Categoria', 'Descripcion', 'Monto', 'Modelo_Relacionado', 'Responsable', 'Es_Prestamo', 'Cuotas_Totales', 'Cuotas_Pagadas', 'Saldo_Pendiente']
    if os.path.exists(FILE_GASTOS):
        try: 
            df_g = pd.read_csv(FILE_GASTOS); df_g['Fecha'] = pd.to_datetime(df_g['Fecha'])
            for c in cols_gastos: 
                if c not in df_g.columns: df_g[c] = 0
        except: df_g = pd.DataFrame(columns=cols_gastos)
    else: df_g = pd.DataFrame(columns=cols_gastos)

    if os.path.exists(FILE_CONFIG):
        with open(FILE_CONFIG, 'r') as f: mods = json.load(f)
    else: mods = {} 

    return df, df_a, df_g, mods

def guardar_todo():
    st.session_state.data.to_csv(FILE_DATA, index=False)
    st.session_state.asistencia.to_csv(FILE_ASISTENCIA, index=False)
    st.session_state.gastos.to_csv(FILE_GASTOS, index=False)
    with open(FILE_CONFIG, 'w') as f: json.dump(st.session_state.db_modelos, f)

if 'data' not in st.session_state:
    df, asis, gas, mods = cargar_datos()
    st.session_state.data = df
    st.session_state.asistencia = asis
    st.session_state.gastos = gas
    st.session_state.db_modelos = mods

# --- HELPERS ---
def get_quincena_dates(fecha_ref):
    """
    Calcula fechas de corte para quincenas y devuelve 6 valores exactos.
    """
    if fecha_ref.day <= 15:
        # Q1
        q_act_ini = fecha_ref.replace(day=1)
        q_act_fin = fecha_ref.replace(day=15)
        nom_act = f"Q1 {fecha_ref.strftime('%b')}"
        
        q_prev_fin = fecha_ref.replace(day=1) - timedelta(days=1)
        q_prev_ini = q_prev_fin.replace(day=16)
        nom_prev = f"Q2 {q_prev_fin.strftime('%b')}"
        
        return q_act_ini, q_act_fin, nom_act, q_prev_ini, q_prev_fin, nom_prev
    else:
        # Q2
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
st.sidebar.write("---")
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["📊 Dashboard", "🛏️ Habitaciones (Cupos)", "📝 Registro Diario", "📅 Asistencia", "💸 Caja & Gastos", "💰 Nómina (Admin)", "👤 Detalles", "⚙️ Configuración"])

# --- 1. DASHBOARD ---
if menu == "📊 Dashboard":
    st.title("📊 TABLERO DE CONTROL")
    
    # 1. Preparación de Datos
    today = pd.Timestamp(date.today())
    q_ini, q_fin, q_nom, q_prev_ini, q_prev_fin, q_prev_nom = get_quincena_dates(today)
    
    # Datos Producción
    df = st.session_state.data.copy()
    if not df.empty:
        df['Fecha'] = pd.to_datetime(df['Fecha'])
        df_act = df[(df['Fecha'] >= q_ini) & (df['Fecha'] <= q_fin)]
        df_prev = df[(df['Fecha'] >= q_prev_ini) & (df['Fecha'] <= q_prev_fin)]
        total_act = df_act['Total_USD'].sum()
        
        # Calcular Top Model
        if not df_act.empty:
            top_model_row = df_act.groupby('Nickname')['Total_USD'].sum()
            if not top_model_row.empty:
                top_model_name = top_model_row.idxmax()
                top_model_val = top_model_row.max()
            else:
                top_model_name = "N/A"; top_model_val = 0
        else:
             top_model_name = "N/A"; top_model_val = 0
    else:
        df_act = pd.DataFrame(); total_act = 0; top_model_name = "N/A"; top_model_val = 0

    # Datos Asistencia (CORREGIDO - ROBUSTO)
    df_att = st.session_state.asistencia.copy()
    if not df_att.empty:
        df_att['Fecha'] = pd.to_datetime(df_att['Fecha'])
        # Normalizamos a fecha sin hora para comparaciones exactas
        df_att['Fecha_Date'] = df_att['Fecha'].dt.date
        q_ini_date = q_ini.date()
        q_fin_date = q_fin.date()
        q_prev_ini_date = q_prev_ini.date()
        q_prev_fin_date = q_prev_fin.date()
        today_date = today.date()
        
        # Filtro Inteligente: Busca "Falta", "No", "Sin Excusa" o la "X"
        # Esto soluciona el problema de sincronización si el texto guardado varía
        def es_falta(estado):
            estado_str = str(estado).lower()
            return "falta" in estado_str or "sin excusa" in estado_str or "❌" in estado_str
        
        # Faltas Hoy
        faltas_hoy = df_att[
            (df_att['Fecha_Date'] == today_date) & 
            (df_att['Estado'].apply(es_falta))
        ].shape[0]
        
        # Faltas Quincena Actual
        mask_q_act_att = (df_att['Fecha_Date'] >= q_ini_date) & (df_att['Fecha_Date'] <= q_fin_date)
        df_att_act = df_att[mask_q_act_att]
        faltas_q_act = df_att_act[df_att_act['Estado'].apply(es_falta)].shape[0]
        
        # Faltas Quincena Anterior
        mask_q_prev_att = (df_att['Fecha_Date'] >= q_prev_ini_date) & (df_att['Fecha_Date'] <= q_prev_fin_date)
        df_att_prev = df_att[mask_q_prev_att]
        faltas_q_prev = df_att_prev[df_att_prev['Estado'].apply(es_falta)].shape[0]
        
        days_passed = (today - q_ini).days + 1
        promedio_faltas = faltas_q_act / max(1, days_passed)
    else:
        faltas_hoy = 0; faltas_q_act = 0; faltas_q_prev = 0; promedio_faltas = 0; df_att_act = pd.DataFrame()

    # --- FILA 1: KPIs ---
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: 
        st.markdown(f"<div class='cyber-card glow'><h3 style='margin:0;color:#fff'>PRODUCCIÓN</h3><h2 style='color:#00f2ff;margin:5px 0'>$ {total_act:,.0f}</h2><p>{q_nom}</p></div>", unsafe_allow_html=True)
    with c2:
        delta_faltas = faltas_q_act - faltas_q_prev
        st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>FALTAS (Q)</h3><h2 style='color:#fff;margin:5px 0'>{faltas_q_act}</h2><p style='color:{'#f00' if delta_faltas>0 else '#0f0'}'>{delta_faltas:+d} vs Ant</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='cyber-card gold-glow'><h3 style='margin:0;color:#FFD700'>👑 TOP MODEL</h3><h2 style='color:#fff;margin:5px 0'>{top_model_name}</h2><p>$ {top_model_val:,.0f} USD</p></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>FALTAS HOY</h3><h2 style='color:#fff;margin:5px 0'>{faltas_hoy}</h2><p>Del día</p></div>", unsafe_allow_html=True)
    
    meta_global = sum([d.get('meta_quincenal', 0) for d in st.session_state.db_modelos.values()])
    avance_global = (total_act / meta_global * 100) if meta_global > 0 else 0
    with c5: 
        st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>META</h3><h2 style='color:#fff;margin:5px 0'>{avance_global:.1f}%</h2><p>DE ${meta_global:,.0f}</p></div>", unsafe_allow_html=True)

    # --- FILA 2: GRÁFICOS ---
    g1, g2 = st.columns([1, 1])
    with g1:
        st.subheader("🌐 PLATAFORMAS (Ganancias)")
        if not df_act.empty:
            pl = df_act.groupby('Pagina')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=False)
            figp = px.bar(pl, x='Pagina', y='Total_USD', text_auto='.0f', color='Total_USD', color_continuous_scale=['#222', '#D500F9'])
            figp.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0,r=0,t=0,b=0), coloraxis_showscale=False)
            st.plotly_chart(figp, use_container_width=True)
        else: st.info("Sin datos.")

    with g2:
        st.subheader("🏆 RANKING GANANCIAS")
        if not df_act.empty:
            rk_earn = df_act.groupby('Nickname')['Total_USD'].sum().reset_index().sort_values('Total_USD', ascending=True)
            figr = px.bar(rk_earn, x='Total_USD', y='Nickname', orientation='h', text_auto='.0f')
            figr.update_traces(marker_color='#00F2FF')
            figr.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', margin=dict(l=0,r=0,t=0,b=0), xaxis_title="USD", yaxis_title="")
            st.plotly_chart(figr, use_container_width=True)
        else: st.info("Sin datos.")

    # --- FILA 3: TABLAS DETALLADAS ---
    st.divider()
    r1, r2 = st.columns([2, 1])
    with r1:
        st.subheader("📊 PROGRESO DE METAS")
        data_ranking = []
        for nick, data in st.session_state.db_modelos.items():
            prod_mod = df_act[df_act['Nickname'] == nick]['Total_USD'].sum() if not df_act.empty else 0
            meta_mod = data.get('meta_quincenal', 1)
            pct = (prod_mod / meta_mod) if meta_mod > 0 else 0
            data_ranking.append({"Modelo": nick, "USD": prod_mod, "Meta": meta_mod, "Progreso": pct})
        
        df_rank = pd.DataFrame(data_ranking).sort_values("Progreso", ascending=False)
        st.dataframe(df_rank, column_config={"Progreso": st.column_config.ProgressColumn("Meta Alcanzada", format="%.1f%%", min_value=0, max_value=1), "USD": st.column_config.NumberColumn("Producido", format="$ %.2f"), "Meta": st.column_config.NumberColumn("Meta", format="$ %.0f")}, hide_index=True, use_container_width=True)

    with r2:
        st.subheader("⚠️ RANKING FALTAS")
        if not df_att_act.empty:
            # Reusamos la función de filtro
            faltas_rank = df_att_act[df_att_act['Estado'].apply(es_falta)].groupby("Nickname").size().reset_index(name="Faltas")
            faltas_rank = faltas_rank.sort_values("Faltas", ascending=False)
            st.dataframe(faltas_rank, hide_index=True, use_container_width=True, column_config={"Faltas": st.column_config.NumberColumn("Cant. Faltas")})
        else:
            st.success("¡Sin faltas esta quincena!")

# --- 2. HABITACIONES (MATRIZ) ---
elif menu == "🛏️ Habitaciones (Cupos)":
    st.title("🛏️ MAPA DE OCUPACIÓN SEMANAL")
    st.markdown("Visualización de cupos asignados por Jornada.")
    html = """
    <table class="occupancy-table">
        <thead>
            <tr>
                <th style="width:10%;">HAB</th>
                <th>🌅 MAÑANA<br><span style="font-size:0.7em; opacity:0.7;">06:00 - 14:00</span></th>
                <th>☀️ TARDE<br><span style="font-size:0.7em; opacity:0.7;">14:00 - 22:00</span></th>
                <th>🌙 NOCHE<br><span style="font-size:0.7em; opacity:0.7;">22:00 - 06:00</span></th>
            </tr>
        </thead>
        <tbody>
    """
    for r in range(1, 6):
        html += f"<tr><td style='font-size:1.5em; font-weight:bold; color:#00F2FF;'>{r}</td>"
        for turno in ["Mañana", "Tarde", "Noche"]:
            ocupante = None
            for nick, data in st.session_state.db_modelos.items():
                if data.get('habitacion') == r and data.get('turno') == turno:
                    ocupante = nick
                    break
            if ocupante: html += f"<td><div class='model-badge'><span class='model-name'>{ocupante}</span><span class='model-meta'>Asignada</span></div></td>"
            else: html += f"<td><span class='free-slot'>🟢 DISPONIBLE</span></td>"
        html += "</tr>"
    html += "</tbody></table>"
    st.markdown(html, unsafe_allow_html=True)
    st.info("ℹ️ Para asignar una modelo a un cupo libre, ve a **Configuración > Editar Modelo** y selecciona el turno y habitación correspondientes.")

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
                    if st.form_submit_button("GUARDAR"):
                        rg = []
                        for p, d in ip.items():
                            if d['v']>0:
                                u = d['v'] if d['t']=='usd' else d['v']*d['p']
                                rg.append({'Fecha':pd.to_datetime(fr), 'Nickname':ns, 'Nombre_Real':dt['nombre_real'], 'Documento':dt['documento'], 'Tipo_Modelo':dt['tipo'], 'Pagina':p, 'Tokens':d['v'] if d['t']=='tok' else 0, 'Valor_Token':d['p'] if d['t']=='tok' else 0, 'TRM_Registro':0, 'Total_USD':u})
                        if rg:
                            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame(rg)], ignore_index=True)
                            guardar_todo(); st.success("Ok"); st.rerun()
    with c2:
        st.subheader("EDICIÓN RÁPIDA")
        if not st.session_state.data.empty:
            edt = st.data_editor(st.session_state.data.sort_values('Fecha', ascending=False), column_config={"Borrar":st.column_config.CheckboxColumn("X"), "Total_USD":st.column_config.NumberColumn("USD", format="$ %.2f")}, num_rows="dynamic", key="me", height=600)
            if st.button("💾 CONFIRMAR CAMBIOS"): st.session_state.data = edt; guardar_todo(); st.success("Ok")

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
                            guardar_todo(); st.success("Ok"); st.rerun()
    with c2:
        st.subheader("Historial")
        if not st.session_state.asistencia.empty:
            sh = st.session_state.asistencia.sort_values('Fecha', ascending=False).head(15)
            sh['Fecha'] = sh['Fecha'].dt.date
            st.dataframe(sh[['Fecha', 'Nickname', 'Estado']], use_container_width=True, hide_index=True)
            
    with st.expander("✏️ CORREGIR HISTORIAL"):
        if not st.session_state.asistencia.empty:
            da = st.session_state.asistencia
            fd = st.date_input("Fecha", date.today(), key="fc")
            ds = da[da['Fecha'].dt.date == fd]
            if not ds.empty:
                st.dataframe(ds)
                with st.form("fcorr"):
                    me = st.selectbox("Modelo", ds['Nickname'].unique())
                    ns = st.selectbox("Estado", ["✅ Asistió", "⚠️ Excusa", "❌ Falta"])
                    if st.form_submit_button("Corregir"):
                        ix = st.session_state.asistencia[(st.session_state.asistencia['Fecha'].dt.date==fd)&(st.session_state.asistencia['Nickname']==me)].index
                        st.session_state.asistencia.at[ix[0], 'Estado'] = ns
                        guardar_todo(); st.rerun()

# --- 5. CAJA Y GASTOS ---
elif menu == "💸 Caja & Gastos":
    st.title("💸 CAJA MENOR")
    t1, t2 = st.tabs(["Nuevo", "Historial"])
    with t1:
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
            if st.form_submit_button("REGISTRAR"):
                ng = {"ID":str(uuid.uuid4())[:8], "Fecha":pd.to_datetime(fg), "Categoria":cg, "Descripcion":ds, "Monto":mg, "Modelo_Relacionado":mr if mr else "", "Es_Prestamo":es_p, "Cuotas_Totales":cu, "Cuotas_Pagadas":0, "Saldo_Pendiente":mg}
                st.session_state.gastos = pd.concat([st.session_state.gastos, pd.DataFrame([ng])], ignore_index=True)
                guardar_todo(); st.success("Ok"); st.rerun()
    with t2:
        if not st.session_state.gastos.empty:
            dg = st.session_state.gastos.copy(); dg['Fecha'] = pd.to_datetime(dg['Fecha']).dt.date
            st.dataframe(dg[['Fecha', 'Categoria', 'Monto', 'Modelo_Relacionado', 'Saldo_Pendiente']], use_container_width=True)

# --- 6. NÓMINA (PROTEGIDA) ---
elif menu == "💰 Nómina (Admin)":
    st.title("🔐 ZONA SEGURA: NÓMINA")
    pwd = st.text_input("Ingrese Contraseña", type="password")
    
    if pwd == PASSWORD_ADMIN:
        st.success("Acceso Autorizado")
        
        # RESUMEN GLOBAL
        st.markdown("### 🌐 ESTADO FINANCIERO DEL ESTUDIO")
        
        today = date.today()
        # Se llama a la función corregida, ignoramos las variables que no necesitamos con _
        qi, qf, _, _, _, _ = get_quincena_dates(pd.Timestamp(today))
        
        col_g1, col_g2, col_g3 = st.columns(3)
        g_ini = col_g1.date_input("Inicio Periodo", qi, key="gi")
        g_fin = col_g2.date_input("Fin Periodo", qf, key="gf")
        g_trm = col_g3.number_input("TRM PAGO", value=4100, step=10, key="gt")
        
        if not st.session_state.data.empty:
            df = st.session_state.data.copy(); df['Fecha'] = pd.to_datetime(df['Fecha'])
            dfg = df[(df['Fecha'].dt.date >= g_ini) & (df['Fecha'].dt.date <= g_fin)]
            
            if not dfg.empty:
                total_usd = dfg['Total_USD'].sum()
                total_bruto_cop = total_usd * g_trm
                
                # Nomina estimada
                nom_est = 0
                for nk in dfg['Nickname'].unique():
                    inf = st.session_state.db_modelos.get(nk, {})
                    pct = PORCENTAJE_SATELITE if inf.get('tipo') == "Satelite" else PORCENTAJE_PLANTA
                    pusd = dfg[dfg['Nickname'] == nk]['Total_USD'].sum()
                    pg = (pusd * g_trm) * (pct/100)
                    pg -= (pg * TASA_RETEFUENTE)
                    nom_est += pg
                
                # Gastos operativos
                gastos_op = 0
                if not st.session_state.gastos.empty:
                     dg = st.session_state.gastos.copy(); dg['Fecha'] = pd.to_datetime(dg['Fecha'])
                     gastos_op = dg[(dg['Fecha'].dt.date >= g_ini) & (dg['Fecha'].dt.date <= g_fin) & (dg['Categoria'] != 'Adelanto Modelo')]['Monto'].sum()
                
                gan = total_bruto_cop - nom_est - gastos_op
                
                k1, k2, k3 = st.columns(3)
                k1.metric("FACTURACIÓN BRUTA", f"${total_bruto_cop:,.0f} COP", f"${total_usd:,.2f} USD")
                k2.metric("NÓMINA TOTAL", f"${nom_est:,.0f} COP", delta_color="inverse")
                
                delta_color = "normal" if gan > 0 else "inverse"
                k3.metric("GANANCIA ESTUDIO", f"${gan:,.0f} COP", f"- ${gastos_op:,.0f} Gastos", delta_color=delta_color)
            else:
                st.info("Sin producción en este rango.")
        
        st.divider()
        st.markdown("### 🧾 LIQUIDACIÓN INDIVIDUAL")
        c1, c2 = st.columns([1, 2])
        with c1:
            np = st.selectbox("Modelo", sorted(list(st.session_state.db_modelos.keys())), key="ps")
            
            # Busqueda de prestamos
            cuota_sugerida = 0
            info_prestamo = ""
            if not st.session_state.gastos.empty:
                gas = st.session_state.gastos
                prests = gas[(gas['Es_Prestamo'] == True) & (gas['Modelo_Relacionado'] == np) & (gas['Saldo_Pendiente'] > 0)]
                for ix, row in prests.iterrows():
                    val_c = row['Monto']/row['Cuotas_Totales']
                    cuota_sugerida += val_c
                    info_prestamo += f"Cuota {int(row['Cuotas_Pagadas']+1)}/{int(row['Cuotas_Totales'])} "
            
            if cuota_sugerida > 0:
                st.warning(f"⚠️ DEBE CUOTA: ${cuota_sugerida:,.0f} ({info_prestamo})")
                if st.button("COBRAR Y ABONAR"):
                    for ix, row in prests.iterrows():
                        st.session_state.gastos.at[ix, 'Cuotas_Pagadas'] += 1
                        st.session_state.gastos.at[ix, 'Saldo_Pendiente'] -= (row['Monto']/row['Cuotas_Totales'])
                    guardar_todo(); st.success("Cobrado"); st.rerun()

            ded = st.number_input("Deducciones Finales", value=float(cuota_sugerida), step=10000.0)
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
                        st.download_button("Descargar", b, file_name=f"Pago_{np}.pdf")
            else: st.warning("Sin datos.")
    else: st.warning("Área restringida.")

# --- 7. DETALLES (MODEL DASHBOARD UPGRADED) ---
elif menu == "👤 Detalles":
    st.title("👤 CENTRO DE COMANDO")
    if st.session_state.db_modelos:
        cs, _ = st.columns([1, 3])
        with cs: nh = st.selectbox("Seleccionar Modelo", sorted(list(st.session_state.db_modelos.keys())), key="hs")
        dat = st.session_state.db_modelos[nh]
        
        # Obtenemos fechas
        qi, qf, qn, qpi, qpf, qpn = get_quincena_dates(pd.Timestamp(date.today()))
        
        # 1. ENCABEZADO PERFIL
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"### 💎 {dat['nombre_real']}")
        c2.metric("Tipo", dat['tipo']); c3.metric("Turno", dat.get('turno','-')); c4.metric("Meta Quincenal", f"${dat.get('meta_quincenal',0):,.0f}")
        st.divider()

        if not st.session_state.data.empty:
            df = st.session_state.data.copy(); df['Fecha'] = pd.to_datetime(df['Fecha'])
            
            # Filtros de datos
            df_mod = df[df['Nickname'] == nh]
            df_curr = df_mod[(df_mod['Fecha'] >= qi) & (df_mod['Fecha'] <= qf)]
            df_prev = df_mod[(df_mod['Fecha'] >= qpi) & (df_mod['Fecha'] <= qpf)]
            
            prod_curr = df_curr['Total_USD'].sum()
            prod_prev = df_prev['Total_USD'].sum()
            
            # --- 2. KPIS PRINCIPALES ---
            k1, k2, k3, k4 = st.columns(4)
            delta_prod = prod_curr - prod_prev
            
            with k1: 
                st.markdown(f"<div class='cyber-card glow'><h3 style='margin:0;color:#fff'>ACTUAL ({qn})</h3><h1 style='color:#00f2ff;margin:10px 0'>$ {prod_curr:,.0f}</h1><p style='color:{'#0f0' if delta_prod>=0 else '#f00'}'>{delta_prod:+.0f} vs {qpn}</p></div>", unsafe_allow_html=True)
            
            dias_trabajados = df_curr['Fecha'].dt.date.nunique()
            promedio = prod_curr / max(1, dias_trabajados)
            with k2:
                st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>PROMEDIO DIARIO</h3><h2 style='color:#fff;margin:10px 0'>$ {promedio:,.0f}</h2><p>En {dias_trabajados} días</p></div>", unsafe_allow_html=True)
                
            # Calcular Mejor Día (Histórico)
            if not df_mod.empty:
                best_day_row = df_mod.groupby('Fecha')['Total_USD'].sum().sort_values(ascending=False).head(1)
                if not best_day_row.empty:
                    bd_val = best_day_row.values[0]
                    bd_date = best_day_row.index[0].strftime('%d %b')
                else: bd_val=0; bd_date="-"
            else: bd_val=0; bd_date="-"
            
            with k3:
                st.markdown(f"<div class='cyber-card gold-glow'><h3 style='margin:0;color:#FFD700'>RÉCORD DIARIO</h3><h2 style='color:#fff;margin:10px 0'>$ {bd_val:,.0f}</h2><p>{bd_date}</p></div>", unsafe_allow_html=True)

            mt = dat.get('meta_quincenal', 1)
            avance = (prod_curr / mt * 100) if mt > 0 else 0
            with k4:
                st.markdown(f"<div class='cyber-card'><h3 style='margin:0;color:#aaa'>META</h3><h2 style='color:#fff;margin:10px 0'>{avance:.1f}%</h2><p>Faltan: ${max(0, mt-prod_curr):,.0f}</p></div>", unsafe_allow_html=True)

            # --- 3. GRÁFICO COMPARATIVO (EVOLUCIÓN) ---
            st.subheader("📈 EVOLUCIÓN COMPARATIVA (Día a Día)")
            
            # Preparamos datos para superponer líneas (Día 1 a 15 de la quincena)
            def preparar_evolucion(dframe, label):
                if dframe.empty: return pd.DataFrame()
                # Extraer el día relativo de la quincena (1-15)
                dframe['Dia_Q'] = dframe['Fecha'].apply(lambda x: x.day if x.day <= 15 else x.day - 15)
                # Agrupar por día relativo
                grp = dframe.groupby('Dia_Q')['Total_USD'].sum().reset_index()
                grp['Periodo'] = label
                return grp
            
            ev_curr = preparar_evolucion(df_curr, f"Actual ({qn})")
            ev_prev = preparar_evolucion(df_prev, f"Anterior ({qpn})")
            
            if not ev_curr.empty or not ev_prev.empty:
                df_ev = pd.concat([ev_curr, ev_prev])
                fig_ev = px.line(df_ev, x="Dia_Q", y="Total_USD", color="Periodo", markers=True, 
                                 color_discrete_map={f"Actual ({qn})": "#00F2FF", f"Anterior ({qpn})": "#888888"})
                fig_ev.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', xaxis_title="Día de la Quincena", yaxis_title="USD")
                st.plotly_chart(fig_ev, use_container_width=True)
            else:
                st.info("No hay suficientes datos para comparar evolución.")

            # --- 4. ANÁLISIS POR DÍA DE SEMANA Y PLATAFORMA ---
            g1, g2 = st.columns(2)
            
            with g1:
                st.subheader("📅 MEJORES DÍAS (Histórico)")
                if not df_mod.empty:
                    # Crear columna nombre día
                    # Mapeo para español
                    dias_es = {0:"Lunes", 1:"Martes", 2:"Miércoles", 3:"Jueves", 4:"Viernes", 5:"Sábado", 6:"Domingo"}
                    df_mod['Dia_Semana'] = df_mod['Fecha'].dt.dayofweek.map(dias_es)
                    
                    # Promedio por día
                    day_perf = df_mod.groupby('Dia_Semana')['Total_USD'].mean().reindex(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]).reset_index()
                    
                    fig_d = px.bar(day_perf, x="Dia_Semana", y="Total_USD", title="Promedio de Ganancias por Día", text_auto='.0f')
                    fig_d.update_traces(marker_color='#D500F9')
                    fig_d.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white')
                    st.plotly_chart(fig_d, use_container_width=True)
            
            with g2:
                st.subheader("🌐 MIX DE PLATAFORMAS (Actual)")
                if not df_curr.empty:
                    plat_mix = df_curr.groupby('Pagina')['Total_USD'].sum().reset_index()
                    fig_p = px.pie(plat_mix, values='Total_USD', names='Pagina', hole=0.4, title=f"Distribución {qn}")
                    fig_p.update_traces(textinfo='percent+label')
                    fig_p.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font_color='white', showlegend=False)
                    st.plotly_chart(fig_p, use_container_width=True)
                else: st.info("Sin datos esta quincena.")
                
            # --- 5. TABLAS DE DATOS ---
            t1, t2 = st.tabs(["📄 Historial Producción", "📅 Historial Asistencia"])
            with t1: st.dataframe(df_mod.sort_values('Fecha', ascending=False)[['Fecha', 'Pagina', 'Total_USD', 'Tokens']], use_container_width=True)
            with t2: 
                if not st.session_state.asistencia.empty:
                    das = st.session_state.asistencia
                    st.dataframe(das[das['Nickname']==nh].sort_values('Fecha', ascending=False)[['Fecha', 'Estado', 'Observacion']], use_container_width=True)
        else: st.warning("No hay datos de producción registrados.")
    else: st.info("No hay modelos registradas.")

# --- 8. CONFIGURACIÓN ---
elif menu == "⚙️ Configuración":
    st.title("⚙️ ADMIN")
    t1, t2 = st.tabs(["Editar", "Crear"])
    with t1:
        if st.session_state.db_modelos:
            md = st.selectbox("Sel", sorted(list(st.session_state.db_modelos.keys())))
            d = st.session_state.db_modelos[md]
            with st.form("ed"):
                c1, c2 = st.columns(2)
                nm = c1.text_input("Nombre", d['nombre_real']); dc = c1.text_input("Doc", d['documento']); mt = c1.number_input("Meta", value=d.get('meta_quincenal', 0))
                ix = 0 if d['tipo']=="Planta" else 1
                tp = c2.radio("Tipo", ["Planta", "Satelite"], index=ix, horizontal=True)
                tn = c2.selectbox("Turno", TURNOS, index=TURNOS.index(d.get('turno','Mañana')) if d.get('turno') in TURNOS else 0)
                pl = c2.multiselect("Plats", PLATAFORMAS_MAESTRAS, default=d.get('plataformas', []))
                rm = c2.number_input("Room", 0, 5, d.get('habitacion', 0))
                if st.form_submit_button("Guardar"):
                    st.session_state.db_modelos[md] = {"nombre_real": nm, "documento": dc, "tipo": tp, "turno": tn, "plataformas": pl, "meta_quincenal": mt, "habitacion": rm}
                    guardar_todo(); st.success("Ok"); st.rerun()
    with t2:
        with st.form("nw"):
            c1, c2 = st.columns(2)
            nk = c1.text_input("Nick"); nm = c1.text_input("Nombre"); dc = c1.text_input("Doc"); mt = c1.number_input("Meta")
            tp = c2.radio("Tipo", ["Planta", "Satelite"], horizontal=True); tn = c2.selectbox("Turno", TURNOS); pl = c2.multiselect("Plats", PLATAFORMAS_MAESTRAS); rm = c2.number_input("Room", 0, 5)
            if st.form_submit_button("Crear"):
                if nk:
                    st.session_state.db_modelos[nk] = {"nombre_real": nm, "documento": dc, "tipo": tp, "turno": tn, "plataformas": pl, "meta_quincenal": mt, "habitacion": rm}
                    guardar_todo(); st.success("Ok"); st.rerun()