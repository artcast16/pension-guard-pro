import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
DB_FILE = "data_pension.csv"
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

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

# --- LÓGICA DE RECOMENDACIÓN ---
def calcular_sugerencia():
    if dolar is not None and sp500 is not None and len(dolar) > 5:
        d_h, d_a = float(dolar.iloc[-1]), float(dolar.iloc[-5])
        s_h, s_a = float(sp500.iloc[-1]), float(sp500.iloc[-5])
        if d_h > d_a and s_h > s_a: return "C"
        elif d_h < d_a and s_h < s_a: return "E"
        return "D"
    return "D"

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

# Recomendación Actual (Siempre visible arriba)
sug_hoy = calcular_sugerencia()
color_alert = {"C": "success", "D": "warning", "E": "error"}
msj_alert = {"C": "ESCENARIO FAVORABLE", "D": "ESCENARIO MIXTO", "E": "ALERTA DE REFUGIO"}

st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {sug_hoy}")
if sug_hoy == "C": st.success(msj_alert["C"])
elif sug_hoy == "D": st.warning(msj_alert["D"])
else: st.error(msj_alert["E"])

# SIDEBAR
with st.sidebar:
    st.header("📂 Gestión de Datos")
    archivo_subido = st.file_uploader("Sube el Excel de Planvital", type=["xlsx"])
    
    if archivo_subido is not None:
        try:
            df = pd.read_excel(archivo_subido, skiprows=7)
            df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df.columns = ['Fecha', 'Cuota_C', 'Cuota_D', 'Cuota_E']
            df['Fecha_dt'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d')
            df['Sugerencia_IA'] = sug_hoy
            # GUARDADO FÍSICO PARA EVITAR EL LOOP
            df.to_csv(DB_FILE, index=False)
            st.success("✅ ¡Archivo guardado con éxito!")
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")
    
    if os.path.exists(DB_FILE):
        if st.button("🗑️ Borrar base de datos"):
            os.remove(DB_FILE)
            st.rerun()

# --- DESPLIEGUE DE GRÁFICOS ---
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha_dt'])
    df_p = df_p.sort_values('Fecha_dt')
    
    # Gráfico de dos pisos
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
    for f in ["C", "D", "E"]:
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p[f'Cuota_{f}'], name=f"Fondo {f}", 
                                 line=dict(color=colores[f], width=3)), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['Sugerencia_IA'], mode="markers+text", 
                             text=df_p['Sugerencia_IA'], textposition="top center", name="Historial IA",
                             marker=dict(size=12, symbol="square", color="white")), row=2, col=1)

    fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b", row=2, col=1)
    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified")
    fig.update_yaxes(title_text="Valor Cuota", row=1, col=1)
    fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("👈 El sistema no tiene datos. Por favor, carga el Excel una vez para activar los gráficos.")
