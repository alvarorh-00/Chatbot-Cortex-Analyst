"""
Core package for Sistema de Resolución de Incidencias de Pedidos
"""

from .auth import get_snowflake_session, get_available_semantic_views, show_header_and_sidebar
from .analyst import get_analyst_response, process_user_input, get_analyst_response_cortex
from .incidencia import (
    display_incidences_form, 
    display_incidencia_summary, 
    build_initial_prompt,
    save_incidencia_to_snowflake
)
from .ui import (
    display_conversation,
    display_message,
    display_sql_query,
    display_charts_tab,
    handle_user_inputs,
    handle_error_notifications,
    display_warnings
)
from .utils import reset_session_state
from .queries import (
    build_query,
    execute_vista_query,
    get_diagnostico_paso1,
    get_diagnostico_paso2,
    get_all_analyst_results
)
from .ai_analysis import (
    get_ai_analysis,
    get_available_cortex_models,
    build_analysis_prompt,
    analyze_with_cortex
)

__all__ = [
    'get_snowflake_session',
    'get_available_semantic_views',
    'show_header_and_sidebar',
    'get_analyst_response',
    'get_analyst_response_cortex',
    'process_user_input',
    'display_incidences_form',
    'display_incidencia_summary',
    'build_initial_prompt',
    'save_incidencia_to_snowflake',
    'display_conversation',
    'display_message',
    'display_sql_query',
    'display_charts_tab',
    'handle_user_inputs',
    'handle_error_notifications',
    'display_warnings',
    'reset_session_state',
    'build_query',
    'execute_vista_query',
    'get_diagnostico_paso1',
    'get_diagnostico_paso2',
    'get_all_analyst_results',
    'get_ai_analysis',
    'get_available_cortex_models',
    'build_analysis_prompt',
    'analyze_with_cortex'
]

