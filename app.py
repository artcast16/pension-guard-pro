import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
DB_FILE = "data_pension.csv"
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE MERCADO ---
@st.cache_data(ttl=3600)
def obtener_mercado():
    try:
        d = yf.download("CLP=X", period="1mo", interval="1d", progress=False)['Close']
        s = yf.download("^GSPC", period="1mo", interval="1d", progress=False)['Close']
        # Limpieza por si vienen con multi-índice
        d = d.iloc[:, 0] if isinstance(d, pd.DataFrame) else d
        s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        return d, s
    except: return None, None

dolar, sp500 = obtener_mercado()

# --- RECOMENDACIÓN ---
def calcular_sugerencia():
    if dolar is not None and sp500 is not None:
        d_h, d_a = float(dolar.iloc[-1]), float(dolar.iloc[-5])
        s_h, s_a = float(sp500.iloc[-1]), float(sp500.iloc[-5])
        if d_h > d_a and s_h > s_a: return "C", "ESCENARIO FAVORABLE", "success"
        if d_h < d_a and s_h < s_a: return "E", "ALERTA DE REFUGIO", "error"
    return "D", "ESCENARIO MIXTO", "warning"

f_sug, m_sug, t_alerta = calcular_sugerencia()

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

# Caja de recomendación destacada
st.markdown(f"""
<div style="background-color:{'#28a745' if t_alerta=='success' else '#dc3545' if t_alerta=='error' else '#ffc107'}; 
padding:20px; border-radius:10px; text-align:center;">
<h2 style="color:white; margin:0;">RECOMENDACIÓN: 100% FONDO {f_sug}</h2>
<p style="color:white; margin:0;">{m_sug}</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR (CARGA ROBUSTA)
with st.sidebar:
    st.header("📂 Carga de Datos")
    # El motor 'openpyxl' es necesario para archivos .xlsx
    archivo = st.file_uploader("Subir Excel Planvital", type=["xlsx"])
    if archivo:
        try:
            # Forzamos motor openpyxl y leemos
            df = pd.read_excel(archivo, engine='openpyxl', skiprows=7)
            df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df.columns = ['Fecha', 'C', 'D', 'E']
            # Normalizar fechas para que no se agrupen por mes
            df['Fecha_dt'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d')
            df['Sugerencia_IA'] = f_sug
            df.to_csv(DB_FILE, index=False)
            st.success("✅ Sincronizado Correctamente")
            st.rerun()
        except Exception as e:
            st.error(f"Error al procesar: {e}")

# --- GRÁFICO DIARIO ---
st.markdown("---")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha_dt'])
    df_p = df_p.sort_values('Fecha_dt')

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    # Piso 1: Fondos
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['C'], name="Fondo C", line=dict(color="#FF4B4B", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['D'], name="Fondo D", line=dict(color="#FFA500", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['E'], name="Fondo E", line=dict(color="#00FF00", width=3)), row=1, col=1)

    # Piso 2: IA (Letras)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['Sugerencia_IA'], mode="markers+text", 
                             text=df_p['Sugerencia_IA'], textposition="top center", name="Sugerencia",
                             marker=dict(size=12, symbol="square", color="white")), row=2, col=1)

    # CONFIGURACIÓN EJE X DIARIO
    fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b", tickangle=-45, row=2, col=1)
    fig.update_layout(template="plotly_dark", height=700, hovermode="x unified", showlegend=True)
    fig.update_yaxes(title_text="Valor ($)", row=1, col=1)
    fig.update_yaxes(title_text="Fondo", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Por favor, sube el archivo Excel para activar el historial gráfico.")
