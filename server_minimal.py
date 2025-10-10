# Q-FAZ Servidor Completo - Backend + Frontend
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar app FastAPI
app = FastAPI(title="Q-FAZ Backend + Frontend", version="1.0.0")

# CORS para permitir frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos do frontend (se existir)
if os.path.exists("frontend/build"):
    app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
    logger.info("✅ Frontend React encontrado em frontend/build")
elif os.path.exists("build"):
    app.mount("/static", StaticFiles(directory="build/static"), name="static") 
    logger.info("✅ Frontend React encontrado em build")
else:
    logger.warning("⚠️ Frontend React não encontrado - apenas API")

@app.get("/")
async def serve_frontend():
    """Servir frontend React ou página inicial"""
    # Tentar servir o frontend React
    frontend_paths = [
        "frontend/build/index.html",
        "build/index.html", 
        "index.html"
    ]
    
    for path in frontend_paths:
        if os.path.exists(path):
            logger.info(f"✅ Servindo frontend: {path}")
            return FileResponse(path)
    
    # Se não encontrar, retornar API info
    return {
        "message": "🚀 Q-FAZ Backend + Frontend",
        "status": "online",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "frontend": "React app not built yet - use /api/ endpoints"
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

# Endpoints da API que o frontend precisa
@app.post("/api/upload-storm")
async def upload_storm_placeholder(file: UploadFile = File(...)):
    """Placeholder para upload da Storm"""
    return {
        "message": "Storm upload recebido (funcionalidade será implementada)",
        "filename": file.filename,
        "size": len(await file.read()) if file else 0
    }

@app.post("/api/process-banks") 
async def process_banks_placeholder(files: list[UploadFile] = File(...)):
    """Placeholder para processamento de bancos"""
    return {
        "message": f"Processamento de {len(files)} arquivos recebido (funcionalidade será implementada)",
        "files": [f.filename for f in files],
        "job_id": "placeholder-123",
        "total_records": 0
    }

@app.get("/api/download-result/{job_id}")
async def download_result_placeholder(job_id: str):
    """Placeholder para download"""
    return {
        "message": f"Download do job {job_id} (funcionalidade será implementada)"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Iniciando servidor na porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)