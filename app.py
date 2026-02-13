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

# --- FUNCIONES DE MERCADO ROBUSTAS ---
@st.cache_data(ttl=3600)
def obtener_data_robusta(ticker):
    try:
        # Intentamos descarga directa para evitar bloqueos
        df = yf.download(ticker, period="3mo", interval="1d", progress=False)
        if not df.empty:
            return df['Close']
        return None
    except: return None

# Captura de los 4 pilares
dolar = obtener_data_robusta("CLP=X")
sp500 = obtener_data_robusta("^GSPC")
cobre = obtener_data_robusta("HG=F")
ipsa = obtener_data_robusta("^IPSA")

def evaluar_inteligente(d, s):
    if d is None or s is None: return "D", "Esperando datos...", "warning"
    # Comparamos hoy vs hace 5 días hábiles
    sube_dolar = d.iloc[-1] > d.iloc[-5]
    sube_sp500 = s.iloc[-1] > s.iloc[-5]
    if sube_dolar and sube_sp500: return "C", "ESCENARIO FAVORABLE (RIESGO OK)", "success"
    elif not sube_dolar and not sube_sp500: return "E", "ALERTA DE REFUGIO (CONSERVADOR)", "error"
    else: return "D", "ESCENARIO MIXTO (CAUTELA)", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)
st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

# --- MÉTRICAS E INDICADORES (LOS 4) ---
st.markdown("---")
cols_met = st.columns(4)
def mostrar_metrica(col, titulo, data, es_moneda=True):
    if data is not None and len(data) >= 2:
        val = float(data.iloc[-1])
        delta = val - float(data.iloc[-2])
        p = "$" if es_moneda else ""
        col.metric(titulo, f"{p}{val:,.2f}", f"{delta:,.2f}")
    else: col.metric(titulo, "Buscando...", "0.00")

mostrar_metrica(cols_met[0], "💵 Dólar", dolar)
mostrar_metrica(cols_met[1], "🏗️ Cobre", cobre)
mostrar_metrica(cols_met[2], "🇺🇸 S&P 500", sp500, False)
mostrar_metrica(cols_met[3], "🇨🇱 IPSA", ipsa, False)

# --- GRÁFICOS DE INDICADORES (RECUADROS PEQUEÑOS) ---
st.markdown("### 📊 Panel de Indicadores")
g1, g2, g3, g4 = st.columns(4)
def mini_grafico(data, color):
    fig = go.Figure(go.Scatter(x=data.index, y=data.values, line=dict(color=color, width=1.5), fill='tozeroy'))
    fig.update_layout(height=150, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", 
                      xaxis=dict(visible=False), yaxis=dict(visible=False, autorange=True))
    return fig

if dolar is not None: g1.plotly_chart(mini_grafico(dolar, "#00FFAA"), use_container_width=True)
if cobre is not None: g2.plotly_chart(mini_grafico(cobre, "#FF7F50"), use_container_width=True)
if sp500 is not None: g3.plotly_chart(mini_grafico(sp500, "#FF4B4B"), use_container_width=True)
if ipsa is not None: g4.plotly_chart(mini_grafico(ipsa, "#00BFFF"), use_container_width=True)

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
            st.success("¡Sincronizado!")
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

# --- COMPARATIVA EVOLUCIONADA (DOS PISOS) ---
st.markdown("---")
st.subheader("📈 Análisis de Realidad: Valores vs Sugerencias")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    if not df_p.empty:
        df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha'], format='%d/%m/%Y')
        df_p = df_p.sort_values('Fecha_dt')
        
        # Creamos dos filas: una grande para valores y una pequeña para la IA
        fig_master = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.05, row_heights=[0.8, 0.2])
        
        c_fondos = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        # Fila 1: Valores Cuota
        for f in ["C", "D", "E"]:
            fig_master.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p[f'Cuota_{f}'], 
                                           name=f"Fondo {f}", line=dict(color=c_fondos[f], width=3)), row=1, col=1)
        
        # Fila 2: La sugerencia de la IA (como una línea de tiempo separada)
        fig_master.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['Sugerencia_IA'], 
                                       mode="markers+text", text=df_p['Sugerencia_IA'], 
                                       textposition="top center", name="Línea IA",
                                       marker=dict(size=12, symbol="square", color="white")), row=2, col=1)

        fig_master.update_layout(template="plotly_dark", height=700, showlegend=True, hovermode="x unified")
        fig_master.update_yaxes(title_text="Valor Cuota ($)", row=1, col=1, autorange=True)
        fig_master.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        
        st.plotly_chart(fig_master, use_container_width=True)
