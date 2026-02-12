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
DB_FILE = "movimientos_pensionado.csv"
HISTORIAL_SUGERENCIAS = "historial_sugerencias.csv" # Nuevo archivo para el gráfico de pie

st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- FUNCIONES ---
@st.cache_data(ttl=3600)
def obtener_data(ticker, nombre):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        return data['Close'] if not data.empty and len(data) > 1 else None
    except: return None

# --- DATOS ---
dolar = obtener_data("CLP=X", "Dólar")
cobre = obtener_data("HG=F", "Cobre")
sp500 = obtener_data("^GSPC", "S&P 500")
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

# --- GUARDAR HISTORIAL DE SUGERENCIAS (Para el nuevo gráfico) ---
fecha_hoy = datetime.now().strftime("%d/%m")
if f_sug:
    try:
        if os.path.exists(HISTORIAL_SUGERENCIAS):
            df_h = pd.read_csv(HISTORIAL_SUGERENCIAS)
        else:
            df_h = pd.DataFrame(columns=["Fecha", "Fondo"])
        
        # Solo agregar si el último registro no es de hoy
        if df_h.empty or df_h.iloc[-1]["Fecha"] != fecha_hoy:
            nuevo_h = pd.DataFrame([[fecha_hoy, f_sug]], columns=["Fecha", "Fondo"])
            df_h = pd.concat([df_h, nuevo_h]).tail(10) # Mantener solo los últimos 10
            df_h.to_csv(HISTORIAL_SUGERENCIAS, index=False)
    except: pass

# --- INTERFAZ ---
st.title("🛡️ PensionGuard Pro")
st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

# (Mantener bloque de métricas y gráficos igual que el anterior...)
# ... [Aquí irían las métricas y gráficos que ya tienes] ...

# --- NUEVO GRÁFICO DE PIE: TENDENCIA DE RECOMENDACIONES ---
st.markdown("---")
st.subheader("📅 Estabilidad de Recomendaciones (Últimos 10 días)")

if os.path.exists(HISTORIAL_SUGERENCIAS):
    df_h = pd.read_csv(HISTORIAL_SUGERENCIAS)
    # Crear una fila de columnas para mostrar las letras
    cols_h = st.columns(10)
    indices = df_h.index.tolist()
    
    for i in range(10):
        with cols_h[i]:
            if i < len(indices):
                item = df_h.iloc[i]
                color = "green" if item['Fondo'] == "C" else "orange" if item['Fondo'] == "D" else "red"
                st.markdown(f"<div style='text-align: center; border: 1px solid #ddd; border-radius: 5px; padding: 5px;'><b>{item['Fecha']}</b><br><span style='color: {color}; font-size: 24px;'>{item['Fondo']}</span></div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='text-align: center; color: #ccc;'>-<br>--</div>", unsafe_allow_html=True)
else:
    st.write("El historial se empezará a construir a partir de hoy.")

# SIDEBAR (Igual que antes)
with st.sidebar:
    st.header("📝 Mi Bitácora")
    # ... [Resto del código del sidebar] ...
