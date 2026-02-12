import streamlit as st
import yfinance as yf
import pandas as pd
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURACIÓN ---
MI_CORREO = "arturocast@gmail.com"
MI_PASSWORD_APP = "atyz mpvi eimd bydi"

st.set_page_config(page_title="PensionGuard Pro", layout="wide")
DB_FILE = "movimientos_pensionado.csv"

# --- FUNCIONES ---
@st.cache_data(ttl=3600)
def obtener_data(ticker, nombre):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        if not data.empty and len(data) > 1:
            return data['Close']
        else:
            st.caption(f"⚠️ {nombre}: No disponible en este momento.")
            return None
    except:
        st.caption(f"⚠️ {nombre}: Error de conexión.")
        return None

# --- OBTENCIÓN INDEPENDIENTE DE DATOS ---
dolar = obtener_data("CLP=X", "Dólar")
cobre = obtener_data("HG=F", "Cobre")
sp500 = obtener_data("^GSPC", "S&P 500")
ipsa = obtener_data("^IPSA", "IPSA")

# --- LÓGICA DE ESTRATEGIA ROBUSTA ---
def evaluar_inteligente(d, s):
    # Si faltan los datos base para decidir, sugerimos precaución (D)
    if d is None or s is None:
        return "D", "Sugerencia basada en datos parciales. Se recomienda cautela.", "warning"
    
    sube_dolar = d.iloc[-1] > d.iloc[-5]
    sube_sp500 = s.iloc[-1] > s.iloc[-5]
    
    if sube_dolar and sube_sp500:
        return "C", "ESCENARIO FAVORABLE: Impulso detectado en mercados internacionales.", "success"
    elif not sube_dolar and not sube_sp500:
        return "E", "ALERTA DE REFUGIO: Debilidad generalizada. Considerar Fondo E.", "error"
    else:
        return "D", "ESCENARIO MIXTO: Sin tendencia clara. Mantener equilibrio en Fondo D.", "warning"

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")

f_sug, m_sug, t_alerta = evaluar_inteligente(dolar, sp500)

if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)

st.info(f"💡 **Mix Sugerido:** 100% Fondo {f_sug}")

# MÉTRICAS
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)

with m1:
    if dolar is not None: 
        st.metric("Dólar", f"${dolar.iloc[-1]:.2f}", f"{(dolar.iloc[-1]-dolar.iloc[-2]):.2f}")
    else: st.metric("Dólar", "N/A")

with m2:
    if cobre is not None: 
        st.metric("Cobre", f"US${cobre.iloc[-1]:.2f}", f"{(cobre.iloc[-1]-cobre.iloc[-2]):.2f}")
    else: st.metric("Cobre", "N/A")

with m3:
    if sp500 is not None: 
        st.metric("S&P 500", f"{sp500.iloc[-1]:.0f}", f"{(sp500.iloc[-1]-sp500.iloc[-2]):.2f}")
    else: st.metric("S&P 500", "N/A")

with m4:
    if ipsa is not None: 
        st.metric("IPSA", f"{ipsa.iloc[-1]:.0f}", f"{(ipsa.iloc[-1]-ipsa.iloc[-2]):.2f}")
    else: st.metric("IPSA", "N/A")

# GRÁFICOS DINÁMICOS
st.markdown("---")
st.subheader("📊 Tendencias Pro")
c1, c2 = st.columns(2)

with c1:
    if dolar is not None:
        st.write("**Dólar (USD/CLP)**")
        st.line_chart(dolar)
    if sp500 is not None:
        st.write("**S&P 500 (Wall Street)**")
        st.line_chart(sp500)

with c2:
    if cobre is not None:
        st.write("**Cobre (Londres)**")
        st.line_chart(cobre)
    if ipsa is not None:
        st.write("**IPSA (Santiago)**")
        st.line_chart(ipsa)

# SIDEBAR
with st.sidebar:
    st.header("📝 Mi Bitácora")
    f_act = st.radio("Fondo actual:", ["C", "D", "E"])
    if st.button("Guardar Cambio"):
        nuevo = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), f_act]], columns=["Fecha", "Fondo"])
        nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
        st.success("Guardado en la nube.")
    if os.path.isfile(DB_FILE):
        st.divider()
        st.dataframe(pd.read_csv(DB_FILE).tail(5))
