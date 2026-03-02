"""
Módulo de autenticación y sesión de Snowflake
"""

import os
import streamlit as st
from snowflake.snowpark import Session
from .utils import reset_session_state, get_config


def get_snowflake_session(user: str, password: str):
    """Crea la sesión usando credenciales del usuario + valores estáticos del entorno."""
    try:
        config = get_config()
        connection_parameters = {
            "account": config["snowflake_account"],
            "warehouse": config["snowflake_warehouse"],
            "user": user,
            "password": password
        }
        return Session.builder.configs(connection_parameters).create()
    except Exception as e:
        st.sidebar.error("Usuario o contraseña incorrectos.")
        return None


def get_available_semantic_views():
    """Obtiene la lista de Semantic Views disponibles en la cuenta."""
    if "snowpark_session" not in st.session_state:
        return []
    
    session_local = st.session_state.snowpark_session
    
    try:
        df = session_local.sql("SHOW SEMANTIC VIEWS IN ACCOUNT").to_pandas()
        if df.empty:
            return []
        
        df.columns = [col.strip().replace('"', '').upper() for col in df.columns]
        if all(col in df.columns for col in ['DATABASE_NAME', 'SCHEMA_NAME', 'NAME']):
            return (df['DATABASE_NAME'] + "." + df['SCHEMA_NAME'] + "." + df['NAME']).tolist()

        return []
    except Exception as e:
        return []


def show_header_and_sidebar():
    """Muestra el sidebar con login y configuración."""
    with st.sidebar:
        st.title("🔐 Acceso")
        
        if "snowpark_session" not in st.session_state:
            with st.form("login_form"):
                user_val = st.text_input("Usuario de Snowflake")
                pass_val = st.text_input("Contraseña", type="password")
                submit = st.form_submit_button("Entrar", use_container_width=True)
                
                if submit:
                    if user_val and pass_val:
                        session_obj = get_snowflake_session(user_val, pass_val)
                        if session_obj:
                            st.session_state.snowpark_session = session_obj
                            st.session_state.user_email = user_val
                            st.session_state.user_name = user_val.split('@')[0] if '@' in user_val else user_val
                            st.rerun()
                    else:
                        st.warning("Por favor, completa ambos campos.")
            st.stop() 
        
        # --- CÓDIGO SI YA ESTÁ LOGUEADO ---
        session = st.session_state.snowpark_session
        st.success("✅ Conectado")
        st.write(f"👤 **Usuario:** {session.get_current_user()}")
        st.write(f"🏗️ **Warehouse:** {session.get_current_warehouse()}")
        
        if st.button("Cerrar Sesión", type="primary", use_container_width=True):
            session.close()
            del st.session_state.snowpark_session
            reset_session_state()
            st.rerun()

        st.divider()
        
        # --- SEMANTIC VIEW ---
        st.markdown("### ⚙️ Configuración")
        available_views = get_available_semantic_views()

        if not available_views:
            st.warning("⚠️ No hay modelos semánticos disponibles.")
        else:
            def on_model_change():
                # Solo resetear el chat, no la incidencia
                st.session_state.messages = []
                st.session_state.active_suggestion = None
                st.session_state.warnings = []
            
            st.selectbox(
                "Semantic View:",
                available_views,
                key="selected_semantic_model_path",
                help="Contiene el árbol de decisión y SPs a ejecutar",
                on_change=on_model_change
            )
        
        # --- MODELO CORTEX ---
        st.markdown("#### 🤖 Modelo IA")
        
        cortex_models = [
            "mistral-large",
            "mixtral-8x7b", 
            "snowflake-arctic",
            "llama3-70b",
            "llama3-8b",
            "mistral-7b",
            "gemma-7b"
        ]
        
        # Inicializar modelo por defecto si no existe
        if "cortex_model" not in st.session_state:
            st.session_state.cortex_model = "mistral-large"
        
        st.selectbox(
            "Modelo Cortex:",
            cortex_models,
            key="cortex_model",
            help="Modelo de IA que analizará los datos de las vistas",
            index=cortex_models.index(st.session_state.get("cortex_model", "mistral-large"))
        )
        
        st.divider()
        
        # --- ACCIONES ---
        if st.session_state.incidencia_data is not None:
            if st.button("🔄 Nueva Incidencia", use_container_width=True):
                reset_session_state()
                st.rerun()
        
        if st.button("🗑️ Limpiar Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.warnings = []
            st.rerun()
