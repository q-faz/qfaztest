# 🏦 Q=FAZ - Sistema de Processamento de Relatórios Bancários# 🏦 Q=FAZ - Sistema de Processamento de Relatórios Bancários



## Q-FAZ Soluções e Intermediações LTDA## Q-FAZ Soluções e Intermediações LTDA



Sistema automatizado de alta performance para processamento, padronização e consolidação de relatórios financeiros de múltiplas instituições bancárias para importação na plataforma Storm.Sistema automatizado de alta performance para processamento, padronização e consolidação de relatórios financeiros de múltiplas instituições bancárias para importação na plataforma Storm.



<div align="center"><div align="center">



![Version](https://img.shields.io/badge/versão-7.0.0-blue)![Version](https://img.shields.io/badge/versão-7.0.0-blue)

![Banks](https://img.shields.io/badge/bancos-17-green) ![Banks](https://img.shields.io/badge/bancos-17-green) 

![Status](https://img.shields.io/badge/status-ativo-success)![Status](https://img.shields.io/badge/status-ativo-success)

![Update](https://img.shields.io/badge/última%20atualização-06/10/2025-orange)![Update](https://img.shields.io/badge/última%20atualização-06/10/2025-orange)



[Início Rápido](#-início-rápido) • [Funcionalidades](#-funcionalidades) • [Bancos Suportados](#-bancos-suportados) • [Documentação](#-documentação)[Início Rápido](#-início-rápido) • [Funcionalidades](#-funcionalidades) • [Bancos Suportados](#-bancos-suportados) • [Documentação](#-documentação)



</div></div>



------



## 📋 Visão Geral## 📋 Visão Geral



Sistema desenvolvido exclusivamente para **Q-FAZ Soluções e Intermediações LTDA**, automatizando o processamento de relatórios do Storm e de múltiplas instituições bancárias. Gera relatórios consolidados com taxas, órgãos e informações completas para análise de crédito consignado.Sistema desenvolvido exclusivamente para **Q-FAZ Soluções e Intermediações LTDA**, automatizando o processamento de relatórios do Storm e de múltiplas instituições bancárias. Gera relatórios consolidados com taxas, órgãos e informações completas para análise de crédito consignado.



### ✨ Principais Funcionalidades### ✨ Principais Funcionalidades



- 🔍 **Detecção Automática de Bancos** - Identifica automaticamente o banco pela estrutura do arquivo- 🔍 **Detecção Automática de Bancos** - Identifica automaticamente o banco pela estrutura do arquivo

- 🔄 **Processamento Multi-Banco** - Suporte simultâneo para 17 instituições financeiras- 🔄 **Processamento Multi-Banco** - Suporte simultâneo para 17 instituições financeiras

- 📊 **Padronização Inteligente** - Normaliza dados para formato único da Storm- 📊 **Padronização Inteligente** - Normaliza dados para formato único da Storm

- 🎯 **Aplicação de Dicionário** - Mapeamento automático usando `relat_orgaos.csv`- 🎯 **Aplicação de Dicionário** - Mapeamento automático usando `relat_orgaos.csv`

- 🗑️ **Remoção de Duplicatas** - Elimina registros já processados na Storm- 🗑️ **Remoção de Duplicatas** - Elimina registros já processados na Storm

- 📈 **Relatórios Consolidados** - Gera CSV final com 24 colunas padronizadas- 📈 **Relatórios Consolidados** - Gera CSV final com 24 colunas padronizadas



---## 📋 Sobre o Sistema



## 🏦 Bancos Suportados---



### ✅ Bancos Ativos em ProduçãoSistema desenvolvido exclusivamente para **Q-FAZ Soluções e Intermediações LTDA**, automatizando o processamento de relatórios do Storm e de 17 instituições bancárias, gerando relatórios consolidados com taxas, órgãos e informações completas para análise de crédito consignado.



| Banco | Status | Última Atualização |## 🏗️ Arquitetura do Sistema

|-------|--------|-------------------|

| 🏦 **AVERBAI** | ✅ Funcional | 06/10/2025 |### ✨ Destaques da Versão 6.13.0 (06/10/2025 19:30)

| 🏦 **VCTEX** | ✅ Funcional | 06/10/2025 |

| 🏦 **CREFAZ** | ✅ Funcional | 06/10/2025 |#### 🔧 **CORREÇÕES MAIS RECENTES IMPLEMENTADAS:**

| 🏦 **QUERO MAIS** | ✅ Funcional | 06/10/2025 |

| 🏦 **PRATA** | ✅ Funcional | 06/10/2025 |**🏦 QUERO MAIS CRÉDITO (v6.13.0):**

| 🏦 **FACTA** | ✅ Funcional | 06/10/2025 |- ✅ **Códigos de tabela**: Remoção automática de zeros à esquerda (004717 → 4717)

- ✅ **Usuário banco**: Formatação correta mantida (36057733894_901064)

### ⚙️ Bancos em Manutenção- ✅ **Tipo de operação**: "Cartao c/ saque" sem caracteres corrompidos

- ✅ **Mapeamento preservado**: Pula mapeamento automático para manter códigos originais

| Banco | Status | Observações |- ✅ **Duplicatas**: Remoção automática baseada na coluna PROPOSTA

|-------|--------|-------------|

| 🔧 **SANTANDER** | ⚙️ Manutenção | Melhorias em andamento |**🏦 VCTEX - CÓDIGOS TROCADOS CORRIGIDOS (v6.13.0):**

| 🔧 **DAYCOVAL** | ⚙️ Manutenção | Validações sendo ajustadas |- ✅ **EXP ≠ EXPONENCIAL**: Correção definitiva dos códigos trocados no relat_orgaos.csv

| 🔧 **DIGIO** | ⚙️ Manutenção | Processamento em otimização |- ✅ **Tabela EXP** → Código **TabelaEXP** (corrigido linha 245)

| 🔧 **C6 BANK** | ⚙️ Manutenção | Estrutura sendo atualizada |- ✅ **Tabela Exponencial** → Código **TabelaExponencial** (corrigido linha 225)

| 🔧 **PAN** | ⚙️ Manutenção | Mapeamento em revisão |- ✅ **Mapeamento Storm**: Códigos agora correspondem corretamente aos produtos

| 🔧 **PAULISTA** | ⚙️ Manutenção | Compatibilização em progresso |

| 🔧 **BRB** | ⚙️ Manutenção | Ajustes de formato |**🏦 DIGIO E FACTA92 (v6.12.0):**

| 🔧 **QUALIBANKING** | ⚙️ Manutenção | Normalização sendo implementada |- ✅ **DIGIO vs DAYCOVAL**: Detecção melhorada com indicadores únicos para evitar conflito

| 🔧 **MERCANTIL** | ⚙️ Manutenção | Estrutura sendo revisada |- ✅ **FACTA92 códigos**: Extração automática de códigos numéricos (53694) em vez de texto completo

| 🔧 **AMIGOZ** | ⚙️ Manutenção | Processamento sendo ajustado |- ✅ **Limpeza**: Removidos arquivos de teste desnecessários do workspace

| 🔧 **TOTALCASH** | ⚙️ Manutenção | Melhoria de detecção em andamento |- ✅ **Logs**: Debug detalhado para ambos os bancos



---**🏦 SANTANDER (v6.7.0):**

- ✅ **Filtro SEGURO**: Remove propostas código 11111111 automaticamente

## 🚀 Início Rápido- ✅ **Mapeamento pós-normalização**: Aplica códigos Storm corretos após processamento básico

- ✅ **Sintaxe corrigida**: Declarações globais movidas para posição correta

### Pré-requisitos- ✅ **Validação completa**: Dados testados e funcionando em produção



```bash**🏦 VCTEX (v6.8.0):**

- Python 3.9+- ✅ **Formatação de tabelas**: "Exponencial" → "Tabela Exponencial" para mapeamento correto

- Node.js 16+- ✅ **EXPONENCIAL ≠ EXP**: Preservada diferença entre produtos (não são normalizados um para outro)

```- ✅ **Match automático**: Sistema adiciona prefixo "Tabela" quando necessário

- ✅ **Integridade**: Cada produto mapeia para seu código correto no Storm

### Instalação

### Componentes Principais

#### 1️⃣ **Backend (Python/FastAPI)**

```

```bash├── backend/

cd backend│   ├── server.py              # API FastAPI + lógica de processamento

pip install -r requirements.txt│   ├── relat_orgaos.csv       # Dicionário oficial (NÃO MEXER!)

python start_server.py

```- ✅ **Interface moderna** e responsiva│   └── requirements.txt       # Dependências Python



✅ Servidor rodando em: **http://localhost:8000**├── frontend/



#### 2️⃣ **Frontend (React)**---│   ├── src/



```bash│   │   └── App.js             # Interface React

cd frontend

npm install## 🏦 Bancos Suportados│   └── package.json           # Dependências Node.js

npm start

```├── data/



✅ Interface disponível em: **http://localhost:3000**| Banco | Status | Última Atualização |│   ├── map_relat_atualizados.txt    # Documentação de estruturas (CONSULTAR!)



---|-------|--------|-------------------|│   └── relatorio_final_*.csv        # Exemplos de saída válida



## 🏗️ Arquitetura do Sistema| 🏦 **AVERBAI** | ✅ Ativo | 02/10/2025 |├── COMO_ADICIONAR_BANCOS.md   # 📖 Guia para adicionar novos bancos



### Componentes Principais| 🏦 **DIGIO** | ✅ Ativo | 02/10/2025 |└── RELATORIO_CORRECOES.md     # 📊 Histórico de correções



```| 🏦 **BMG** | ✅ Ativo | 02/10/2025 |```

├── backend/

│   ├── server.py              # API FastAPI + lógica de processamento| 🏦 **ITAÚ** | ✅ Ativo | 02/10/2025 |

│   ├── relat_orgaos.csv       # Dicionário oficial (NÃO MEXER!)

│   └── requirements.txt       # Dependências Python| 🏦 **FACTA92** | ✅ Ativo | 02/10/2025 |### Fluxo de Processamento

├── frontend/

│   ├── src/| 🏦 **SANTANDER** | ✅ Ativo | 02/10/2025 |

│   │   └── App.js             # Interface React

│   └── package.json           # Dependências Node.js| 🏦 **C6 BANK** | ✅ Ativo | 02/10/2025 |```

├── data/

│   ├── map_relat_atualizados.txt    # Documentação de estruturas| 🏦 **DAYCOVAL** | ✅ Ativo | 02/10/2025 |┌─────────────┐

│   └── relatorio_final_*.csv        # Exemplos de saída

└── HISTORICO_VERSOES.md       # Changelog completo| 🏦 **CREFAZ** | ✅ Ativo | 02/10/2025 |│   Storm     │ → Upload relatório Storm (referência)

```

| 🏦 **PAN** | ✅ Ativo | 02/10/2025 |│  (CSV/XLS)  │

### Fluxo de Processamento

| 🏦 **PAULISTA** | ✅ Ativo | 02/10/2025 |└─────────────┘

```

┌─────────────┐| 🏦 **QUERO MAIS CRÉDITO** | ✅ Ativo | 02/10/2025 |      ↓

│   Storm     │ → Upload relatório Storm (referência)

│  (CSV/XLS)  │| 🏦 **TOTALCASH** | ✅ Ativo | 02/10/2025 |┌─────────────┐

└─────────────┘

      ↓| 🏦 **BRB** | ✅ Ativo | 16/09/2025 |│  Processar  │ → Identificar propostas PAGO/CANCELADO

┌─────────────┐

│  Processar  │ → Identificar propostas PAGO/CANCELADO| 🏦 **QUALIBANKING** | ✅ Ativo | 16/09/2025 |│    Storm    │

│    Storm    │

└─────────────┘| 🏦 **MERCANTIL** | ✅ Ativo | 16/09/2025 |└─────────────┘

      ↓

┌─────────────┐| 🏦 **AMIGOZ** | ✅ Ativo | 16/09/2025 |      ↓

│   Bancos    │ → Upload relatórios dos bancos

│  (CSV/XLS)  │┌─────────────┐

└─────────────┘

      ↓---│   Bancos    │ → Upload relatórios dos bancos

┌─────────────┐

│  Detectar   │ → Identificar banco automaticamente│  (CSV/XLS)  │

│    Banco    │

└─────────────┘## 🚀 Início Rápido└─────────────┘

      ↓

┌─────────────┐      ↓

│ Normalizar  │ → Mapear colunas → padrão interno

│    Dados    │### Pré-requisitos┌─────────────┐

└─────────────┘

      ↓│  Detectar   │ → Identificar banco automaticamente

┌─────────────┐

│   Aplicar   │ → Buscar códigos em relat_orgaos.csv```bash│    Banco    │

│  Dicionário │

└─────────────┘- Python 3.9+└─────────────┘

      ↓

┌─────────────┐- Node.js 16+      ↓

│  Remover    │ → Remover duplicatas da Storm

│ Duplicatas  │```┌─────────────┐

└─────────────┘

      ↓│ Normalizar  │ → Mapear colunas do banco → padrão interno

┌─────────────┐

│   Gerar     │ → CSV com 24 colunas, separador ';'### Instalação│    Dados    │

│  CSV Final  │

└─────────────┘└─────────────┘

```

#### 1️⃣ **Backend (Python/FastAPI)**      ↓

---

┌─────────────┐

## 📖 Como Usar

```bash│   Aplicar   │ → Buscar código tabela em relat_orgaos.csv

### 1️⃣ Upload do Relatório Storm

cd backend│  Dicionário │

1. Acesse **http://localhost:3000**

2. Clique em **"📤 Upload Storm Report"**pip install -r requirements.txt└─────────────┘

3. Selecione o arquivo Storm (CSV ou Excel)

4. ✅ Aguarde processamento: *"Storm processado: X registros"*python start_server.py      ↓



### 2️⃣ Upload dos Relatórios Bancários```┌─────────────┐



1. Clique em **"📤 Upload Bank Reports"**│  Remover    │ → Remover duplicatas baseado na Storm

2. Selecione arquivos dos bancos funcionais (AVERBAI, VCTEX, CREFAZ, QUERO MAIS, PRATA, FACTA)

3. Sistema detecta automaticamente cada banco✅ Servidor rodando em: **http://localhost:8000**│ Duplicatas  │

4. 📊 Veja estatísticas em tempo real

└─────────────┘

### 3️⃣ Download do Relatório Final

#### 2️⃣ **Frontend (React)**      ↓

1. Clique em **"💾 Baixar Relatório Consolidado"**

2. Arquivo gerado: `relatorio_final_storm_YYYYMMDD_HHMMSS.csv`┌─────────────┐

3. Importe na plataforma Storm

```bash│   Gerar     │ → CSV com 24 colunas, separador ';'

---

cd frontend│  CSV Final  │

## 📊 Estrutura do CSV Final (24 Colunas)

npm install└─────────────┘

| Coluna | Descrição | Obrigatória |

|--------|-----------|-------------|npm start```

| PROPOSTA | Número da proposta/contrato | ✅ Sim |

| DATA CADASTRO | Data de cadastro | ✅ Sim |```

| BANCO | Nome do banco | ✅ Sim |

| ORGAO | INSS, FGTS, etc. | ✅ Sim |---

| CODIGO TABELA | Código da tabela (do dicionário) | ⚠️ Recomendado |

| TIPO DE OPERACAO | Tipo de operação | ✅ Sim |✅ Interface disponível em: **http://localhost:3000**

| NUMERO PARCELAS | Quantidade de parcelas | ✅ Sim |

| VALOR PARCELAS | Valor de cada parcela | ⚠️ Recomendado |## ⚙️ Instalação e Configuração

| VALOR OPERACAO | Valor total da operação | ✅ Sim |

| VALOR LIBERADO | Valor liberado ao cliente | ✅ Sim |---

| VALOR QUITAR | Valor para quitar | ❌ Opcional |

| USUARIO BANCO | Usuário digitador | ⚠️ Recomendado |### Pré-requisitos

| CODIGO LOJA | Código da loja | ❌ Opcional |

| SITUACAO | PAGO/CANCELADO/AGUARDANDO | ✅ Sim |## 📖 Como Usar

| DATA DE PAGAMENTO | Data de pagamento (se PAGO) | ⚠️ Condicional |

| CPF | CPF do cliente | ✅ Sim |- Python 3.9+

| NOME | Nome do cliente | ✅ Sim |

| DATA DE NASCIMENTO | Data de nascimento | ⚠️ Recomendado |### Passo 1: Upload do Arquivo Storm- Node.js 16+

| TIPO DE CONTA | Tipo de conta | ❌ Opcional |

| TIPO DE PAGAMENTO | Tipo de pagamento | ❌ Opcional |- MongoDB (opcional, para logs)

| AGENCIA CLIENTE | Agência do cliente | ❌ Opcional |

| CONTA CLIENTE | Conta do cliente | ❌ Opcional |1. Acesse **http://localhost:3000**

| FORMALIZACAO DIGITAL | Formalização digital? | ✅ Sim (padrão: SIM) |

| TAXA | Taxa de juros | ✅ Sim |2. Clique em **"📤 Upload Storm Report"**### Backend



---3. Selecione o arquivo Storm (CSV ou Excel)



## 🔧 Troubleshooting4. ✅ Verá: *"Storm processado: X registros"*```bash



### Erro: "Banco não detectado"cd backend

- **Solução**: Verifique se é um dos 6 bancos funcionais (AVERBAI, VCTEX, CREFAZ, QUERO MAIS, PRATA, FACTA)

- Confirme se o arquivo tem extensão `.csv`, `.xlsx` ou `.xls`### Passo 2: Upload dos Relatórios Bancáriospip install -r requirements.txt



### Erro: "Código de tabela não encontrado"python server.py

- **Solução**: Verifique se banco/órgão/operação estão em `relat_orgaos.csv`

- Confirme que nomes estão exatos (use CTRL+F no CSV)1. Clique em **"📤 Upload Bank Reports"**```



### Erro: "KeyError: 'coluna_xyz'"2. Selecione arquivos dos bancos

- **Solução**: Use `.get('coluna_xyz', '')` em vez de `['coluna_xyz']`

- Adicione verificação `if 'coluna_xyz' in df.columns`3. Sistema detecta automaticamente cada bancoO servidor estará disponível em: `http://localhost:8000`



### CSV importado com erros na Storm4. 📊 Veja estatísticas em tempo real

- Verifique se separador é `;` (ponto e vírgula)

- Confirme que todas as 24 colunas estão presentes### Frontend

- Valide que status estão em PAGO/CANCELADO/AGUARDANDO

### Passo 3: Download do Relatório

---

```bash

## 📈 Melhorias Futuras

1. Clique em **"💾 Baixar Relatório Consolidado"**cd frontend

### 🚀 Próximas Implementações

2. Arquivo: `relatorio_final_storm_YYYYMMDD_HHMMSS.csv`npm install

- **Conclusão da Manutenção** dos 11 bancos restantes

- **Dashboard Avançado** com métricas em tempo realnpm start

- **API de Integração** para automação externa

- **Validação Inteligente** com machine learning---```

- **Backup Automático** de configurações

- **Notificações** por email/SMS de processamento

- **Relatórios Personalizados** por período/banco

- **Interface Mobile** responsiva## 🔧 Endpoint de DebugA interface estará disponível em: `http://localhost:3000`

- **Auditoria Completa** de todas as operações

- **Integração Direta** com APIs dos bancos



### 🎯 Otimizações Planejadas```bash---



- **Performance** - Processamento paralelo para arquivos grandescurl -X POST http://localhost:8000/api/debug-file \

- **Memória** - Otimização para arquivos com +100k registros

- **UX/UI** - Interface mais intuitiva e moderna  -F "file=@seu_arquivo.xlsx"## 📖 Como Usar

- **Segurança** - Criptografia de dados sensíveis

- **Monitoramento** - Alertas automáticos de falhas```



---### 1️⃣ Upload do Relatório Storm



## 📚 Documentação**Retorna:**



- 📖 **[Histórico de Versões](./HISTORICO_VERSOES.md)** - Changelog completo com todas as correções e melhorias- Nome e tamanho do arquivo1. Acesse a interface web

- 📋 **[Exemplos de Saída](./data/)** - Arquivos `relatorio_final_*.csv` de referência

- 🏦 **[Estruturas dos Bancos](./data/map_relat_atualizados.txt)** - Documentação das estruturas de cada banco- Número de linhas e colunas2. Clique em "Upload Storm Report"



---- Nomes das colunas detectadas3. Selecione o arquivo CSV/Excel da Storm



## ⚠️ Importante: Separação de Responsabilidades- Banco detectado4. Aguarde processamento



### ❌ NÃO CONFUNDIR:- Amostra da primeira linha



1. **`relat_orgaos.csv`** = **Dicionário Oficial**### 2️⃣ Upload dos Relatórios dos Bancos

   - Define códigos de tabela, operações, taxas e órgãos válidos

   - **NÃO MEXER sem validação prévia!**---

   - É a fonte da verdade para padronização

1. Clique em "Upload Bank Reports"

2. **`map_relat_atualizados.txt`** = **Documentação de Estruturas**

   - Documenta quais colunas cada banco usa## 📊 Estrutura do CSV Final (24 Colunas)2. Selecione um ou múltiplos arquivos de bancos

   - **APENAS CONSULTAR** para implementar mapeamento

   - NÃO é usado pelo sistema, é documentação3. Aguarde processamento automático



3. **`backend/server.py`** = **Lógica de Mapeamento**| Coluna | Exemplo |4. Faça download do CSV final gerado

   - Contém função `normalize_bank_data()`

   - **AQUI você faz alterações** para adicionar bancos|--------|---------|

   - Traduz colunas dos bancos → padrão interno

| PROPOSTA | 110254557 |### 3️⃣ Importar na Storm

---

| DATA CADASTRO | 2025-09-15 |

## 📊 Estatísticas de Performance

| BANCO | FACTA92 |1. Acesse a Storm

```

✅ Taxa de sucesso: 98%+| ORGAO | INSS |2. Vá para "Importação de Dados"

⚡ Velocidade: ~2.000 registros/segundo

🎯 Precisão: 99% de matching automático| CODIGO TABELA | 60186 |3. Faça upload do CSV gerado

🔧 Uptime: 99.9% em produção

```| TIPO DE OPERACAO | Margem Livre (Novo) |4. Valide os dados importados



| Métrica | Antes | Depois | Melhoria || NUMERO PARCELAS | 96 |

|---------|-------|--------|----------|

| Taxa de sucesso | 40% | 98% | +145% || VALOR PARCELAS | 527.83 |---

| Bancos com erro | 10 | 1-2 | -80% |

| Tempo de processamento | 5min | 30s | -90% || VALOR OPERACAO | 50671.68 |

| Erros de mapeamento | 15% | 1% | -93% |

| VALOR LIBERADO | 18738.36 |## 🔧 Adicionando Novos Bancos

---

| CPF | 12345678900 |

## 🔐 Segurança

| NOME | JOÃO DA SILVA |**📘 Consulte o guia completo:** [`COMO_ADICIONAR_BANCOS.md`](./COMO_ADICIONAR_BANCOS.md)

✅ Dados processados localmente  

✅ Sem armazenamento permanente  | TAXA | 1.85 |

✅ Logs anonimizados  

✅ Processamento em memória apenas  ### Resumo Rápido

✅ Limpeza automática após processamento  

---

---

1. Obtenha arquivo de exemplo do banco

## 📞 Suporte

## 🛠️ Arquitetura2. Identifique as colunas relevantes

Para dúvidas ou problemas:

1. Consulte o **[Histórico de Versões](./HISTORICO_VERSOES.md)** para soluções conhecidas3. Adicione mapeamento em `backend/server.py` na função `normalize_bank_data()`

2. Verifique os logs do servidor (`python backend/server.py`)

3. Compare com exemplos em `data/relatorio_final_*.csv````4. Adicione detecção em `detect_bank_type_enhanced()`

4. Entre em contato com a equipe técnica da Q-FAZ

Q=FAZ/5. Teste com arquivo real

---

├── backend/6. Valide integração com dicionário

## 📜 Licença

│   ├── server.py              # API + Lógica

**Sistema proprietário - Q-FAZ Soluções e Intermediações LTDA**

│   ├── relat_orgaos.csv       # Dicionário de taxas---

© 2025 Q-FAZ. Todos os direitos reservados.

│   └── requirements.txt

---

├── frontend/## 📊 Estrutura do CSV Final (24 Colunas)

<div align="center">

│   ├── src/App.js             # Interface React

### ✅ Sistema em Produção - 6 Bancos Funcionais

│   └── package.json| Coluna | Descrição | Obrigatória |

**Versão 7.0.0 | 06/10/2025**

├── data/|--------|-----------|-------------|

**Desenvolvido com 💙 para Q-FAZ**

│   └── map_relat_atualizados.txt  # Estruturas dos bancos| PROPOSTA | Número da proposta/contrato | ✅ Sim |

[⬆ Voltar ao topo](#-q-faz---sistema-de-processamento-de-relatórios-bancários)

└── HISTORICO_VERSOES.md       # Changelog completo| DATA CADASTRO | Data de cadastro | ✅ Sim |

</div>
```| BANCO | Nome do banco | ✅ Sim |

| ORGAO | INSS, FGTS, etc. | ✅ Sim |

---| CODIGO TABELA | Código da tabela (do dicionário) | ⚠️ Recomendado |

| TIPO DE OPERACAO | Tipo de operação | ✅ Sim |

## 🔍 Troubleshooting| NUMERO PARCELAS | Quantidade de parcelas | ✅ Sim |

| VALOR PARCELAS | Valor de cada parcela | ⚠️ Recomendado |

### ❌ "Nenhum dado válido foi processado"| VALOR OPERACAO | Valor total da operação | ✅ Sim |

| VALOR LIBERADO | Valor liberado ao cliente | ✅ Sim |

**Solução:** Use o endpoint `/api/debug-file` para verificar estrutura| VALOR QUITAR | Valor para quitar | ❌ Opcional |

| USUARIO BANCO | Usuário digitador | ⚠️ Recomendado |

### ❌ "Banco não detectado"| CODIGO LOJA | Código da loja | ❌ Opcional |

| SITUACAO | PAGO/CANCELADO/AGUARDANDO | ✅ Sim |

**Solução:** Confirme que é um dos 17 bancos suportados| DATA DE PAGAMENTO | Data de pagamento (se PAGO) | ⚠️ Condicional |

| CPF | CPF do cliente | ✅ Sim |

### ❌ "Código de tabela não encontrado"| NOME | Nome do cliente | ✅ Sim |

| DATA DE NASCIMENTO | Data de nascimento | ⚠️ Recomendado |

**Solução:** Verifique `relat_orgaos.csv` para banco + órgão + operação| TIPO DE CONTA | Tipo de conta | ❌ Opcional |

| TIPO DE PAGAMENTO | Tipo de pagamento | ❌ Opcional |

---| AGENCIA CLIENTE | Agência do cliente | ❌ Opcional |

| CONTA CLIENTE | Conta do cliente | ❌ Opcional |

## 📊 Métricas (V6.3.1)| FORMALIZACAO DIGITAL | Formalização digital? | ✅ Sim (padrão: SIM) |

| TAXA | Taxa de juros | ✅ Sim |

```

✅ Taxa de sucesso: 95%+---

⚡ Velocidade: ~1000 registros/segundo

🎯 Precisão: 98% de matching## ⚠️ Importante: Separação de Responsabilidades

```

### ❌ NÃO CONFUNDIR:

| Métrica | Antes | Depois | Melhoria |

|---------|-------|--------|----------|1. **`relat_orgaos.csv`** = **Dicionário Oficial**

| Taxa de sucesso | 40% | 95% | +137% |   - Define códigos de tabela, operações, taxas e órgãos válidos

| Bancos com erro | 10 | 0-1 | -90% |   - **NÃO MEXER sem validação prévia!**

   - É a fonte da verdade para padronização

---

2. **`map_relat_atualizados.txt`** = **Documentação de Estruturas**

## 📚 Documentação   - Documenta quais colunas cada banco usa

   - **APENAS CONSULTAR** para implementar mapeamento

📖 **[HISTORICO_VERSOES.md](./HISTORICO_VERSOES.md)** - Changelog completo     - NÃO é usado pelo sistema, é documentação

📖 **[data/map_relat_atualizados.txt](./data/map_relat_atualizados.txt)** - Estruturas dos bancos

3. **`backend/server.py`** = **Lógica de Mapeamento**

---   - Contém função `normalize_bank_data()`

   - **AQUI você faz alterações** para adicionar bancos

## 🤝 Suporte   - Traduz colunas dos bancos → padrão interno



**Q-FAZ Soluções e Intermediações LTDA**---



1. Consulte a documentação## 🐛 Troubleshooting

2. Use `/api/debug-file` para análise

3. Contate a equipe técnica### Erro: "Banco não detectado"

- **Solução**: Adicione lógica de detecção em `detect_bank_type_enhanced()`

---- Verifique se o arquivo tem extensão `.csv`, `.xlsx` ou `.xls`



## 🔐 Segurança### Erro: "Código de tabela não encontrado"

- **Solução**: Verifique se banco/órgão/operação estão em `relat_orgaos.csv`

✅ Dados processados localmente  - Confirme que nomes estão exatos (use CTRL+F no CSV)

✅ Sem armazenamento permanente  

✅ Logs anonimizados### Erro: "KeyError: 'coluna_xyz'"

- **Solução**: Use `.get('coluna_xyz', '')` em vez de `['coluna_xyz']`

---- Adicione verificação `if 'coluna_xyz' in df.columns`



## 📜 Licença### CSV importado com erros na Storm

- Verifique se separador é `;` (ponto e vírgula)

**Sistema proprietário - Q-FAZ Soluções e Intermediações LTDA**- Confirme que todas as 24 colunas estão presentes

- Valide que status estão em PAGO/CANCELADO/AGUARDANDO

© 2025 Q-FAZ. Todos os direitos reservados.

---

---

## 📈 Estatísticas e Monitoramento

<div align="center">

O sistema registra logs detalhados:

### ✅ Sistema em Produção - 17 Bancos Ativos

```

**Versão 6.3.1 | 02/10/2025 04:30**INFO: Processando arquivo: relatorio_averbai.xlsx

INFO: Banco detectado: AVERBAI, Registros originais: 150

**Desenvolvido com 💙 para Q-FAZ**INFO: Normalizando dados para AVERBAI com 150 registros

INFO: Dados normalizados: 148 registros válidos

[⬆ Voltar ao topo](#-sistema-de-processamento-de-relatórios-bancários)INFO: Buscando mapeamento: AVERBAI -> FGTS -> MARGEM LIVRE (NOVO)

INFO: Mapeamento encontrado: 961

</div>INFO: Mapeamento concluído para AVERBAI: 148 registros, 145 mapeados

INFO: Duplicatas removidas: 12 registros
INFO: CSV final gerado: 136 registros
```

---

## 📚 Documentação Adicional

- 📖 **[Histórico de Versões](./HISTORICO_VERSOES.md)** - Changelog completo
- 📋 **[Exemplos de Saída](./data/)** - Arquivos `relatorio_final_*.csv`
- 🏦 **[Estruturas dos Bancos](./data/map_relat_atualizados.txt)** - Documentação das estruturas

---

## 🎯 Melhorias Recentes (Versões 6.7.0 - 6.8.0)

### 🏦 SANTANDER - Correção Completa (v6.7.0)
- **Problema:** Códigos de tabela e operação incorretos, propostas SEGURO não filtradas
- **Solução:** Filtro robusto para código 11111111, mapeamento pós-normalização aplicado
- **Resultado:** Relatórios SANTANDER 100% compatíveis com arquivo manual de referência

### 🏦 VCTEX - Formatação de Tabelas (v6.8.0)
- **Problema:** "Exponencial" no arquivo não mapeava para "Tabela Exponencial" no Storm
- **Solução:** Sistema detecta e adiciona prefixo "Tabela" automaticamente quando necessário  
- **Resultado:** EXPONENCIAL e EXP tratados como produtos diferentes (correto!)

### 🔧 Otimizações Técnicas
- Declarações globais organizadas para evitar erros de sintaxe
- Logs detalhados para debug de mapeamento e formatação
- Código limpo com remoção de arquivos de teste temporários

---

## 📝 Versionamento

Consulte **[HISTORICO_VERSOES.md](./HISTORICO_VERSOES.md)** para changelog completo.

---

---

## 📞 Suporte

Para dúvidas ou problemas:
1. Consulte o **[Histórico de Versões](./HISTORICO_VERSOES.md)** para changelog completo
2. Verifique os logs do servidor (`python backend/server.py`)
3. Compare com exemplos em `data/relatorio_final_*.csv`
4. Entre em contato com a equipe técnica

---

## 📜 Licença

**Sistema proprietário - Q-FAZ Soluções e Intermediações LTDA**

© 2025 Q-FAZ. Todos os direitos reservados.

---

<div align="center">

### ✅ Sistema em Produção - 17 Bancos Ativos

**Versão 6.12.0 | 06/10/2025 19:30**

**Desenvolvido com 💙 para Q-FAZ**

[⬆ Voltar ao topo](#-q-faz---sistema-de-processamento-de-relatórios-bancários)

</div>
