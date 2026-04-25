# Usa una imagen ligera de Python
FROM python:3.14-slim

# Variables de entorno (ejemplo, reemplaza si tienes otras)
ENV GH_TOKEN=""
ENV GH_USERNAME=""

# Evita buffers en stdout/stderr para logs en tiempo real
ENV PYTHONUNBUFFERED=1

# Instala dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Establece directorio de trabajo
WORKDIR /app

# Copia archivos de la app
COPY index.py input.css requirements.txt templates/ ./

# Instala pip y requirements si existe
RUN pip install --upgrade pip \
    && if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# Descarga Tailwind CSS
RUN mkdir -p .tailwind \
    && curl -L https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-linux-x64 \
       -o .tailwind/tailwind \
    && chmod +x .tailwind/tailwind

# Comando por defecto al iniciar el contenedor
CMD ["python", "index.py"]