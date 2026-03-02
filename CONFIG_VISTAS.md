# Configuración Actual del Sistema - Vistas Snowflake

## Vistas Configuradas

El sistema está configurado para ejecutar **2 vistas** en serie para analizar cada incidencia:

### **PASO 1: Tipo de Pedido**
**Vista:** `V_DIAGNOSTICO_PASO1_TIPO_PEDIDO`

Determina el tipo de pedido basado en el código de proceso de agregación.

#### Parámetros de entrada (WHERE):
```
CO_UNECO = <valor formulario: "uneco">
CO_CENTRO_LOGISTICO = <valor formulario: "almacen">
CO_PEDIDO_HOST = <valor formulario: "pedido_host">
```

#### Valores retornados:
- `TIPO_PEDIDO`: AGRUPADOS, AUTOVENTA, PEDIDO DIRECTO A CENTRO, ALMACENABLE, PREPACK, OTRO TIPO
- `CO_PEDIDO`: Código del pedido
- `CO_UNECO`: UNECO consultor
- `CO_CENTRO_LOGISTICO`: Centro logístico
- `CO_PEDIDO_HOST`: Pedido host

#### Lógica (CASE):
```
'03' → AGRUPADOS
'01' → AUTOVENTA
'02', '06' → PEDIDO DIRECTO A CENTRO
'04' + sin prepack → ALMACENABLE
'04' + con prepack → PREPACK
default → OTRO TIPO
```

---

### **PASO 2: Estado ASN**
**Vista:** `V_DIAGNOSTICO_PASO2_ESTADO_ASN`

Obtiene detalles del ASN, estado del entrega y diferencias de revisión.

#### Parámetros de entrada (WHERE):
```
CO_PEDIDO = <valor formulario: "pedido_host">
```

#### Valores retornados:
- `CO_PEDIDO`: Código pedido
- `CO_POSICION_PEDIDO`: Posición en el pedido
- `DS_DESCRIPCION_CORTA`: Descripción del artículo
- `CO_MATERIAL`: Material
- `CO_ALBARAN`: Albarán/ASN
- `ASN`: Identificador ASN concatenado
- `CO_ESTADO_PREALBARAN`: Estado del pre-albarán
- `FECHA_ULT_REVISION`: Última fecha revisar
- `QT_PEDIDO`: Cantidad pedida
- `CANTIDAD_REVISADA_ASN`: Cantidad revisada del ASN
- `DIFERENCIAS_REVISION`: Diferencias (Pedido - Revisado)
- `CO_REFERENCIA`: Referencia
- `CO_REFERENCIA_TALLA`: Talla de referencia

#### Cálculos:
```
CANTIDAD_REVISADA_ASN = Σ(+cantidad cuando positivo, -cantidad cuando negativo)
DIFERENCIAS_REVISION = QT_PEDIDO - CANTIDAD_REVISADA_ASN
```

---

## Mapeo Formulario → Vistas

| Campo Formulario | Variable Python | BD Snowflake | VW Paso 1 | VW Paso 2 |
|---|---|---|---|---|
| UNECO | `incidencia_data["uneco"]` | CO_UNECO | ✅ WHERE | - |
| Almacén | `incidencia_data["almacen"]` | CO_CENTRO_LOGISTICO | ✅ WHERE | - |
| Pedido Host | `incidencia_data["pedido_host"]` | CO_PEDIDO_HOST | ✅ WHERE | ✅ WHERE |
| Referencia | `incidencia_data["referencia"]` | CO_REFERENCIA | - | (Select) |
| FEO | `incidencia_data["feo"]` | (fecha) | - | - |
| FIS | `incidencia_data["fis"]` | (fecha) | - | - |
| Es Prepack | `incidencia_data["es_prepack"]` | CO_IND_PREPACK | (CASE) | - |
| Descripción | `incidencia_data["descripcion"]` | - | - | - |

---

## Flujo Ejecución

