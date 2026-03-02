# 🚀 Sistema de Resolución de Incidencias de Pedidos

Esta aplicación de **Streamlit** actúa como un sistema inteligente para la **resolución de incidencias de pedidos**, combinando:
- **Formulario estructurado** para captura de datos de incidencia
- **Vistas analíticas de Snowflake** para diagnóstico automatizado
- **Análisis con IA (Cortex)** para interpretación en lenguaje natural
- **Interfaz conversacional** para seguimiento y resolución

---

## 🎯 Flujo de Trabajo

### 1. **Captura de Incidencia**
Usuario completa formulario con información específica:
- **UNECO**
- **Pedido Host**
- **Almacén / Centro Logístico**
- **Referencia**
- **Fechas (FEO, FIS)**
- **Estado Prepack**
- **Descripción del problema**

### 2. **Análisis Automatizado**
El sistema ejecuta vistas de Snowflake en paralelo:

#### **Vista Paso 1: Tipo de Pedido**
```sql
SELECT * FROM V_DIAGNOSTICO_PASO1_TIPO_PEDIDO 
WHERE CO_UNECO = '{uneco}' 
  AND CO_CENTRO_LOGISTICO = '{almacen}'
  AND CO_PEDIDO_HOST = '{pedido_host}'
```

#### **Vista Paso 2: Estado ASN**
```sql
SELECT * FROM V_DIAGNOSTICO_PASO2_ESTADO_ASN 
WHERE CO_PEDIDO = '{pedido_host}'
```

### 3. **Análisis con IA (Snowflake Cortex)**
La IA analiza los resultados y genera:
- 📊 **Interpretación del tipo de pedido**
- 📦 **Análisis del estado del ASN**
- ⚠️ **Identificación de diferencias/problemas**
- ✅ **Recomendaciones concretas de resolución**

### 4. **Presentación de Resultados**
- **Análisis en lenguaje natural** (generado por IA)
- **Tablas de datos detalladas** (con descarga CSV)
- **Conversación interactiva** para seguimiento

---

## 🤖 Análisis con IA (Snowflake Cortex)

El sistema usa **Snowflake Cortex COMPLETE** para analizar los datos de las vistas y generar respuestas en lenguaje natural.

### Modelos Disponibles:
- `mistral-large` (recomendado, por defecto)
- `mixtral-8x7b`
- `snowflake-arctic`
- `llama3-70b`
- `llama3-8b`
- `mistral-7b`
- `gemma-7b`

El modelo se selecciona desde el **sidebar** de la aplicación.

### Estructura del Análisis:
1. **Contexto**: Datos de la incidencia + resultados de las vistas
2. **Prompt**: Instrucciones para interpretar y analizar
3. **Respuesta IA**: Análisis estructurado con:
   - Tipo de pedido identificado
   - Estado del ASN
   - Problemas detectados
   - Recomendaciones de resolución
   - Alertas críticas

---

## 🏗️ Arquitectura del Sistema

```
Usuario
  ↓
[Formulario Incidencia]
  ↓
[Vistas Snowflake] → Diagnóstico Paso 1 (Tipo Pedido)
                   → Diagnóstico Paso 2 (Estado ASN)
  ↓
[Snowflake Cortex] → Análisis con IA
  ↓
[UI Streamlit] → Respuesta en lenguaje natural + Tablas de datos
```

---

## 🧠 1. ¿Qué es Cortex Analyst?

**Nota histórica:** Este sistema originalmente usaba Cortex Analyst API con Semantic Views. La arquitectura actual usa **consultas directas a vistas + Cortex COMPLETE** para mayor control y flexibilidad.

Cortex Analyst es un servicio totalmente gestionado de Snowflake diseñado para la **Analítica Self-Serve**. Proporciona una experiencia de analítica conversacional sobre datos estructurados con una precisión de grado empresarial.

### Beneficios Clave:
* **Analítica Self-Serve:** Permite a usuarios de negocio obtener respuestas mediante lenguaje natural sin conocimientos técnicos de SQL.
* **Text-to-SQL de Alta Precisión:** Supera a las soluciones "hazlo tú mismo" (DIY) gracias a su motor *agentic* optimizado que comprende profundamente el contexto del dato.
* **Integración Flexible:** Disponible vía REST API, facilitando su integración en Streamlit, Slack, Teams o cualquier aplicación personalizada.

<div align="center">
    <img src="doc/img/Arquitectura.png" alt="Arquitectura" width="800">  
    <br>
  <em>Flujo de comunicación entre la App de Streamlit y Snowflake Cortex Analyst.</em>
</div>

