"""
Módulo de IA para análisis e interpretación de resultados
Usa Snowflake Cortex para generar respuestas en lenguaje natural
"""

from typing import Dict, List
import pandas as pd
import streamlit as st


def get_available_cortex_models() -> List[str]:
    """Obtiene los modelos Cortex disponibles en la cuenta."""
    # Modelos comunes de Snowflake Cortex
    return [
        "mistral-large",
        "mixtral-8x7b",
        "snowflake-arctic",
        "llama3-70b",
        "llama3-8b",
        "mistral-7b",
        "gemma-7b"
    ]


def build_analysis_prompt(incidencia_data: Dict, results: Dict) -> str:
    """
    Construye el prompt para que la IA analice los resultados.
    
    Args:
        incidencia_data: Datos del formulario de incidencia
        results: Resultados de las vistas ejecutadas
        
    Returns:
        Prompt formateado para el LLM
    """
    
    # Construir contexto de la incidencia
    context = f"""Eres un asistente experto en logística y gestión de pedidos. 
Analiza la siguiente incidencia de pedido y los datos obtenidos de las vistas de diagnóstico.

**DATOS DE LA INCIDENCIA:**
- UNECO: {incidencia_data.get('uneco')}
- Pedido Host: {incidencia_data.get('pedido_host')}
- Almacén/Centro: {incidencia_data.get('almacen')}
- Referencia: {incidencia_data.get('referencia')}
- FEO: {incidencia_data.get('feo')}
- FIS: {incidencia_data.get('fis')}
- Es Prepack: {incidencia_data.get('es_prepack')}
- Tiene marca prepack: {incidencia_data.get('tiene_marca_prepack')}
- Descripción: {incidencia_data.get('descripcion')}
"""
    
    # Agregar datos de Paso 1 (Tipo de Pedido)
    if results.get("diagnostico_paso1"):
        paso1 = results["diagnostico_paso1"]
        if paso1["data"] is not None and not paso1["data"].empty:
            df1 = paso1["data"]
            context += f"\n\n**DIAGNÓSTICO PASO 1 - TIPO DE PEDIDO:**\n"
            context += f"Se encontraron {len(df1)} registro(s):\n"
            context += df1.to_string(index=False, max_rows=5)
        elif paso1["error"]:
            context += f"\n\n**DIAGNÓSTICO PASO 1:** Error - {paso1['error']}"
        else:
            context += f"\n\n**DIAGNÓSTICO PASO 1:** No se encontraron datos"
    
    # Agregar datos de Paso 2 (Estado ASN)
    if results.get("diagnostico_paso2"):
        paso2 = results["diagnostico_paso2"]
        if paso2["data"] is not None and not paso2["data"].empty:
            df2 = paso2["data"]
            context += f"\n\n**DIAGNÓSTICO PASO 2 - ESTADO ASN:**\n"
            context += f"Se encontraron {len(df2)} registro(s):\n"
            context += df2.to_string(index=False, max_rows=10)
        elif paso2["error"]:
            context += f"\n\n**DIAGNÓSTICO PASO 2:** Error - {paso2['error']}"
        else:
            context += f"\n\n**DIAGNÓSTICO PASO 2:** No se encontraron datos"
    
    # Instrucciones para la IA
    context += """

**TU TAREA:**
1. Analiza la información de la incidencia y los datos de diagnóstico
2. Identifica el TIPO DE PEDIDO y explica qué significa
3. Analiza el ESTADO del ASN y las DIFERENCIAS DE REVISIÓN si las hay
4. Identifica el PROBLEMA PRINCIPAL de esta incidencia
5. Proporciona RECOMENDACIONES concretas para resolver la incidencia
6. Menciona si hay ALERTAS o puntos críticos a revisar

**FORMATO DE RESPUESTA:**
- Usa lenguaje claro y profesional en español
- Usa emojis para mejorar la legibilidad (📊 📦 ⚠️ ✅ ❌)
- Estructura tu respuesta con títulos claros
- Si hay diferencias de revisión, resáltalas claramente
- Si no hay datos, indica posibles razones
- Da una respuesta de 1 linea, comentando solo como está el pedido

Genera tu análisis ahora:"""
    
    return context


def analyze_with_cortex(prompt: str, model: str = "mistral-large") -> tuple[str, str]:
    """
    Ejecuta análisis usando Snowflake Cortex COMPLETE.
    
    Args:
        prompt: Prompt con contexto y datos
        model: Modelo de Cortex a usar
        
    Returns:
        (respuesta_ia, error_msg)
    """
    if "snowpark_session" not in st.session_state:
        return None, "No hay sesión activa de Snowflake"
    
    try:
        session = st.session_state.snowpark_session
        
        # Escapar comillas simples en el prompt
        prompt_escaped = prompt.replace("'", "''")
        
        # Construir query para Snowflake Cortex
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            '{prompt_escaped}'
        ) AS response
        """
        
        print(f"\n🤖 Llamando a Cortex modelo: {model}")
        print(f"Longitud del prompt: {len(prompt)} caracteres")
        
        result = session.sql(query).collect()
        
        if result and len(result) > 0:
            response_text = result[0]["RESPONSE"]
            return response_text, None
        else:
            return None, "No se obtuvo respuesta del modelo Cortex"
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error en Cortex: {error_msg}")
        
        # Si el modelo no está disponible, sugerir alternativas
        if "does not exist" in error_msg.lower() or "not found" in error_msg.lower():
            return None, f"El modelo '{model}' no está disponible. Intenta con: {', '.join(get_available_cortex_models()[:3])}"
        
        return None, f"Error al analizar con Cortex: {error_msg}"


def get_ai_analysis(incidencia_data: Dict, results: Dict, model: str = "mistral-large") -> Dict:
    """
    Obtiene análisis completo de la incidencia usando IA.
    
    Args:
        incidencia_data: Datos del formulario
        results: Resultados de las vistas
        model: Modelo de Cortex a usar
        
    Returns:
        Diccionario con análisis y metadatos
    """
    
    # Construir prompt
    prompt = build_analysis_prompt(incidencia_data, results)
    
    # Analizar con Cortex
    analysis, error = analyze_with_cortex(prompt, model)
    
    return {
        "analysis": analysis,
        "error": error,
        "model": model,
        "prompt_length": len(prompt)
    }


def extract_key_metrics(df: pd.DataFrame, vista_type: str) -> Dict:
    """
    Extrae métricas clave de un DataFrame para análisis rápido.
    
    Args:
        df: DataFrame con resultados
        vista_type: 'paso1' o 'paso2'
        
    Returns:
        Diccionario con métricas clave
    """
    if df is None or df.empty:
        return {}
    
    metrics = {
        "num_registros": len(df),
        "columnas": list(df.columns)
    }
    
    if vista_type == "paso1":
        if "TIPO_PEDIDO" in df.columns:
            metrics["tipo_pedido"] = df["TIPO_PEDIDO"].iloc[0] if len(df) > 0 else None
    
    elif vista_type == "paso2":
        if "DIFERENCIAS_REVISION" in df.columns:
            total_dif = df["DIFERENCIAS_REVISION"].sum()
            metrics["diferencias_total"] = float(total_dif) if pd.notna(total_dif) else 0
            metrics["hay_diferencias"] = metrics["diferencias_total"] != 0
        
        if "CO_ESTADO_PREALBARAN" in df.columns:
            estados = df["CO_ESTADO_PREALBARAN"].value_counts().to_dict()
            metrics["estados_asn"] = estados
    
    return metrics
