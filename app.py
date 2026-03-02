"""
Sistema de Resolución de Incidencias de Pedidos
================================================
Captura incidencias mediante formulario y usa Cortex Analyst
para ejecutar SPs según árbol de decisión configurado en Semantic View.
"""
import streamlit as st
from core import (
    show_header_and_sidebar,
    reset_session_state,
    display_incidences_form,
    display_incidencia_summary,
    build_initial_prompt,
    process_user_input,
    display_conversation,
    handle_user_inputs,
    handle_error_notifications,
    display_warnings
)


def main():
    """Función principal de la aplicación."""
    st.set_page_config(
        page_title="Resolución de Incidencias de Pedidos", 
        layout="wide", 
        page_icon="📦"
    )
    st.title("📦 Sistema de Resolución de Incidencias de Pedidos")
    
    # Inicializar estado ANTES de show_header_and_sidebar
    if "incidencia_data" not in st.session_state:
        st.session_state.incidencia_data = None
    if "messages" not in st.session_state:
        reset_session_state()
    
    show_header_and_sidebar()
    
    # FLUJO: Si no hay incidencia capturada, mostrar formulario
    if st.session_state.incidencia_data is None:
        st.markdown("### Complete el formulario para reportar una incidencia")
        st.info("💡 Una vez enviada la incidencia, Agente Foundry analizará el caso y ejecutará los procedimientos necesarios según el árbol de decisión configurado.")
        display_incidences_form()
    else:
        # Si ya hay incidencia capturada, mostrar el chat con Cortex Analyst
        st.success(f"✅ Incidencia registrada: {st.session_state.incidencia_data.get('id', 'N/A')[:8]}...")
        
        with st.expander("📋 Ver datos de la incidencia", expanded=False):
            display_incidencia_summary(st.session_state.incidencia_data)
        
        st.markdown("---")
        st.markdown("### 💬 Resolución de Incidencia con Cortex Analyst")
        
        # Si el chat está vacío, iniciamos con el contexto de la incidencia
        if len(st.session_state.messages) == 0:
            initial_prompt = build_initial_prompt(st.session_state.incidencia_data)
            process_user_input(initial_prompt)
        
        display_conversation()
        handle_user_inputs()
        handle_error_notifications()
        display_warnings()


if __name__ == "__main__":
    main()