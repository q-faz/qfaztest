"""Script para iniciar o servidor FastAPI"""
import os
import uvicorn

if __name__ == "__main__":
<<<<<<< HEAD
    port = int(os.getenv("PORT", 8000))  # Lê a porta do Azure
=======
    port = int(os.getenv("PORT", 8000))
>>>>>>> 4faf4a7 (Atualizações do projeto)
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )
