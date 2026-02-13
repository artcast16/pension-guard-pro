import streamlit as st
import yfinance as yf
import pandas as pd
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURACIÓN DE ARCHIVOS ---
DB_FILE = "movimientos_pensionado.csv"

st.set_page_config(page_title="PensionGuard Pro", layout="wide")

# --- FUNCIONES DE DATOS ---
@st.cache_data(ttl=3600)
def obtener_data(ticker, nombre):
    try:
        data = yf.Ticker(ticker).history(period="3mo")
        if not data.empty and len(data) > 1:
            return data['Close']
        return None
    except Exception:
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

st.info(f"💡 **Mix Sugerido Hoy:** 100% Fondo {f_sug}")

# --- MÉTRICAS ---
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

# --- GRÁFICOS DE MERCADO ---
st.markdown("### 📊 Gráficos de Tendencia")
c1, c2 = st.columns(2)

def crear_grafico(data, titulo, color):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data.index, y=data.values, mode='lines', line=dict(color=color, width=2)))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0), title=titulo,
                      yaxis=dict(autorange=True, fixedrange=False))
    return fig

with c1:
    if dolar is not None:
        st.plotly_chart(crear_grafico(dolar, "Evolución Dólar", "#00FFAA"), use_container_width=True)
with c2:
    if sp500 is not None:
        st.plotly_chart(crear_grafico(sp500, "Evolución S&P 500", "#FF4B4B"), use_container_width=True)

# --- SECCIÓN DE REALIDAD EVOLUCIONADA ---
st.markdown("---")
st.subheader("📈 Comparativa de Fondos vs. Sugerencia del Centinela")

if os.path.exists(DB_FILE):
    df_real = pd.read_csv(DB_FILE)
    if not df_real.empty:
        df_real['Fecha_dt'] = pd.to_datetime(df_real['Fecha'], format="%d/%m/%Y")
        df_real = df_real.sort_values('Fecha_dt')
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        colores = {"C": "#FF4B4B", "D": "#FFA500", "E": "#00FF00"}
        
        # Líneas de los Fondos
        for f in ["C", "D", "E"]:
            if f"Cuota_{f}" in df_real.columns:
                fig.add_trace(go.Scatter(x=df_real['Fecha'], y=df_real[f"Cuota_{f}"], 
                                         name=f"Fondo {f}", line=dict(color=colores[f], width=2)), secondary_y=True)

        # Marcadores de Mi Posición + Sugerencia IA
        fig.add_trace(go.Scatter(x=df_real['Fecha'], y=df_real['Mi_Fondo'], 
                                 name="Mi Posición (Letra=IA)", mode="markers+text",
                                 text=df_real['Sugerencia_IA'], textposition="top center",
                                 marker=dict(size=12, symbol="diamond", color="white")), secondary_y=False)

        fig.update_yaxes(title_text="Posición", secondary_y=False, tickvals=["C", "D", "E"])
        fig.update_yaxes(title_text="Valor Cuota ($)", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Ingresa los datos de los tres fondos en el panel lateral.")

# --- SIDEBAR (BITÁCORA PRO) ---
with st.sidebar:
    st.header("📝 Registro Avanzado")
    fecha_reg = st.date_input("Fecha:", datetime.now())
    
    st.write("Valor Cuota Planvital:")
    v_c = st.number_input("Fondo C ($)", min_value=0.0, format="%.2f")
    v_d = st.number_input("Fondo D ($)", min_value=0.0, format="%.2f")
    v_e = st.number_input("Fondo E ($)", min_value=0.0, format="%.2f")
    
    mi_f = st.radio("¿En qué fondo estabas ese día?", ["C", "D", "E"])
    
    if st.button("Guardar Datos"):
        nuevo = pd.DataFrame([[fecha_reg.strftime("%d/%m/%Y"), v_c, v_d, v_e, mi_f, f_sug]], 
                             columns=["Fecha", "Cuota_C", "Cuota_D", "Cuota_E", "Mi_Fondo", "Sugerencia_IA"])
        if os.path.exists(DB_FILE):
            df_ex = pd.read_csv(DB_FILE)
            df_final = pd.concat([df_ex, nuevo]).drop_duplicates(subset=['Fecha'], keep='last')
        else:
            df_final = nuevo
        df_final.to_csv(DB_FILE, index=False)
        st.success("¡Datos guardados!")
        st.rerun()
