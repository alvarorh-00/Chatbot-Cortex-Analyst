"""
Módulo de utilidades generales
"""

import streamlit as st


def reset_session_state():
    """Reinicia el estado de la sesión."""
    st.session_state.messages = []
    st.session_state.active_suggestion = None
    st.session_state.warnings = []
    st.session_state.incidencia_data = None
