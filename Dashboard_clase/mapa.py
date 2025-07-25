import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium

def show_map_tab():
    st.header("🗺️ Mapa Interactivo por Departamento")

    if 'df_fact' not in st.session_state:
        st.warning("Primero debes construir la tabla de hechos en la pestaña 'Transformación y Métricas'.")
        return

    df_fact = st.session_state['df_fact']
    dim_geo = st.session_state['dim_geo']
    dim_tiempo = st.session_state['dim_tiempo']

    # Merge de tabla de hechos con dimensiones
    df = df_fact.merge(dim_geo, on='id_geo').merge(dim_tiempo, on='id_tiempo')

    # Selector de métrica
    metricas = {
        'Cobertura Neta (%)': 'cobertura_neta',
        'Cobertura Bruta (%)': 'cobertura_bruta',
        'Tasa de Matriculación 5-16 (%)': 'tasa_matriculaci_n_5_16'
    }

    metrica_label = st.selectbox("Selecciona la métrica", list(metricas.keys()))
    metrica_col = metricas[metrica_label]

    # Selector de año
    años = sorted(df['a_o'].unique())
    año_sel = st.selectbox("Selecciona el año", años, index=len(años)-1)

    # Agrupación por código de departamento
    df_filtrado = df[df['a_o'] == año_sel]
    resumen = (
        df_filtrado
        .groupby(['c_digo_departamento', 'departamento'])[metrica_col]
        .mean()
        .reset_index()
        .rename(columns={'c_digo_departamento': 'codigo_departamento'})
    )
    resumen['codigo_departamento'] = resumen['codigo_departamento'].astype(str).str.zfill(2)

    # Leer shapefile
    try:
        gdf = gpd.read_file("data/shapes/MGN_ANM_DPTOS.shp")
    except Exception as e:
        st.error(f"❌ Error al leer el archivo .shp: {e}")
        return

    # Unir shapefile con datos
    codigo_col = "DPTO_CCDGO"
    gdf[codigo_col] = gdf[codigo_col].astype(str).str.zfill(2)
    resumen[codigo_col] = resumen["codigo_departamento"]
    gdf_merged = gdf.merge(resumen, on=codigo_col, how="left")

    # Mostrar tabla para depurar
    st.write("✅ Datos combinados para el mapa:")
    st.dataframe(gdf_merged[[codigo_col, 'departamento', metrica_col]].head())

    # Crear mapa con estilo limpio
    m = folium.Map(location=[4.6, -74.1], zoom_start=5, tiles="CartoDB positron")

    # Coropletas
    folium.Choropleth(
        geo_data=gdf_merged,
        name="choropleth",
        data=gdf_merged,
        columns=[codigo_col, metrica_col],
        key_on=f"feature.properties.{codigo_col}",
        fill_color="YlOrRd",
        fill_opacity=0.75,
        line_opacity=0.3,
        nan_fill_color="lightgray",
        legend_name=f"{metrica_label} - {año_sel}",
        highlight=True
    ).add_to(m)

    # Tooltips personalizados
    folium.GeoJson(
        gdf_merged,
        name="Labels",
        style_function=lambda x: {"fillColor": "transparent", "color": "transparent"},
        tooltip=folium.GeoJsonTooltip(
            fields=["departamento", metrica_col],
            aliases=["Departamento:", f"{metrica_label}:"],
            localize=True,
            sticky=True,
            labels=True,
            style="""
                background-color: white;
                border: 1px solid black;
                border-radius: 3px;
                box-shadow: 3px;
            """
        )
    ).add_to(m)

    folium.LayerControl().add_to(m)

    st.subheader(f"🧭 {metrica_label} por Departamento - {año_sel}")
    st_folium(m, width=750, height=550, returned_objects=[])


