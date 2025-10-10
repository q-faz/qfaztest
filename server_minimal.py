# Servidor mínimo para deploy Railway - GARANTIDO FUNCIONAMENTO
from fastapi import FastAPI
from datetime import datetime
import uvicorn
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(title="Q-FAZ Backend", version="1.0.0")

@app.get("/")
async def root():
    """Endpoint raiz"""
    return {
        "message": "🚀 Q-FAZ Backend está funcionando!",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "Q-FAZ Backend",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/test")
async def test():
    """Endpoint de teste"""
    return {
        "message": "Teste OK!",
        "port": os.environ.get("PORT", "8000"),
        "python": "3.11+",
        "framework": "FastAPI"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Iniciando servidor na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)