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

# --- FUNCIONES DE MERCADO BLINDADAS ---
@st.cache_data(ttl=3600)
def obtener_dato_puro(ticker):
    try:
        data = yf.download(ticker, period="1mo", interval="1d", progress=False)
        if not data.empty:
            return data['Close']
        return None
    except: return None

# Captura de indicadores
dolar = obtener_dato_puro("CLP=X")
sp500 = obtener_dato_puro("^GSPC")
cobre = obtener_dato_puro("HG=F")
ipsa = obtener_dato_puro("^IPSA")

def evaluar_inteligente(d, s):
    try:
        if d is None or s is None or len(d) < 5 or len(s) < 5:
            return "D", "Esperando sincronización...", "warning"
        
        d_h, d_a = float(d.iloc[-1]), float(d.iloc[-5])
        s_h, s_a = float(s.iloc[-1]), float(s.iloc[-5])
        
        if d_h > d_a and s_h > s_a: return "C", "ESCENARIO FAVORABLE", "success"
        elif d_h < d_a and s_h < s_a: return "E", "ALERTA DE REFUGIO", "error"
        else: return "D", "ESCENARIO MIXTO", "warning"
    except: return "D", "Calculando...", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)
st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

# --- MÉTRICAS ---
st.markdown("---")
m_cols = st.columns(4)
def mostrar_metrica_segura(col, titulo, data, es_moneda=True):
    try:
        if data is not None and not data.empty and len(data) >= 2:
            val = float(data.iloc[-1])
            delta = val - float(data.iloc[-2])
            p = "$" if es_moneda else ""
            col.metric(titulo, f"{p}{val:,.2f}", f"{delta:,.2f}")
        else: col.metric(titulo, "N/A")
    except: col.metric(titulo, "Error Datos")

mostrar_metrica_segura(m_cols[0], "💵 Dólar", dolar)
mostrar_metrica_segura(m_cols[1], "🏗️ Cobre", cobre)
mostrar_metrica_segura(m_cols[2], "🇺🇸 S&P 500", sp500, False)
mostrar_metrica_segura(m_cols[3], "🇨🇱 IPSA", ipsa, False)

# --- PANEL DE INDICADORES ---
st.markdown("### 📊 Panel de Tendencias")
g_cols = st.columns(4)
def mini_graf(data, color, col_st):
    try:
        if data is not None and not data.empty:
            fig = go.Figure(go.Scatter(x=data.index, y=data.values, line=dict(color=color, width=1.5), fill='tozeroy'))
            fig.update_layout(height=120, margin=dict(l=0,r=0,t=0,b=0), template="plotly_dark", 
                              xaxis=dict(visible=False), yaxis=dict(visible=False, autorange=True))
            col_st.plotly_chart(fig, use_container_width=True)
    except: col_st.write("Gráfico no disponible")

mini_graf(dolar, "#00FFAA", g_cols[0])
mini_graf(cobre, "#FF7F50", g_cols[1])
mini_graf(sp500, "#FF4B4B", g_cols[2])
mini_graf(ipsa, "#00BFFF", g_cols[3])

# --- SIDEBAR ---
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

# --- EL GRÁFICO DE DOS PISOS (TU IDEA) ---
st.markdown("---")
st.subheader("📈 Mi Realidad: Valores vs Sugerencias")
if os.path.exists(DB_FILE):
    df_p = pd.read_csv(DB_FILE)
    if not df_p.empty:
        df_p['Fecha_dt'] = pd.to_datetime(df_p['Fecha'], format='%d/%m/%Y')
        df_p = df_p.sort_values('Fecha_dt')
        
        # Subplots: Fila 1 para valores (80%), Fila 2 para la IA (20%)
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.8, 0.2])
        c_f = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        # Piso 1: Gráfico de Dinero
        for f in ["C", "D", "E"]:
            fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p[f'Cuota_{f}'], name=f"Fondo {f}", 
                                     line=dict(color=c_f[f], width=3)), row=1, col=1)
        
        # Piso 2: Gráfico de IA (Letras)
        fig.add_trace(go.Scatter(x=df_p['Fecha_dt'], y=df_p['Sugerencia_IA'], mode="markers+text", 
                                 text=df_p['Sugerencia_IA'], textposition="top center", name="Sugerencia IA",
                                 marker=dict(size=14, symbol="square", color="white", line=dict(width=2, color="black"))), row=2, col=1)

        fig.update_layout(template="plotly_dark", height=700, hovermode="x unified", legend=dict(orientation="h", y=1.1))
        fig.update_yaxes(title_text="Valor Cuota ($)", row=1, col=1, autorange=True)
        fig.update_yaxes(title_text="IA", row=2, col=1, categoryorder="array", categoryarray=["E", "D", "C"])
        st.plotly_chart(fig, use_container_width=True)
