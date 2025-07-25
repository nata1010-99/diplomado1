import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Colores institucionales
UST_BLUE = "#002855"
UST_YELLOW = "#FFD100"
UST_GRAY = "#F5F5F5"
UST_WHITE = "#FFFFFF"

# Estilos visuales
st.markdown(f"""
    <style>
    .main {{
        background-color: {UST_GRAY};
    }}
    .stApp {{
        background-color: {UST_WHITE};
        color: #000000;
        font-family: 'Segoe UI', sans-serif;
    }}
    .stButton>button {{
        background-color: {UST_YELLOW};
        color: black;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5em 1em;
    }}
    .stDownloadButton>button {{
        background-color: {UST_BLUE};
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5em 1em;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-weight: bold;
        background-color: {UST_WHITE};
        color: {UST_BLUE};
        border-radius: 6px 6px 0 0;
        border: 1px solid #CCC;
    }}
    </style>
""", unsafe_allow_html=True)


def show_transform_tab():
    st.title("📊 Dashboard Educativo: Modelo Estrella")

    if 'df_raw' not in st.session_state:
        st.warning("🔺 Primero debes cargar los datos desde la pestaña correspondiente.")
        return

    df = st.session_state['df_raw'].copy()

    tabla_deptos = (
        df.query("departamento != 'NACIONAL'")
        [['c_digo_departamento', 'departamento']]
        .drop_duplicates()
        .groupby('c_digo_departamento')
        .sample(n=1, random_state=1)
        .reset_index(drop=True)
    )

    df = (
        df.query("departamento != 'NACIONAL'")
        .drop(columns='departamento')
        .merge(tabla_deptos, on='c_digo_departamento', how='left')
    )

    st.markdown("### 🔧 Etapas del Flujo de Trabajo")
    etapas = [
        "1️⃣ Limpieza de datos",
        "2️⃣ Enriquecimiento con datos del DANE",
        "3️⃣ Construcción de dimensiones",
        "4️⃣ Modelo estrella y tabla de hechos",
        "5️⃣ Visualización y métricas clave",
        "6️⃣ Descarga y resumen detallado"
    ]
    for etapa in etapas:
        st.markdown(f"- {etapa}")

    st.markdown("---")
    st.subheader("1️⃣ Limpieza y Validación de Datos")

    columnas_relevantes = [
        'a_o', 'departamento', 'municipio', 'c_digo_departamento',
        'poblaci_n_5_16', 'tasa_matriculaci_n_5_16',
        'cobertura_neta', 'cobertura_bruta'
    ]
    columnas_faltantes = [col for col in columnas_relevantes if col not in df.columns]
    if columnas_faltantes:
        st.error(f"❌ Columnas faltantes: {columnas_faltantes}")
        return

    df = df[columnas_relevantes]
    df.columns = [c.lower() for c in df.columns]
    for col in df.columns:
        if col not in ['departamento', 'municipio', 'c_digo_departamento']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df_clean = df.dropna()

    col1, col2 = st.columns(2)
    col1.metric("Registros originales", len(st.session_state['df_raw']))
    col2.metric("Registros válidos", len(df_clean))

    # ========= 2️⃣ Enriquecimiento con Datos del DANE =========
    st.markdown("---")
    st.subheader("2️⃣ Enriquecimiento con Datos del DANE")

    if 'df_pob' in st.session_state and not st.session_state['df_pob'].empty:
        df_pob = st.session_state['df_pob'].copy()

        columnas_esperadas = ['DPNOM', 'DPMP', 'AÑO', 'Población']
        if not all(col in df_pob.columns for col in columnas_esperadas):
            st.error("❌ Las columnas esperadas no están presentes en el archivo de población.")
            return

        df_pob["Población"] = (
            df_pob["Población"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .str.replace(",", "", regex=False)
            .astype(float)
        )

        poblacion_agregada = df_pob.groupby(['DPNOM', 'DPMP', 'AÑO'], as_index=False)['Población'].sum()

        df_enriq = df_clean.merge(
            poblacion_agregada,
            left_on=['departamento', 'municipio', 'a_o'],
            right_on=['DPNOM', 'DPMP', 'AÑO'],
            how='left'
        )

        df_enriq = df_enriq.dropna(subset=['Población'])
        df_enriq['%_matriculados_vs_pob_total'] = (
            df_enriq['poblaci_n_5_16'] / df_enriq['Población']) * 100

        df_clean = df_enriq
        st.success("✅ Datos enriquecidos correctamente con los nombres originales.")
    else:
        st.info("ℹ️ No se han cargado datos del DANE. Puedes continuar sin el enriquecimiento.")

    # ========= 3️⃣ Dimensiones =========
    st.markdown("---")
    st.subheader("3️⃣ Dimensiones del Modelo Estrella")

    def crear_dimension(df, cols, nombre, sort_col=None):
        dim = df[cols].drop_duplicates()
        if sort_col:
            dim = dim.sort_values(by=sort_col)
        dim = dim.reset_index(drop=True)
        dim[f"id_{nombre}"] = dim.index + 1
        return dim[[f"id_{nombre}"] + cols]

    dim_tiempo = crear_dimension(df_clean, ['a_o'], 'tiempo')
    dim_geo = df_clean[['c_digo_departamento', 'departamento', 'municipio']].copy()
    dim_geo = dim_geo.sort_values(by=['c_digo_departamento', 'municipio'])
    dim_geo = dim_geo.drop_duplicates(subset=['c_digo_departamento'], keep='first').reset_index(drop=True)
    dim_geo['id_geo'] = dim_geo.index + 1
    dim_geo = dim_geo[['id_geo', 'c_digo_departamento', 'departamento', 'municipio']]

    col3, col4 = st.columns(2)
    col3.metric("Dimensión Tiempo", len(dim_tiempo))
    col4.metric("Dimensión Geográfica", len(dim_geo))

    # ========= 4️⃣ Tabla de Hechos =========
    st.markdown("---")
    st.subheader("4️⃣ Tabla de Hechos")

    df_fact = df_clean.merge(dim_tiempo, on='a_o') \
                      .merge(dim_geo, on=['departamento', 'municipio', 'c_digo_departamento'], how='inner')

    columnas_fact = ['id_tiempo', 'id_geo', 'poblaci_n_5_16',
                     'tasa_matriculaci_n_5_16', 'cobertura_neta', 'cobertura_bruta']
    if '%_matriculados_vs_pob_total' in df_fact.columns:
        columnas_fact.append('%_matriculados_vs_pob_total')

    df_fact = df_fact[columnas_fact]

    st.success(f"✅ Tabla de hechos construida con {len(df_fact):,} registros.")
    st.session_state['df_fact'] = df_fact
    st.session_state['dim_geo'] = dim_geo
    st.session_state['dim_tiempo'] = dim_tiempo

    # ========= 5️⃣ Visualización =========
    st.markdown("---")
    st.subheader("5️⃣ Indicadores y Visualizaciones")

    escolaridad_prom = df_fact.groupby('id_geo')[['tasa_matriculaci_n_5_16']].mean().reset_index()
    escolaridad_prom = escolaridad_prom.merge(dim_geo, on='id_geo')
    top_mpios = escolaridad_prom.sort_values(by='tasa_matriculaci_n_5_16', ascending=False).head(10)

    fig = px.bar(
        top_mpios,
        x='municipio',
        y='tasa_matriculaci_n_5_16',
        title='Top 10 Municipios con Mayor Tasa de Escolaridad (5-16 años)',
        labels={'tasa_matriculaci_n_5_16': 'Tasa de Escolaridad (%)'},
        color='tasa_matriculaci_n_5_16',
        color_continuous_scale=px.colors.sequential.Blues,
        text='tasa_matriculaci_n_5_16'
    )
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        coloraxis_showscale=False,
        yaxis_title='Tasa de Escolaridad (%)',
        xaxis_title='Municipio',
        plot_bgcolor='white'
    )
    st.plotly_chart(fig, use_container_width=True)

    cobertura_depto = df_fact.merge(dim_geo, on='id_geo') \
        .groupby('departamento')['cobertura_neta'].mean().sort_values(ascending=False).head(10)

    st.markdown("🏛️ **Top Departamentos por Cobertura Neta Promedio**")
    st.dataframe(cobertura_depto.reset_index())

    # ========= 6️⃣ Descarga =========
    st.markdown("---")
    st.subheader("6️⃣ Descarga y Resumen")

    st.dataframe(df_fact.head(50))
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_fact.to_excel(writer, index=False, sheet_name='TablaHechos')
    output.seek(0)

    st.download_button(
        label="📥 Descargar Tabla de Hechos",
        data=output,
        file_name='tabla_hechos_educacion.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    df_fact_ext = df_fact.merge(dim_geo, on='id_geo').merge(dim_tiempo, on='id_tiempo')
    resumen = df_fact_ext.groupby(['departamento', 'a_o'])[
        ['tasa_matriculaci_n_5_16', 'cobertura_neta', 'cobertura_bruta']].mean().reset_index()
    st.dataframe(resumen.head(20))