### Seguridad y Gobernanza (Privacy-First)
La IA de Cortex opera bajo los estándares de seguridad más estrictos de Snowflake:
* **Aislamiento de Datos:** Snowflake **no entrena** sus modelos con datos del cliente.
* **Inferencia Local:** Los datos y prompts nunca salen del perímetro de gobernanza de Snowflake.
* **RBAC Nativo:** Integración total con el control de acceso basado en roles. Si el usuario no tiene permiso `SELECT` sobre la tabla, la IA no puede consultar los datos.
* **Transparencia:** Para generar el SQL, solo utiliza los metadatos definidos en el modelo semántico.

---

## 🏗️ 2. El Modelo Semántico (Semantic Views)

El éxito de Cortex Analyst reside en el **Modelo Semántico**. Es el componente que traduce el lenguaje humano a la estructura técnica de la base de datos. Se puede configurar mediante archivos YAML o **Semantic Views**.

 <div align="center">
  <img src="doc/img/image.png" alt="Semantic View" width="800">  
    <br>
  <em>Ejemplo de configuración de Semantic View.</em>
</div>



### Componentes del Modelo:
* **Tablas Lógicas:** Representan entidades comerciales (Clientes, Pedidos, Productos). Incluyen descripciones detalladas y `sample_values`.
* **Dimensiones y Hechos:** Clasificación de datos categóricos (país, categoría) frente a datos cuantitativos a nivel de fila (montos, cantidades).
* **Métricas y Filtros:** Expresiones precalculadas (`expr`) para KPIs (ej: Ingresos totales = `SUM(price * qty)`). Aseguran que toda la empresa use la misma fórmula.
* **Relaciones:** Define explícitamente todos los **Joins**. Cortex Analyst **no unirá tablas** si no están declaradas explícitamente en el modelo.

### Mejores Prácticas:
* **Descripciones > Sinónimos:** Los modelos actuales deducen sinónimos; lo vital es una descripción de negocio clara y detallada.
* **Integración con Cortex Search:** Se puede vincular a columnas de alta cardinalidad para permitir búsquedas difusas (ej: encontrar "Gúgel" como "Google").

---

## ⚡ 3. Consultas Verificadas (Verified Queries)

Es la herramienta más potente para optimizar la precisión y el rendimiento del sistema.

* **¿Qué son?:** Pares de "Pregunta de usuario" + "SQL verificado" (se recomiendan de 10 a 20 ejemplos).
* **Beneficios:**
    * **Precisión:** Guían a la IA en lógicas de negocio complejas (como árboles de decisión).
    * **Velocidad:** Reducen la latencia al evitar llamadas innecesarias al LLM.
    * **Onboarding:** Pueden aparecer como sugerencias iniciales (`use_as_onboarding_question = true`).

---

## ⚙️ 4. Configuración en Snowflake

Para habilitar el servicio en esta aplicación, es necesario asignar los siguientes roles y privilegios:

1.  **Roles de Cortex:**
    * `SNOWFLAKE.CORTEX_USER`: Acceso general a funciones de IA.
    * `SNOWFLAKE.CORTEX_ANALYST_USER`: Acceso específico solo para Cortex Analyst (más seguro).

2.  **Privilegios de Acceso:**
    ```sql
    -- El rol de la App debe tener acceso a los metadatos y datos
    GRANT USAGE ON DATABASE MI_DB TO ROLE MI_ROL;
    GRANT USAGE ON SCHEMA MI_DB.MI_ESQUEMA TO ROLE MI_ROL;
    GRANT SELECT ON ALL SEMANTIC VIEWS IN SCHEMA MI_DB.MI_ESQUEMA TO ROLE MI_ROL;
    GRANT USAGE ON WAREHOUSE MI_WH TO ROLE MI_ROL;
    ```

---

## 💻 5. Instalación Local (VS Code)

1.  **Entorno Virtual:**
    ```bash
    python -m venv venv
    source venv/Scripts/activate
    ```

2.  **Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Secrets (`.streamlit/secrets.toml`):**
    ```toml
    [snowflake]
    account = "tu_id_cuenta.region"
    warehouse = "TU_WH"
    # El usuario y password se solicitan dinámicamente en la App
    ```

4.  **Ejecución:**
    ```bash
    streamlit run cortex_analyst_v2.py
    ```

---

## 🔄 6. Conversación Multi-turno (Contexto Iterativo)

La aplicación soporta conversaciones multi-turno, lo que permite al usuario profundizar en los datos. Por ejemplo:
1. *"¿Cuáles fueron las ventas del año pasado?"*
2. *"¿Y de esas, cuáles corresponden a España?"* (La IA recuerda el contexto anterior).

---

> **Nota:** Este proyecto está diseñado bajo el paradigma **Privacy-First**. La seguridad de los datos es la prioridad y se apoya totalmente en el RBAC nativo de Snowflake.