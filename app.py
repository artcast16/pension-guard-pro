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

# --- FUNCIONES DE MERCADO ---
@st.cache_data(ttl=3600)
def obtener_dato_puro(ticker):
    try:
        # Descargamos el último mes de datos
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not data.empty:
            # Nos aseguramos de devolver una Serie limpia de precios de cierre
            return data['Close'].squeeze() 
        return None
    except: return None

# Captura de indicadores
dolar = obtener_dato_puro("CLP=X")
sp500 = obtener_dato_puro("^GSPC")
cobre = obtener_dato_puro("HG=F")
ipsa = obtener_dato_puro("^IPSA")

def evaluar_inteligente(d, s):
    # Si falta algún dato, devolvemos un estado neutral (D)
    if d is None or s is None or len(d) < 5 or len(s) < 5:
        return "D", "Esperando sincronización de mercados...", "warning"
    
    # Extraemos valores individuales para la comparación
    d_hoy, d_antes = float(d.iloc[-1]), float(d.iloc[-5])
    s_hoy, s_antes = float(s.iloc[-1]), float(s.iloc[-5])
    
    sube_dolar = d_hoy > d_antes
    sube_sp500 = s_hoy > s_antes
    
    if sube_dolar and sube_sp500: 
        return "C", "ESCENARIO FAVORABLE (RIESGO OK)", "success"
    elif not sube_dolar and not sube_sp500: 
        return "E", "ALERTA DE REFUGIO (CONSERVADOR)", "error"
    else: 
        return "D", "ESCENARIO MIXTO (CAUTELA)", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)
st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

# --- MÉTRICAS (LOS 4 INDICADORES) ---
st.markdown("---")
m_cols = st.columns(4)
def mostrar_metrica(col, titulo, data, es_moneda=True):
    if data is not None and len(data) >= 2:
        val = float(data.iloc[-1])
        delta = val - float(data.iloc[-2])
        p = "$" if es_moneda else ""
        col.metric(titulo, f"{p}{val:,.2f}", f"{delta:,.2f}")
    else: col.metric(titulo, "N/A")

mostrar_metrica(m_cols[0], "💵 Dólar", dolar)
mostrar_metrica(m_cols[1], "🏗️ Cobre", cobre)
mostrar_metrica(m_cols[2], "🇺🇸 S&P 500", sp500, False)
mostrar_metrica(m_cols[3], "🇨🇱 IPSA", ipsa, False)

# --- PANEL DE MINI GRÁFICOS ---
st.markdown("### 📊 Panel de Indicadores")
g1, g2, g3, g4 = st.columns(4)
def mini_graf(data, color):
    if data is None: return None
    fig = go.Figure(go.Scatter(x=data.index, y=data.values, line=dict(color=color, width=1.5), fill='tozeroy'))
    fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", 
                      xaxis=dict(visible=False), yaxis=dict(visible=False, autorange=True))
    return fig

if dolar is not None: g1.plotly_chart(mini_graf(dolar, "#00FFAA"), use_container_width=True)
if cobre is not None: g2.plotly_chart(mini_graf(cobre, "#FF7F50"), use_container_width=True)
if sp500 is not None: g3.plotly_chart(mini_graf(sp500, "#FF4B4B"), use_container_width=True)
if ipsa is not None: g4.plotly_chart(mini_graf(ipsa, "#00BFFF"), use_container_width=True)

# --- SIDEBAR: CARGA DE DATOS ---
with st.sidebar:
    st.header("📂 Datos Planvital")
    archivo_excel = st.file_uploader("Subir Excel", type=["xlsx"])
    if archivo_excel:
        try:
            df_nuevo = pd.read_excel(archivo_excel, skiprows=7)
            df_nuevo = df_nuevo[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df_nuevo.columns = ['Fecha', 'Cuota_C', 'Cuota_D', 'Cuota_E']
            df_nuevo['Fecha'] = pd.to_datetime(df_nuevo['Fecha']).dt.strftime('%d/%m/%Y')
            df_nuevo['Mi_Fondo'] = "D" 
            df_nuevo['Sugerencia_IA'] = f_sug
            if os.path.exists(DB_FILE):
                df_ex = pd.read_csv(DB_FILE)
                df_final = pd.concat([df_ex, df_nuevo]).drop_duplicates(subset=['Fecha'], keep='last')
            else: df_final = df_nuevo
            df_final.to_csv(DB_FILE, index=False)
            st.success("¡Datos actualizados!")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- COMPARATIVA DE DOS PISOS ---
st.markdown("---")
st.subheader("📈 Mi Realidad: Valores vs Sugerencias")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    if not df_p.empty:
        df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha'], format='%d/%m/%Y')
        df_p = df_p.sort_values('Fecha_dt')
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.75, 0.25])
        c_f = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        # Piso 1: Fondos
        for f in ["C", "D", "E"]:
            fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p[f'Cuota_{f}'], name=f"Fondo {f}", 
                                     line=dict(color=c_f[f], width=3)), row=1, col=1)
        
        # Piso 2: IA (Separado abajo)
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['Sugerencia_IA'], mode="markers+text", 
                                 text=df_p['Sugerencia_IA'], textposition="top center", name="Línea IA",
                                 marker=dict(size=12, symbol="square", color="white")), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=650, hovermode="x unified")
        fig.update_yaxes(title_text="Valor ($)", row=1, col=1, autorange=True)
        fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        st.plotly_chart(fig, use_container_width=True)
