"""
Cortex Analyst App - Semantic Views Edition
==========================================
Esta versión utiliza Semantic Views y mantiene Verified Queries.
"""

import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException


# --- CONFIGURACIÓN DE CONEXIÓN .streamlit/secrets.toml
# --- 1. CONEXIÓN ---
# def get_snowflake_session():
#     if "snowpark_session" not in st.session_state:
#         try:
#             # Intentamos conectar usando los secretos
#             st.session_state.snowpark_session = Session.builder.configs(st.secrets["snowflake"]).create()
#         except Exception as e:
#             st.error(f"Error de conexión a Snowflake: {e}")
#             st.stop()
#     return st.session_state.snowpark_session


def get_snowflake_session(user, password):
    """Crea la sesión usando credenciales del usuario + valores estáticos del secreto."""
    try:
        connection_parameters = {
            "account": st.secrets["snowflake"]["account"],
            "warehouse": st.secrets["snowflake"]["warehouse"],
            "user": user,
            "password": password,
            # El rol es opcional; si no se pone, Snowflake usa el predeterminado del usuario
            "role": st.secrets["snowflake"].get("role") 
        }
        return Session.builder.configs(connection_parameters).create()
    except Exception as e:
        st.sidebar.error("Usuario o contraseña incorrectos.")
        return None

# session = get_snowflake_session()



# # --- CONFIGURACIÓN API ---
# HOST = session.get_current_account().replace('"', '').lower() #URL de la cuenta para construir endpoint
# BASE_URL = f"https://{HOST}.snowflakecomputing.com"
# API_ENDPOINT = f"{BASE_URL}/api/v2/cortex/analyst/message"
# API_TIMEOUT = 60 #segundos 

def get_available_semantic_views():
    # Buscamos la sesión que guardamos en el login
    if "snowpark_session" not in st.session_state:
        return []
    
    # Usamos la sesión del estado de Streamlit
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
def main():
    st.set_page_config(page_title="Cortex Analyst", layout="wide")
    st.title("Cortex Analyst")
    st.markdown("Interactúa con tus datos usando lenguaje natural a través de Semantic Views.")

    show_header_and_sidebar()
    

    # --- 4. CHAT ---
    if "messages" not in st.session_state:
        reset_session_state()
    
    # Si el chat está vacío, lanzamos la pregunta inicial
    if len(st.session_state.messages) == 0:
        process_user_input("What questions can I ask?")
        
    display_conversation()
    handle_user_inputs()
    handle_error_notifications()
    display_warnings()

def reset_session_state():
    st.session_state.messages = []
    st.session_state.active_suggestion = None
    st.session_state.warnings = []
    st.session_state.form_submitted = {}

def show_header_and_sidebar():
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
                            st.rerun()
                    else:
                        st.warning("Por favor, completa ambos campos.")
            st.stop() 
        
        # --- CÓDIGO SI YA ESTÁ LOGUEADO ---
        session = st.session_state.snowpark_session
        st.write(f"👤 **Usuario:** {session.get_current_user()}")
        st.write(f"🏗️ **Warehouse:** {session.get_current_warehouse()}")
        st.write(f"**Role:** {session.get_current_role()}")
        
        if st.button("Cerrar Sesión", type="primary"):
            session.close()
            del st.session_state.snowpark_session
            st.session_state.messages = [] 
            st.rerun()

        # --- 3. CARGA DE MODELOS SEMÁNTICOS ---
        available_views = get_available_semantic_views()

        if not available_views:
            st.warning("⚠️ No tienes acceso a ningún modelo semántico con tu rol actual.")
        else:
            st.selectbox(
                "Selecciona el área de datos:",
                available_views,
                key="selected_semantic_model_path",
                on_change=reset_session_state # Importante para limpiar el chat al cambiar de modelo
            )
        
        st.divider()
        if st.button("Clear Chat History", use_container_width=True):
            reset_session_state()
            st.rerun()

