#!/bin/bash

# Script universal de deploy - funciona em qualquer plataforma
echo "🚀 Iniciando Q-FAZ Backend..."

# Instalar dependências
pip install --no-cache-dir -r requirements.txt

# Criar diretórios necessários
mkdir -p temp logs

# Verificar se está funcionando
python -c "import fastapi; print('✅ FastAPI OK')"
python -c "import pandas; print('✅ Pandas OK')"
python -c "import server; print('✅ Server OK')"

# Iniciar servidor
echo "🎯 Iniciando servidor na porta $PORT..."
uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1