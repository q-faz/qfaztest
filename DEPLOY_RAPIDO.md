# 🚀 Guia Rápido: Deploy Azure em 10 Passos

## Para Q-FAZ - Sistema V6.3.1

---

## ⚡ Caminho Mais Rápido (Azure App Service)

### 1️⃣ **Criar .gitignore** (2 min)
```bash
# Copie o arquivo .gitignore já criado na raiz do projeto
# Ele já está configurado!
```

### 2️⃣ **Inicializar Git** (2 min)
```bash
cd c:\Users\natha\Documents\projeto\Q=FAZ
git init
git add .
git commit -m "Sistema Q-FAZ V6.3.1"
```

### 3️⃣ **Criar Repositório no GitHub** (3 min)
```
1. Acesse: https://github.com/new
2. Nome: qfaz-sistema
3. Privado: ✅ (recomendado)
4. Criar repositório
```

### 4️⃣ **Subir para GitHub** (2 min)
```bash
git remote add origin https://github.com/SEU_USUARIO/qfaz-sistema.git
git branch -M main
git push -u origin main
```

### 5️⃣ **Criar Conta Azure** (5 min)
```
1. Acesse: https://azure.microsoft.com/pt-br/
2. "Conta gratuita" - Ganhe créditos!
3. Preencha dados
4. Confirme email
```

### 6️⃣ **Criar Resource Group** (1 min)
```
Portal Azure → Resource groups → Create
- Nome: rg-qfaz
- Região: Brazil South
```

### 7️⃣ **Criar App Service - Backend** (3 min)
```
Portal Azure → App Services → Create

✅ Resource Group: rg-qfaz
✅ Name: qfaz-backend
✅ Publish: Code
✅ Runtime: Python 3.11
✅ OS: Linux
✅ Region: Brazil South
✅ Pricing: B1 (Basic) - ~R$100/mês

→ Review + Create
```

### 8️⃣ **Conectar GitHub** (2 min)
```
No App Service criado:
→ Deployment Center
→ Source: GitHub
→ Autorizar
→ Selecionar: qfaz-sistema / main
→ Save

✅ Azure faz deploy automático!
```

### 9️⃣ **Upload relat_orgaos.csv** (3 min)
```
No App Service:
→ Advanced Tools (Kudu)
→ Go → Debug Console → CMD
→ Navegar: /home/site/wwwroot/
→ Arrastar relat_orgaos.csv
```

### 🔟 **Testar!** (1 min)
```
Acessar:
https://qfaz-backend.azurewebsites.net

✅ Se aparecer JSON, funcionou!
```

---

## 🎯 Repetir para Frontend (Opcional)

```
Mesmos passos 7-8, mas com:
✅ Name: qfaz-frontend
✅ Runtime: Node 18 LTS
```

---

## ⏱️ Tempo Total: ~25 minutos

## 💰 Custo: ~R$ 100-200/mês

---

## 📝 Comandos Úteis

### Ver Logs:
```bash
# No portal Azure
App Service → Log stream
```

### Reiniciar:
```bash
App Service → Overview → Restart
```

### Atualizar Código:
```bash
# No seu computador
git add .
git commit -m "Atualização"
git push

# Azure faz deploy automático!
```

---

## ✅ Checklist Rápido

- [ ] Git instalado
- [ ] Repositório no GitHub
- [ ] Conta Azure criada
- [ ] App Service backend criado
- [ ] GitHub conectado
- [ ] relat_orgaos.csv enviado
- [ ] Testado e funcionando

---

## 🆘 Problemas?

### Erro no deploy:
```
1. Ver logs (Log stream)
2. Verificar requirements.txt
3. Reiniciar App Service
```

### Não carrega:
```
1. Verificar Configuration → PORT = 8000
2. Ver Application Settings
3. Restart
```

### Arquivos não aparecem:
```
1. Verificar .gitignore
2. Fazer git add novamente
3. Push
```

---

<div align="center">

**🚀 Pronto! Sistema no Azure!**

**Consulte DEPLOY_AZURE.md para detalhes completos**

</div>
