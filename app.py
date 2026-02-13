import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- CONFIGURACIÓN ---
DB_FILE = "data_pension.csv"
st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- MOTOR DE CÁLCULO IA ---
@st.cache_data(ttl=3600)
def obtener_sugerencia_directa():
    try:
        d = yf.download("CLP=X", period="1mo", interval="1d", progress=False)['Close']
        s = yf.download("^GSPC", period="1mo", interval="1d", progress=False)['Close']
        
        # Aplanamos datos por si vienen con multi-índice
        d = d.iloc[:, 0] if isinstance(d, pd.DataFrame) else d
        s = s.iloc[:, 0] if isinstance(s, pd.DataFrame) else s
        
        d_hoy, d_antes = float(d.iloc[-1]), float(d.iloc[-5])
        s_hoy, s_antes = float(s.iloc[-1]), float(s.iloc[-5])
        
        if d_hoy > d_antes and s_hoy > s_antes: return "C", "ESCENARIO FAVORABLE", "success"
        if d_hoy < d_antes and s_hoy < s_antes: return "E", "ALERTA DE REFUGIO", "error"
        return "D", "ESCENARIO MIXTO", "warning"
    except:
        return "D", "SINCRONIZANDO MERCADOS", "info"

f_sug, m_sug, t_alerta = obtener_sugerencia_directa()

# --- INTERFAZ SUPERIOR ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

col_sug, col_info = st.columns([1, 2])
with col_sug:
    st.metric("RECOMENDACIÓN", f"100% FONDO {f_sug}")
with col_info:
    if t_alerta == "success": st.success(f"✅ {m_sug}")
    elif t_alerta == "warning": st.warning(f"⚠️ {m_sug}")
    elif t_alerta == "error": st.error(f"🚨 {m_sug}")
    else: st.info(m_sug)

# --- PANEL LATERAL (CARGA) ---
with st.sidebar:
    st.header("📂 Carga de Datos")
    archivo = st.file_uploader("Subir Excel Planvital", type=["xlsx"])
    if archivo:
        try:
            # Leemos el excel saltando las filas de encabezado de Planvital
            df = pd.read_excel(archivo, skiprows=7)
            # Buscamos las columnas por nombre exacto
            df = df[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df.columns = ['Fecha', 'C', 'D', 'E']
            # Guardamos
            df.to_csv(DB_FILE, index=False)
            st.success("¡Datos guardados!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al leer Excel: {e}")
    
    if os.path.exists(DB_FILE):
        if st.button("🗑️ Borrar Historial"):
            os.remove(DB_FILE)
            st.rerun()

# --- GRÁFICOS ---
st.markdown("---")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha'])
    df_p = df_p.sort_values('Fecha_dt')

    # Gráfico 1: Valores Cuota
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.07, row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['C'], name="Fondo C", line=dict(color="#FF4B4B", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['D'], name="Fondo D", line=dict(color="#FFA500", width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['E'], name="Fondo E", line=dict(color="#00FF00", width=3)), row=1, col=1)

    # Gráfico 2: Marcador de posición (Aquí usamos una línea simple para evitar errores)
    fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=[f_sug]*len(df_p), name="Sugerencia IA", 
                             mode="lines+markers", line=dict(dash='dash', color='white')), row=2, col=1)

    fig.update_layout(template="plotly_dark", height=600, hovermode="x unified", legend=dict(orientation="h", y=1.1))
    fig.update_yaxes(title_text="Valor Cuota ($)", row=1, col=1)
    fig.update_yaxes(title_text="Fondo", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("💡 Sube el Excel de Planvital para ver el historial de tus fondos.")
