import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- ESTADO DE SESIÓN ---
# Esto evita que los datos se borren al refrescar o interactuar
if 'datos_listos' not in st.session_state:
    st.session_state.datos_listos = False
if 'df_historial' not in st.session_state:
    st.session_state.df_historial = pd.DataFrame()

# --- MOTOR DE DATOS MERCADO ---
@st.cache_data(ttl=3600)
def obtener_mercado(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not df.empty:
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            return df['Close'].dropna()
    except: return None
    return None

dolar = obtener_mercado("CLP=X")
sp500 = obtener_mercado("^GSPC")

# --- LÓGICA DE PROCESAMIENTO (CALLBACK) ---
def procesar_excel():
    if st.session_state.archivo_subido is not None:
        try:
            df = pd.read_excel(st.session_state.archivo_subido, skiprows=7)
            df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df.columns = ['Fecha', 'Cuota_C', 'Cuota_D', 'Cuota_E']
            df['Fecha_dt'] = pd.to_datetime(df['Fecha'])
            
            # Evaluación IA (Dólar vs S&P 500)
            d_h, d_a = float(dolar.iloc[-1]), float(dolar.iloc[-5])
            s_h, s_a = float(sp500.iloc[-1]), float(sp500.iloc[-5])
            sug = "C" if d_h > d_a and s_h > s_a else ("E" if d_h < d_a and s_h < s_a else "D")
            
            df['Sugerencia_IA'] = sug
            st.session_state.df_historial = df.sort_values('Fecha_dt')
            st.session_state.datos_listos = True
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro")

# SIDEBAR
with st.sidebar:
    st.header("📂 Cargar Historial")
    st.file_uploader(
        "Sube el Excel de Planvital", 
        type=["xlsx"], 
        key="archivo_subido", 
        on_change=procesar_excel # Aquí está el truco para romper el loop
    )
    if st.session_state.datos_listos:
        st.success("✅ Datos sincronizados")
        if st.button("Limpiar datos"):
            st.session_state.datos_listos = False
            st.rerun()

# --- GRÁFICOS ---
if st.session_state.datos_listos:
    df_p = st.session_state.df_historial
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
    for f in ["C", "D", "E"]:
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p[f'Cuota_{f}'], name=f"Fondo {f}", 
                                 line=dict(color=colores[f], width=2)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['Sugerencia_IA'], mode="markers+text", 
                             text=df_p['Sugerencia_IA'], textposition="top center", name="Sugerencia IA",
                             marker=dict(size=10, color="white")), row=2, col=1)

    fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b", row=2, col=1)
    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified")
    fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("👈 Sube tu archivo Excel en el panel izquierdo para comenzar el análisis.")
