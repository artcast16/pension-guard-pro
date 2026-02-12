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
except:
return None

# --- OBTENCIÓN DE DATOS MERCADO ---
dolar = obtener_data("CLP=X", "Dólar")
sp500 = obtener_data("^GSPC", "S&P 500")
cobre = obtener_data("HG=F", "Cobre")
ipsa = obtener_data("^IPSA", "IPSA")

# --- LÓGICA DE ESTRATEGIA ---
def evaluar_inteligente(d, s):
if d is None or s is None:
return "D", "Esperando datos...", "warning"
sube_dolar = d.iloc[-1] > d.iloc[-5]
sube_sp500 = s.iloc[-1] > s.iloc[-5]
if sube_dolar and sube_sp500:
return "C", "ESCENARIO FAVORABLE", "success"
elif not sube_dolar and not sube_sp500:
return "E", "ALERTA DE REFUGIO", "error"
else:
return "D", "ESCENARIO MIXTO", "warning"

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

# --- INTERFAZ PRINCIPAL ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

if t_alerta == "success":
st.success(m_sug)
elif t_alerta == "warning":
st.warning(m_sug)
else:
st.error(m_sug)

st.info(f"💡 Mix Sugerido Hoy: 100% Fondo {f_sug}")

# --- MÉTRICAS CON FLECHAS DE TENDENCIA ---
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

mostrar_metrica(m1, "Dólar", dolar)
mostrar_metrica(m2, "Cobre", cobre)
mostrar_metrica(m3, "S&P 500", sp500, False)
mostrar_metrica(m4, "IPSA", ipsa, False)

# --- GRÁFICOS DE MERCADO CON ZOOM ---
st.markdown("### 📊 Gráficos de Tendencia")
c1, c2 = st.columns(2)
with c1:
if dolar is not None:
st.markdown("Evolución Dólar (CLP)")
st.line_chart(dolar)
with c2:
if sp500 is not None:
st.markdown("Evolución S&P 500 (Wall Street)")
st.line_chart(sp500)

# --- SECCIÓN DE REALIDAD (GRÁFICO DE CORRELACIÓN) ---
st.markdown("---")
st.subheader("📈 Mi Realidad: Mi Fondo vs. Valor Cuota Planvital")

if os.path.exists(DB_FILE):
df_real = pd.read_csv(DB_FILE)
if not df_real.empty:
mapping = {'E': 1, 'D': 2, 'C': 3}
df_real['Nivel'] = df_real['Fondo'].map(mapping)

else:
st.info("Ingresa tu primer valor en el panel lateral para ver la correlación.")

# --- SIDEBAR (BITÁCORA) ---
with st.sidebar:
st.header("📝 Mi Bitácora")
fecha_reg = st.date_input("Fecha del dato:", datetime.now())
f_act = st.radio("Fondo en esa fecha:", ["C", "D", "E"])
v_cuota = st.number_input("Valor Cuota Planvital ($):", min_value=0.0, step=0.01, format="%.2f")
