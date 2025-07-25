import streamlit as st
import pandas as pd
import requests
from transformacion_secop import clean_secop_data  

# ===========================================================
# FUNCION: Cargar datos desde SECOP Integrado
# ===========================================================
def load_data_from_api(limit: int = 5000) -> pd.DataFrame:
    """
    Carga datos desde la API de SECOP Integrado (datos.gov.co).
    Args:
        limit (int): Límite de registros (por defecto 5000).
    Returns:
        pd.DataFrame: DataFrame con los datos cargados o vacío si falla.
    """
    api_url = f"https://www.datos.gov.co/resource/rpmr-utcd.json?$limit={limit}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        return df
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al conectar con la API: {e}")
    except Exception as e:
        st.error(f"❌ Error inesperado: {e}")
    return pd.DataFrame()

# ===========================================================
# FUNCION: Mostrar pestaña de carga de datos
# ===========================================================
def show_data_tab():
    st.header("📥 Carga de Datos desde SECOP Integrado")

    st.markdown("""
    Este conjunto de datos proviene del portal [datos.gov.co](https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-Integrado/rpmr-utcd).
    
    Haz clic en el botón para obtener datos directamente desde la API de **SECOP Integrado**.
    """)

    if st.button("🔄 Cargar datos"):
        with st.spinner("Cargando datos desde la API de SECOP..."):
            df_raw = load_data_from_api(limit=5000)  # ✅ Límite ajustado

        if not df_raw.empty:
            df_clean = clean_secop_data(df_raw)
            st.session_state['df_raw'] = df_clean
            st.success(f"✅ ¡Datos cargados exitosamente! ({len(df_clean)} filas)")
            st.dataframe(df_clean.head(10))
        else:
            st.warning("⚠️ No se encontraron datos o ocurrió un error.")
    else:
        st.info("Haz clic en el botón para cargar los datos.")

# ===========================================================
# FUNCION: Obtener df_raw limpio para usar en otras partes
# ===========================================================
def get_df_raw(limit: int = 5000) -> pd.DataFrame:
    df = load_data_from_api(limit)
    if not df.empty:
        return clean_secop_data(df)
    else:
        return pd.DataFrame()

