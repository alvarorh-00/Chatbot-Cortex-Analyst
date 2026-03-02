# Core Package - Sistema de Resolución de Incidencias

Estructura modular del sistema de resolución de incidencias de pedidos con integración a vistas de Snowflake.

## Estructura de Módulos

```
core/
├── __init__.py         # Inicialización del package y exports
├── auth.py            # Autenticación y gestión de sesión Snowflake
├── analyst.py         # Ejecución de queries en vistas
├── queries.py         # Configuración y construcción de queries SQL
├── incidencia.py      # Gestión de incidencias (formulario, guardado)
├── ui.py              # Componentes de UI (chat, mensajes, tablas)
└── utils.py           # Utilidades generales (reset state, helpers)
```

## Flujo de Funcionamiento

### 1. **Captura de Incidencia** (`incidencia.py`)
Usuario completa formulario con:
- UNECO
- Pedido Host (CO_PEDIDO)
- Almacén / Centro Logístico
- Referencia
- Fechas (FEO, FIS)
- Estado Prepack (Sí/No)
- Descripción

### 2. **Análisis con Vistas** (`queries.py` + `analyst.py`)
Sistema ejecuta dos vistas en paralelo:

#### **Paso 1: Tipo de Pedido**
```sql
SELECT * FROM V_DIAGNOSTICO_PASO1_TIPO_PEDIDO 
WHERE 
  CO_UNECO = '{uneco}'
  AND CO_CENTRO_LOGISTICO = '{almacen}'
  AND CO_PEDIDO_HOST = '{pedido_host}'
```

Retorna: Tipo de pedido (AGRUPADO, AUTOVENTA, etc.)

#### **Paso 2: Estado ASN**
```sql
SELECT * FROM V_DIAGNOSTICO_PASO2_ESTADO_ASN 
WHERE 
  CO_PEDIDO = '{pedido_host}'
```

Retorna: Estado del ASN, cantidades, diferencias de revisión

### 3. **Presentación de Resultados** (`ui.py`)
Muestra tablas con:
- Botones de descarga CSV
- Formateo automático
- Errores claramente identificados

---

## Configuración de Vistas

En `core/queries.py`, modificar `VISTA_CONFIG`:

```python
VISTA_CONFIG = {
    "diagnostico_paso1": {
        "name": "V_DIAGNOSTICO_PASO1_TIPO_PEDIDO",
        "params": {
            "CO_UNECO": "uneco",           # Campo tabla ← campo formulario
            "CO_CENTRO_LOGISTICO": "almacen",
            "CO_PEDIDO_HOST": "pedido_host"
        },
        "description": "Diagnóstico Paso 1: Tipo de Pedido"
    },
    "diagnostico_paso2": {
        "name": "V_DIAGNOSTICO_PASO2_ESTADO_ASN",
        "params": {
            "CO_PEDIDO": "pedido_host"
        },
        "description": "Diagnóstico Paso 2: Estado ASN"
    }
}
```

### Mapeo de Parámetros

| Campo Formulario | Variable incidencia_data | Tabla Snowflake |
|---|---|---|
| UNECO | `uneco` | `CO_UNECO` |
| Almacén | `almacen` | `CO_CENTRO_LOGISTICO` |
| Pedido Host | `pedido_host` | `CO_PEDIDO_HOST`, `CO_PEDIDO` |
| Referencia | `referencia` | (a definir si se usa) |

---

## Descripción de Módulos

### `auth.py`
- **`get_snowflake_session(user, password)`**: Crea sesión Snowflake
- **`get_available_semantic_views()`**: Lista Semantic Views (si se usa)
- **`show_header_and_sidebar()`**: Login y configuración

### `queries.py` ⭐
- **`VISTA_CONFIG`**: Diccionario de vistas y parámetros
- **`build_query(vista_key, incidencia_data)`**: Construye SQL
- **`execute_vista_query(vista_key, incidencia_data)`**: Ejecuta contra Snowflake
- **`get_diagnostico_paso1(incidencia_data)`**: Obtiene tipo de pedido
- **`get_diagnostico_paso2(incidencia_data)`**: Obtiene estado ASN
- **`get_all_analyst_results(incidencia_data)`**: Ejecuta ambas vistas

### `analyst.py` ⭐
- **`get_analyst_response(messages)`**: Ejecuta vistas con datos de incidencia
- **`process_user_input(prompt)`**: Procesa entrada, ejecuta vistas y genera análisis de IA
- **`format_analyst_response(results, ai_analysis)`**: Formatea respuesta con análisis + datos

