import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
DB_FILE = "data_pension.csv"
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE MERCADO (SIMPLE Y RÁPIDO) ---
@st.cache_data(ttl=3600)
def obtener_sugerencia():
    try:
        # Descarga mínima para no ralentizar
        d = yf.download("CLP=X", period="5d", progress=False)['Close']
        s = yf.download("^GSPC", period="5d", progress=False)['Close']
        
        d_h, d_a = float(d.iloc[-1]), float(d.iloc[0])
        s_h, s_a = float(s.iloc[-1]), float(s.iloc[0])
        
        if d_h > d_a and s_h > s_a: return "C", "ESCENARIO FAVORABLE", "#28a745"
        if d_h < d_a and s_h < s_a: return "E", "ALERTA DE REFUGIO", "#dc3545"
        return "D", "ESCENARIO MIXTO", "#ffc107"
    except:
        return "D", "SINCRONIZANDO MERCADO...", "#6c757d"

f_sug, m_sug, color_sug = obtener_sugerencia()

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

# Caja de recomendación (Siempre visible)
st.markdown(f"""
<div style="background-color:{color_sug}; padding:20px; border-radius:10px; text-align:center;">
<h2 style="color:white; margin:0;">RECOMENDACIÓN: 100% FONDO {f_sug}</h2>
<p style="color:white; margin:0;">{m_sug}</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR (CARGA ULTRA-RÁPIDA)
with st.sidebar:
    st.header("📂 Carga de Datos")
    archivo = st.file_uploader("Subir Excel Planvital", type=["xlsx"])
    if archivo:
        try:
            # Procesar y guardar de inmediato
            df = pd.read_excel(archivo, engine='openpyxl', skiprows=7)
            df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df.columns = ['Fecha', 'C', 'D', 'E']
            df['Fecha_dt'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d')
            df['IA'] = f_sug
            df.to_csv(DB_FILE, index=False)
            st.success("✅ ¡Sincronizado! Los gráficos aparecerán abajo.")
            # No usamos rerun aquí para evitar el loop infinito
        except Exception as e:
            st.error(f"Error: {e}")

# --- DESPLIEGUE DE GRÁFICOS ---
st.markdown("---")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha_dt'])
    df_p = df_p.sort_values('Fecha_dt')

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
    
    # Fondos
    colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
    for f in ["C", "D", "E"]:
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p[f], name=f"Fondo {f}", 
                                 line=dict(color=colores[f], width=3)), row=1, col=1)

    # IA (Días del calendario)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['IA'], mode="markers+text", 
                             text=df_p['IA'], textposition="top center", name="Historial Sugerido",
                             marker=dict(size=12, symbol="square", color="white")), row=2, col=1)

    # Eje X configurado para días del 1 al 12 (o lo que traiga el excel)
    fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b", tickangle=-45)
    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified")
    fig.update_yaxes(title_text="Valor Cuota", row=1, col=1)
    fig.update_yaxes(title_text="Sugerencia", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("⚠️ Sin datos históricos. Sube el Excel para activar los gráficos.")
