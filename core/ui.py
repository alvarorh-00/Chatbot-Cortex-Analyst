"""
Módulo de componentes de interfaz de usuario (UI)
"""

from datetime import datetime
from typing import Dict, List
import pandas as pd
import streamlit as st


def display_message(content: List[Dict], message_index: int, request_id: str = None):
    """Muestra el contenido de un mensaje (texto, tablas, sugerencias o SQL)."""
    for item in content:
        if item["type"] == "text":
            st.markdown(item["text"])
        elif item["type"] == "data_table":
            # Mostrar tabla de datos
            st.dataframe(item["data"], use_container_width=True)
            
            # Botón de descarga
            csv = item["data"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar tabla como CSV",
                data=csv,
                file_name=f"analyst_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime='text/csv',
                key=f"download_{message_index}_{id(item)}"
            )
        elif item["type"] == "suggestions":
            for i, suggestion in enumerate(item["suggestions"]):
                if st.button(suggestion, key=f"sug_{message_index}_{i}"):
                    st.session_state.active_suggestion = suggestion
                    st.rerun()
        elif item["type"] == "sql":
            display_sql_query(item["statement"], message_index, item["confidence"], request_id)


def display_sql_query(sql: str, message_index: int, confidence: dict, request_id: str = None):
    """Muestra una consulta SQL con sus resultados."""
    with st.expander("SQL Query", expanded=False):
        st.code(sql, language="sql")
        # Mostrar VERIFIED QUERIES si se usaron
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
                    
                    # Botón de descarga
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar datos como CSV",
                        data=csv,
                        file_name=f"analyst_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime='text/csv',
                    )
                with tab2:
                    display_charts_tab(df, message_index)
        else:
            st.error(f"SQL Error: {err_msg}")
    
    if request_id:
        display_feedback_section(request_id)


def get_query_exec_result(query: str):
    """Ejecuta una consulta SQL en Snowflake."""
    if "snowpark_session" not in st.session_state:
        return None, "No hay sesión activa."
    
    session_ejecucion = st.session_state.snowpark_session
    
    try:
        return session_ejecucion.sql(query).to_pandas(), None
    except Exception as e:
        return None, str(e)


def display_sql_confidence(confidence: dict):
    """Muestra información sobre verified queries usadas."""
    vq = confidence["verified_query_used"]
    with st.popover("✅ Verified Query Used"):
        st.markdown(f"**Name:** {vq['name']}")
        st.markdown(f"**Question:** {vq['question']}")
        st.markdown(f"**Verified by:** {vq['verified_by']}")
        st.code(vq["sql"], language="sql")


def display_charts_tab(df: pd.DataFrame, message_index: int):
    """Muestra opciones de gráficos para los datos."""
    if len(df.columns) >= 2:
        # Detectar columnas de fecha
        cols = list(df.columns)
        date_cols = [c for c in cols if "DATE" in c.upper() or "TIME" in c.upper()]
        
        # Si hay fechas, las ponemos por defecto en el eje X
        default_x = date_cols[0] if date_cols else cols[0]
        
        x = st.selectbox("Eje X", cols, index=cols.index(default_x), key=f"x_{message_index}")
        y = st.selectbox("Eje Y", [c for c in cols if c != x], key=f"y_{message_index}")
        
        chart_type = st.selectbox("Tipo de gráfico", ["Lineas", "Barras"], key=f"t_{message_index}")
        
        if chart_type == "Lineas":
            st.line_chart(df.set_index(x)[y])
        else:
            st.bar_chart(df.set_index(x)[y])


def display_conversation():
    """Muestra toda la conversación del chat."""
    for idx, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            display_message(message["content"], idx, message.get("request_id"))


def handle_user_inputs():
    """Maneja la entrada de texto del usuario."""
    # Import local para evitar dependencias circulares
    from .analyst import process_user_input
    
    user_input = st.chat_input("¿Qué necesitas saber?")
    if user_input:
        process_user_input(user_input)
    elif st.session_state.active_suggestion:
        sug = st.session_state.active_suggestion
        st.session_state.active_suggestion = None
        process_user_input(sug)


def handle_error_notifications():
    """Muestra notificaciones de error si las hay."""
    if st.session_state.get("fire_API_error_notify"):
        st.toast("¡Ha ocurrido un error en la API!", icon="🚨")
        st.session_state["fire_API_error_notify"] = False


def display_warnings():
    """Muestra advertencias si las hay."""
    for warning in st.session_state.warnings:
        st.warning(warning["message"], icon="⚠️")


def display_feedback_section(request_id: str):
    """Lógica de feedback (simplificada para el ejemplo)."""
    pass
