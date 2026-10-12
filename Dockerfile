# ==============================================================================
# Backend - Django (modo desarrollo, hot-reload)
#
# La imagen solo aporta las dependencias de Python. El codigo se monta desde
# el host en /app via docker-compose, por eso no hace falta recompilar.
# Contexto de build: la raiz del proyecto (COPY backend/...).
# ==============================================================================
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# postgresql-client -> poder usar psql dentro del contenedor para depurar la BD
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Primero los requirements para que la capa se cachee entre cambios de codigo
COPY backend/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

COPY backend/ /app/

EXPOSE 8080

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
