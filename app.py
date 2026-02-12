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
def obtener_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        return data['Close'] if not data.empty and len(data) > 1 else None
    except: return None

def enviar_alerta_email(mensaje):
    try:
        msg = EmailMessage()
        msg.set_content(mensaje)
        msg['Subject'] = "🛡️ Alerta PensionGuard Pro"
        msg['From'] = MI_CORREO
        msg['To'] = MI_CORREO
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(MI_CORREO, MI_PASSWORD_APP)
            server.send_message(msg)
        return True
    except: return False

# --- DATOS ---
dolar = obtener_data("CLP=X")
cobre = obtener_data("HG=F")
sp500 = obtener_data("^GSPC")
ipsa = obtener_data("^IPSA")

# --- LÓGICA ---
def evaluar(d, s):
    if d is None or s is None: return "D", "Esperando datos...", "info"
    if d.iloc[-1] > d.iloc[-5] and s.iloc[-1] > s.iloc[-5]:
        return "C", "ESCENARIO FAVORABLE: Impulso en mercados.", "success"
    if d.iloc[-1] < d.iloc[-5] and s.iloc[-1] < s.iloc[-5]:
        return "E", "RIESGO DETECTADO: Sugerencia refugio en Fondo E.", "error"
    return "D", "ESCENARIO MIXTO: Mantener cautela.", "warning"

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
f_sug, m_sug, t_alerta = evaluar(dolar, sp500)

if t_alerta == "success": st.success(m_sug)
elif t_alerta == "warning": st.warning(m_sug)
else: st.error(m_sug)

st.info(f"💡 **Mix Sugerido:** 100% Fondo {f_sug}")

# MÉTRICAS
st.markdown("---")
m1, m2, m3, m4 = st.columns(4)
with m1:
    if dolar is not None: st.metric("Dólar", f"${dolar.iloc[-1]:.2f}", f"{dolar.iloc[-1]-dolar.iloc[-2]:.2f}")
with m2:
    if cobre is not None: st.metric("Cobre", f"US${cobre.iloc[-1]:.2f}", f"{cobre.iloc[-1]-cobre.iloc[-2]:.2f}")
with m3:
    if sp500 is not None: st.metric("S&P 500", f"{sp500.iloc[-1]:.0f}", f"{sp500.iloc[-1]-sp500.iloc[-2]:.2f}")
with m4:
    if ipsa is not None: st.metric("IPSA", f"{ipsa.iloc[-1]:.0f}", f"{ipsa.iloc[-1]-ipsa.iloc[-2]:.2f}")

# GRÁFICOS (4 Gráficos en 2 filas)
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
    f_act = st.radio("Fondo:", ["C", "D", "E"])
    if st.button("Guardar"):
        nuevo = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), f_act]], columns=["Fecha", "Fondo"])
        nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
        st.success("Listo")
