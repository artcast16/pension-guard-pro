import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "movimientos_pensionado.csv"
HISTORIAL_SUGERENCIAS = "historial_sugerencias.csv"

st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- FUNCIONES DE DATOS ---
@st.cache_data(ttl=3600)
def obtener_data(ticker, nombre):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        return data['Close'] if not data.empty and len(data) > 1 else None
    except: return None

# --- OBTENCIÓN DE DATOS MERCADO ---
dolar = obtener_data("CLP=X", "Dólar")
sp500 = obtener_data("^GSPC", "S&P 500")
cobre = obtener_data("HG=F", "Cobre")
ipsa = obtener_data("^IPSA", "IPSA")

# --- LÓGICA DE ESTRATEGIA ---
def evaluar_inteligente(d, s):
    if d is None or s is None: return "D", "Esperando datos...", "warning"
    sube_dolar = d.iloc[-1] > d.iloc[-5]
    sube_sp500 = s.iloc[-1] > s.iloc[-5]
    if sube_dolar and sube_sp500: return "C", "ESCENARIO FAVORABLE", "success"
    elif not sube_dolar and not sube_sp500: return "E", "ALERTA DE REFUGIO", "error"
    else: return "D", "ESCENARIO MIXTO", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ PRINCIPAL ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)

st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

--- MÉTRICAS CON FLECHAS DE TENDENCIA ---
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)

def mostrar_metrica(col, titulo, data, es_moneda=True):
if data is not None and len(data) >= 2:
actual = data.iloc[-1]
anterior = data.iloc[-2]
delta = actual - anterior
prefijo = "$" if es_moneda else ""
col.metric(titulo, f"{prefijo}{actual:,.2f}", f"{delta:,.2f}")
else:
col.metric(titulo, "N/A")

with m1: mostrar_metrica(st, "Dólar", dolar)
with m2: mostrar_metrica(st, "Cobre", cobre)
with m3: mostrar_metrica(st, "S&P 500", sp500, False)
with m4: mostrar_metrica(st, "IPSA", ipsa, False)

--- GRÁFICOS DE MERCADO CON ZOOM ---
st.markdown("### 📊 Gráficos de Tendencia")
c1, c2 = st.columns(2)
with c1:
if dolar is not None:
st.markdown("Evolución Dólar (Últimos días)")
st.line_chart(dolar)
with c2:
if sp500 is not None:
st.markdown("Evolución S&P 500 (Wall Street)")
st.line_chart(sp500)

# --- SECCIÓN DE REALIDAD (TU GRÁFICO DE CORRELACIÓN) ---
st.markdown("---")
st.subheader("📈 Mi Realidad: Mi Fondo vs. Valor Cuota Planvital")

if os.path.exists(DB_FILE):
    df_real = pd.read_csv(DB_FILE)
    if not df_real.empty:
        # Mapeo para el gráfico
        mapping = {'E': 1, 'D': 2, 'C': 3}
        df_real['Nivel'] = df_real['Fondo'].map(mapping)
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=df_real['Fecha'], y=df_real['Nivel'], name="Mi Fondo", line=dict(color='orange', width=3, shape='hv')), secondary_y=False)
        fig.add_trace(go.Scatter(x=df_real['Fecha'], y=df_real['Valor_Cuota'], name="Valor Cuota ($)", line=dict(color='green', width=4)), secondary_y=True)
        
        fig.update_yaxes(title_text="Fondo", secondary_y=False, tickvals=[1, 2, 3], ticktext=["E", "D", "C"])
        fig.update_yaxes(title_text="Valor Cuota ($)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aún no hay datos en tu bitácora. Ingresa tu primer valor en el panel lateral.")

# --- SIDEBAR (BITÁCORA) ---
with st.sidebar:
    st.header("📝 Mi Bitácora")
    fecha_reg = st.date_input("Fecha del dato:", datetime.now())
    f_act = st.radio("Fondo en esa fecha:", ["C", "D", "E"])
    v_cuota = st.number_input("Valor Cuota Planvital ($):", min_value=0.0, step=0.01, format="%.2f")
    
    if st.button("Guardar Registro"):
        nuevo = pd.DataFrame([[fecha_reg.strftime("%d/%m/%Y"), f_act, v_cuota]], 
                             columns=["Fecha", "Fondo", "Valor_Cuota"])
        if os.path.exists(DB_FILE):
            df_ex = pd.read_csv(DB_FILE)
            df_final = pd.concat([df_ex, nuevo]).drop_duplicates(subset=['Fecha'], keep='last')
            df_final['tmp'] = pd.to_datetime(df_final['Fecha'], format="%d/%m/%Y")
            df_final = df_final.sort_values('tmp').drop(columns=['tmp'])
        else:
            df_final = nuevo
        df_final.to_csv(DB_FILE, index=False)
        st.success(f"Dato guardado.")
        st.rerun()

