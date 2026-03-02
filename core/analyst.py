"""
Módulo de interacción con Cortex Analyst API y Vistas de Snowflake
"""

import requests
from typing import Dict, List, Optional, Tuple
import streamlit as st
from .ui import display_message
from .queries import get_all_analyst_results
from .ai_analysis import get_ai_analysis


def get_analyst_response_cortex(messages: List[Dict]) -> Tuple[Dict, Optional[str]]:
    """DEPRECATED: Usa Cortex Analyst API (mantener para compatibilidad)."""
    
    if "snowpark_session" not in st.session_state:
        return {}, "No hay una sesión activa de Snowflake."
    
    session = st.session_state.snowpark_session
    model_path = st.session_state.selected_semantic_model_path
    
    host = session.get_current_account().replace('"', '').lower()
    base_url = f"https://{host}.snowflakecomputing.com"
    api_endpoint = f"{base_url}/api/v2/cortex/analyst/message"
    
    request_body = {
        "messages": messages,
        "semantic_view": model_path 
    }

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
            timeout=60
        )
        
        parsed_content = response.json()
        if response.status_code == 200:
            return parsed_content, None
        else:
            error_msg = f"Error {response.status_code}: {parsed_content.get('message', 'Error desconocido')}"
            return parsed_content, error_msg
    except Exception as e:
        return {}, f"Error de red: {str(e)}"


def get_analyst_response(messages: List[Dict]) -> Dict:
    """
    Obtiene análisis de la incidencia ejecutando vistas de Snowflake.
    
    Retorna diccionario con resultados de:
    - diagnostico: Información diagnóstica
    - procedimientos: Procedimientos recomendados
    - historial: Incidencias similares
    """
    
    if "incidencia_data" not in st.session_state or st.session_state.incidencia_data is None:
        return {
            "error": "No hay datos de incidencia disponibles",
            "diagnostico": None,
            "procedimientos": None,
            "historial": None
        }
    
    # Ejecutar todas las vistas con los datos de la incidencia
    results = get_all_analyst_results(st.session_state.incidencia_data)
    
    return results


def process_user_input(prompt: str):
    """Procesa la entrada del usuario y obtiene respuesta del Analyst (vistas + IA)."""
    st.session_state.warnings = []
    new_user_message = {"role": "user", "content": [{"type": "text", "text": prompt}]}
    st.session_state.messages.append(new_user_message)
    
    with st.chat_message("user"):
        display_message(new_user_message["content"], len(st.session_state.messages) - 1)

    with st.chat_message("analyst"):
        # Paso 1: Ejecutar vistas de Snowflake
        with st.spinner("📊 Consultando vistas de Snowflake..."):
            response = get_analyst_response(st.session_state.messages)
        
        # Paso 2: Analizar con IA si hay datos
        ai_analysis = None
        model = st.session_state.get("cortex_model", "mistral-large")
        
        if "incidencia_data" in st.session_state and st.session_state.incidencia_data:
            with st.spinner(f"🤖 Analizando con IA ({model})..."):
                ai_analysis = get_ai_analysis(
                    st.session_state.incidencia_data, 
                    response,
                    model=model
                )
        
        # Construir mensaje de respuesta con análisis de IA + datos
        analyst_message = {
            "role": "analyst",
            "content": format_analyst_response(response, ai_analysis),
            "request_id": "N/A",
            "raw_data": response,  # Datos crudos de las vistas
            "ai_analysis": ai_analysis  # Análisis de IA
        }

        st.session_state.messages.append(analyst_message)
        st.rerun()


def format_analyst_response(results: Dict, ai_analysis: Optional[Dict] = None) -> List[Dict]:
    """
    Formatea los resultados de las vistas en formato de mensaje,
    incluyendo análisis de IA si está disponible.
    """
    content = []
    
    # 1. ANÁLISIS DE IA (si está disponible)
    if ai_analysis:
        if ai_analysis.get("error"):
            content.append({
                "type": "text",
                "text": f"⚠️ **Nota**: No se pudo generar análisis de IA: {ai_analysis['error']}\n\nMostrando datos sin procesar:"
            })
        elif ai_analysis.get("analysis"):
            content.append({
                "type": "text",
                "text": "## 🤖 Análisis Inteligente\n\n" + ai_analysis["analysis"]
            })
            content.append({
                "type": "text",
                "text": "\n---\n\n## 📊 Datos Detallados"
            })
    
    # 2. DATOS DE LAS VISTAS
    
    # Diagnóstico Paso 1: Tipo de Pedido
    if results.get("diagnostico_paso1"):
        diag_p1 = results["diagnostico_paso1"]
        if diag_p1["error"]:
            content.append({
                "type": "text",
                "text": f"❌ Error en {diag_p1['vista']}: {diag_p1['error']}"
            })
        elif diag_p1["data"] is not None and not diag_p1["data"].empty:
            content.append({
                "type": "text",
                "text": f"### {diag_p1['vista']}"
            })
            content.append({
                "type": "data_table",
                "data": diag_p1["data"]
            })
        else:
            content.append({
                "type": "text",
                "text": f"⚠️ {diag_p1['vista']}: No se encontraron resultados"
            })
    
    # Diagnóstico Paso 2: Estado ASN
    if results.get("diagnostico_paso2"):
        diag_p2 = results["diagnostico_paso2"]
        if diag_p2["error"]:
            content.append({
                "type": "text",
                "text": f"❌ Error en {diag_p2['vista']}: {diag_p2['error']}"
            })
        elif diag_p2["data"] is not None and not diag_p2["data"].empty:
            content.append({
                "type": "text",
                "text": f"### {diag_p2['vista']}"
            })
            content.append({
                "type": "data_table",
                "data": diag_p2["data"]
            })
        else:
            content.append({
                "type": "text",
                "text": f"⚠️ {diag_p2['vista']}: No se encontraron resultados"
            })
    
    if not content:
        content.append({
            "type": "text",
            "text": "❌ No se encontraron datos en las vistas configuradas.\n\nVerifica que:\n1. Las vistas existan en Snowflake\n2. Los parámetros de búsqueda sean correctos\n3. Las vistas contengan datos para esta incidencia"
        })
    
    return content
