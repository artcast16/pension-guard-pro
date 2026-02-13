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
def obtener_data(ticker, nombre):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        return data['Close'] if not data.empty else None
    except: return None

dolar = obtener_data("CLP=X", "Dólar")
sp500 = obtener_data("^GSPC", "S&P 500")
cobre = obtener_data("HG=F", "Cobre")
ipsa = obtener_data("^IPSA", "IPSA")

def evaluar_inteligente(d, s):
    if d is None or s is None: return "D", "Esperando datos...", "warning"
    sube_dolar = d.iloc[-1] > d.iloc[-5]
    sube_sp500 = s.iloc[-1] > s.iloc[-5]
    if sube_dolar and sube_sp500: return "C", "ESCENARIO FAVORABLE", "success"
    elif not sube_dolar and not sube_sp500: return "E", "ALERTA DE REFUGIO", "error"
    else: return "D", "ESCENARIO MIXTO", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)
st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

# --- MÉTRICAS ---
m1, m2, m3, m4 = st.columns(4)
def mostrar_metrica(col, titulo, data, es_moneda=True):
    if data is not None and len(data) >= 2:
        val = data.iloc[-1]
        delta = val - data.iloc[-2]
        p = "$" if es_moneda else ""
        col.metric(titulo, f"{p}{val:,.2f}", f"{delta:,.2f}")
    else: col.metric(titulo, "N/A")

mostrar_metrica(m1, "Dólar", dolar)
mostrar_metrica(m2, "Cobre", cobre)
mostrar_metrica(m3, "S&P 500", sp500, False)
mostrar_metrica(m4, "IPSA", ipsa, False)

# --- GRÁFICOS MERCADO ---
st.markdown("### 📊 Gráficos de Tendencia")
c1, c2 = st.columns(2)
def crear_grafico(data, titulo, color):
    fig = go.Figure(go.Scatter(x=data.index, y=data.values, line=dict(color=color, width=2)))
    fig.update_layout(height=250, margin=dict(l=0,r=0,t=30,b=0), template="plotly_dark", yaxis=dict(autorange=True))
    return fig

if dolar is not None: c1.plotly_chart(crear_grafico(dolar, "Dólar", "#00FFAA"), use_container_width=True)
if sp500 is not None: c2.plotly_chart(crear_grafico(sp500, "S&P 500", "#FF4B4B"), use_container_width=True)

# --- SIDEBAR: CARGA DE DATOS ---
with st.sidebar:
    st.header("📂 Cargar Datos")
    archivo_excel = st.file_uploader("Subir Excel Planvital", type=["xlsx"])
    
    if archivo_excel:
        try:
            df_nuevo = pd.read_excel(archivo_excel, skiprows=7)
            df_nuevo = df_nuevo[['Fechas', 'Fondo C', 'Fondo D', 'Fondo E']].dropna()
            df_nuevo.columns = ['Fecha', 'Cuota_C', 'Cuota_D', 'Cuota_E']
            # Normalización de fecha robusta
            df_nuevo['Fecha'] = pd.to_datetime(df_nuevo['Fecha']).dt.strftime('%d/%m/%Y')
            df_nuevo['Mi_Fondo'] = "D" 
            df_nuevo['Sugerencia_IA'] = f_sug
            
            if os.path.exists(DB_FILE):
                df_ex = pd.read_csv(DB_FILE)
                df_final = pd.concat([df_ex, df_nuevo]).drop_duplicates(subset=['Fecha'], keep='last')
            else: df_final = df_nuevo
            
            df_final.to_csv(DB_FILE, index=False)
            st.success("¡Excel procesado!")
            st.rerun()
        except Exception as e:
            st.error(f"Error al leer Excel: {e}")

    st.markdown("---")
    st.header("📝 Mi Posición")
    mi_f = st.radio("Fondo donde estoy hoy:", ["C", "D", "E"])
    if st.button("Marcar posición actual"):
        if os.path.exists(DB_FILE):
            df_m = pd.read_csv(DB_FILE)
            hoy_str = datetime.now().strftime('%d/%m/%Y')
            df_m.loc[df_m['Fecha'] == hoy_str, 'Mi_Fondo'] = mi_f
            df_m.to_csv(DB_FILE, index=False)
            st.success("Posición marcada")
            st.rerun()

# --- COMPARATIVA ---
st.markdown("---")
st.subheader("📈 Mi Realidad: Comparativa de Fondos")
if os.path.exists(DB_FILE):
    df_plot = pd.read_csv(DB_FILE)
    if not df_plot.empty:
        df_plot['Fecha_dt'] = pd.to_datetime(df_plot['Fecha'], format='%d/%m/%Y')
        df_plot = df_plot.sort_values('Fecha_dt')
        
        fig_comp = make_subplots(specs=[[{"secondary_y": True}]])
        cols = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        for f in ["C", "D", "E"]:
            c_name = f"Cuota_{f}"
            if c_name in df_plot.columns:
                fig_comp.add_trace(go.Scatter(x=df_plot['Fecha_dt'], y=df_plot[c_name], 
                                             name=f"Fondo {f}", line=dict(color=cols[f], width=3)), secondary_y=True)
        
        fig_comp.add_trace(go.Scatter(x=df_plot['Fecha_dt'], y=df_plot['Mi_Fondo'], 
                                     mode="markers+text", text=df_plot['Sugerencia_IA'],
                                     name="IA Sugirió", textfont=dict(color="white"),
                                     marker=dict(size=14, symbol="diamond", color="white", line=dict(width=2, color="black"))), secondary_y=False)
        
        fig_comp.update_layout(template="plotly_dark", height=600, hovermode="x unified",
                              legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        fig_comp.update_yaxes(title_text="Fondo Sugerido", secondary_y=False, categoryorder="array", categoryarray=["E", "D", "C"])
        fig_comp.update_yaxes(title_text="Valor Cuota ($)", secondary_y=True, autorange=True)
        
        st.plotly_chart(fig_comp, use_container_width=True)
