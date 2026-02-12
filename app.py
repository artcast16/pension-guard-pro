with st.sidebar:
    st.header("📝 Mi Bitácora")
    
    # 1. Selección de Fecha (Por defecto hoy, pero editable)
    fecha_registro = st.date_input("Fecha del dato:", datetime.now())
    fecha_str = fecha_registro.strftime("%d/%m/%Y")
    
    # 2. Selección de Fondo
    f_act = st.radio("Fondo en esa fecha:", ["C", "D", "E"])
    
    # 3. Ingreso de Valor Cuota
    valor_cuota = st.number_input("Valor Cuota Planvital ($):", min_value=0.0, step=0.01, format="%.2f")
    
    if st.button("Guardar Registro"):
        nuevo = pd.DataFrame([[
            fecha_str, 
            f_act, 
            valor_cuota
        ]], columns=["Fecha", "Fondo", "Valor_Cuota"])
        
        # Guardar y ordenar para que el gráfico no se vuelva loco si ingresas fechas desordenadas
        if os.path.exists(DB_FILE):
            df_existente = pd.read_csv(DB_FILE)
            df_final = pd.concat([df_existente, nuevo]).drop_duplicates(subset=['Fecha'], keep='last')
            # Intentar ordenar por fecha real para que el gráfico sea coherente
            df_final['tmp_fecha'] = pd.to_datetime(df_final['Fecha'], format="%d/%m/%Y")
            df_final = df_final.sort_values('tmp_fecha').drop(columns=['tmp_fecha'])
        else:
            df_final = nuevo
            
        df_final.to_csv(DB_FILE, index=False)
        st.success(f"Dato del {fecha_str} guardado.")
