"""
Módulo de gestión de incidencias
"""

import uuid
from datetime import datetime
from typing import Dict
import pandas as pd
import streamlit as st


def display_incidences_form():
    """Muestra el formulario de captura de incidencias."""
    
    with st.form("incidence_form", clear_on_submit=True):
        # ID y timestamps automáticos
        incidence_id = str(uuid.uuid4())
        hora_inicio = datetime.now()
        
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.markdown("**🆔 ID de Incidencia:**")
            st.code(incidence_id[:8] + "...", language=None)
        with col_info2:
            st.markdown("**🕐 Hora de inicio:**")
            st.code(hora_inicio.strftime("%Y-%m-%d %H:%M:%S"), language=None)
        
        st.markdown("---")
        st.markdown("### 📋 Información del Pedido")
        
        col1, col2 = st.columns(2)
        
        with col1:
            uneco = st.text_input("UNECO *", placeholder="Código UNECO")
            pedido_host = st.text_input("Pedido Host *", placeholder="Número de pedido")
            almacen = st.text_input("Almacén o centro afectado *", placeholder="Nombre del almacén")
            referencia = st.text_input("Referencia afectada *", placeholder="Código de referencia")
        
        with col2:
            feo = st.date_input("FEO (Fecha) *", help="Fecha estimada de origen")
            fis = st.date_input("FIS (Fecha) *", help="Fecha de inicio de servicio")
            fecha_disponible = st.date_input("Fecha disponible de la mercancía *")
        
        st.markdown("### 📦 Información de Prepack")
        col3, col4 = st.columns(2)
        
        with col3:
            es_prepack = st.radio("¿Es un prepack? *", ["Sí", "No"], horizontal=True, index=1)
        
        with col4:
            tiene_marca_prepack = st.radio("¿Tiene puesta la marca de prepack? *", ["Sí", "No"], horizontal=True, index=1)
        
        st.markdown("### 📄 Descripción")
        descripcion = st.text_area(
            "Breve descripción de la incidencia *",
            placeholder="Describa detalladamente la incidencia encontrada...",
            height=150
        )
        
        st.markdown("### 📎 Adjuntos (opcional)")
        uploaded_files = st.file_uploader(
            "Adjuntar archivos",
            accept_multiple_files=True,
            help="Puede adjuntar imágenes, documentos PDF, Excel, etc."
        )
        
        st.markdown("---")
        st.caption("_* Campos obligatorios_")
        
        # Botón de envío
        submitted = st.form_submit_button("✅ Registrar Incidencia y Comenzar Análisis", use_container_width=True, type="primary")
        
        if submitted:
            # Validar campos obligatorios
            if not all([uneco, pedido_host, almacen, referencia, descripcion]):
                st.error("⚠️ Por favor, complete todos los campos obligatorios (marcados con *)")
            else:
                hora_finalizacion = datetime.now()
                
                # Preparar datos de la incidencia
                incidencia_data = {
                    "id": incidence_id,
                    "hora_inicio": hora_inicio,
                    "hora_finalizacion": hora_finalizacion,
                    "correo_electronico": st.session_state.get("user_email", "N/A"),
                    "nombre": st.session_state.get("user_name", "N/A"),
                    "uneco": uneco,
                    "pedido_host": pedido_host,
                    "almacen": almacen,
                    "referencia": referencia,
                    "feo": feo,
                    "fis": fis,
                    "fecha_disponible": fecha_disponible,
                    "es_prepack": es_prepack,
                    "tiene_marca_prepack": tiene_marca_prepack,
                    "descripcion": descripcion,
                    "num_adjuntos": len(uploaded_files) if uploaded_files else 0,
                    "adjuntos": [f.name for f in uploaded_files] if uploaded_files else []
                }
                
                # Guardar en el estado
                st.session_state.incidencia_data = incidencia_data
                
                # Opcional: Guardar en Snowflake
                # save_incidencia_to_snowflake(incidencia_data)
                
                st.success("✅ Incidencia registrada correctamente")
                st.info("🤖 Iniciando análisis con Cortex Analyst...")
                st.rerun()


def save_incidencia_to_snowflake(data: Dict) -> bool:
    """Guarda la incidencia en Snowflake (opcional)."""
    if "snowpark_session" not in st.session_state:
        return False
    
    try:
        session = st.session_state.snowpark_session
        
        # Preparar DataFrame
        df_data = data.copy()
        # Convertir fechas a string
        for col in ['hora_inicio', 'hora_finalizacion', 'feo', 'fis', 'fecha_disponible']:
            if col in df_data:
                df_data[col] = str(df_data[col])
        
        # Convertir lista de adjuntos a string
        if 'adjuntos' in df_data:
            df_data['adjuntos'] = ','.join(df_data['adjuntos'])
        
        df = pd.DataFrame([df_data])
        
        # Guardar en tabla (ajustar nombre según tu esquema)
        table_name = "INCIDENCIAS_PEDIDOS"
        session.write_pandas(
            df,
            table_name,
            auto_create_table=True,
            overwrite=False
        )
        return True
    except Exception as e:
        st.warning(f"No se pudo guardar en Snowflake: {str(e)}")
        return False


def display_incidencia_summary(data: Dict):
    """Muestra un resumen de la incidencia capturada."""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Información General**")
        st.write(f"📧 {data.get('correo_electronico', 'N/A')}")
        st.write(f"👤 {data.get('nombre', 'N/A')}")
        st.write(f"🆔 {data.get('id', 'N/A')[:13]}...")
    
    with col2:
        st.markdown("**Datos del Pedido**")
        st.write(f"UNECO: {data.get('uneco', 'N/A')}")
        st.write(f"Pedido: {data.get('pedido_host', 'N/A')}")
        st.write(f"Almacén: {data.get('almacen', 'N/A')}")
        st.write(f"Referencia: {data.get('referencia', 'N/A')}")
    
    with col3:
        st.markdown("**Fechas y Prepack**")
        st.write(f"FEO: {data.get('feo', 'N/A')}")
        st.write(f"FIS: {data.get('fis', 'N/A')}")
        st.write(f"Es prepack: {data.get('es_prepack', 'N/A')}")
        st.write(f"Marca prepack: {data.get('tiene_marca_prepack', 'N/A')}")
    
    st.markdown("**Descripción:**")
    st.info(data.get('descripcion', 'N/A'))
    
    if data.get('num_adjuntos', 0) > 0:
        st.markdown(f"**Adjuntos:** {data.get('num_adjuntos')} archivo(s)")


def build_initial_prompt(incidencia_data: Dict) -> str:
    """Construye el prompt inicial para Cortex Analyst con los datos de la incidencia."""
    prompt = f"""Tengo una incidencia de pedido con los siguientes datos:

- UNECO: {incidencia_data.get('uneco')}
- Pedido Host: {incidencia_data.get('pedido_host')}
- Almacén: {incidencia_data.get('almacen')}
- Referencia: {incidencia_data.get('referencia')}
- FEO: {incidencia_data.get('feo')}
- FIS: {incidencia_data.get('fis')}
- Fecha disponible mercancía: {incidencia_data.get('fecha_disponible')}
- Es prepack: {incidencia_data.get('es_prepack')}
- Tiene marca prepack: {incidencia_data.get('tiene_marca_prepack')}
- Descripción: {incidencia_data.get('descripcion')}

¿Qué procedimientos debo ejecutar para resolver esta incidencia según el árbol de decisión?"""
    
    return prompt
