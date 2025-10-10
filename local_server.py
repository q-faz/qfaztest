# Servidor local Q-FAZ
# Execute: python local_server.py

import uvicorn
import os
import sys
from pathlib import Path

# Adicionar diretório backend ao path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Importar servidor
from server import app

if __name__ == "__main__":
    print("🚀 Q-FAZ Local Server")
    print("📍 URL: http://localhost:8000")
    print("🔍 Health: http://localhost:8000/health")
    print("📊 API: http://localhost:8000/api/")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,  # Recarrega automaticamente
        log_level="info"
    )