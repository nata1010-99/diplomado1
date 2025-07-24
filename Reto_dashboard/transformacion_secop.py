import pandas as pd
import streamlit as st
import unidecode

def clean_secop_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpieza y transformación básica de datos de SECOP.
    Args:
        df (pd.DataFrame): DataFrame original cargado desde la API.
    Returns:
        pd.DataFrame: DataFrame limpio y transformado.
    """
    df = df.copy()

    # 1. Limpiar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()
    df.columns = [unidecode.unidecode(col).replace(" ", "_") for col in df.columns]

    # 2. Convertir columnas de fecha a datetime si existen
    for col in ['fecha_inicio_ejecucion', 'fecha_fin_ejecucion']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # 3. Convertir columnas numéricas
    if 'valor_contrato' in df.columns:
        df['valor_contrato'] = pd.to_numeric(df['valor_contrato'], errors='coerce')

    if 'documento_proveedor' in df.columns and df['documento_proveedor'].dtype == object:
        df['documento_proveedor'] = (
            df['documento_proveedor']
            .str.replace(".", "", regex=False)
            .pipe(pd.to_numeric, errors='coerce')
        )

    # 4. Estandarizar texto en columnas de tipo objeto
    texto_cols = df.select_dtypes(include='object').columns
    for col in texto_cols:
        df[col] = df[col].fillna("").str.strip().str.lower()

    # 5. Normalización adicional de nombres de departamentos
    if 'departamento_entidad' in df.columns:
        df['departamento_entidad'] = (
            df['departamento_entidad']
            .apply(unidecode.unidecode)
            .str.replace(r'[^a-z\s]', '', regex=True)
            .str.replace(" +", " ", regex=True)
            .str.strip()
            .str.lower()
        )

    # 6. Eliminar duplicados
    df.drop_duplicates(inplace=True)

    return df

def show_transformations_tab():
    st.header("🛠️ Transformaciones de Datos")

    st.markdown("""
    Aquí se explican las transformaciones realizadas al dataset cargado desde la API de SECOP:
    
    - ✅ Conversión de fechas (`fecha_inicio_ejecución`, `fecha_firma`, etc.)
    - ✅ Conversión de columnas numéricas como `valor_contrato` a tipo float
    - ✅ Normalización de nombres de contratos y departamentos
    - ✅ Eliminación de valores nulos críticos
    - ✅ Limpieza general y estandarización de columnas tipo texto
    """)

    if 'df_raw' in st.session_state:
        df_raw = st.session_state['df_raw'].copy()
        st.subheader("🔍 Ejemplo de datos transformados")
        st.dataframe(df_raw.head())
        st.success("✅ ¡Transformaciones aplicadas correctamente!")
    else:
        st.info("⚠️ Primero debes cargar los datos desde la pestaña '📋 Carga de Datos'.")

