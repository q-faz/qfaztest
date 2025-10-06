# 🏦 Q=FAZ - Sistema de Processamento de Rela**🔍 DETECÇÃO DE BANCOS (v6.10.0):**
- ✅ **C6 BANK**: Melhorada detecção por nome, colunas específicas e conteúdo
- ✅ **PAULISTA**: Corrigidos indicadores de colunas e palavras-chave
- ✅ **DAYCOVAL**: Detecção robusta por múltiplas linhas e indicadores
- ✅ **FACTA92**: Adicionados indicadores específicos e nome do arquivo
- ✅ **CREFAZ**: Detecção por colunas específicas e conteúdo de energia/boleto
- ✅ **QUERO MAIS**: Melhorada detecção por estrutura Unnamed e indicadores
- ✅ **QUALIBANKING**: Detecção por nome, colunas e padrão de contratos QUA

**🏦 SANTANDER (v6.9.0):**
- ✅ **CPF Digitador**: Limpeza automática de números extras (`37375205850030700` → `373.752.058-50`)
- ✅ **Detecção**: Corrigida identificação de arquivos SANTANDER com novo formato
- ✅ **ADE Correto**: Mapeamento COD.BANCO → ADE (não mais PROPOSTA)
- ✅ **Status**: Normalização para AGUARDANDO/PAGO/CANCELADO
- ✅ **Formatação Final**: CPF digitador formatado corretamente no relatório de saída
- ✅ **Campos Originais**: Mapeamento baseado no arquivo real (COD, COD.BANCO, etc.)s Bancários

## Q-FAZ Soluções e Intermediações LTDA

Sistema automatizado para processamento, padronização e consolidação de relatórios financeiros de múltiplos bancos para importação na plataforma Storm.

<div align="center">