def get_analyst_response(messages: List[Dict]) -> Tuple[Dict, Optional[str]]:
    """Calcula el endpoint y envía la petición usando la sesión activa."""
    
    # 1. Recuperamos la sesión del estado de Streamlit
    if "snowpark_session" not in st.session_state:
        return {}, "No hay una sesión activa de Snowflake."
    
    session = st.session_state.snowpark_session
    model_path = st.session_state.selected_semantic_model_path
    
    # 2. CONFIGURACIÓN DINÁMICA DEL ENDPOINT
    # Lo calculamos aquí dentro porque aquí ya sabemos que 'session' existe
    host = session.get_current_account().replace('"', '').lower()
    base_url = f"https://{host}.snowflakecomputing.com"
    api_endpoint = f"{base_url}/api/v2/cortex/analyst/message"
    
    # 3. PREPARACIÓN DE LA PETICIÓN
    request_body = {
        "messages": messages,
        "semantic_view": model_path 
    }

    # El token se extrae de la conexión actual
    token = session._conn._conn.rest.token

    headers = {
        "Authorization": f'Snowflake Token="{token}"',
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        response = requests.post(
            api_endpoint, 
            headers=headers, 
            json=request_body, 
            timeout=60 # Timeout de 1 minuto
        )
        
        parsed_content = response.json()
        if response.status_code == 200:
            return parsed_content, None
        else:
            error_msg = f"Error {response.status_code}: {parsed_content.get('message', 'Error desconocido')}"
            return parsed_content, error_msg
    except Exception as e:
        return {}, f"Error de red: {str(e)}"

# --- PROCESAMIENTO Y VISUALIZACIÓN ---

def process_user_input(prompt: str):
    st.session_state.warnings = []
    new_user_message = {"role": "user", "content": [{"type": "text", "text": prompt}]}
    st.session_state.messages.append(new_user_message)
    
    with st.chat_message("user"):
        display_message(new_user_message["content"], len(st.session_state.messages) - 1)

    with st.chat_message("analyst"):
        with st.spinner("Waiting for Analyst's response..."):
            response, error_msg = get_analyst_response(st.session_state.messages)
            if error_msg is None:
                analyst_message = {
                    "role": "analyst",
                    "content": response["message"]["content"],
                    "request_id": response["request_id"],
                }
            else:
                analyst_message = {
                    "role": "analyst",
                    "content": [{"type": "text", "text": error_msg}],
                    "request_id": response.get("request_id", "N/A"),
                }
                st.session_state["fire_API_error_notify"] = True

            if "warnings" in response:
                st.session_state.warnings = response["warnings"]

            st.session_state.messages.append(analyst_message)
            st.rerun()

def display_message(content: List[Dict], message_index: int, request_id: str = None):
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "suggestions":
            for i, suggestion in enumerate(item["suggestions"]):
                if st.button(suggestion, key=f"sug_{message_index}_{i}"):
                    st.session_state.active_suggestion = suggestion
                    st.rerun()
        elif item["type"] == "sql":
            display_sql_query(item["statement"], message_index, item["confidence"], request_id)

def display_sql_query(sql: str, message_index: int, confidence: dict, request_id: str = None):
    with st.expander("SQL Query", expanded=False):
        st.code(sql, language="sql")
        # Aquí se muestran las VERIFIED QUERIES si se usaron
        if confidence and confidence.get("verified_query_used"):
            display_sql_confidence(confidence)

    with st.expander("Results", expanded=True):
        df, err_msg = get_query_exec_result(sql)
        if df is not None:
            if df.empty:
                st.write("No data returned.")
            else:
                tab1, tab2 = st.tabs(["Data 📄", "Chart 📉"])
                with tab1:
                    st.dataframe(df, use_container_width=True)
                with tab2:
                    display_charts_tab(df, message_index)
        else:
            st.error(f"SQL Error: {err_msg}")
    
    if request_id:
        display_feedback_section(request_id)

# --- FUNCIONES AUXILIARES (Tablas, Feedback, etc.) ---

#@st.cache_data(show_spinner=False)
def get_query_exec_result(query: str):
    # 1. Recuperamos la sesión del estado de Streamlit
    if "snowpark_session" not in st.session_state:
        return None, "No hay sesión activa."
    
    session_ejecucion = st.session_state.snowpark_session
    
    try:
        # 2. Ejecutamos la consulta
        return session_ejecucion.sql(query).to_pandas(), None
    except Exception as e:
        return None, str(e)

def display_sql_confidence(confidence: dict):
    vq = confidence["verified_query_used"]
    with st.popover("✅ Verified Query Used"):
        st.markdown(f"**Name:** {vq['name']}")
        st.markdown(f"**Question:** {vq['question']}")
        st.markdown(f"**Verified by:** {vq['verified_by']}")
        st.code(vq["sql"], language="sql")

def handle_user_inputs():
    user_input = st.chat_input("What is your question?")
    if user_input:
        process_user_input(user_input)
    elif st.session_state.active_suggestion:
        sug = st.session_state.active_suggestion
        st.session_state.active_suggestion = None
        process_user_input(sug)

def display_conversation():
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            display_message(message["content"], idx, message.get("request_id"))

def handle_error_notifications():
    if st.session_state.get("fire_API_error_notify"):
        st.toast("An API error has occurred!", icon="🚨")
        st.session_state["fire_API_error_notify"] = False

def display_warnings():
    for warning in st.session_state.warnings:
        st.warning(warning["message"], icon="⚠️")

def display_charts_tab(df: pd.DataFrame, message_index: int):
    if len(df.columns) >= 2:
        cols = list(df.columns)
        x = st.selectbox("X axis", cols, key=f"x_{message_index}")
        y = st.selectbox("Y axis", [c for c in cols if c != x], key=f"y_{message_index}")
        if st.selectbox("Type", ["Bar", "Line"], key=f"t_{message_index}") == "Bar":
            st.bar_chart(df.set_index(x)[y])
        else:
            st.line_chart(df.set_index(x)[y])

def display_feedback_section(request_id: str):
    # Lógica de feedback simplificada para el ejemplo
    pass

if __name__ == "__main__":
    main()