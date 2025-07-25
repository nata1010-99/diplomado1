import streamlit as st
import pandas as pd
import requests
import os

# ===================================================================
# Función: load_data_from_api
# ===================================================================
def load_data_from_api(limit: int = 50000) -> pd.DataFrame:
    """
    Carga datos desde la API de Socrata en formato JSON y los convierte en un DataFrame de pandas.
    """
    api_url = f"https://www.datos.gov.co/resource/nudc-7mev.json?$limit={limit}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de conexión: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
    return pd.DataFrame()

# ===================================================================
# Función: load_dane_local_files
# ===================================================================
def load_dane_local_files() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Carga dos archivos locales del DANE:
    - Info_2005_2019.xlsx (población)
    - Info_2020_2035.xlsx (densidad escolar)
    """
    try:
        path_poblacion = os.path.join("..", "Datos", "Info_2005_2019.xlsx")
        path_densidad = os.path.join("..", "Datos", "Info_2020_2035.xlsx")

        df_poblacion = pd.read_excel(path_poblacion)
        df_densidad = pd.read_excel(path_densidad)
        return df_poblacion, df_densidad

    except Exception as e:
        st.error(f"❌ Error al cargar archivos locales: {e}")
        return pd.DataFrame(), pd.DataFrame()

# ===================================================================
# Función: show_data_tab
# ===================================================================
def show_data_tab():
    """
    Muestra la interfaz de carga de datos desde la API del MEN y archivos del DANE.
    """
    st.header("📥 Carga de Datos")

    # ========== API MEN ==========
    st.subheader("📡 Cargar datos del MEN (API)")
    st.markdown("Fuente: [datos.gov.co](https://www.datos.gov.co/Educaci-n/MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR-B-SICA/nudc-7mev)")

    if st.button("🔄 Cargar datos del MEN"):
        with st.spinner("Cargando desde la API..."):
            df_raw = load_data_from_api()

        if not df_raw.empty:
            st.session_state['df_raw'] = df_raw
            st.success(f"✅ {len(df_raw)} registros cargados")
            st.dataframe(df_raw.head())
        else:
            st.warning("⚠️ No se encontraron datos.")

    st.divider()

    # ========== ARCHIVOS LOCALES ==========
    st.subheader("📂 Cargar archivos locales del DANE")
    st.markdown("""
    Archivos esperados en la carpeta `Datos/`:
    - `Info_2005_2019.xlsx` → población
    - `Info_2020_2035.xlsx` → densidad escolar
    """)

    if st.button("📂 Cargar desde carpeta local"):
        with st.spinner("Cargando archivos..."):
            df_pob, df_dens = load_dane_local_files()

        if not df_pob.empty and not df_dens.empty:
            st.session_state['df_poblacion'] = df_pob
            st.session_state['df_densidad'] = df_dens
            st.success("✅ Archivos locales cargados correctamente")
            st.dataframe(df_pob.head())
            st.dataframe(df_dens.head())
        else:
            st.warning("⚠️ No se pudo cargar uno o ambos archivos.")

    st.divider()

    # ========== SUBIDA MANUAL ==========
    st.subheader("📤 O sube los archivos manualmente")

    col1, col2 = st.columns(2)
    with col1:
        up_pob = st.file_uploader("📁 Info_2005_2019.xlsx", type="xlsx", key="poblacion")
    with col2:
        up_dens = st.file_uploader("📁 Info_2020_2035.xlsx", type="xlsx", key="densidad")

    if up_pob:
        try:
            df_pob = pd.read_excel(up_pob)
            st.session_state['df_poblacion'] = df_pob
            st.success("✅ Población cargada correctamente")
            st.dataframe(df_pob.head())
        except Exception as e:
            st.error(f"❌ Error al cargar población: {e}")

    if up_dens:
        try:
            df_dens = pd.read_excel(up_dens)
            st.session_state['df_densidad'] = df_dens
            st.success("✅ Densidad escolar cargada correctamente")
            st.dataframe(df_dens.head())
        except Exception as e:
            st.error(f"❌ Error al cargar densidad: {e}")