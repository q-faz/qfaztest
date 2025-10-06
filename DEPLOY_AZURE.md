# 🚀 Guia de Deploy no Azure - Sistema Q-FAZ
## Como Subir o Sistema para a Nuvem

**Última atualização:** 02/10/2025 04:30  
**Para:** Q-FAZ Soluções e Intermediações LTDA

---

## 📋 Índice

1. [Pré-requisitos](#-pré-requisitos)
2. [Preparar o Código (Git)](#-preparar-o-código-git)
3. [Opções de Deploy no Azure](#-opções-de-deploy-no-azure)
4. [Deploy Recomendado: Azure App Service](#-deploy-recomendado-azure-app-service)
5. [Deploy Alternativo: Azure Container Instances](#-deploy-alternativo-azure-container-instances)
6. [Configurações de Segurança](#-configurações-de-segurança)
7. [Custos Estimados](#-custos-estimados)
8. [Troubleshooting](#-troubleshooting)

---

## 🎯 Pré-requisitos

### 1. Conta Azure
```
✅ Conta Microsoft Azure (pode ser trial gratuito)
✅ Cartão de crédito (para verificação)
✅ Azure CLI instalado (opcional, mas recomendado)
```

### 2. Git Instalado
```bash
# Verificar se tem Git
git --version

# Se não tiver, baixe em: https://git-scm.com/
```

### 3. Conta GitHub (Recomendado)
```
✅ Criar conta em https://github.com
✅ Ou usar Azure DevOps (alternativa)
```

---

## 📦 Preparar o Código (Git)

### Passo 1: Criar .gitignore

Crie o arquivo `.gitignore` na raiz do projeto:

```bash
# No PowerShell, já na pasta do projeto
New-Item -ItemType File -Path .gitignore -Force
```

**Conteúdo do .gitignore:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
backend/Lib/
backend/Scripts/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Environment
.env
.env.local
.env.production.local

# IDEs
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Build
frontend/build/

# ⚠️ IMPORTANTE: Dados sensíveis
# Não subir pro Git!
backend/relat_orgaos.csv
data/*.csv
*.xlsx
*.xls

# Temporários
temp/
tmp/
*.tmp
```

### Passo 2: Inicializar Git

```bash
# No PowerShell, na pasta do projeto
cd c:\Users\natha\Documents\projeto\Q=FAZ

# Inicializar repositório
git init

# Adicionar arquivos
git add .

# Primeiro commit
git commit -m "Initial commit - Sistema Q-FAZ V6.3.1"
```

### Passo 3: Subir para GitHub

```bash
# Criar repositório no GitHub primeiro (via web)
# Depois linkar:

git remote add origin https://github.com/SEU_USUARIO/qfaz-sistema.git
git branch -M main
git push -u origin main
```

---

## 🌐 Opções de Deploy no Azure

### Opção 1: Azure App Service (Recomendado) ⭐
```
✅ Mais fácil de configurar
✅ Auto-scaling
✅ Deploy direto do GitHub
✅ SSL grátis
💰 ~R$ 100-300/mês
```

### Opção 2: Azure Container Instances
```
✅ Uso de Docker
✅ Mais controle
⚠️ Requer conhecimento de containers
💰 ~R$ 50-150/mês
```

### Opção 3: Azure VM (Virtual Machine)
```
✅ Controle total
⚠️ Mais complexo de gerenciar
⚠️ Requer manutenção
💰 ~R$ 200-500/mês
```

---

## 🚀 Deploy Recomendado: Azure App Service

### Passo 1: Criar Conta Azure

1. Acesse: https://azure.microsoft.com/pt-br/
2. Clique em "Conta gratuita"
3. **Ganhe créditos grátis** por 30 dias!

### Passo 2: Preparar Arquivos de Deploy

#### 2.1 Criar `requirements.txt` no backend

```bash
cd backend
pip freeze > requirements.txt
```

**Ou criar manualmente:**
```txt
fastapi==0.118.0
uvicorn[standard]==0.32.0
pandas==2.3.3
openpyxl==3.1.5
python-multipart==0.0.20
python-dotenv==1.1.1
motor==3.7.1
```

#### 2.2 Criar `startup.sh` no backend

```bash
#!/bin/bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

#### 2.3 Criar arquivo de configuração Azure

Crie `azure-deploy.yml` na raiz:

```yaml
# Azure App Service deployment config
runtime:
  backend:
    python: 3.11
    startup: "uvicorn server:app --host 0.0.0.0 --port 8000"
  
  frontend:
    node: 18
    build: "npm run build"
    startup: "npm start"

env:
  PORT: 8000
  NODE_ENV: production
```

### Passo 3: Criar App Service no Azure

#### Via Portal Azure (Interface Gráfica):

1. **Login no Azure Portal**
   - Acesse: https://portal.azure.com

2. **Criar Resource Group**
   ```
   - Clique em "Resource groups"
   - "+ Create"
   - Nome: "rg-qfaz-producao"
   - Região: "Brazil South" (São Paulo)
   - Clique "Review + Create"
   ```

3. **Criar App Service - Backend**
   ```
   - Busque "App Services"
   - "+ Create" → "Web App"
   
   Configurações:
   - Resource Group: rg-qfaz-producao
   - Name: qfaz-backend (será qfaz-backend.azurewebsites.net)
   - Publish: Code
   - Runtime stack: Python 3.11
   - Operating System: Linux
   - Region: Brazil South
   - Pricing: B1 (Basic) - R$ ~100/mês
   
   - Clique "Review + Create"
   ```

4. **Criar App Service - Frontend**
   ```
   - Repita o processo
   - Name: qfaz-frontend
   - Runtime stack: Node 18 LTS
   - Resto igual
   ```

### Passo 4: Deploy do Backend

#### Via GitHub (Recomendado):

1. **No Azure Portal:**
   ```
   - Abra seu App Service (qfaz-backend)
   - Menu lateral: "Deployment Center"
   - Source: GitHub
   - Autorize a conexão com GitHub
   - Selecione:
     - Organization: Sua conta
     - Repository: qfaz-sistema
     - Branch: main
   - Clique "Save"
   ```

2. **Azure vai automaticamente:**
   - Detectar `requirements.txt`
   - Instalar dependências
   - Rodar o servidor
   - Fazer deploy em cada push no GitHub!

#### Via Azure CLI (Alternativa):

```bash
# Instalar Azure CLI: https://docs.microsoft.com/cli/azure/install-azure-cli

# Login
az login

# Deploy
cd backend
az webapp up --name qfaz-backend --resource-group rg-qfaz-producao --runtime "PYTHON:3.11"
```

### Passo 5: Deploy do Frontend

```bash
# Build do frontend
cd frontend
npm run build

# Deploy via Azure CLI
az webapp up --name qfaz-frontend --resource-group rg-qfaz-producao --runtime "NODE:18-lts"
```

### Passo 6: Configurar Variáveis de Ambiente

1. **No Azure Portal:**
   ```
   - Abra qfaz-backend
   - Menu: "Configuration"
   - "+ New application setting"
   
   Adicione:
   - PORT: 8000
   - FRONTEND_URL: https://qfaz-frontend.azurewebsites.net
   - PYTHON_VERSION: 3.11
   
   - Clique "Save"
   ```

2. **Para o Frontend:**
   ```
   Adicione:
   - REACT_APP_API_URL: https://qfaz-backend.azurewebsites.net
   - NODE_ENV: production
   ```

### Passo 7: Configurar CORS

No backend (`server.py`), adicione:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://qfaz-frontend.azurewebsites.net",
        "http://localhost:3000"  # Para dev local
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Passo 8: Upload do relat_orgaos.csv

⚠️ **IMPORTANTE:** Não suba arquivos sensíveis pro Git!

**Opção 1 - Via Portal Azure:**
```
1. Abra qfaz-backend
2. Menu: "Advanced Tools" (Kudu)
3. "Go" → Abre nova aba
4. Menu: "Debug console" → "CMD"
5. Navegue até: /home/site/wwwroot/
6. Arraste e solte relat_orgaos.csv
```

**Opção 2 - Via FTP:**
```
1. No App Service, vá em "Deployment Center"
2. Clique em "FTPS credentials"
3. Use FileZilla ou WinSCP
4. Faça upload do arquivo
```

---

## 🐳 Deploy Alternativo: Azure Container Instances

Se preferir usar Docker:

### Passo 1: Criar Dockerfiles

**Backend Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**
```dockerfile
FROM node:18-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Passo 2: Build e Push

```bash
# Login no Azure Container Registry
az acr login --name qfazregistry

# Build
docker build -t qfazregistry.azurecr.io/backend:latest ./backend
docker build -t qfazregistry.azurecr.io/frontend:latest ./frontend

# Push
docker push qfazregistry.azurecr.io/backend:latest
docker push qfazregistry.azurecr.io/frontend:latest
```

### Passo 3: Deploy

```bash
# Backend
az container create \
  --resource-group rg-qfaz-producao \
  --name qfaz-backend \
  --image qfazregistry.azurecr.io/backend:latest \
  --dns-name-label qfaz-backend \
  --ports 8000

# Frontend
az container create \
  --resource-group rg-qfaz-producao \
  --name qfaz-frontend \
  --image qfazregistry.azurecr.io/frontend:latest \
  --dns-name-label qfaz-frontend \
  --ports 80
```

---

## 🔐 Configurações de Segurança

### 1. SSL/HTTPS (Grátis no Azure)

```
✅ Azure App Service já inclui SSL grátis
✅ Domínio: *.azurewebsites.net automaticamente HTTPS
```

### 2. Domínio Customizado (Opcional)

```bash
# Se tiver domínio próprio (ex: qfaz.com.br)
az webapp config hostname add \
  --webapp-name qfaz-backend \
  --resource-group rg-qfaz-producao \
  --hostname api.qfaz.com.br
```

### 3. Firewall e IP Whitelist

No Portal Azure:
```
1. Abra App Service
2. Menu: "Networking"
3. "Access restriction"
4. Adicione regras de IP permitidos
```

### 4. Backup Automático

```
1. No App Service
2. Menu: "Backups"
3. Configure backup diário
4. Armazenamento: Azure Storage
```

---

## 💰 Custos Estimados

### Cenário 1: Básico (Recomendado para início)
```
✅ 2x App Service B1 (Basic): ~R$ 200/mês
✅ Azure Storage (backups): ~R$ 10/mês
✅ Bandwidth: ~R$ 20/mês
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 TOTAL: ~R$ 230/mês
```

### Cenário 2: Produção (Mais recursos)
```
✅ 2x App Service P1V2: ~R$ 500/mês
✅ Azure Storage: ~R$ 20/mês
✅ Bandwidth: ~R$ 50/mês
✅ Application Insights (logs): ~R$ 30/mês
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 TOTAL: ~R$ 600/mês
```

### Cenário 3: Container Instances
```
✅ 2x Container Instances: ~R$ 150/mês
✅ Azure Container Registry: ~R$ 50/mês
✅ Storage: ~R$ 20/mês
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 TOTAL: ~R$ 220/mês
```

**💡 Dica:** Comece com **Cenário 1** e escale conforme necessário!

---

## 🔧 Troubleshooting

### Erro: "Application Error"

**Solução:**
```bash
# Ver logs
az webapp log tail --name qfaz-backend --resource-group rg-qfaz-producao

# Ou no portal:
Portal Azure → App Service → "Log stream"
```

### Erro: "ModuleNotFoundError"

**Solução:**
```
✅ Verificar requirements.txt completo
✅ Forçar redeploy
✅ Reiniciar App Service
```

### Erro: CORS

**Solução:**
```python
# No server.py, adicionar:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporário para teste
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Erro: "Port already in use"

**Solução:**
```python
# No server.py, usar variável de ambiente
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

## 📊 Monitoramento

### Application Insights (Recomendado)

1. **Criar Application Insights:**
   ```
   Portal Azure → "+ Create" → "Application Insights"
   - Nome: qfaz-insights
   - Resource Group: rg-qfaz-producao
   ```

2. **Conectar ao App Service:**
   ```
   App Service → "Application Insights"
   → "Turn on Application Insights"
   → Selecione qfaz-insights
   ```

3. **Ver Métricas:**
   ```
   - Tempo de resposta
   - Taxa de erro
   - Uso de CPU/Memória
   - Requisições por segundo
   ```

---

## 🚀 Comandos Rápidos

### Deploy Rápido (após setup inicial)

```bash
# Backend
cd backend
git add .
git commit -m "Update backend"
git push

# Frontend
cd frontend
npm run build
git add .
git commit -m "Update frontend"
git push

# Azure faz deploy automático!
```

### Reiniciar Serviços

```bash
# Backend
az webapp restart --name qfaz-backend --resource-group rg-qfaz-producao

# Frontend
az webapp restart --name qfaz-frontend --resource-group rg-qfaz-producao
```

### Ver URLs

```bash
az webapp show --name qfaz-backend --resource-group rg-qfaz-producao --query defaultHostName --output tsv
# Resultado: qfaz-backend.azurewebsites.net

az webapp show --name qfaz-frontend --resource-group rg-qfaz-producao --query defaultHostName --output tsv
# Resultado: qfaz-frontend.azurewebsites.net
```

---

## 📝 Checklist Final

### Antes do Deploy:
- [ ] Código no GitHub
- [ ] .gitignore configurado
- [ ] requirements.txt atualizado
- [ ] Variáveis de ambiente definidas
- [ ] CORS configurado
- [ ] relat_orgaos.csv preparado (upload manual)

### Pós-Deploy:
- [ ] Backend acessível (testar /api/debug-file)
- [ ] Frontend carregando
- [ ] Upload de arquivos funcionando
- [ ] Processamento funcionando
- [ ] Download de relatório funcionando
- [ ] Logs sem erros críticos

---

## 🎯 URLs Finais

Após deploy completo:

```
🌐 Backend API:
https://qfaz-backend.azurewebsites.net

🌐 Frontend:
https://qfaz-frontend.azurewebsites.net

🔍 Debug Endpoint:
https://qfaz-backend.azurewebsites.net/api/debug-file
```

---

## 📞 Suporte

### Recursos Azure:
- 📖 Documentação: https://docs.microsoft.com/azure
- 💬 Suporte: Portal Azure → "Help + support"
- 📱 Chat: Disponível no portal

### Q-FAZ:
- 📧 Contate a equipe técnica
- 📖 Consulte HISTORICO_VERSOES.md
- 🐛 Use endpoint /api/debug-file

---

<div align="center">

**🚀 Sistema Q-FAZ V6.3.1 - Pronto para o Azure!**

**Desenvolvido com 💙 para Q-FAZ**

**02/10/2025 04:30**

</div>
