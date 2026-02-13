import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
DB_FILE = "data_pension.csv"
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE MERCADO (TRABAJANDO EN SEGUNDO PLANO) ---
@st.cache_data(ttl=3600)
def obtener_sugerencia():
    try:
        d = yf.download("CLP=X", period="5d", progress=False)['Close']
        s = yf.download("^GSPC", period="5d", progress=False)['Close']
        d_h, d_a = float(d.iloc[-1]), float(d.iloc[0])
        s_h, s_a = float(s.iloc[-1]), float(s.iloc[0])
        if d_h > d_a and s_h > s_a: return "C", "ESCENARIO FAVORABLE", "#28a745"
        if d_h < d_a and s_h < s_a: return "E", "ALERTA DE REFUGIO", "#dc3545"
        return "D", "ESCENARIO MIXTO", "#ffc107"
    except:
        return "D", "SINCRONIZANDO...", "#6c757d"

f_sug, m_sug, color_sug = obtener_sugerencia()

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

# Recomendación fija
st.markdown(f"""
<div style="background-color:{color_sug}; padding:20px; border-radius:10px; text-align:center; border: 2px solid white;">
<h1 style="color:white; margin:0;">100% FONDO {f_sug}</h1>
<p style="color:white; margin:0; font-size:1.2em;">{m_sug}</p>
</div>
""", unsafe_allow_html=True)

# SIDEBAR CON TRIGGER
with st.sidebar:
    st.header("📂 CARGA DE DATOS")
    archivo = st.file_uploader("Subir Excel Planvital", type=["xlsx"])
    
    if archivo:
        if st.button("📥 1. PROCESAR ARCHIVO"):
            try:
                df = pd.read_excel(archivo, engine='openpyxl', skiprows=7)
                df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
                df.columns = ['Fecha', 'C', 'D', 'E']
                df['Fecha_dt'] = pd.to_datetime(df['Fecha']).dt.strftime('%Y-%m-%d')
                df['IA'] = f_sug
                df.to_csv(DB_FILE, index=False)
                st.success("✅ ¡DATOS SINCRONIZADOS!")
            except Exception as e:
                st.error(f"Error: {e}")

    st.markdown("---")
    if os.path.exists(DB_FILE):
        st.info("Hay datos guardados en el sistema.")
        if st.button("🚀 2. GENERAR DASHBOARD"):
            st.rerun()
        if st.button("🗑️ BORRAR TODO"):
            os.remove(DB_FILE)
            st.rerun()

# --- ÁREA DE GRÁFICOS (EL DESPLIEGUE) ---
st.markdown("---")
if os.path.exists(DB_FILE):
    try:
        df_p = pd.read_csv(DB_FILE)
        df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha_dt'])
        df_p = df_p.sort_values('Fecha_dt')

        # Gráfico Robusto
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
        
        # Líneas de Fondos
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['C'], name="Fondo C", line=dict(color="#FF4B4B", width=4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['D'], name="Fondo D", line=dict(color="#FFA500", width=4)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['E'], name="Fondo E", line=dict(color="#00FF00", width=4)), row=1, col=1)

        # Línea de Sugerencia (IA)
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['IA'], mode="markers+text", 
                                 text=df_p['IA'], textposition="top center", name="IA",
                                 marker=dict(size=15, symbol="diamond", color="white")), row=2, col=1)

        # Forzar visualización de días (1 al 12 de feb, etc.)
        fig.update_xaxes(type='date', dtick="D1", tickformat="%d %b", tickangle=-45)
        fig.update_layout(template="plotly_dark", height=700, hovermode="x unified", legend=dict(orientation="h", y=1.1))
        fig.update_yaxes(title_text="Valor Cuota", row=1, col=1)
        fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error al graficar: {e}")
else:
    st.warning("⚠️ Esperando carga de datos. Usa el panel lateral para subir tu Excel.")
