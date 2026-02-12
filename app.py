import streamlit as st
import yfinance as yf
import pandas as pd
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime

# --- CONFIGURACIÓN DE SEGURIDAD ---
MI_CORREO = "arturocast@gmail.com"
MI_PASSWORD_APP = "atyz mpvi eimd bydi"

st.set_page_config(page_title="PensionGuard Pro", layout="wide")
DB_FILE = "movimientos_pensionado.csv"

# --- FUNCIÓN DE ENVÍO DE EMAIL ---
def enviar_alerta_email(mensaje_texto):
    try:
        msg = EmailMessage()
        msg.set_content(mensaje_texto)
        msg['Subject'] = "🛡️ ALERTA PensionGuard Pro: Acción Sugerida"
        msg['From'] = MI_CORREO
        msg['To'] = MI_CORREO
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(MI_CORREO, MI_PASSWORD_APP)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# --- OBTENCIÓN DE DATOS ---
@st.cache_data(ttl=3600)
def obtener_data(ticker):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        return data['Close'] if not data.empty and len(data) > 1 else None
    except: return None

dolar = obtener_data("CLP=X")
cobre = obtener_data("HG=F")
sp500 = obtener_data("^GSPC")
ipsa = obtener_data("^IPSA")

# --- LÓGICA DE ESTRATEGIA (C-D-E) ---
def evaluar_estrategia(d, c, s):
    if d is None or s is None: return "D", "Esperando datos...", "info"
    sube_dolar = d.iloc[-1] > d.iloc[-5]
    sube_sp500 = s.iloc[-1] > s.iloc[-5]
    if sube_dolar and sube_sp500:
        return "C", "OPORTUNIDAD: Mercados al alza y dólar fuerte.", "success"
    elif not sube_dolar and not sube_sp500:
        return "E", "REFUGIO: Caída generalizada. Proteger capital.", "error"
    else:
        return "D", "PRECAUCIÓN: Mercado volátil.", "warning"

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro: Centinela Arturo")
fondo_sugerido, analisis, tipo_alerta = evaluar_estrategia(dolar, cobre, sp500)

if tipo_alerta == "error": st.error(f"🚨 {analisis}")
elif tipo_alerta == "success": st.success(f"📈 {analisis}")
else: st.warning(f"⚠️ {analisis}")

st.info(f"💡 **Mix Sugerido:** 100% Fondo {fondo_sugerido}")

# MÉTRICAS
st.markdown("---")
cols = st.columns(4)
with cols[0]:
    if dolar is not None: st.metric("Dólar", f"${dolar.iloc[-1]:.2f}", f"{(dolar.iloc[-1]-dolar.iloc[-2]):.2f}")
with cols[1]:
    if cobre is not None: st.metric("Cobre", f"US${cobre.iloc[-1]:.2f}", f"{(cobre.iloc[-1]-cobre.iloc[-2]):.2f}")
with cols[2]:
    if sp500 is not None: st.metric("S&P 500", f"{sp500.iloc[-1]:.0f}", f"{(sp500.iloc[-1]-sp500.iloc[-2]):.2f}")
with cols[3]:
    if ipsa is not None: st.metric("IPSA (Chile)", f"{ipsa.iloc[-1]:.0f}", f"{(ipsa.iloc[-1]-ipsa.iloc[-2]):.2f}")

# --- GRÁFICOS (CORREGIDOS PARA LA NUBE) ---
st.markdown("---")
ca, cb = st.columns(2)
with ca:
    if dolar is not None:
        st.write("**Evolución Dólar**")
        st.line_chart(dolar) # Quitamos el color fijo para evitar el error de longitud
with cb:
    if cobre is not None:
        st.write("**Evolución Cobre**")
        st.line_chart(cobre)

# BARRA LATERAL
with st.sidebar:
    st.header("📝 Mi Bitácora Pro")
    f_dest = st.radio("Fondo actual:", ["C", "D", "E"])
    if st.button("Guardar Cambio"):
        nuevo = pd.DataFrame([[datetime.now().strftime("%d/%m/%Y"), f_dest]], columns=["Fecha", "Fondo"])
        nuevo.to_csv(DB_FILE, mode='a', header=not os.path.exists(DB_FILE), index=False)
        st.success("Guardado.")
    if os.path.isfile(DB_FILE):
        st.divider()
        st.dataframe(pd.read_csv(DB_FILE).tail(5))
