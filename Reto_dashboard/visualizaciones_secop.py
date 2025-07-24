import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from scipy.stats import pearsonr
from cargar_datos_secop import get_df_raw
import unidecode
import re

# ---------- Configuración ----------
st.set_page_config(page_title="Visualización de Contratación Pública", layout="wide")
sns.set(style="whitegrid")

# ---------- Normalización y correcciones ----------
def normalizar_departamento(nombre):
    if pd.isna(nombre):
        return ""
    nombre = unidecode.unidecode(nombre.lower().strip())
    nombre = re.sub(r"[-_\.]", " ", nombre)
    nombre = re.sub(r"\s+", " ", nombre)
    return nombre

def corregir_alias_departamento(nombre):
    alias_dict = {
        "bogota dc": "bogota",
        "distrito capital de bogota": "bogota",
        "san andres providencia y santa catalina": "san andres",
        "no definido": "sin_departamento"
    }
    return alias_dict.get(nombre, nombre)

# ---------- Cache de carga de datos ----------
@st.cache_data
def cargar_datos_contratacion():
    df = get_df_raw(limit=50000)
    if 'fecha_inicio_ejecuci_n' in df.columns:
        df['fecha_inicio_ejecuci_n'] = pd.to_datetime(df['fecha_inicio_ejecuci_n'], errors='coerce')
        df = df.sort_values(by='fecha_inicio_ejecuci_n')
    return df

@st.cache_data
def cargar_poblacion():
    df_2005_2019 = pd.read_excel("../Datos/Info_2005_2019.xlsx")
    df_2020_2035 = pd.read_excel("../Datos/Info_2020_2035.xlsx")
    df_pob = pd.concat([df_2005_2019, df_2020_2035], ignore_index=True)
    df_pob = df_pob[df_pob['ÁREA GEOGRÁFICA'].str.lower() == 'total']
    df_pob = df_pob[df_pob['AÑO'].notna()]
    df_pob['AÑO'] = df_pob['AÑO'].astype(int)
    df_pob['departamento_entidad'] = df_pob['DPNOM'].apply(normalizar_departamento).apply(corregir_alias_departamento)
    return df_pob

# ---------- Visualización ----------
def show_visualizations_tab():
    st.header("📊 Visualizaciones de contratación pública")

    df_raw = cargar_datos_contratacion()
    df_pob = cargar_poblacion()

    # ---------- Tasa de contratos por 1.000 habitantes ----------
    st.subheader("🏙️ ¿Qué departamentos presentan mayor tasa de contratos por cada 1.000 habitantes?")

    año_reciente = df_pob['AÑO'].max()
    df_pob_dep = df_pob[df_pob['AÑO'] == año_reciente].groupby('departamento_entidad', as_index=False)['Población'].sum()

    df_contratos = df_raw.copy()
    df_contratos = df_contratos[df_contratos['departamento_entidad'].notna()]
    df_contratos['departamento_entidad'] = (
        df_contratos['departamento_entidad'].apply(normalizar_departamento).apply(corregir_alias_departamento)
    )

    df_contratos_por_dep = df_contratos.groupby('departamento_entidad', as_index=False).size()
    df_contratos_por_dep.rename(columns={'size': 'num_contratos'}, inplace=True)

    df_tasa = pd.merge(df_contratos_por_dep, df_pob_dep, on='departamento_entidad', how='left')
    df_tasa['contratos_por_1000_hab'] = (df_tasa['num_contratos'] / df_tasa['Población']) * 1000

    # ⚠️ Diagnóstico de departamentos sin población cruzada
    # st.dataframe(df_tasa[df_tasa['Población'].isna()][['departamento_entidad', 'num_contratos']])

    # 📋 Mostrar tabla completa
    st.markdown("📋 **Ranking completo por tasa de contratación**")
    st.dataframe(df_tasa.sort_values(by='contratos_por_1000_hab', ascending=False), use_container_width=True)

    # 📊 Top 10 en gráfica
    df_top = df_tasa.sort_values(by='contratos_por_1000_hab', ascending=False).head(10)
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_top, x='contratos_por_1000_hab', y='departamento_entidad', palette='viridis', ax=ax1)
    ax1.set_title("Top 10 departamentos con mayor tasa de contratación por 1.000 habitantes")
    ax1.set_xlabel("Contratos por cada 1.000 habitantes")
    ax1.set_ylabel("Departamento")
    st.pyplot(fig1)

    # ---------- Correlación población vs contratos ----------
    st.subheader("📈 ¿Se corresponde el volumen de contratación con la población?")
    df_correl = pd.merge(df_contratos_por_dep, df_pob_dep, on='departamento_entidad', how='inner')

    fig2, ax2 = plt.subplots(figsize=(10, 6))
    sns.scatterplot(data=df_correl, x='Población', y='num_contratos', ax=ax2)
    ax2.set_title("Relación entre población y número de contratos")
    ax2.set_xlabel("Población estimada en 2035")
    ax2.set_ylabel("Número de contratos")
    ax2.grid(True)
    st.pyplot(fig2)

    if len(df_correl) >= 2:
        corr, _ = pearsonr(df_correl['Población'], df_correl['num_contratos'])
        st.markdown(f"📈 **Correlación de Pearson**: `{corr:.2f}`")
    else:
        st.warning("⚠️ No hay suficientes datos para calcular la correlación.")

    # ---------- Evolución mensual por tipo ----------
    st.subheader("📅 Evolución mensual del valor contratado por tipo de contrato")
    df_contratos['tipo_de_contrato'] = df_contratos['tipo_de_contrato'].fillna("").str.strip().str.lower()
    df_contratos = df_contratos[df_contratos['fecha_inicio_ejecuci_n'].notna()]
    df_contratos['anio_mes'] = df_contratos['fecha_inicio_ejecuci_n'].dt.to_period('M')

    df_evol = df_contratos.groupby(['anio_mes', 'tipo_de_contrato'])['valor_contrato'].sum().reset_index()
    df_evol['anio_mes'] = df_evol['anio_mes'].dt.to_timestamp()
    df_evol = df_evol[df_evol['anio_mes'].dt.year >= 2018]

    fig3, ax3 = plt.subplots(figsize=(14, 7))
    sns.lineplot(data=df_evol, x='anio_mes', y='valor_contrato', hue='tipo_de_contrato', marker='o', ax=ax3)
    ax3.set_title("Evolución mensual del valor contratado por tipo de contrato")
    ax3.set_xlabel("Fecha")
    ax3.set_ylabel("Valor total contratado")
    ax3.legend(title='Tipo de contrato', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    st.pyplot(fig3)

    # ---------- Total por tipo de contrato ----------
    st.subheader("💰 ¿Qué tipo de contratos concentran mayores valores?")
    totales_tipo = df_evol.groupby('tipo_de_contrato')['valor_contrato'].sum().sort_values(ascending=False)
    st.bar_chart(totales_tipo)

    # ---------- Tabla detallada ----------
    with st.expander("🔍 Ver tabla mensual por tipo de contrato"):
        df_pivot = df_evol.pivot(index='anio_mes', columns='tipo_de_contrato', values='valor_contrato').fillna(0)
        st.dataframe(df_pivot, use_container_width=True)

# ---------- Ejecutar ----------
if __name__ == "__main__":
    show_visualizations_tab()