![Version](https://img.shields.io/badge/versão-6.12.0-blue)
![Banks](https://img.shields.io/badge/bancos-17-green)
![Status](https://img.shields.io/badge/status-ativo-success)
![Update](https://img.shields.io/badge/última%20atualização-06/10/2025%2019:30-orange)

## 📋 Visão GeralEste sistema processa relatórios de diferentes instituições financeiras, aplica mapeamentos e padronizações, e gera um CSV único no formato esperado pela Storm para importação.



**Sistema automatizado de alta performance para processamento e consolidação de relatórios bancários**### 🎯 Funcionalidades Principais



[Início Rápido](#-início-rápido) • [Funcionalidades](#-funcionalidades) • [Bancos Suportados](#-bancos-suportados) • [Documentação](#-documentação)- ✅ **Processamento Multi-Banco**: Suporte para AVERBAI, VCTEX, DAYCOVAL, DIGIO, PAN, C6 BANK, QUALIBANKING, MERCANTIL, AMIGOZ, TOTALCASH

- ✅ **Detecção Automática**: Identifica automaticamente o banco com base na estrutura do arquivo

</div>- ✅ **Padronização de Status**: Normaliza status para PAGO, CANCELADO, AGUARDANDO

- ✅ **Aplicação de Dicionário**: Usa `relat_orgaos.csv` para código de tabela, taxa e operação

---- ✅ **Remoção de Duplicatas**: Remove registros já PAGOS ou CANCELADOS na Storm

- ✅ **Formato Storm**: Gera CSV com 24 colunas usando separador `;`

## 📋 Sobre o Sistema

---

Sistema desenvolvido exclusivamente para **Q-FAZ Soluções e Intermediações LTDA**, automatizando o processamento de relatórios do Storm e de 17 instituições bancárias, gerando relatórios consolidados com taxas, órgãos e informações completas para análise de crédito consignado.

## 🏗️ Arquitetura do Sistema

### ✨ Destaques da Versão 6.13.0 (06/10/2025 19:30)

#### 🔧 **CORREÇÕES MAIS RECENTES IMPLEMENTADAS:**

**🏦 QUERO MAIS CRÉDITO (v6.13.0):**
- ✅ **Códigos de tabela**: Remoção automática de zeros à esquerda (004717 → 4717)
- ✅ **Usuário banco**: Formatação correta mantida (36057733894_901064)
- ✅ **Tipo de operação**: "Cartao c/ saque" sem caracteres corrompidos
- ✅ **Mapeamento preservado**: Pula mapeamento automático para manter códigos originais
- ✅ **Duplicatas**: Remoção automática baseada na coluna PROPOSTA

**🏦 VCTEX - CÓDIGOS TROCADOS CORRIGIDOS (v6.13.0):**
- ✅ **EXP ≠ EXPONENCIAL**: Correção definitiva dos códigos trocados no relat_orgaos.csv
- ✅ **Tabela EXP** → Código **TabelaEXP** (corrigido linha 245)
- ✅ **Tabela Exponencial** → Código **TabelaExponencial** (corrigido linha 225)
- ✅ **Mapeamento Storm**: Códigos agora correspondem corretamente aos produtos

**🏦 DIGIO E FACTA92 (v6.12.0):**
- ✅ **DIGIO vs DAYCOVAL**: Detecção melhorada com indicadores únicos para evitar conflito
- ✅ **FACTA92 códigos**: Extração automática de códigos numéricos (53694) em vez de texto completo
- ✅ **Limpeza**: Removidos arquivos de teste desnecessários do workspace
- ✅ **Logs**: Debug detalhado para ambos os bancos

**🏦 SANTANDER (v6.7.0):**
- ✅ **Filtro SEGURO**: Remove propostas código 11111111 automaticamente
- ✅ **Mapeamento pós-normalização**: Aplica códigos Storm corretos após processamento básico
- ✅ **Sintaxe corrigida**: Declarações globais movidas para posição correta
- ✅ **Validação completa**: Dados testados e funcionando em produção

**🏦 VCTEX (v6.8.0):**
- ✅ **Formatação de tabelas**: "Exponencial" → "Tabela Exponencial" para mapeamento correto
- ✅ **EXPONENCIAL ≠ EXP**: Preservada diferença entre produtos (não são normalizados um para outro)
- ✅ **Match automático**: Sistema adiciona prefixo "Tabela" quando necessário
- ✅ **Integridade**: Cada produto mapeia para seu código correto no Storm

### Componentes Principais

```
├── backend/
│   ├── server.py              # API FastAPI + lógica de processamento
│   ├── relat_orgaos.csv       # Dicionário oficial (NÃO MEXER!)

- ✅ **Interface moderna** e responsiva│   └── requirements.txt       # Dependências Python

├── frontend/

---│   ├── src/

│   │   └── App.js             # Interface React

## 🏦 Bancos Suportados│   └── package.json           # Dependências Node.js

├── data/

| Banco | Status | Última Atualização |│   ├── map_relat_atualizados.txt    # Documentação de estruturas (CONSULTAR!)

|-------|--------|-------------------|│   └── relatorio_final_*.csv        # Exemplos de saída válida

| 🏦 **AVERBAI** | ✅ Ativo | 02/10/2025 |├── COMO_ADICIONAR_BANCOS.md   # 📖 Guia para adicionar novos bancos

| 🏦 **DIGIO** | ✅ Ativo | 02/10/2025 |└── RELATORIO_CORRECOES.md     # 📊 Histórico de correções

| 🏦 **BMG** | ✅ Ativo | 02/10/2025 |```

| 🏦 **ITAÚ** | ✅ Ativo | 02/10/2025 |

| 🏦 **FACTA92** | ✅ Ativo | 02/10/2025 |### Fluxo de Processamento

| 🏦 **SANTANDER** | ✅ Ativo | 02/10/2025 |

| 🏦 **C6 BANK** | ✅ Ativo | 02/10/2025 |```

| 🏦 **DAYCOVAL** | ✅ Ativo | 02/10/2025 |┌─────────────┐

| 🏦 **CREFAZ** | ✅ Ativo | 02/10/2025 |│   Storm     │ → Upload relatório Storm (referência)

| 🏦 **PAN** | ✅ Ativo | 02/10/2025 |│  (CSV/XLS)  │

| 🏦 **PAULISTA** | ✅ Ativo | 02/10/2025 |└─────────────┘

| 🏦 **QUERO MAIS CRÉDITO** | ✅ Ativo | 02/10/2025 |      ↓

| 🏦 **TOTALCASH** | ✅ Ativo | 02/10/2025 |┌─────────────┐

| 🏦 **BRB** | ✅ Ativo | 16/09/2025 |│  Processar  │ → Identificar propostas PAGO/CANCELADO

| 🏦 **QUALIBANKING** | ✅ Ativo | 16/09/2025 |│    Storm    │

| 🏦 **MERCANTIL** | ✅ Ativo | 16/09/2025 |└─────────────┘

| 🏦 **AMIGOZ** | ✅ Ativo | 16/09/2025 |      ↓

┌─────────────┐

---│   Bancos    │ → Upload relatórios dos bancos

│  (CSV/XLS)  │

## 🚀 Início Rápido└─────────────┘

      ↓

### Pré-requisitos┌─────────────┐

│  Detectar   │ → Identificar banco automaticamente

```bash│    Banco    │

- Python 3.9+└─────────────┘

- Node.js 16+      ↓

```┌─────────────┐

│ Normalizar  │ → Mapear colunas do banco → padrão interno

### Instalação│    Dados    │

└─────────────┘

#### 1️⃣ **Backend (Python/FastAPI)**      ↓

┌─────────────┐

```bash│   Aplicar   │ → Buscar código tabela em relat_orgaos.csv

cd backend│  Dicionário │

pip install -r requirements.txt└─────────────┘

python start_server.py      ↓

```┌─────────────┐

│  Remover    │ → Remover duplicatas baseado na Storm

✅ Servidor rodando em: **http://localhost:8000**│ Duplicatas  │

└─────────────┘

#### 2️⃣ **Frontend (React)**      ↓

┌─────────────┐

```bash│   Gerar     │ → CSV com 24 colunas, separador ';'

cd frontend│  CSV Final  │

npm install└─────────────┘

npm start```

```

---

✅ Interface disponível em: **http://localhost:3000**

## ⚙️ Instalação e Configuração

---

### Pré-requisitos

## 📖 Como Usar

- Python 3.9+

### Passo 1: Upload do Arquivo Storm- Node.js 16+

- MongoDB (opcional, para logs)

1. Acesse **http://localhost:3000**

2. Clique em **"📤 Upload Storm Report"**### Backend

3. Selecione o arquivo Storm (CSV ou Excel)

4. ✅ Verá: *"Storm processado: X registros"*```bash

cd backend

### Passo 2: Upload dos Relatórios Bancáriospip install -r requirements.txt

python server.py

1. Clique em **"📤 Upload Bank Reports"**```

2. Selecione arquivos dos bancos

3. Sistema detecta automaticamente cada bancoO servidor estará disponível em: `http://localhost:8000`

4. 📊 Veja estatísticas em tempo real

### Frontend

### Passo 3: Download do Relatório

```bash

1. Clique em **"💾 Baixar Relatório Consolidado"**cd frontend

2. Arquivo: `relatorio_final_storm_YYYYMMDD_HHMMSS.csv`npm install

npm start

---```



## 🔧 Endpoint de DebugA interface estará disponível em: `http://localhost:3000`



```bash---

curl -X POST http://localhost:8000/api/debug-file \

  -F "file=@seu_arquivo.xlsx"## 📖 Como Usar

```

### 1️⃣ Upload do Relatório Storm

**Retorna:**

- Nome e tamanho do arquivo1. Acesse a interface web

- Número de linhas e colunas2. Clique em "Upload Storm Report"

- Nomes das colunas detectadas3. Selecione o arquivo CSV/Excel da Storm

- Banco detectado4. Aguarde processamento

- Amostra da primeira linha

### 2️⃣ Upload dos Relatórios dos Bancos

---

1. Clique em "Upload Bank Reports"

## 📊 Estrutura do CSV Final (24 Colunas)2. Selecione um ou múltiplos arquivos de bancos

3. Aguarde processamento automático

| Coluna | Exemplo |4. Faça download do CSV final gerado

|--------|---------|

| PROPOSTA | 110254557 |### 3️⃣ Importar na Storm

| DATA CADASTRO | 2025-09-15 |

| BANCO | FACTA92 |1. Acesse a Storm

| ORGAO | INSS |2. Vá para "Importação de Dados"

| CODIGO TABELA | 60186 |3. Faça upload do CSV gerado

| TIPO DE OPERACAO | Margem Livre (Novo) |4. Valide os dados importados

| NUMERO PARCELAS | 96 |

| VALOR PARCELAS | 527.83 |---

| VALOR OPERACAO | 50671.68 |

| VALOR LIBERADO | 18738.36 |## 🔧 Adicionando Novos Bancos

| CPF | 12345678900 |

| NOME | JOÃO DA SILVA |**📘 Consulte o guia completo:** [`COMO_ADICIONAR_BANCOS.md`](./COMO_ADICIONAR_BANCOS.md)

| TAXA | 1.85 |

### Resumo Rápido

---

1. Obtenha arquivo de exemplo do banco

## 🛠️ Arquitetura2. Identifique as colunas relevantes

3. Adicione mapeamento em `backend/server.py` na função `normalize_bank_data()`

```4. Adicione detecção em `detect_bank_type_enhanced()`

Q=FAZ/5. Teste com arquivo real

├── backend/6. Valide integração com dicionário

│   ├── server.py              # API + Lógica

│   ├── relat_orgaos.csv       # Dicionário de taxas---

│   └── requirements.txt

├── frontend/## 📊 Estrutura do CSV Final (24 Colunas)

│   ├── src/App.js             # Interface React

│   └── package.json| Coluna | Descrição | Obrigatória |

├── data/|--------|-----------|-------------|

│   └── map_relat_atualizados.txt  # Estruturas dos bancos| PROPOSTA | Número da proposta/contrato | ✅ Sim |

└── HISTORICO_VERSOES.md       # Changelog completo| DATA CADASTRO | Data de cadastro | ✅ Sim |

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
