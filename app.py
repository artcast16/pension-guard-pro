import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE MERCADO RESILIENTE ---
@st.cache_data(ttl=3600)
def obtener_data(ticker):
    try:
        df = yf.download(ticker, period="1mo", interval="1d", progress=False)['Close']
        if isinstance(df, pd.DataFrame): df = df.iloc[:, 0]
        return df.dropna()
    except: return pd.Series()

# Captura de datos
dolar = obtener_data("CLP=X")
sp500 = obtener_data("^GSPC")
cobre = obtener_data("HG=F")
ipsa = obtener_data("^IPSA")

# --- CÁLCULO DE IA SEGURO ---
def calcular_ia():
    try:
        if len(dolar) > 5 and len(sp500) > 5:
            d_h, d_a = float(dolar.iloc[-1]), float(dolar.iloc[-5])
            s_h, s_a = float(sp500.iloc[-1]), float(sp500.iloc[-5])
            if d_h > d_a and s_h > s_a: return "C", "FAVORABLE", "#28a745"
            if d_h < d_a and s_h < s_a: return "E", "CONSERVADOR", "#dc3545"
    except: pass
    return "D", "ESCENARIO MIXTO", "#ffc107"

f_sug, m_sug, c_sug = calcular_ia()

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

# Indicadores (Métricas) con protección contra IndexError
cols = st.columns(4)
for i, (nom, data) in enumerate([("Dólar", dolar), ("S&P 500", sp500), ("Cobre", cobre), ("IPSA", ipsa)]):
    if not data.empty:
        val = float(data.iloc[-1])
        # Solo calculamos delta si hay al menos 2 datos
        delta = val - float(data.iloc[-2]) if len(data) >= 2 else 0
        cols[i].metric(nom, f"{val:,.2f}", f"{delta:,.2f}" if delta != 0 else None)
    else:
        cols[i].metric(nom, "Sincronizando...")

# Recomendación
st.markdown(f"""<div style="background-color:{c_sug}; padding:15px; border-radius:10px; text-align:center; margin:10px 0; border:1px solid white;">
<h2 style="color:white; margin:0;">100% FONDO {f_sug}</h2><p style="color:white; margin:0;">{m_sug}</p></div>""", unsafe_allow_html=True)

# --- CARGA Y GRÁFICO INMEDIATO ---
st.sidebar.header("📂 DATOS")
archivo = st.sidebar.file_uploader("Subir Excel Planvital", type=["xlsx"])

if archivo:
    try:
        df = pd.read_excel(archivo, engine='openpyxl', skiprows=7)
        df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
        df.columns = ['Fecha', 'C', 'D', 'E']
        df['Fecha_dt'] = pd.to_datetime(df['Fecha'])
        df = df.sort_values('Fecha_dt')
        
        # Gráfico Robusto
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])
        colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        for f in ["C", "D", "E"]:
            fig.add_trace(go.Scatter(x=df['Fecha_dt'], y=df[f], name=f"Fondo {f}", 
                                     line=dict(color=colores[f], width=3)), row=1, col=1)
        
        # Marcador IA usando las fechas del Excel
        fig.add_trace(go.Scatter(x=df['Fecha_dt'], y=[f_sug]*len(df), mode="markers+text", 
                                 text=f_sug, textposition="top center", name="Sugerencia",
                                 marker=dict(size=10, symbol="diamond", color="white")), row=2, col=1)

        fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b")
        fig.update_layout(template="plotly_dark", height=600, hovermode="x unified", margin=dict(t=20, b=20))
        fig.update_yaxes(title_text="Valor ($)", row=1, col=1)
        fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error al procesar Excel: {e}")
else:
    st.info("👈 Sube el Excel para activar el Centinela.")
