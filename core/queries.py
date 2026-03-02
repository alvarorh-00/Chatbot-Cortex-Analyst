"""
Módulo de queries SQL para resolución de incidencias
Define queries paramétrizadas que se ejecutan contra vistas de Snowflake
"""

from typing import Dict, List
import pandas as pd
import streamlit as st


# Mapear las vistas de Snowflake que has creado y sus parámetros
VISTA_CONFIG = {
    "diagnostico_paso1": {
        "name": "CORTEX_ANALYST_DEMO.CHATBOT_V2.V_DIAGNOSTICO_PASO1_TIPO_PEDIDO",
        "params": {
            "CO_UNECO": "uneco",
            "CO_CENTRO_LOGISTICO": "almacen",
            "CO_PEDIDO_HOST": "pedido_host"
        },
        "description": "📊 Diagnóstico Paso 1: Tipo de Pedido"
    },
    "diagnostico_paso2": {
        "name": "CORTEX_ANALYST_DEMO.CHATBOT_V2.V_DIAGNOSTICO_PASO2_ESTADO_ASN",
        "params": {
            "CO_PEDIDO": "pedido"
        },
        "description": "📊 Diagnóstico Paso 2: Estado ASN y Revisiones"
    }
}


def build_query(vista_key: str, incidencia_data: Dict) -> tuple[str, Dict]:
    """
    Construye una query paramétrica para una vista específica.
    
    Args:
        vista_key: Clave de la vista en VISTA_CONFIG
        incidencia_data: Diccionario con datos de la incidencia
        
    Returns:
        (query_sql, parametros)
    """
    if vista_key not in VISTA_CONFIG:
        raise ValueError(f"Vista '{vista_key}' no configurada")
    
    vista = VISTA_CONFIG[vista_key]
    vista_name = vista["name"]
    param_mapping = vista["params"]
    
    # Construir WHERE clause con los parámetros disponibles
    where_conditions = []
    params = {}
    
    for col_name, data_key in param_mapping.items():
        # Buscar el valor en incidencia_data
        if data_key in incidencia_data:
            value = incidencia_data[data_key]
            # Escapar valores string
            if isinstance(value, str):
                where_conditions.append(f"{col_name} = '{value}'")
            else:
                where_conditions.append(f"{col_name} = {value}")
            params[col_name] = value
    
    # Construir query
    if where_conditions:
        query = f"SELECT * FROM {vista_name} WHERE {' AND '.join(where_conditions)}"
    else:
        query = f"SELECT * FROM {vista_name}"
    
    return query, params


def execute_vista_query(vista_key: str, incidencia_data: Dict) -> tuple[pd.DataFrame, str]:
    """
    Ejecuta una query contra una vista de Snowflake.
    
    Args:
        vista_key: Clave de la vista a consultar
        incidencia_data: Datos de la incidencia
        
    Returns:
        (DataFrame con resultados, mensaje de error si lo hay)
    """
    if "snowpark_session" not in st.session_state:
        return None, "No hay sesión activa de Snowflake"
    
    try:
        session = st.session_state.snowpark_session
        
        # Construir y ejecutar query
        query, params = build_query(vista_key, incidencia_data)
        
        # Log de debug (opcional)
        print(f"Ejecutando query para {vista_key}:")
        print(query)
        
        df = session.sql(query).to_pandas()
        
        return df, None
    except Exception as e:
        return None, f"Error ejecutando vista '{vista_key}': {str(e)}"


def get_diagnostico_paso1(incidencia_data: Dict) -> tuple[pd.DataFrame, str]:
    """Obtiene el diagnóstico paso 1: tipo de pedido."""
    return execute_vista_query("diagnostico_paso1", incidencia_data)


def get_diagnostico_paso2(incidencia_data: Dict) -> tuple[pd.DataFrame, str]:
    """Obtiene el diagnóstico paso 2: estado ASN."""
    return execute_vista_query("diagnostico_paso2", incidencia_data)


def get_all_analyst_results(incidencia_data: Dict) -> Dict:
    """
    Ejecuta todas las vistas para obtener un análisis completo.
    
    Returns:
        Diccionario con resultados de todas las vistas
    """
    results = {}
    
    # Diagnóstico Paso 1: Tipo de Pedido
    df_p1, err_p1 = get_diagnostico_paso1(incidencia_data)
    results["diagnostico_paso1"] = {
        "data": df_p1,
        "error": err_p1,
        "vista": VISTA_CONFIG["diagnostico_paso1"]["description"]
    }
    
    # Diagnóstico Paso 2: Estado ASN
    df_p2, err_p2 = get_diagnostico_paso2(incidencia_data)
    results["diagnostico_paso2"] = {
        "data": df_p2,
        "error": err_p2,
        "vista": VISTA_CONFIG["diagnostico_paso2"]["description"]
    }
    
    return results