### `ai_analysis.py` 🤖 **NUEVO**
- **`get_ai_analysis(incidencia_data, results, model)`**: Orquesta análisis con IA
- **`build_analysis_prompt(incidencia_data, results)`**: Construye prompt con contexto
- **`analyze_with_cortex(prompt, model)`**: Ejecuta Snowflake Cortex COMPLETE
- **`get_available_cortex_models()`**: Lista modelos disponibles
- **`extract_key_metrics(df, vista_type)`**: Extrae métricas de DataFrames

### `incidencia.py`
- **`display_incidences_form()`**: Formulario de captura
- **`save_incidencia_to_snowflake(data)`**: Guarda en tabla
- **`display_incidencia_summary(data)`**: Muestra resumen
- **`build_initial_prompt(incidencia_data)`**: Construye prompt inicial

### `ui.py`
- **`display_message(content, message_index)`**: Renderiza mensajes/tablas
- **`display_conversation()`**: Historial del chat
- **`handle_user_inputs()`**: Input del usuario
- **`handle_error_notifications()`**: Notificaciones

### `utils.py`
- **`reset_session_state()`**: Limpia sesión

---

## 🤖 Análisis con IA (Snowflake Cortex)

### Flujo de Análisis Inteligente

1. **Captura datos**: Usuario completa formulario
2. **Ejecuta vistas**: Sistema consulta V_DIAGNOSTICO_PASO1 y PASO2
3. **Construye prompt**: Se crea contexto con datos de incidencia + resultados
4. **Llama a Cortex**: `SNOWFLAKE.CORTEX.COMPLETE(modelo, prompt)`
5. **Recibe análisis**: IA interpreta datos y genera respuesta en lenguaje natural
6. **Muestra resultados**: Análisis de IA + tablas de datos detalladas

### Prompt de Análisis

El prompt incluye:
- **Datos de incidencia**: UNECO, Pedido Host, Almacén, Referencia, fechas, descripción
- **Datos de Paso 1**: Tipo de pedido obtenido de la vista
- **Datos de Paso 2**: Estado ASN, diferencias de revisión, cantidades
- **Instrucciones**: Analizar, identificar problemas, dar recomendaciones

### Modelos Disponibles

Configurables desde el sidebar de la app:
- `mistral-large` (recomendado, por defecto)
- `mixtral-8x7b`
- `snowflake-arctic`
- `llama3-70b`
- `llama3-8b`
- `mistral-7b`
- `gemma-7b`

### Estructura de Respuesta IA

La IA analiza y responde con:
1. **Tipo de pedido** y explicación
2. **Estado del ASN** (Diferencias de revisión, cantidades)
3. **Problema principal** identificado
4. **Recomendaciones** concretas
5. **Alertas** o puntos críticos

### Ejemplo de Uso

```python
from core.ai_analysis import get_ai_analysis

# Después de ejecutar vistas
results = get_all_analyst_results(incidencia_data)

# Generar análisis con IA
ai_response = get_ai_analysis(
    incidencia_data=incidencia_data,
    results=results,
    model="mistral-large"
)

if ai_response["error"]:
    print(f"Error: {ai_response['error']}")
else:
    print(ai_response["analysis"])  # Texto en lenguaje natural
```

### Personalizar el Prompt

Para cambiar cómo la IA analiza los datos, editar `build_analysis_prompt()` en `core/ai_analysis.py`:
- Agregar más contexto (campos adicionales)
- Cambiar instrucciones al modelo
- Modificar formato de salida esperado

---

## Cómo Agregar Nuevas Vistas

1. Crear vista en Snowflake
2. Agregar entrada en `VISTA_CONFIG` en `core/queries.py`
3. Crear función `get_nuevo_diagnostico()` 
4. Agregar en `get_all_analyst_results()`
5. Importar en `__init__.py`

Ejemplo:
```python
# En queries.py
"diagnostico_paso3": {
    "name": "V_DIAGNOSTICO_PASO3_INVENTARIOS",
    "params": {
        "CO_REFERENCIA": "referencia",
        "CO_ALMACEN": "almacen"
    },
    "description": "Diagnóstico Paso 3: Inventarios"
}

def get_diagnostico_paso3(incidencia_data):
    return execute_vista_query("diagnostico_paso3", incidencia_data)
```

---

## Debugging

Para ver las queries ejecutadas, habilita logs en `core/queries.py`:
```python
# Línea ~70 - Ya habilitado por defecto:
print(f"Ejecutando query para {vista_key}:")
print(query)
```

Ver en consola Streamlit los SQL exactos que se ejecutan.

---

## Dependencias

- `streamlit`: Framework UI
- `snowflake-snowpark-python`: Conexión Snowflake
- `pandas`: Manipulación datos
- `requests`: (Cortex API opcional si se reaktiva)

