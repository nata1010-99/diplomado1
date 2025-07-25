import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def show_visualization_tab():
    st.header("📈 Visualizaciones por Departamento")

    # Verificaciones
    if 'df_poblacion' in st.session_state:
        st.success("✅ Base de población cargada")
    else:
        st.warning("⚠️ Base de población NO cargada")

    if 'df_densidad' in st.session_state:
        st.success("✅ Base de densidad escolar cargada")
    else:
        st.warning("⚠️ Base de densidad escolar NO cargada")

    if 'df_fact' not in st.session_state:
        st.warning("Primero debes construir la tabla de hechos en la pestaña 'Transformación y Métricas'.")
        return

    # Preparación de datos
    df_fact = st.session_state['df_fact']
    dim_geo = st.session_state['dim_geo']
    dim_tiempo = st.session_state['dim_tiempo']
    df = df_fact.merge(dim_geo, on='id_geo').merge(dim_tiempo, on='id_tiempo')
    df.columns = [col.lower() for col in df.columns]
    deptos = sorted(df['departamento'].unique())

    # GRAFICO 1
    st.subheader("📊 Serie de tiempo: Tasa de Matriculación vs Cobertura Neta")
    selected_depto_1 = st.selectbox("Selecciona un departamento (Gráfico 1)", deptos)
    df_1 = df[df['departamento'] == selected_depto_1]
    df_1 = df_1.groupby('a_o')[['tasa_matriculaci_n_5_16', 'cobertura_neta']].mean().reset_index()

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_1['a_o'], y=df_1['tasa_matriculaci_n_5_16'],
                              name='Tasa de Matriculación (5-16)', mode='lines+markers', yaxis='y1', line=dict(color='blue')))
    fig1.add_trace(go.Scatter(x=df_1['a_o'], y=df_1['cobertura_neta'],
                              name='Cobertura Neta', mode='lines+markers', yaxis='y2', line=dict(color='orange')))
    fig1.update_layout(title=f"Serie de tiempo - {selected_depto_1}",
                       xaxis=dict(title='Año'),
                       yaxis=dict(title='Tasa de Matriculación (%)', tickfont=dict(color='blue')),
                       yaxis2=dict(title='Cobertura Neta (%)', overlaying='y', side='right', tickfont=dict(color='orange')),
                       legend=dict(x=0.01, y=0.99),
                       height=500)
    st.plotly_chart(fig1, use_container_width=True)

    # GRAFICO 2
    st.subheader("📊 Serie de tiempo: Cobertura Bruta vs Otra Métrica")
    selected_depto_2 = st.selectbox("Selecciona un departamento (Gráfico 2)", deptos, index=deptos.index(selected_depto_1))
    df_2 = df[df['departamento'] == selected_depto_2].groupby('a_o')[['cobertura_bruta']].mean().reset_index()

    if 'repitencia_secundaria' in df.columns:
        df_2['otra_metrica'] = df[df['departamento'] == selected_depto_2].groupby('a_o')['repitencia_secundaria'].mean().values
        nombre_metrica = 'Repitencia secundaria'
    else:
        df_2['otra_metrica'] = df[df['departamento'] == selected_depto_2].groupby('a_o')['tasa_matriculaci_n_5_16'].mean().values
        nombre_metrica = 'Tasa de Matriculación (5-16)'

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_2['a_o'], y=df_2['cobertura_bruta'],
                              name='Cobertura Bruta', mode='lines+markers', yaxis='y1', line=dict(color='green')))
    fig2.add_trace(go.Scatter(x=df_2['a_o'], y=df_2['otra_metrica'],
                              name=nombre_metrica, mode='lines+markers', yaxis='y2', line=dict(color='purple')))
    fig2.update_layout(title=f"Cobertura Bruta vs {nombre_metrica} - {selected_depto_2}",
                       xaxis=dict(title='Año'),
                       yaxis=dict(title='Cobertura Bruta (%)', tickfont=dict(color='green')),
                       yaxis2=dict(title=nombre_metrica, overlaying='y', side='right', tickfont=dict(color='purple')),
                       legend=dict(x=0.01, y=0.99),
                       height=500)
    st.plotly_chart(fig2, use_container_width=True)

    # GRAFICOS DE POBLACION (solo si df_poblacion existe)
    if 'df_poblacion' in st.session_state:
        df_pob = st.session_state['df_poblacion'].copy()
        df_pob.columns = [col.lower() for col in df_pob.columns]

        st.subheader("🌍 Composición Urbana vs Rural - Pie Chart")
        if 'área geográfica' in df_pob.columns:
            df_pob_depto = df_pob[df_pob['dpnom'] == selected_depto_1].groupby('área geográfica')['población'].sum().reset_index()
        elif 'área_geográfica' in df_pob.columns:
            df_pob_depto = df_pob[df_pob['dpnom'] == selected_depto_1].groupby('área_geográfica')['población'].sum().reset_index()
        else:
            st.error("⚠️ No se encuentra la columna de 'Área Geográfica'")
            df_pob_depto = pd.DataFrame()

        if not df_pob_depto.empty:
            fig3 = px.pie(df_pob_depto, names=df_pob_depto.columns[0], values='población',
                          title=f"Distribución poblacional urbana/rural - {selected_depto_1}",
                          color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig3, use_container_width=True)

        # GRAFICO 4 - Evolución de la población total por año
        st.subheader("📈 Evolución de la población total")
        df_pob_total = df_pob[df_pob['dpnom'] == selected_depto_1].groupby('año')['población'].sum().reset_index()
        fig4 = px.line(df_pob_total, x='año', y='población',
                       title=f"Evolución de la población total en {selected_depto_1}",
                       markers=True)
        st.plotly_chart(fig4, use_container_width=True)

        # GRAFICO 5 - Comparación urbana vs rural por año
        st.subheader("🏙️ Población Urbana vs Rural por Año")
        df_pob_tipo = df_pob[df_pob['dpnom'] == selected_depto_1].groupby(['año', 'área geográfica'])['población'].sum().reset_index()
        fig5 = px.bar(df_pob_tipo, x='año', y='población', color='área geográfica',
                      barmode='group',
                      title=f"Población Urbana vs Rural por año - {selected_depto_1}")
        st.plotly_chart(fig5, use_container_width=True)

        # GRAFICO 6 - Porcentaje acumulado urbano vs rural
        st.subheader("📊 Porcentaje acumulado de población urbana/rural")
        df_sum = df_pob[df_pob['dpnom'] == selected_depto_1].groupby('área geográfica')['población'].sum().reset_index()
        df_sum['%'] = df_sum['población'] / df_sum['población'].sum() * 100
        fig6 = px.pie(df_sum, names='área geográfica', values='población',
                      title=f"Distribución porcentual acumulada - {selected_depto_1}",
                      hole=0.4)
        st.plotly_chart(fig6, use_container_width=True)
