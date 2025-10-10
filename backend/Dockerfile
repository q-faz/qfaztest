FROM python:3.11-slim

WORKDIR /app

# Otimizações para deploy mais rápido
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar dependências Python
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt

# Copiar código da aplicação
COPY backend /app

# Criar diretório para uploads temporários
RUN mkdir -p /app/temp

# Definir porta como variável de ambiente
ENV PORT=8000
EXPOSE $PORT

# Health check para verificar se a aplicação está rodando
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:$PORT/health')" || exit 1

# Comando otimizado para produção
CMD uvicorn server:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 65