```
1. Usuario completa formulario
   ↓
2. Guarda en st.session_state.incidencia_data
   ↓
3. Llama a process_user_input() con prompt inicial
   ↓
4. get_analyst_response() extrae incidencia_data
   ↓
5. get_all_analyst_results(incidencia_data)
   ├─→ get_diagnostico_paso1(incidencia_data)
   │   └─→ execute_vista_query("diagnostico_paso1", incidencia_data)
   │       └─→ build_query("diagnostico_paso1", incidencia_data)
   │           └─→ SQL: SELECT * FROM VW_PASO1 WHERE CO_UNECO='...' AND CO_CENTRO_LOGISTICO='...' AND CO_PEDIDO_HOST='...'
   │
   └─→ get_diagnostico_paso2(incidencia_data)
       └─→ execute_vista_query("diagnostico_paso2", incidencia_data)
           └─→ build_query("diagnostico_paso2", incidencia_data)
               └─→ SQL: SELECT * FROM VW_PASO2 WHERE CO_PEDIDO='...'
   ↓
6. format_analyst_response(results)
   └─→ [Paso 1 tabla] + [Paso 2 tabla]
   ↓
7. display_conversation() muestra en chat
```

---

## Archivos de Configuración

### **core/queries.py** - Define las vistas
```python
VISTA_CONFIG = {
    "diagnostico_paso1": {
        "name": "V_DIAGNOSTICO_PASO1_TIPO_PEDIDO",
        "params": {
            "CO_UNECO": "uneco",
            "CO_CENTRO_LOGISTICO": "almacen",
            "CO_PEDIDO_HOST": "pedido_host"
        },
        "description": "📊 Diagnóstico Paso 1: Tipo de Pedido"
    },
    "diagnostico_paso2": {
        "name": "V_DIAGNOSTICO_PASO2_ESTADO_ASN",
        "params": {
            "CO_PEDIDO": "pedido_host"
        },
        "description": "📊 Diagnóstico Paso 2: Estado ASN y Revisiones"
    }
}
```

### **core/analyst.py** - Ejecuta las vistas
```python
def get_analyst_response(messages):
    return get_all_analyst_results(st.session_state.incidencia_data)
```

### **core/incidencia.py** - Captura formulario
```python
incidencia_data = {
    "uneco": uneco,
    "almacen": almacen,
    "pedido_host": pedido_host,
    # ... más campos
}
st.session_state.incidencia_data = incidencia_data
```

---

## Debugging y Logs

Los SQL generados se imprimen en consola (terminal donde corre Streamlit):

```
Ejecutando query para diagnostico_paso1:
SELECT * FROM V_DIAGNOSTICO_PASO1_TIPO_PEDIDO WHERE CO_UNECO = 'UNECO123' AND CO_CENTRO_LOGISTICO = 'MADRID' AND CO_PEDIDO_HOST = 'PEDIDO456'

Ejecutando query para diagnostico_paso2:
SELECT * FROM V_DIAGNOSTICO_PASO2_ESTADO_ASN WHERE CO_PEDIDO = 'PEDIDO456'
```

---

## Próximos Pasos (Extensión)

Si quieres agregar más vistas (PASO 3, 4, etc.):

1. **Crear vista en Snowflake**
   ```sql
   CREATE OR REPLACE VIEW V_DIAGNOSTICO_PASO3_... AS
   SELECT ... FROM ... WHERE CO_CAMPO = ?
   ```

2. **Agregar en queries.py**
   ```python
   "diagnostico_paso3": {
       "name": "V_DIAGNOSTICO_PASO3_...",
       "params": {"CO_CAMPO": "formulario_key"},
       "description": "..."
   }
   ```

3. **Agregar función**
   ```python
   def get_diagnostico_paso3(incidencia_data):
       return execute_vista_query("diagnostico_paso3", incidencia_data)
   ```

4. **Agregar en get_all_analyst_results()**
   ```python
   df_p3, err_p3 = get_diagnostico_paso3(incidencia_data)
   results["diagnostico_paso3"] = {...}
   ```

---

## Solución de Problemas

| Problema | Causa | Solución |
|---|---|---|
| "Error ejecutando vista" | Vista no existe | Verificar nombre en Snowflake |
| "No se encontraron resultados" | Parámetros incorrectos | Verificar UNECO, ALMACEN, PEDIDO en tabla origen |
| Tabla vacía | WHERE muy restrictivo | Revisar datos en VW_COMP_cabecera_DOCUMENTO_COMPRAS |
| SQL syntax error | Campo mal mapeado | Verificar nombres exactos de columnas |

