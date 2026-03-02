"""
Módulo de utilidades generales
"""

import os
import streamlit as st
try:
    import tomllib
except ImportError:
    import tomli as tomllib


def get_config():
    """
    Obtiene la configuración desde variables de entorno.
    
    Soporta dos modos:
    1. STREAMLIT_SECRETS_TOML: Contenido completo del archivo secrets.toml como variable
    2. Variables individuales: SNOWFLAKE_ACCOUNT y SNOWFLAKE_WAREHOUSE
    
    Raises: ValueError si no se encuentra configuración válida.
    """
    
    # Opción 1: Leer desde STREAMLIT_SECRETS_TOML (contenido del archivo)
    secrets_content = os.environ.get("STREAMLIT_SECRETS_TOML")
    if secrets_content:
        try:
            secrets_dict = tomllib.loads(secrets_content)
            return {
                "snowflake_account": secrets_dict.get("snowflake", {}).get("account"),
                "snowflake_warehouse": secrets_dict.get("snowflake", {}).get("warehouse"),
            }
        except Exception as e:
            raise ValueError(
                f"Error al parsear STREAMLIT_SECRETS_TOML: {str(e)}\n"
                f"Asegúrate que el contenido es válido TOML"
            )
    
    # Opción 2: Leer variables individuales
    account = os.environ.get("SNOWFLAKE_ACCOUNT")
    warehouse = os.environ.get("SNOWFLAKE_WAREHOUSE")
    
    if account and warehouse:
        return {
            "snowflake_account": account,
            "snowflake_warehouse": warehouse,
        }
    
    # Si no hay ninguna configuración
    missing = []
    if not account:
        missing.append("SNOWFLAKE_ACCOUNT")
    if not warehouse:
        missing.append("SNOWFLAKE_WAREHOUSE")
    
    raise ValueError(
        f"Variables de entorno faltantes: {', '.join(missing)}\n\n"
        f"Configura de una de estas formas:\n"
        f"1. Variable STREAMLIT_SECRETS_TOML con contenido TOML:\n"
        f"   export STREAMLIT_SECRETS_TOML=\"$(cat secrets.toml)\"\n\n"
        f"2. O variables individuales:\n"
        f"   export SNOWFLAKE_ACCOUNT=xy12345.us-east-1\n"
        f"   export SNOWFLAKE_WAREHOUSE=COMPUTE_WH"
    )


def reset_session_state():
    """Reinicia el estado de la sesión."""
    st.session_state.messages = []
    st.session_state.active_suggestion = None
    st.session_state.warnings = []
    st.session_state.incidencia_data = None
