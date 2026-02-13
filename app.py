import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE MERCADO (LOS 4 INDICADORES) ---
@st.cache_data(ttl=3600)
def obtener_indicadores():
    datos = {}
    tickers = {"Dólar": "CLP=X", "S&P 500": "^GSPC", "Cobre": "HG=F", "IPSA": "^IPSA"}
    for nombre, t in tickers.items():
        try:
            df = yf.download(t, period="5d", progress=False)['Close']
            datos[nombre] = df
        except: datos[nombre] = None
    return datos

mercado = obtener_indicadores()

# --- RECOMENDACIÓN IA ---
def calcular_ia():
    try:
        d, s = mercado["Dólar"], mercado["S&P 500"]
        d_h, d_a = float(d.iloc[-1]), float(d.iloc[0])
        s_h, s_a = float(s.iloc[-1]), float(s.iloc[0])
        if d_h > d_a and s_h > s_a: return "C", "FAVORABLE", "#28a745"
        if d_h < d_a and s_h < s_a: return "E", "CONSERVADOR", "#dc3545"
    except: pass
    return "D", "MIXTO", "#ffc107"

f_sug, m_sug, c_sug = calcular_ia()

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

# Fila de Indicadores (Los que pediste al inicio)
cols = st.columns(4)
for i, (nombre, data) in enumerate(mercado.items()):
    if data is not None:
        val = float(data.iloc[-1])
        delta = val - float(data.iloc[-2])
        cols[i].metric(nombre, f"{val:,.2f}", f"{delta:,.2f}")

# Caja de Recomendación
st.markdown(f"""<div style="background-color:{c_sug}; padding:15px; border-radius:10px; text-align:center; margin-top:10px;">
<h2 style="color:white; margin:0;">100% FONDO {f_sug} ({m_sug})</h2></div>""", unsafe_allow_html=True)

# --- CARGA Y GRÁFICO (TODO EN UNO) ---
st.sidebar.header("📂 DATOS")
archivo = st.sidebar.file_uploader("Subir Excel Planvital", type=["xlsx"])

if archivo:
    try:
        # Procesamiento ultra-veloz
        df = pd.read_excel(archivo, engine='openpyxl', skiprows=7)
        df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
        df.columns = ['Fecha', 'C', 'D', 'E']
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha_dt')
        
        # Gráfico de dos pisos (Filtro por días)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        
        # Fondos
        colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        for f in ["C", "D", "E"]:
            fig.add_trace(go.Scatter(x=df['Fecha_dt'], y=df[f], name=f"Fondo {f}", 
                                     line=dict(color=colores[f], width=3)), row=1, col=1)
        
        # IA separada abajo
        fig.add_trace(go.Scatter(x=df['Fecha_dt'], y=[f_sug]*len(df), mode="markers+text", 
                                 text=f_sug, textposition="top center", name="Sugerencia",
                                 marker=dict(size=12, symbol="diamond", color="white")), row=2, col=1)

        # Forzar visualización de días exactos (Eje X limpio)
        fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b", tickangle=-45)
        fig.update_layout(template="plotly_dark", height=600, margin=dict(t=20, b=20), hovermode="x unified")
        fig.update_yaxes(title_text="Valor Cuota", row=1, col=1)
        fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("⚠️ Sube el Excel para ver el gráfico histórico.")
