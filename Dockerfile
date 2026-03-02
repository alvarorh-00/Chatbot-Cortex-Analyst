# Usar imagen base de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Crear directorio de configuración de Streamlit
RUN mkdir -p ~/.streamlit

# Crear archivo de configuración de Streamlit
RUN echo "\
[client]\n\
showErrorDetails = true\n\
\n\
[logger]\n\
level = \"info\"\n\
\n\
[server]\n\
port = 8501\n\
headless = true\n\
" > ~/.streamlit/config.toml

# Exponer el puerto de Streamlit
EXPOSE 8501


# Ejecutar la aplicación
CMD ["streamlit", "run", "app.py"]
