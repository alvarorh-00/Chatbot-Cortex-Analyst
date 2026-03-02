# Docker Setup para Chatbot de Resolución de Incidencias

## Construcción de la imagen Docker

```bash
docker build -t chatbot-incidencias .
```

## Ejecución con Docker directamente

```bash
docker run -p 8501:8501 chatbot-incidencias
```

## Ejecución con Docker Compose (recomendado)

Para iniciar la aplicación:

```bash
docker-compose up -d
```

Para detener la aplicación:

```bash
docker-compose down
```

Para ver los logs:

```bash
docker-compose logs -f chatbot
```

Para reconstruir la imagen:

```bash
docker-compose up -d --build
```

## Acceso a la aplicación

Una vez que el contenedor esté en ejecución, accede a la aplicación en:

```
http://localhost:8501
```

## Variable de entorno para Snowflake

Si necesitas pasar credenciales de Snowflake, crea un archivo `.env` en la raíz del proyecto:

```env
SNOWFLAKE_USER=tu_usuario
SNOWFLAKE_PASSWORD=tu_contraseña
SNOWFLAKE_ACCOUNT=tu_cuenta
SNOWFLAKE_DATABASE=tu_base_datos
SNOWFLAKE_SCHEMA=tu_esquema
SNOWFLAKE_WAREHOUSE=tu_warehouse
```

Luego descomenta la línea `env_file` en `docker-compose.yml`.

**Nota:** No cargues el archivo `.env` a Git. Está en `.gitignore`.

## Requisitos previos

- Docker instalado (versión 20.10 o superior)
- Docker Compose instalado (versión 1.29 o superior)
