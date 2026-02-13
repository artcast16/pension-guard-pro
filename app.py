import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURACIÓN ---
DB_FILE = "movimientos_pensionado_v2.csv"
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE DATOS REPARADOR ---
@st.cache_data(ttl=3600)
def obtener_data_limpia(ticker):
    try:
        # Descargamos y aplanamos los datos para evitar el error de Yahoo Finance
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not df.empty:
            df = df[['Close']].copy()
            df.columns = ['Close'] # Forzamos nombre de columna simple
            return df['Close']
        return None
    except: return None

# Captura de los 4 indicadores
dolar = obtener_data_limpia("CLP=X")
cobre = obtener_data_limpia("HG=F")
sp500 = obtener_data_limpia("^GSPC")
ipsa = obtener_data_limpia("^IPSA")

def evaluar_inteligente(d, s):
    try:
        if d is None or s is None or len(d) < 5: return "D", "Sincronizando...", "warning"
        d_h, d_a = float(d.iloc[-1]), float(d.iloc[-5])
        s_h, s_a = float(s.iloc[-1]), float(s.iloc[-5])
        if d_h > d_a and s_h > s_a: return "C", "ESCENARIO FAVORABLE", "success"
        elif d_h < d_a and s_h < s_a: return "E", "ALERTA DE REFUGIO", "error"
        else: return "D", "ESCENARIO MIXTO", "warning"
    except: return "D", "Calculando...", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)

# --- MÉTRICAS ---
st.markdown("---")
m_cols = st.columns(4)
def metrica_robusta(col, titulo, data, es_moneda=True):
    try:
        if data is not None and len(data) >= 2:
            v, a = float(data.iloc[-1]), float(data.iloc[-2])
            p = "$" if es_moneda else ""
            col.metric(titulo, f"{p}{v:,.2f}", f"{v-a:,.2f}")
        else: col.metric(titulo, "N/A")
    except: col.metric(titulo, "S/D")

metrica_robusta(m_cols[0], "💵 Dólar", dolar)
metrica_robusta(m_cols[1], "🏗️ Cobre", cobre)
metrica_robusta(m_cols[2], "🇺🇸 S&P 500", sp500, False)
metrica_robusta(m_cols[3], "🇨🇱 IPSA", ipsa, False)

# --- PANEL DE TENDENCIAS (REPARADO) ---
st.markdown("### 📊 Panel de Tendencias")
g_cols = st.columns(4)
def dibujar_mini(data, color, col_st):
    if data is not None:
        fig = go.Figure(go.Scatter(x=data.index, y=data.values, line=dict(color=color, width=2), fill='tozeroy'))
        fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", 
                          xaxis=dict(visible=False), yaxis=dict(visible=False, autorange=True))
        col_st.plotly_chart(fig, use_container_width=True)

dibujar_mini(dolar, "#00FFAA", g_cols[0])
dibujar_mini(cobre, "#FF7F50", g_cols[1])
dibujar_mini(sp500, "#FF4B4B", g_cols[2])
dibujar_mini(ipsa, "#00BFFF", g_cols[3])

# --- SIDEBAR ---
with st.sidebar:
    st.header("📂 Datos Planvital")
    archivo = st.file_uploader("Subir Excel", type=["xlsx"])
    if archivo:
        try:
            df_n = pd.read_excel(archivo, skiprows=7)
            df_n = df_n[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df_n.columns = ['Fecha', 'Cuota_C', 'Cuota_D', 'Cuota_E']
            df_n['Fecha'] = pd.to_datetime(df_n['Fecha']).dt.strftime('%Y-%m-%d')
            df_n['Mi_Fondo'] = "D"
            df_n['Sugerencia_IA'] = f_sug
            if os.path.exists(DB_FILE):
                df_e = pd.read_csv(DB_FILE)
                df_f = pd.concat([df_e, df_n]).drop_duplicates(subset=['Fecha'], keep='last')
            else: df_f = df_n
            df_f.to_csv(DB_FILE, index=False)
            st.success("¡Sincronizado!")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- GRÁFICO DE DOS PISOS (REPARADO) ---
st.markdown("---")
st.subheader("📈 Mi Realidad: Valores vs Sugerencias")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    if not df_p.empty:
        df_p['Fecha'] = pd.to_datetime(df_p['Fecha'])
        df_p = df_p.sort_values('Fecha')
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.75, 0.25])
        colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        for f in ["C", "D", "E"]:
            fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p[f'Cuota_{f}'], name=f"Fondo {f}", 
                                     line=dict(color=colores[f], width=3), connectgaps=True), row=1, col=1)
        
        fig.add_trace(go.Scatter(x=df_p['Fecha'], y=df_p['Sugerencia_IA'], mode="markers+text", 
                                 text=df_p['Sugerencia_IA'], textposition="top center", name="IA",
                                 marker=dict(size=12, symbol="square", color="white")), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=600, margin=dict(t=30), hovermode="x unified")
        fig.update_yaxes(title_text="Valor ($)", row=1, col=1, autorange=True)
        fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        st.plotly_chart(fig, use_container_width=True)
