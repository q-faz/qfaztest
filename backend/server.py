from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import pandas as pd
import numpy as np
import tempfile
import json
import io
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class ProcessingJob(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "processing"  # processing, completed, failed
    message: str = ""
    processed_records: int = 0
    total_records: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    result_file: Optional[str] = None

class ReportSummary(BaseModel):
    bank_name: str
    total_records: int
    duplicates_removed: int
    status_distribution: Dict[str, int]
    mapped_records: int = 0
    unmapped_records: int = 0

# ===== MAPEAMENTOS COMPLETOS MELHORADOS =====

# Status normalization - Mapeamento COMPLETO
STATUS_MAPPING = {
    # ===== PAGO variants ===== (proposta finalizada e paga)
    "pago": "PAGO", 
    "paga": "PAGO", 
    "integrada": "PAGO", 
    "integrado": "PAGO",
    "finalizado": "PAGO", 
    "finalizada": "PAGO", 
    "finalizada / paga": "PAGO",
    "emitido": "PAGO", 
    "quitado": "PAGO", 
    "quitada": "PAGO", 
    "concluido": "PAGO", 
    "concluída": "PAGO", 
    "liberado": "PAGO", 
    "liberada": "PAGO",
    "desembolsado": "PAGO",
    "desembolsada": "PAGO",
    "valor desembolsado para a conta do cliente operação concluída.": "PAGO",
    "proposta integrada": "PAGO", 
    "int": "PAGO",
    "prova de vida aprovada / aguardando pagamento": "PAGO",
    "aprovado": "PAGO",
    "aprovada": "PAGO",
    "pago ao cliente": "PAGO",
    "credito liberado": "PAGO",
    
    # ===== CANCELADO variants ===== (proposta cancelada/reprovada)
    "cancelado": "CANCELADO", 
    "cancelada": "CANCELADO", 
    "reprovado": "CANCELADO", 
    "reprovada": "CANCELADO", 
    "rejeitado": "CANCELADO", 
    "rejeitada": "CANCELADO",
    "negado": "CANCELADO", 
    "negada": "CANCELADO", 
    "recusado": "CANCELADO",
    "recusada": "CANCELADO",
    "expirado": "CANCELADO", 
    "expirada": "CANCELADO", 
    "inválido": "CANCELADO", 
    "inválida": "CANCELADO",
    "invalido": "CANCELADO",
    "invalida": "CANCELADO",
    "cancelado devido a proposta expirada.": "CANCELADO",
    "cancelado permanentemente": "CANCELADO",
    "operação cancelada para desaverbação.": "CANCELADO",
    "reprovada - mesa de formalização": "CANCELADO",
    "reprovada - mesa de formalizacao": "CANCELADO",
    "proposta expirada": "CANCELADO",
    "rep": "CANCELADO", 
    "can": "CANCELADO",
    "reprovada por averbadora": "CANCELADO",
    "reprovada pelo banco": "CANCELADO",
    "nao aprovado": "CANCELADO",
    "não aprovado": "CANCELADO",
    "desistencia": "CANCELADO",
    "desistência": "CANCELADO",
    "cliente desistiu": "CANCELADO",
    
    # ===== AGUARDANDO variants ===== (proposta em processamento/pendente)
    "digitada / aguardando formalização": "AGUARDANDO",
    "digitada / aguardando formalizaÇÃo": "AGUARDANDO",
    "digitada / aguardando formalizacao": "AGUARDANDO",
    "emitido/aguardando averbação": "AGUARDANDO",
    "emitido/aguardando averbacao": "AGUARDANDO",
    "emitido/aguardando averbaã§ã£o": "AGUARDANDO",
    "criada / aguardando link de formalização": "AGUARDANDO",
    "criada / aguardando link de formalizacao": "AGUARDANDO",
    "aguardando saldo cip": "AGUARDANDO",
    "aguardando portabilidade": "AGUARDANDO",
    "aguardando prova de vida / assinatura": "AGUARDANDO",
    "aguardando prova de vida": "AGUARDANDO",
    "aguardando assinatura": "AGUARDANDO",
    "ajustar troco": "AGUARDANDO",
    "andamento": "AGUARDANDO", 
    "and": "AGUARDANDO", 
    "em andamento": "AGUARDANDO",
    "pendente": "AGUARDANDO", 
    "pendencia": "AGUARDANDO",
    "pendência": "AGUARDANDO",
    "aguardando pagamento": "AGUARDANDO",
    "aguardando": "AGUARDANDO",
    "pendência autorização": "AGUARDANDO",
    "pendencia autorizacao": "AGUARDANDO",
    "pendência / documentação": "AGUARDANDO",
    "pendencia / documentacao": "AGUARDANDO",
    "pendente documentacao": "AGUARDANDO",
    "pendente documentação": "AGUARDANDO",
    "link de prova de vida e coleta de assinatura enviado para o cliente.": "AGUARDANDO",
    "pendência de autorização da qitech para pagamento.": "AGUARDANDO",
    "pendente formalizacao": "AGUARDANDO",
    "pendente formalização": "AGUARDANDO",
    "aguardar aumento margem": "AGUARDANDO",
    "digitada": "AGUARDANDO",
    "em aberto": "AGUARDANDO",
    "aberto": "AGUARDANDO",
    "aberta": "AGUARDANDO",
    "formalização": "AGUARDANDO",
    "formalizacao": "AGUARDANDO",
    "checagem - mesa formalização": "AGUARDANDO",
    "checagem - mesa formalizacao": "AGUARDANDO",
    "aguarda form dig web": "AGUARDANDO",
    "analise corban": "AGUARDANDO",
    "análise corban": "AGUARDANDO",
    "em analise": "AGUARDANDO",
    "em análise": "AGUARDANDO",
    "analise": "AGUARDANDO",
    "análise": "AGUARDANDO",
    "processando": "AGUARDANDO",
    "em processamento": "AGUARDANDO",
    "cadastrada": "AGUARDANDO",
    "cadastrado": "AGUARDANDO",
    "nova": "AGUARDANDO",
    "novo": "AGUARDANDO",
    "enviado": "AGUARDANDO",
    "enviada": "AGUARDANDO",
    "aguardando averbacao": "AGUARDANDO",
    "aguardando averbação": "AGUARDANDO"
}

# Tipos de operação padronizados
OPERATION_TYPES = {
    "MARGEM LIVRE (NOVO)": "MARGEM LIVRE (NOVO)",
    "MARGEM LIVRE": "MARGEM LIVRE (NOVO)", 
    "margem livre (novo)": "MARGEM LIVRE (NOVO)",
    "PORTABILIDADE": "PORTABILIDADE",
    "PORTABILIDADE + REFIN": "PORTABILIDADE + REFIN",
    "REFINANCIAMENTO": "REFINANCIAMENTO",
    "REFINANCIAMENTO DA PORTABILIDADE": "REFINANCIAMENTO DA PORTABILIDADE",
    "EMPRÉSTIMO COMPLEMENTAR": "EMPRÉSTIMO COMPLEMENTAR",
    "Saque FGTS": "MARGEM LIVRE (NOVO)",
    "Consignado FGTS": "MARGEM LIVRE (NOVO)",
    "Consignado INSS": "MARGEM LIVRE (NOVO)",
    "Portabilidade + Refin": "PORTABILIDADE + REFIN",
    "Refinanciamento": "REFINANCIAMENTO",
    "Cartão c/ saque": "CARTÃO C/ SAQUE",
    "Cartão c/ saque complementar à vista": "CARTÃO C/ SAQUE COMPLEMENTAR À VISTA"
}

# Global storage for processing state
processing_jobs = {}
storm_data_global = {}

def load_organ_mapping():
    """Carrega o mapeamento de órgãos do arquivo CSV atualizado - MELHORADO sem dependência de usuário"""
    try:
        # Ler o arquivo de mapeamento atualizado usando caminho relativo
        csv_path = os.path.join(os.path.dirname(__file__), 'relat_orgaos.csv')
        # Tentar diferentes encodings
        try:
            df = pd.read_csv(csv_path, encoding='utf-8', sep=';')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(csv_path, encoding='latin-1', sep=';')
            except:
                df = pd.read_csv(csv_path, encoding='iso-8859-1', sep=';')
        
        # Formato REAL do arquivo: BANCO;ORGÃO STORM;TABELA BANCO;CODIGO TABELA STORM;OPERAÇÃO STORM;TAXA STORM
        # NOTA: Campo USUARIO DIGITADOR STORM foi removido para evitar problemas futuros com mudanças de usuário
        mapping = {}
        detailed_mapping = {}  # Mapeamento por BANCO|ORGÃO|OPERAÇÃO (múltiplas opções)
        tabela_mapping = {}     # Mapeamento por BANCO|ORGÃO|OPERAÇÃO|TABELA (mais específico)
        bank_organ_mapping = {} # Mapeamento por BANCO|ORGÃO (mais genérico para fallback)
        
        for _, row in df.iterrows():
            banco = ' '.join(str(row.get('BANCO', '')).strip().upper().split())
            # FIX ENCODING: Usar nomes de colunas como o pandas lê (com caracteres corrompidos)
            orgao = ' '.join(str(row.get('ORG�O STORM', '') or row.get('ÓRGÃO STORM', '')).strip().upper().split())
            # CRÍTICO: Normalizar tabela removendo TODOS os espaços extras (incluindo espaços iniciais)
            tabela_banco_raw = str(row.get('TABELA BANCO', '')).strip()
            tabela_banco = ' '.join(tabela_banco_raw.split())  # Remove espaços extras completamente
            codigo_tabela = str(row.get('CODIGO TABELA STORM', '')).strip()
            operacao_storm = str(row.get('OPERA��O STORM', '') or row.get('OPERAÇÃO STORM', '')).strip()
            taxa_storm = str(row.get('TAXA STORM', '')).strip()
            
            if banco and banco != 'NAN' and codigo_tabela and codigo_tabela != 'NAN':
                # Mapeamento simples (primeira ocorrência por hierarquia)
                if banco not in mapping:
                    mapping[banco] = {}
                if orgao and orgao != 'NAN':
                    if orgao not in mapping[banco]:
                        mapping[banco][orgao] = {}
                    if operacao_storm and operacao_storm != 'NAN':
                        if operacao_storm not in mapping[banco][orgao]:
                            mapping[banco][orgao][operacao_storm] = codigo_tabela
                
                # Mapeamento detalhado por BANCO|ORGÃO|OPERAÇÃO (guarda todas as opções)
                key = f"{banco}|{orgao}|{operacao_storm}"
                if key not in detailed_mapping:
                    detailed_mapping[key] = []
                detailed_mapping[key].append({
                    'codigo_tabela': codigo_tabela,
                    'tabela_banco': tabela_banco,
                    'orgao_storm': orgao,  # ORGÃO padronizado Storm
                    'operacao_storm': operacao_storm,
                    'taxa_storm': taxa_storm
                })
                
                # Mapeamento por TABELA (mais específico e confiável)
                if tabela_banco and tabela_banco != 'NAN':
                    # CRÍTICO: Salvar a chave com tabela em UPPERCASE para matching consistente
                    tabela_key = f"{banco}|{orgao}|{operacao_storm}|{tabela_banco.upper()}"
                    tabela_mapping[tabela_key] = {
                        'codigo_tabela': codigo_tabela,
                        'tabela_banco': tabela_banco,  # Manter original para exibição
                        'orgao_storm': orgao,  # ORGÃO padronizado Storm
                        'operacao_storm': operacao_storm,
                        'taxa_storm': taxa_storm
                    }
                
                # Mapeamento genérico por BANCO|ORGÃO (para fallback quando operação não bate exatamente)
                bank_organ_key = f"{banco}|{orgao}"
                if bank_organ_key not in bank_organ_mapping:
                    bank_organ_mapping[bank_organ_key] = []
                bank_organ_mapping[bank_organ_key].append({
                    'codigo_tabela': codigo_tabela,
                    'tabela_banco': tabela_banco,
                    'orgao_storm': orgao,
                    'operacao_storm': operacao_storm,
                    'taxa_storm': taxa_storm
                })
        
        logging.info(f"Mapeamento carregado: {len(mapping)} bancos, {len(detailed_mapping)} combinações banco+orgao+operacao, {len(tabela_mapping)} por tabela específica, {len(bank_organ_mapping)} por banco+orgao")
        return mapping, detailed_mapping, tabela_mapping, bank_organ_mapping
    except Exception as e:
        logging.error(f"Erro ao carregar mapeamento de órgãos: {str(e)}")
        return {}, {}, {}, {}

# Carregar mapeamento global - ATUALIZADO sem dependência de usuário
ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING = load_organ_mapping()

def reload_organ_mapping():
    """Recarrega o mapeamento de órgãos para pegar novos códigos de tabela adicionados"""
    global ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING
    try:
        logging.info("🔄 Recarregando mapeamento de órgãos...")
        ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING = load_organ_mapping()
        logging.info("✅ Mapeamento recarregado com sucesso!")
        return True
    except Exception as e:
        logging.error(f"❌ Erro ao recarregar mapeamento: {str(e)}")
        return False

def read_file_optimized(file_content: bytes, filename: str) -> pd.DataFrame:
    """Leitura otimizada de arquivos com múltiplas tentativas e melhor detecção de separadores"""
    file_ext = filename.lower().split('.')[-1]
    
    try:
        if file_ext == 'csv':
            # Tentar diferentes encodings e separadores
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                for sep in [';', ',', '\t', '|']:
                    try:
                        df = pd.read_csv(
                            io.BytesIO(file_content), 
                            encoding=encoding, 
                            sep=sep,
                            low_memory=False,
                            na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                            dtype=str  # Manter tudo como string inicialmente
                        )
                        
                        # Verificar se temos múltiplas colunas ou se precisa dividir
                        if len(df.columns) == 1 and sep != ';':
                            # Tentar dividir a única coluna por diferentes separadores
                            first_col = df.columns[0]
                            if ';' in first_col or ',' in first_col or '\t' in first_col:
                                continue  # Tentar próximo separador
                        
                        if len(df.columns) > 1 or (len(df.columns) == 1 and len(df) > 0):
                            logging.info(f"Arquivo lido com encoding {encoding} e separador '{sep}', {len(df.columns)} colunas")
                            return df
                            
                    except (UnicodeDecodeError, pd.errors.ParserError, Exception) as e:
                        continue
            
            # Se chegou aqui, tentar último recurso: detectar automaticamente o separador
            try:
                content_str = file_content.decode('utf-8', errors='ignore')
                # Verificar qual separador aparece mais nas primeiras linhas
                first_lines = content_str.split('\n')[:5]
                separators = {';': 0, ',': 0, '\t': 0, '|': 0}
                
                for line in first_lines:
                    for sep in separators:
                        separators[sep] += line.count(sep)
                
                best_sep = max(separators, key=separators.get)
                if separators[best_sep] > 0:
                    df = pd.read_csv(
                        io.BytesIO(file_content), 
                        encoding='utf-8', 
                        sep=best_sep,
                        low_memory=False,
                        na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                        dtype=str,
                        on_bad_lines='skip'
                    )
                    logging.info(f"Arquivo lido com separador auto-detectado '{best_sep}', {len(df.columns)} colunas")
                    return df
            except Exception as e:
                logging.error(f"Erro na detecção automática: {str(e)}")
            
            raise ValueError("Não foi possível ler o arquivo CSV com nenhum separador")
            
        elif file_ext in ['xlsx', 'xls']:
            # Tentar ler com diferentes configurações
            try:
                # Primeiro tentar leitura normal
                df = pd.read_excel(
                    io.BytesIO(file_content),
                    na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                    dtype=str
                )
                
                # Se o DataFrame está vazio ou tem só NaN, tentar pular linhas
                if df.empty or df.dropna(how='all').empty:
                    raise ValueError("DataFrame vazio após primeira tentativa")
                
                # Verificar se a primeira linha parece ser cabeçalho de metadados
                # (ex: "Relatório de...", "Banco:", etc.)
                if not df.empty:
                    first_row = df.iloc[0].astype(str).str.lower()
                    metadata_indicators = ['relatório', 'relatorio', 'banco:', 'data:', 'período', 
                                          'periodo', 'extração', 'extracao', 'total:', 'página']
                    
                    # Se encontrar indicadores de metadados, tentar pular linhas
                    if any(indicator in ' '.join(first_row.values) for indicator in metadata_indicators):
                        logging.info("Detectado cabeçalho de metadados, tentando pular linhas...")
                        
                        # Tentar pular de 1 a 10 linhas
                        for skip_rows in range(1, 11):
                            try:
                                df_attempt = pd.read_excel(
                                    io.BytesIO(file_content),
                                    skiprows=skip_rows,
                                    na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                                    dtype=str
                                )
                                
                                # Verificar se agora temos dados válidos
                                if not df_attempt.empty and len(df_attempt.columns) > 3:
                                    # Verificar se tem mais dados que a tentativa anterior
                                    valid_rows = df_attempt.dropna(how='all')
                                    if len(valid_rows) > 0:
                                        logging.info(f"Excel lido pulando {skip_rows} linhas, {len(df_attempt.columns)} colunas")
                                        return df_attempt
                            except:
                                continue
                
                # Se chegou aqui, usar o DataFrame original
                logging.info(f"Excel lido normalmente, {len(df.columns)} colunas")
                return df
                
            except Exception as e:
                # Última tentativa: ler todas as sheets e pegar a primeira com dados
                logging.warning(f"Tentativa normal falhou: {str(e)}, tentando ler todas as sheets...")
                try:
                    excel_file = pd.ExcelFile(io.BytesIO(file_content))
                    for sheet_name in excel_file.sheet_names:
                        try:
                            df = pd.read_excel(
                                io.BytesIO(file_content),
                                sheet_name=sheet_name,
                                na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                                dtype=str
                            )
                            if not df.empty and len(df.columns) > 1:
                                logging.info(f"Excel lido da sheet '{sheet_name}', {len(df.columns)} colunas")
                                return df
                        except:
                            continue
                except Exception as sheet_error:
                    logging.error(f"Erro ao ler sheets: {str(sheet_error)}")
                
                raise ValueError(f"Não foi possível ler o arquivo Excel: {str(e)}")
        elif file_ext in ['txt']:
            # TXT pode ser CSV com separadores variados
            try:
                # Tentar como CSV primeiro
                content_str = file_content.decode('utf-8')
            except:
                try:
                    content_str = file_content.decode('latin-1')
                except:
                    content_str = file_content.decode('cp1252')
            
            # Detectar separador
            first_lines = content_str.split('\n')[:5]
            separators = {';': 0, ',': 0, '\t': 0, '|': 0}
            
            for line in first_lines:
                for sep in separators:
                    separators[sep] += line.count(sep)
            
            best_sep = max(separators, key=separators.get)
            if separators[best_sep] > 0:
                df = pd.read_csv(
                    io.BytesIO(file_content), 
                    encoding='utf-8' if file_content.decode('utf-8', errors='ignore') else 'latin-1',
                    sep=best_sep,
                    low_memory=False,
                    na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                    dtype=str,
                    on_bad_lines='skip'
                )
                logging.info(f"Arquivo TXT lido com separador '{best_sep}', {len(df.columns)} colunas")
                return df
            else:
                raise ValueError("Arquivo TXT sem separadores reconhecíveis")
        else:
            raise ValueError(f"Formato não suportado: {file_ext}. Formatos aceitos: CSV, XLSX, XLS, TXT")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao ler arquivo {filename}: {str(e)}")

def detect_bank_type_enhanced(df: pd.DataFrame, filename: str) -> str:
    """Detecção melhorada de tipo de banco baseada na estrutura real dos arquivos"""
    filename_lower = filename.lower()
    df_columns = [str(col).lower().strip() for col in df.columns]
    
    logging.info(f"Detectando banco para arquivo: {filename}")
    logging.info(f"Colunas encontradas: {df_columns[:10]}...")  # Mostrar apenas primeiras 10
    
    # Detecção por nome do arquivo - mais confiável
    if any(indicator in filename_lower for indicator in ['storm', 'contratos', 'digitados']):
        return "STORM"
    elif 'averbai' in filename_lower:
        return "AVERBAI"
    elif 'digio' in filename_lower:
        return "DIGIO"
    elif 'prata' in filename_lower:
        return "PRATA"
    elif 'vctex' in filename_lower:
        return "VCTEX"
    elif 'daycoval' in filename_lower:
        return "DAYCOVAL"
    
    # Detecção por estrutura de colunas específica
    
    # Verificar se é Storm
    storm_indicators = ['ade', 'banco empréstimo', 'status do contrato']
    storm_matches = sum(1 for indicator in storm_indicators if any(indicator in col for col in df_columns))
    if storm_matches >= 2:
        return "STORM"
    
    # Verificar se é AVERBAI (tem colunas específicas como Id, IdTableComissao)
    averbai_indicators = ['id', 'idtablecomissao', 'tipoproduto', 'loginconsultor']
    averbai_matches = sum(1 for indicator in averbai_indicators if any(indicator in col for col in df_columns))
    if averbai_matches >= 2:
        return "AVERBAI"
    
    # Verificar se é DIGIO (melhorada - mais específica)
    if len(df.columns) > 50 and sum(1 for col in df_columns if 'unnamed:' in col) > 20:
        # Verificar dados específicos do Digio em múltiplas linhas
        if not df.empty:
            all_data = ""
            # Verificar primeiras 5 linhas para ser mais preciso
            for i in range(min(5, len(df))):
                row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
                all_data += " " + row_data
                
            logging.info(f"🔍 DIGIO check - dados: {all_data[:200]}...")
            
            # Indicadores únicos do DIGIO (não confundem com DAYCOVAL)
            digio_unique_indicators = ['banco digio', 'digio s.a', 'propostas cadastradas', 'tkt', 'status: ativo', 'status: cancelado', 'status: pago']
            found_digio_indicators = [ind for ind in digio_unique_indicators if ind in all_data]
            
            if found_digio_indicators:
                logging.info(f"✅ DIGIO detectado! Indicadores únicos: {found_digio_indicators}")
                return "DIGIO"
                
            # Se não tem indicadores únicos, verificar se NÃO é DAYCOVAL
            # DAYCOVAL tem indicadores específicos que DIGIO não tem
            daycoval_exclusive_indicators = ['banco daycoval', 'qfz solucoes', 'tp. operação']
            found_daycoval_indicators = [ind for ind in daycoval_exclusive_indicators if ind in all_data]
            
            if not found_daycoval_indicators:
                # Não é DAYCOVAL, pode ser DIGIO se tem estrutura similar
                logging.info(f"📊 DIGIO assumido por estrutura (sem indicadores DAYCOVAL)")
                return "DIGIO"
    
    # Verificar se é PRATA (tem colunas específicas)
    prata_indicators = ['corban master', 'número da proposta', 'prata digital', 'shake de morango']
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        prata_matches = sum(1 for indicator in prata_indicators if indicator in first_row_data)
        if prata_matches >= 1:
            return "PRATA"
    
    # Verificar se é VCTEX (tem colunas específicas)
    vctex_indicators = ['corban master', 'número do contrato', "it's solucoes", 'tabela vamo']
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        vctex_matches = sum(1 for indicator in vctex_indicators if indicator in first_row_data)
        if vctex_matches >= 1:
            return "VCTEX"
    
    # Verificar se é DAYCOVAL (melhorada)
    # 1. Por nome do arquivo
    if 'daycoval' in filename_lower:
        return "DAYCOVAL"
    
    # 2. Por estrutura de colunas específicas
    daycoval_column_indicators = ['cliente', 'cpf/cnpj', 'matrícula', 'dt.cad.', 'dt.base', 'vlr.oper', 'prz. em meses', 'tx.am']
    daycoval_col_matches = sum(1 for indicator in daycoval_column_indicators if any(indicator in col for col in df_columns))
    if daycoval_col_matches >= 5:
        return "DAYCOVAL"
    
    # 3. Por estrutura Unnamed + conteúdo
    unnamed_count = sum(1 for col in df_columns if 'unnamed:' in col)
    logging.info(f"🔍 DAYCOVAL Check - Colunas: {len(df.columns)}, Unnamed: {unnamed_count}")
    
    if len(df.columns) > 20 and unnamed_count > 15:
        # Verificar dados específicos do Daycoval em múltiplas linhas
        if not df.empty:
            all_data = ""
            for i in range(min(5, len(df))):
                row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
                all_data += " " + row_data
            
            logging.info(f"🔍 DAYCOVAL primeiras linhas: {all_data[:300]}")
            
            # Indicadores únicos do DAYCOVAL (não confundem com DIGIO)
            daycoval_unique_indicators = ['banco daycoval', 'qfz solucoes', 'tp. operação', 'detalhado']
            found_daycoval_indicators = [ind for ind in daycoval_unique_indicators if ind in all_data]
            
            # Verificar se NÃO tem indicadores do DIGIO
            digio_exclusive_indicators = ['banco digio', 'digio s.a', 'tkt', 'status: ativo', 'status: cancelado', 'status: pago']
            found_digio_indicators = [ind for ind in digio_exclusive_indicators if ind in all_data]
            
            if found_daycoval_indicators and not found_digio_indicators:
                logging.info(f"✅ DAYCOVAL detectado! Indicadores únicos: {found_daycoval_indicators}")
                return "DAYCOVAL"
            else:
                logging.info(f"⚠️ DAYCOVAL não detectado - indicadores DAYCOVAL: {found_daycoval_indicators}, indicadores DIGIO: {found_digio_indicators}")
    
    # Verificar se é SANTANDER (formato do relatório final)
    santander_indicators = ['proposta', 'banco', 'orgao', 'codigo tabela', 'tipo de operacao']
    santander_matches = sum(1 for indicator in santander_indicators if any(indicator in col for col in df_columns))
    # Verificar se tem "BANCO SANTANDER" nos dados
    if santander_matches >= 4:
        if not df.empty:
            banco_col = next((col for col in df.columns if 'banco' in str(col).lower()), None)
            if banco_col and any('SANTANDER' in str(val).upper() for val in df[banco_col].dropna()):
                return "SANTANDER"
    
    # Detecção por nome do arquivo SANTANDER
    if 'santander' in filename_lower:
        return "SANTANDER"
    
    # Verificar se é CREFAZ (melhorada)
    # 1. Por nome do arquivo
    if 'crefaz' in filename_lower:
        return "CREFAZ"
    
    # 2. Por colunas específicas do CREFAZ
    crefaz_column_indicators = ['data cadastro', 'número da proposta', 'cpf', 'cliente', 'cidade', 'valor liberado', 'prazo', 'status', 'agente']
    crefaz_col_matches = sum(1 for indicator in crefaz_column_indicators if any(indicator in col for col in df_columns))
    if crefaz_col_matches >= 5:
        return "CREFAZ"
    
    # 3. Por conteúdo (indicadores de energia/boleto)
    crefaz_content_indicators = ['produto', 'conveniada', 'cpfl', 'cosern', 'celpe', 'enel', 'cod operação', 'energia', 'boleto']
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        crefaz_matches = sum(1 for indicator in crefaz_content_indicators if indicator in first_row_data)
        if crefaz_matches >= 2:
            return "CREFAZ"
    
    # Verificar se é QUERO MAIS CREDITO (PRIORIDADE ALTA - antes do Paulista)
    # 1. Por nome do arquivo
    if 'quero' in filename_lower and 'mais' in filename_lower:
        logging.info("🎯 QUERO MAIS detectado por nome do arquivo")
        return "QUERO_MAIS"
    
    # 2. Por estrutura de colunas Unnamed específicas
    if len(df.columns) > 40 and sum(1 for col in df_columns if 'unnamed:' in col) > 30:
        # Verificar indicadores específicos do QUERO MAIS (ANTES do Paulista!)
        quero_mais_indicators = ['capital consig', 'quero mais credito', 'relatório de produção', 'promotora', 'grupo qfz', 'cpf correspondente', 'convênio correspondente']
        if not df.empty:
            # Verificar nas primeiras 5 linhas para maior precisão
            all_data = ""
            for i in range(min(5, len(df))):
                row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
                all_data += " " + row_data
            
            logging.info(f"🔍 QUERO MAIS check - dados: {all_data[:200]}...")
            
            # Indicadores únicos do QUERO MAIS (não confundem com PAULISTA)
            quero_mais_unique = ['capital consig', 'quero mais', 'promotora', 'grupo qfz', 'cpf correspondente']
            found_quero_indicators = [ind for ind in quero_mais_unique if ind in all_data]
            
            # Verificar se NÃO tem indicadores do PAULISTA
            paulista_exclusive = ['banco paulista', 'relação de propostas', 'espécie benefício', 'analítico']
            found_paulista_indicators = [ind for ind in paulista_exclusive if ind in all_data]
            
            if found_quero_indicators and not found_paulista_indicators:
                logging.info(f"✅ QUERO MAIS detectado! Indicadores únicos: {found_quero_indicators}")
                return "QUERO_MAIS"
            else:
                logging.info(f"⚠️ QUERO MAIS não detectado - indicadores QUERO: {found_quero_indicators}, PAULISTA: {found_paulista_indicators}")
    
    # Verificar se é BANCO PAN (tem estrutura específica de cartão)
    pan_indicators = ['nº proposta', 'nº operação', 'tipo de operação', 'código do produto', 'nome do produto']
    pan_matches = sum(1 for indicator in pan_indicators if any(indicator in col for col in df_columns))
    if pan_matches >= 3:
        return "PAN"
    
    # Verificar se é C6 BANK (melhorada)
    # 1. Por nome do arquivo
    if 'c6' in filename_lower:
        return "C6"
    
    # 2. Por indicadores nas colunas
    c6_column_indicators = ['nome entidade', 'numero do contrato', 'proposta', 'data da operacao']
    c6_column_matches = sum(1 for indicator in c6_column_indicators if any(indicator in col for col in df_columns))
    if c6_column_matches >= 3:
        return "C6"
    
    # 3. Por conteúdo dos dados
    c6_indicators = ['c6 bank', 'c6 consignado', 'banco c6']
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        if any(indicator in first_row_data for indicator in c6_indicators):
            return "C6"
    
    # Verificar se é FACTA92 (melhorada)
    # 1. Por nome do arquivo
    if 'facta' in filename_lower or 'relatóriovista' in filename_lower.replace(' ', ''):
        return "FACTA92"
    
    # 2. Por colunas específicas do FACTA92
    facta_indicators = ['codigo', 'data_cadastro', 'data_registro', 'proposta', 'convenio', 'averbador', 'tipo_operacao', 'tipo_tabela']
    facta_matches = sum(1 for indicator in facta_indicators if any(indicator in col for col in df_columns))
    if facta_matches >= 4:
        return "FACTA92"
    
    # Verificar se é PAULISTA (detecção melhorada)
    # 1. Por nome do arquivo
    if filename and 'paulista' in filename.lower():
        return "PAULISTA"
    
    # 2. Por colunas específicas do Paulista
    paulista_column_indicators = ['nº proposta', 'contrato', 'data captura', 'cpf/cnpj proponente', 'nome do proponente', 'matrícula']
    paulista_col_matches = sum(1 for indicator in paulista_column_indicators if any(indicator in col for col in df_columns))
    if paulista_col_matches >= 4:
        return "PAULISTA"
    
    # 3. Por indicadores na primeira linha
    paulista_indicators = ['banco paulista', 'relação de propostas', 'analítico', 'espécie benefício']
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        paulista_matches = sum(1 for indicator in paulista_indicators if indicator in first_row_data)
        if paulista_matches >= 2:
            return "PAULISTA"
    
    # 3. Por estrutura de colunas Unnamed específicas do Paulista (MELHORADA)
    paulista_columns = ['Unnamed: 0', 'Unnamed: 1', 'Unnamed: 4', 'Unnamed: 5', 'Unnamed: 14', 'Unnamed: 18']
    paulista_col_matches = sum(1 for col in paulista_columns if col in df_columns)
    if paulista_col_matches >= 5 and len(df_columns) > 20:  # Paulista tem muitas colunas
        # Verificar se tem dados que parecem do Paulista em qualquer linha
        if not df.empty:
            # Procurar em todas as linhas por palavras-chave do Paulista
            all_data = ""
            for i in range(min(5, len(df))):  # Verificar até 5 primeiras linhas
                row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
                all_data += " " + row_data
            
            logging.info(f"🔍 PAULISTA check - dados: {all_data[:200]}...")
            
            # Indicadores únicos do PAULISTA (não confundem com QUERO MAIS)
            paulista_unique_indicators = ['banco paulista', 'relação de propostas', 'espécie benefício', 'analítico']
            found_paulista_indicators = [ind for ind in paulista_unique_indicators if ind in all_data]
            
            # Verificar se NÃO tem indicadores do QUERO MAIS
            quero_mais_exclusive = ['capital consig', 'quero mais', 'promotora', 'grupo qfz', 'cpf correspondente']
            found_quero_indicators = [ind for ind in quero_mais_exclusive if ind in all_data]
            
            # PAULISTA só se tem indicadores únicos E não tem indicadores do QUERO MAIS
            if found_paulista_indicators and not found_quero_indicators:
                logging.info(f"✅ PAULISTA detectado! Indicadores únicos: {found_paulista_indicators}")
                return "PAULISTA"
            elif found_paulista_indicators and found_quero_indicators:
                logging.warning(f"🔄 Conflito PAULISTA vs QUERO MAIS - priorizando QUERO MAIS: {found_quero_indicators}")
                return "QUERO_MAIS"  # Em caso de dúvida, priorizar QUERO MAIS
            else:
                logging.info(f"⚠️ PAULISTA não detectado - indicadores PAULISTA: {found_paulista_indicators}, QUERO: {found_quero_indicators}")
                
            # Fallback: se tem estrutura Unnamed mas não tem indicadores únicos claros
            generic_keywords = ['inss', 'aposentad', 'pensão', 'consignado', 'benefici', 'cpf', 'proposta']
            keyword_matches = sum(1 for word in generic_keywords if word in all_data)
            
            # Só usar fallback se não conflitar com QUERO MAIS
            if keyword_matches >= 3 and not found_quero_indicators:
                logging.info(f"📊 PAULISTA assumido por estrutura + keywords genéricos (sem conflito QUERO MAIS)")
                return "PAULISTA"
    
    # Verificar se é TOTALCASH (tem estrutura específica)
    totalcash_indicators = ['totalcash', 'total cash']
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        if any(indicator in first_row_data for indicator in totalcash_indicators):
            return "TOTALCASH"
    
    # Verificar se é BRB (Banco de Brasília)
    brb_indicators = ['id card', 'nome do cliente', 'benefício', 'cpf do beneficiário', 'data da proposta', 'data da pagamento', 'nº contrato']
    brb_matches = sum(1 for indicator in brb_indicators if any(indicator in col for col in df_columns))
    if brb_matches >= 4:
        # Confirmar com dados
        if not df.empty:
            first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
            if 'brb' in first_row_data or 'banco de brasília' in first_row_data or 'q-faz' in first_row_data:
                return "BRB"
    
    # Verificar se é QUALIBANKING (melhorada)
    # 1. Por nome do arquivo
    if 'quali' in filename_lower or 'qualibanking' in filename_lower:
        return "QUALIBANKING"
    
    # 2. Por colunas específicas
    qualibanking_indicators = ['código', 'tipo', 'etapa', 'nome do produto', 'nome da tabela', 'código da tabela', 'tipo de produto', 'tipo de operação', 'data de cadastro', 'valor da operação']
    qualibanking_matches = sum(1 for indicator in qualibanking_indicators if any(indicator in col for col in df_columns))
    if qualibanking_matches >= 5:
        return "QUALIBANKING"
    
    # 3. Por padrão do número de contrato (QUA0000...)
    if not df.empty:
        for col in df.columns:
            if 'contrato' in str(col).lower() or 'código' in str(col).lower():
                try:
                    sample_val = str(df[col].iloc[0]).upper()
                    if sample_val.startswith('QUA'):
                        return "QUALIBANKING"
                except:
                    continue
    
    # 4. Por conteúdo dos dados
    if not df.empty:
        first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
        if 'qualibanking' in first_row_data or 'quali' in first_row_data:
            return "QUALIBANKING"
    
    # Verificar se é MERCANTIL (Banco Mercantil do Brasil)
    mercantil_indicators = ['numeroproposta', 'codigoconvenio', 'nomeconvenio', 'codigoproduto', 'nomeproduto', 'modalidadecredito', 'situacaoproposta']
    mercantil_matches = sum(1 for indicator in mercantil_indicators if any(indicator in col for col in df_columns))
    if mercantil_matches >= 4:
        # Confirmar com dados
        if not df.empty:
            first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
            if 'mercantil' in first_row_data or 'credfranco' in first_row_data or 'qfz solucoes' in first_row_data:
                return "MERCANTIL"
    
    # Verificar se é AMIGOZ
    amigoz_indicators = ['nr proposta', 'id banksoft', 'vulnerabilidade', 'aceite cliente vulneravel', 'grau de escolaridade', 'tipo de cartão']
    amigoz_matches = sum(1 for indicator in amigoz_indicators if any(indicator in col for col in df_columns))
    if amigoz_matches >= 3:
        # Confirmar com dados
        if not df.empty:
            first_row_data = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
            if 'amigoz' in first_row_data or 'cartão benefício' in first_row_data or 'cartão consignado' in first_row_data:
                return "AMIGOZ"
    
    # Detecção adicional por conteúdo dos dados
    if not df.empty:
        sample_data = str(df.iloc[0]).lower() if len(df) > 0 else ""
        
        if 'averbai' in sample_data or 'fixo 30' in sample_data:
            return "AVERBAI"
        elif 'digio' in sample_data or 'tkt' in sample_data:
            return "DIGIO"
        elif 'prata digital' in sample_data or 'shake de morango' in sample_data:
            return "PRATA"
        elif 'vctex' in sample_data or "it's solucoes" in sample_data:
            return "VCTEX"
        elif 'daycoval' in sample_data:
            return "DAYCOVAL"
    
    # Detecção por padrões de colunas
    if any('proposta' in col for col in df_columns):
        # Se tem muitas colunas unnamed, pode ser Digio ou Daycoval
        if sum(1 for col in df_columns if 'unnamed:' in col) > 20:
            # Distinguir entre DIGIO e DAYCOVAL pela primeira linha
            if not df.empty:
                first_row_content = ' '.join([str(val).lower() for val in df.iloc[0].values if pd.notna(val)])
                if 'daycoval' in first_row_content or 'nr.prop' in first_row_content or 'tp. operação' in first_row_content:
                    return "DAYCOVAL"
                else:
                    return "DIGIO"
            return "DIGIO"  # Default se não conseguir distinguir
        elif sum(1 for col in df_columns if 'unnamed:' in col) > 10:
            return "DAYCOVAL"
        # Se tem ID, provavelmente é Averbai
        elif any('id' in col for col in df_columns):
            return "AVERBAI"
        # Se tem "número da proposta", é Prata
        elif any('número da proposta' in col for col in df_columns):
            return "PRATA"
        # Se tem "número do contrato", é VCTEX
        elif any('número do contrato' in col for col in df_columns):
            return "VCTEX"
    
    # Se não conseguiu detectar, tentar por estrutura geral
    logging.warning(f"Não foi possível detectar automaticamente o tipo de banco para: {filename}")
    logging.warning(f"Número de colunas: {len(df.columns)}")
    logging.warning(f"Colunas Unnamed: {sum(1 for col in df_columns if 'unnamed:' in col)}")
    
    # Última tentativa: análise de conteúdo mais específica
    if not df.empty and len(df.columns) > 1:
        # Verificar conteúdo da primeira linha não vazia
        for idx, row in df.iterrows():
            row_content = ' '.join([str(val).lower() for val in row.values if pd.notna(val) and str(val).strip()])
            if row_content and len(row_content) > 10:  # Linha com conteúdo substantivo
                if 'banco digio' in row_content:
                    return "DIGIO"
                elif 'banco daycoval' in row_content:
                    return "DAYCOVAL"
                elif 'banco paulista' in row_content or 'paulista' in row_content:
                    return "PAULISTA"
                elif 'prata digital' in row_content:
                    return "PRATA"
                elif "it's solucoes" in row_content:
                    return "VCTEX"
                elif 'averbai' in row_content or 'saque fgts' in row_content:
                    return "AVERBAI"
                break
        
        # Tentativa final para Paulista: estrutura Unnamed + palavras-chave
        if len(df_columns) > 20 and sum(1 for col in df_columns if 'unnamed:' in col) > 15:
            # Procurar palavras-chave do Paulista em qualquer parte do DataFrame
            all_text = ""
            for i in range(min(5, len(df))):
                row_text = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
                all_text += " " + row_text
            
            paulista_keywords = ['inss', 'aposentad', 'pensão', 'consignado', 'benefici', 'cpf', 'proposta', 'contrato']
            keyword_matches = sum(1 for word in paulista_keywords if word in all_text)
            
            if keyword_matches >= 2:
                return "PAULISTA"
    
    raise HTTPException(status_code=400, detail=f"Tipo de banco não reconhecido para: {filename}. Estrutura: {len(df.columns)} colunas, {sum(1 for col in df_columns if 'unnamed:' in col)} colunas 'Unnamed'. Primeiras colunas: {df_columns[:5]}")

def process_storm_data_enhanced(df: pd.DataFrame) -> Dict[str, str]:
    """Processamento aprimorado dos dados da Storm"""
    storm_proposals = {}
    
    logging.info(f"Processando Storm com colunas: {list(df.columns)}")
    
    for _, row in df.iterrows():
        proposta = ""
        status = ""
        
        # Tentar diferentes formatos de colunas (case-insensitive)
        for idx, col in enumerate(df.columns):
            col_lower = str(col).lower()
            
            # Procurar coluna de proposta/ADE
            if any(term in col_lower for term in ['ade', 'proposta']) and not proposta:
                proposta = str(row.iloc[idx]).strip()
                
            # Procurar coluna de status
            if any(term in col_lower for term in ['status', 'situacao']) and not status:
                status = str(row.iloc[idx]).strip().lower()
        
        # Fallback: usar posições fixas se não encontrou pelos nomes
        if not proposta and len(df.columns) >= 1:
            proposta = str(row.iloc[0]).strip()
        if not status and len(df.columns) >= 3:
            status = str(row.iloc[2]).strip().lower()
        elif not status and len(df.columns) >= 2:
            status = str(row.iloc[1]).strip().lower()
        
        # Validar se proposta é numérica (ADE válido)
        if proposta and proposta != 'nan' and proposta not in ['ADE', 'ade', 'PROPOSTA']:
            # Limpar proposta (remover caracteres não numéricos exceto dígitos)
            proposta_clean = ''.join(c for c in proposta if c.isdigit())
            if proposta_clean and len(proposta_clean) >= 4:  # ADE deve ter pelo menos 4 dígitos
                normalized_status = STATUS_MAPPING.get(status, status.upper() if status else "AGUARDANDO")
                storm_proposals[proposta_clean] = normalized_status
                logging.info(f"Proposta processada: {proposta_clean} -> {normalized_status}")
    
    logging.info(f"Storm processada: {len(storm_proposals)} propostas")
    return storm_proposals

def normalize_operation_for_matching(operation: str) -> str:
    """Normaliza operação para comparação flexível (remove case sensitivity e preposições)"""
    if not operation:
        return ""
    
    # Normalizar básico
    normalized = ' '.join(operation.strip().split())
    
    # Converter para lowercase para comparação
    normalized_lower = normalized.lower()
    
    # Mapear variações conhecidas para forma canônica
    operation_mappings = {
        'refinanciamento da portabilidade': 'REFINANCIAMENTO DA PORTABILIDADE',
        'refinanciamento de portabilidade': 'REFINANCIAMENTO DA PORTABILIDADE', 
        'refin portabilidade': 'REFINANCIAMENTO DA PORTABILIDADE',
        'portabilidade': 'PORTABILIDADE',
        'refinanciamento': 'REFINANCIAMENTO',
        'margem livre': 'MARGEM LIVRE',
        'margem livre (novo)': 'MARGEM LIVRE (NOVO)',
        'novo': 'MARGEM LIVRE (NOVO)'
    }
    
    # Buscar mapeamento exato primeiro
    if normalized_lower in operation_mappings:
        return operation_mappings[normalized_lower]
    
    # Buscar por palavras-chave
    if 'portabilidade' in normalized_lower and 'refin' in normalized_lower:
        return 'REFINANCIAMENTO DA PORTABILIDADE'
    elif 'portabilidade' in normalized_lower:
        return 'PORTABILIDADE'
    elif 'refinanciamento' in normalized_lower:
        return 'REFINANCIAMENTO'
    elif 'margem' in normalized_lower:
        return 'MARGEM LIVRE (NOVO)'
    
    # Se não encontrou, retorna normalizado em uppercase
    return normalized.upper()

def apply_mapping_daycoval_corrected(organ: str, operation_type: str) -> dict:
    """
    🔧 DAYCOVAL - Mapeamento direto por Órgão + Operação
    DAYCOVAL não tem código da tabela no arquivo, então mapeia por órgão e operação
    """
    organ_normalized = organ.upper().strip()
    operation_normalized = operation_type.upper().strip()
    
    logging.info(f"🔧 DAYCOVAL Mapeamento - ORGAO: '{organ_normalized}', OPERACAO: '{operation_normalized}'")
    
    # Mapear para os padrões do CSV do DAYCOVAL
    # Códigos específicos encontrados no CSV: 803463, 801307, 805994, 821121, 231880
    
    if organ_normalized in ["INSS"]:
        if "PORTABILIDADE" in operation_normalized and "REFIN" in operation_normalized:
            # Refinanciamento da Portabilidade - INSS
            return {
                "codigo_tabela": "805994",  # Padrão DAYCOVAL no CSV
                "banco_storm": "BANCO DAYCOVAL",
                "orgao_storm": "INSS",
                "operacao_storm": "Refinanciamento da Portabilidade",
                "taxa_storm": "2.14"  # Taxa padrão DAYCOVAL
            }
        elif "PORTABILIDADE" in operation_normalized:
            # Portabilidade + Refin - INSS
            return {
                "codigo_tabela": "803463",  # Código comum DAYCOVAL
                "banco_storm": "BANCO DAYCOVAL",
                "orgao_storm": "INSS",
                "operacao_storm": "Portabilidade + Refin",
                "taxa_storm": "2.14"
            }
        elif "REFINANCIAMENTO" in operation_normalized:
            # Refinanciamento - INSS
            return {
                "codigo_tabela": "801307",  # Outro código DAYCOVAL
                "banco_storm": "BANCO DAYCOVAL",
                "orgao_storm": "INSS", 
                "operacao_storm": "Refinanciamento",
                "taxa_storm": "2.14"
            }
        else:
            # Margem Livre Novo - INSS
            return {
                "codigo_tabela": "821121",  # Código DAYCOVAL padrão
                "banco_storm": "BANCO DAYCOVAL",
                "orgao_storm": "INSS",
                "operacao_storm": "Margem Livre (Novo)",
                "taxa_storm": "2.14"
            }
            
    elif organ_normalized in ["SPPREV"]:
        # SPPREV - usar código específico
        return {
            "codigo_tabela": "231880",  # Código DAYCOVAL para SPPREV
            "banco_storm": "BANCO DAYCOVAL", 
            "orgao_storm": "SPPREV",
            "operacao_storm": operation_type,  # Manter operação original
            "taxa_storm": "2.14"
        }
        
    elif organ_normalized in ["EDUCACAO"]:
        # Educação - usar código geral
        return {
            "codigo_tabela": "803463",  # Código geral DAYCOVAL
            "banco_storm": "BANCO DAYCOVAL",
            "orgao_storm": "EDUCACAO", 
            "operacao_storm": operation_type,
            "taxa_storm": "2.14"
        }
    
    # Default - INSS Margem Livre
    logging.warning(f"⚠️ DAYCOVAL Mapeamento não específico para {organ_normalized} + {operation_normalized}, usando default INSS")
    return {
        "codigo_tabela": "803463",  # Código mais comum no CSV
        "banco_storm": "BANCO DAYCOVAL",
        "orgao_storm": "INSS", 
        "operacao_storm": "Margem Livre (Novo)",
        "taxa_storm": "2.14"
    }

def _detect_santander_orgao(row: dict) -> str:
    """Detectar órgão do SANTANDER baseado no CONVENIO/PRODUTO"""
    convenio = str(row.get('CONVENIO', '')).strip().upper()
    produto = str(row.get('PRODUTO', '')).strip().upper()
    
    if 'PREF' in convenio or 'PREFEITURA' in convenio or 'AGUDOS' in convenio or 'RANCHARIA' in convenio:
        return 'PREF. DE AGUDOS - SP'  # Padrão para prefeituras
    elif 'INSS' in convenio or 'INSS' in produto:
        return 'INSS'
    elif 'SEGURO' in convenio or 'SEGURO' in produto:
        return 'INSS'  # Seguro vinculado ao INSS
    else:
        return 'INSS'  # Default

def _get_santander_operation_type(row: dict) -> str:
    """Extrair tipo de operação do SANTANDER baseado no PRODUTO"""
    produto = str(row.get('PRODUTO', '')).strip().upper()
    
    if 'NOVO' in produto and 'REFIN' in produto:
        return 'Margem Livre (Novo)'  # Priorizar NOVO quando ambos estão presentes
    elif 'REFIN' in produto:
        return 'Refinanciamento'
    elif 'NOVO' in produto:
        return 'Margem Livre (Novo)'
    elif 'SEGURO' in produto:
        return 'Margem Livre (Novo)'  # Seguro é geralmente operação nova
    else:
        return 'Margem Livre (Novo)'  # Default

def _extract_santander_codigo_tabela(produto_str: str) -> str:
    """Extrair código tabela do campo PRODUTO do SANTANDER"""
    if not produto_str:
        return ""
    
    produto_str = str(produto_str).strip()
    
    # Padrão: "21387 - 810021387 - 1 OFERTA NOVO COM SEGURO"
    # Queremos extrair o código do meio (810021387)
    import re
    
    # Buscar padrão número - número - texto
    pattern = r'(\d+)\s*-\s*(\d+)\s*-'
    match = re.search(pattern, produto_str)
    if match:
        return match.group(2)  # Segundo número é o código
    
    # Se não encontrar o padrão, buscar números individuais
    numbers = re.findall(r'\d+', produto_str)
    if len(numbers) >= 2:
        # Pegar o maior número (provavelmente o código)
        return max(numbers, key=len)
    elif len(numbers) == 1:
        return numbers[0]
    
    return ""

def apply_mapping_santander_direct_code(codigo_tabela: str) -> dict:
    """Mapeamento direto para BANCO SANTANDER por código tabela extraído"""
    try:
        if not codigo_tabela or not codigo_tabela.isdigit():
            return {}
        
        # Procurar código no mapeamento
        for key, details in TABELA_MAPPING.items():
            if details.get('codigo_tabela') == codigo_tabela and 'BANCO SANTANDER' in key:
                logging.info(f"✅ SANTANDER código {codigo_tabela}: {details.get('orgao_storm')} | {details.get('operacao_storm')} | {details.get('taxa_storm')}")
                return {
                    'orgao_storm': details.get('orgao_storm', ''),
                    'operacao_storm': details.get('operacao_storm', ''),
                    'taxa_storm': details.get('taxa_storm', ''),
                    'codigo_tabela': codigo_tabela
                }
        
        logging.warning(f"⚠️ SANTANDER código {codigo_tabela}: Não encontrado no mapeamento")
        return {}
        
    except Exception as e:
        logging.error(f"❌ Erro no mapeamento direto Santander: {e}")
        return {}

def apply_mapping_averbai_corrected(organ: str, operation_type: str, tabela: str = "") -> dict:
    """Correção específica para AVERBAI - evita códigos 1005/1016 trocados com 994/992"""
    try:
        # Filtrar apenas registros AVERBAI do mapeamento
        averbai_candidates = []
        
        for key, details in TABELA_MAPPING.items():
            parts = key.split('|')
            if len(parts) == 4 and parts[0].upper() == 'AVERBAI':
                averbai_candidates.append((key, details))
        
        # Normalizar entradas
        organ_normalized = ' '.join(organ.strip().upper().split()) if organ else ""
        operation_normalized = normalize_operation_for_matching(operation_type)
        tabela_normalized = ' '.join(tabela.strip().upper().split()) if tabela else ""
        
        logging.info(f"🔎 AVERBAI CORRIGIDO - Buscando: {organ_normalized} | {operation_normalized} | '{tabela_normalized}'")
        
        # Criar lista de candidatos com scoring inteligente
        scored_candidates = []
        
        for key, details in averbai_candidates:
            parts = key.split('|')
            csv_banco, csv_orgao, csv_operacao, csv_tabela = parts
            
            # Normalizar dados do CSV
            csv_orgao_norm = ' '.join(csv_orgao.upper().split())
            csv_operacao_norm = ' '.join(csv_operacao.upper().split())
            csv_tabela_norm = ' '.join(csv_tabela.upper().split())
            
            # Score inicial: 0
            total_score = 0
            match_details = []
            
            # 1. ÓRGÃO deve ser EXATO (obrigatório)
            if csv_orgao_norm == organ_normalized:
                total_score += 1000  # Score alto para órgão correto
                match_details.append("ORGAO_EXATO")
            else:
                continue  # Pular se órgão não bate
            
            # 2. OPERAÇÃO (muito importante) - MELHORADA para distinguir 1005 vs 1016
            if csv_operacao_norm == operation_normalized:
                total_score += 500  # Score alto para operação exata
                match_details.append("OPERACAO_EXATA")
            elif operation_normalized in csv_operacao_norm or csv_operacao_norm in operation_normalized:
                # CORREÇÃO ESPECÍFICA: Distinguir "Refinanciamento da Portabilidade" vs "Refinanciamento Da Portabilidade"
                # Problema: 1016 com "Refinanciamento Da Portabilidade" estava sobrepondo 1005 com "Refinanciamento da Portabilidade"
                
                # Verificar se é match de case sensitivity (da vs Da)
                if csv_operacao_norm.replace("DA", "da") == operation_normalized.replace("DA", "da"):
                    # Match exato ignorando case de "da/Da" - dar score alto mas menor que exato
                    total_score += 450  # Score alto mas menor que operação exata
                    match_details.append("OPERACAO_CASE_SIMILAR")
                else:
                    total_score += 200  # Score médio para operação parcial
                    match_details.append("OPERACAO_PARCIAL")
            else:
                # Verificar palavras-chave comuns
                op_words_input = set(operation_normalized.split())
                op_words_csv = set(csv_operacao_norm.split())
                common_op_words = op_words_input.intersection(op_words_csv)
                if common_op_words:
                    total_score += len(common_op_words) * 50
                    match_details.append(f"OPERACAO_PALAVRAS({len(common_op_words)})")
                else:
                    continue  # Pular se operação não tem nada a ver
            
            # 3. TABELA (decisivo para desempate) - PRIORIDADE ABSOLUTA
            if tabela_normalized and csv_tabela_norm:
                if csv_tabela_norm == tabela_normalized:
                    total_score += 2000  # MATCH PERFEITO - PRIORIDADE ABSOLUTA (dobrado)
                    match_details.append("TABELA_EXATA")
                else:
                    # Análise por palavras mais sofisticada
                    tabela_words = set(w for w in tabela_normalized.split() if len(w) > 2)
                    csv_words = set(w for w in csv_tabela_norm.split() if len(w) > 2)
                    
                    if tabela_words and csv_words:
                        common_words = tabela_words.intersection(csv_words)
                        
                        if tabela_words == csv_words:
                            total_score += 800  # Mesmo conjunto de palavras
                            match_details.append("TABELA_PALAVRAS_IDENTICAS")
                        elif len(common_words) >= len(tabela_words) * 0.8:  # 80% das palavras
                            total_score += 600
                            match_details.append(f"TABELA_ALTA_SIMILARIDADE({len(common_words)}/{len(tabela_words)})")
                        elif len(common_words) >= len(tabela_words) * 0.5:  # 50% das palavras
                            total_score += 400
                            match_details.append(f"TABELA_MEDIA_SIMILARIDADE({len(common_words)}/{len(tabela_words)})")
                        elif common_words:
                            total_score += len(common_words) * 100
                            match_details.append(f"TABELA_ALGUMAS_PALAVRAS({len(common_words)})")
                    
                    # Bonus para substring match
                    if tabela_normalized in csv_tabela_norm or csv_tabela_norm in tabela_normalized:
                        total_score += 200
                        match_details.append("TABELA_SUBSTRING")
            
            # 4. Bonus para taxas mais altas (desempate)
            try:
                taxa_str = details.get('taxa_storm', '0%')
                taxa_float = float(taxa_str.replace('%', '').replace(',', '.'))
                total_score += taxa_float * 10  # Bonus pequeno para taxa mais alta
                match_details.append(f"TAXA_BONUS({taxa_float})")
            except:
                pass
            
            # 5. Priorização de códigos - CORREÇÃO ESPECÍFICA para 1005 vs 1016
            try:
                codigo_str = details.get('codigo_tabela', '0')
                codigo_int = int(codigo_str)
                
                # CORREÇÃO ESPECÍFICA: Quando não há tabela específica, priorizar códigos menores
                # Problema: 1016 (taxa 1,85%) estava ganhando de 1005 (taxa 1,80%) sem tabela
                if not tabela_normalized or len(tabela_normalized) == 0:
                    # Sem tabela específica: priorizar códigos menores (mais estabelecidos)
                    if codigo_int <= 1005:  # Códigos "antigos" têm prioridade
                        total_score += 100
                        match_details.append(f"CODIGO_ESTABELECIDO({codigo_int})")
                    else:
                        # Códigos novos têm menor prioridade quando não há tabela específica
                        total_score += 50
                        match_details.append(f"CODIGO_NOVO_SEM_TABELA({codigo_int})")
                else:
                    # Com tabela específica: códigos maiores podem ter ligeira vantagem
                    if codigo_int >= 1000:
                        total_score += codigo_int * 0.05  # Reduzido de 0.1 para 0.05
                        match_details.append(f"CODIGO_NOVO({codigo_int})")
            except:
                pass
            
            # Adicionar candidato se tem score mínimo
            if total_score >= 1000:  # Pelo menos órgão correto
                scored_candidates.append({
                    'details': details,
                    'score': total_score,
                    'match_info': ' + '.join(match_details),
                    'tabela_csv': csv_tabela_norm
                })
        
        # Ordenar candidatos por score (maior primeiro)
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        
        # Log dos candidatos
        logging.info(f"📊 AVERBAI - Encontrados {len(scored_candidates)} candidatos:")
        for i, candidate in enumerate(scored_candidates[:3]):  # Top 3
            codigo = candidate['details'].get('codigo_tabela', 'N/A')
            taxa = candidate['details'].get('taxa_storm', 'N/A')
            logging.info(f"   {i+1}. Score {candidate['score']}: Código {codigo} | Taxa {taxa}")
            logging.info(f"      Match: {candidate['match_info']}")
        
        if not scored_candidates:
            logging.error(f"❌ AVERBAI - Nenhum candidato encontrado para {organ_normalized} | {operation_normalized}")
            return {}
        
        # Retornar o melhor candidato
        best = scored_candidates[0]
        result = best['details']
        
        logging.info(f"✅ AVERBAI RESULTADO CORRIGIDO: Código {result.get('codigo_tabela')} | Score {best['score']}")
        
        return result
        
    except Exception as e:
        logging.error(f"❌ Erro no mapeamento AVERBAI corrigido: {str(e)}")
        return {}

def apply_mapping(bank_name: str, organ: str, operation_type: str, usuario: str = "", tabela: str = "") -> dict:
    """Aplica mapeamento automático MELHORADO com correção específica para AVERBAI"""
    try:
        # Normalizar nomes para busca (remover espaços extras e converter para uppercase)
        bank_normalized = ' '.join(bank_name.strip().upper().split()) if bank_name else ""
        organ_normalized = ' '.join(organ.strip().upper().split()) if organ else ""
        operation_normalized = normalize_operation_for_matching(operation_type)
        
        # Normalizar tabela (SEM modificações - preservar nomes originais)
        tabela_normalized = ' '.join(tabela.strip().upper().split()) if tabela else ""
        
        # CORREÇÃO ESPECÍFICA PARA AVERBAI - usar função especializada
        if bank_normalized == "AVERBAI":
            logging.info(f"🔧 AVERBAI detectado - usando correção específica")
            return apply_mapping_averbai_corrected(organ, operation_type, tabela)
            
        # CORREÇÃO ESPECÍFICA PARA DAYCOVAL - usar função especializada
        if bank_normalized == "BANCO DAYCOVAL" or bank_normalized == "DAYCOVAL":
            logging.info(f"🔧 DAYCOVAL detectado - usando correção específica por órgão+operação")
            return apply_mapping_daycoval_corrected(organ, operation_type)
            
        # CORREÇÃO ESPECÍFICA PARA SANTANDER - usar mapeamento direto por código
        if bank_normalized == "BANCO SANTANDER" or bank_normalized == "SANTANDER":
            # Para Santander, usar o parâmetro tabela como código_tabela
            if tabela_normalized and tabela_normalized.isdigit():
                logging.info(f"🏦 SANTANDER detectado - usando mapeamento direto por código: {tabela_normalized}")
                return apply_mapping_santander_direct_code(tabela_normalized)
            else:
                logging.warning(f"⚠️ SANTANDER sem código válido ({tabela_normalized}), usando busca tradicional")
        
        logging.info(f"🔍 Buscando mapeamento: BANCO={bank_normalized} | ORGAO={organ_normalized} | OPERACAO={operation_normalized} | TABELA={tabela_normalized}")
        
        logging.info(f"🔍 Buscando mapeamento: BANCO={bank_normalized} | ORGAO={organ_normalized} | OPERACAO={operation_normalized} | TABELA={tabela_normalized}")
        
        # PRIORIDADE 1: Busca EXATA por BANCO + ORGÃO + OPERAÇÃO + TABELA (mais específico e confiável)
        if tabela_normalized:
            best_match = None
            best_match_score = 0
            
            # Log detalhado para AVERBAI
            is_averbai = bank_normalized == "AVERBAI"
            if is_averbai:
                logging.info(f"🔎 AVERBAI - Iniciando busca por tabela: '{tabela_normalized}' (len={len(tabela_normalized)})")
            
            for key, details in TABELA_MAPPING.items():
                parts = key.split('|')
                if len(parts) == 4:
                    key_banco, key_orgao, key_operacao, key_tabela = parts
                    # Normalizar keys removendo espaços extras
                    key_banco_norm = ' '.join(key_banco.upper().split())
                    key_orgao_norm = ' '.join(key_orgao.upper().split())
                    key_operacao_norm = ' '.join(key_operacao.upper().split())
                    key_tabela_norm = ' '.join(key_tabela.upper().split())
                    
                    # Busca EXATA para banco
                    if bank_normalized != key_banco_norm:
                        continue
                    
                    # Busca FLEXÍVEL para órgão (pode variar ligeiramente)
                    organ_match = (
                        organ_normalized == key_orgao_norm or
                        organ_normalized in key_orgao_norm or 
                        key_orgao_norm in organ_normalized
                    )
                    
                    if not organ_match:
                        continue
                    
                    # Para tabela, usar matching inteligente com diferentes níveis de precisão
                    match_score = 0
                    
                    if tabela_normalized == key_tabela_norm:
                        match_score = 5  # Match exato (melhor)
                    else:
                        # Análise por palavras para casos com formatação diferente
                        tabela_words = set(tabela_normalized.split())
                        key_words = set(key_tabela_norm.split())
                        
                        # Remover palavras muito curtas que são ruído
                        tabela_words_filtered = {w for w in tabela_words if len(w) > 2}
                        key_words_filtered = {w for w in key_words if len(w) > 2}
                        
                        # Verificar se todas as palavras significativas batem
                        if tabela_words_filtered and key_words_filtered:
                            if tabela_words_filtered == key_words_filtered:
                                match_score = 4  # Mesmo conjunto de palavras, ordem diferente
                            elif tabela_words_filtered.issubset(key_words_filtered):
                                match_score = 3  # Tabela do banco contém todas as palavras do CSV
                            elif key_words_filtered.issubset(tabela_words_filtered):
                                match_score = 3  # CSV contém todas as palavras da tabela do banco
                            else:
                                # Calcular palavras em comum
                                common_words = tabela_words_filtered.intersection(key_words_filtered)
                                if len(common_words) >= min(2, len(tabela_words_filtered) // 2):
                                    match_score = 2  # Pelo menos metade das palavras batem
                        
                        # Fallback: matching por substring (menos confiável)
                        if match_score == 0:
                            if tabela_normalized in key_tabela_norm or key_tabela_norm in tabela_normalized:
                                match_score = 1
                    
                    # Guardar melhor match
                    if match_score > best_match_score:
                        best_match_score = match_score
                        best_match = details
                        best_match_key = key_tabela_norm
                        
                        # Log detalhado para AVERBAI
                        if is_averbai:
                            logging.info(f"  ✨ MELHOR MATCH até agora: score={match_score}, tabela_csv='{key_tabela_norm}', codigo={details.get('codigo_tabela', 'N/A')}, taxa={details.get('taxa_storm', 'N/A')}")
            
            if best_match:
                if is_averbai:
                    logging.info(f"✅ AVERBAI - Resultado FINAL: score={best_match_score}, key='{best_match_key}', Codigo={best_match['codigo_tabela']}, Taxa={best_match['taxa_storm']}, Operacao={best_match['operacao_storm']}")
                else:
                    logging.info(f"✅ Mapeamento por TABELA (score={best_match_score}): Codigo={best_match['codigo_tabela']} | Taxa={best_match['taxa_storm']} | Operacao={best_match['operacao_storm']}")
                return best_match
            
            # Log se tabela não foi encontrada
            if is_averbai:
                logging.error(f"❌ AVERBAI - TABELA NÃO ENCONTRADA: '{tabela_normalized}' - Tentando fallback genérico")
            else:
                logging.warning(f"⚠️ Tabela '{tabela_normalized}' não encontrada, tentando fallback genérico")
        
        # PRIORIDADE 2: Busca por BANCO + ORGÃO + OPERAÇÃO (usa DETAILED_MAPPING)
        detail_key_candidates = []
        
        for bank_key, organs in ORGAN_MAPPING.items():
            bank_key_norm = ' '.join(bank_key.upper().split())
            # Busca EXATA para banco
            if bank_normalized == bank_key_norm:
                for organ_key, operations in organs.items():
                    organ_key_norm = ' '.join(organ_key.upper().split())
                    # Busca FLEXÍVEL para órgão
                    organ_match = (
                        organ_normalized == organ_key_norm or
                        organ_normalized in organ_key_norm or 
                        organ_key_norm in organ_normalized
                    )
                    if organ_match:
                        for op_key, table_code in operations.items():
                            op_key_norm = ' '.join(op_key.upper().split())
                            # Busca FLEXÍVEL para operação
                            operation_match = (
                                operation_normalized == op_key_norm or
                                operation_normalized in op_key_norm or 
                                op_key_norm in operation_normalized
                            )
                            if operation_match:
                                detail_key = f"{bank_key}|{organ_key}|{op_key}"
                                detail_key_candidates.append(detail_key)
        
        # Processar candidatos do mapeamento detalhado com PRIORIZAÇÃO INTELIGENTE
        if detail_key_candidates:
            best_candidate = None
            best_score = 0
            
            for detail_key in detail_key_candidates:
                options = DETAILED_MAPPING.get(detail_key, [])
                if options:
                    details = options[0]  # Usar primeira opção da lista
                    
                    # Calcular score de especificidade da chave
                    parts = detail_key.split('|')
                    if len(parts) >= 3:
                        operation_part = parts[2]
                        
                        # Score baseado em especificidade
                        score = 0
                        
                        # 1. Match exato de operação (case sensitive) tem prioridade máxima
                        if operation_part == operation_type:
                            score += 1000
                        
                        # 2. Match de operação normalizada
                        elif operation_part.upper() == operation_normalized:
                            score += 500
                        
                        # 3. Operações mais específicas (mais palavras) têm prioridade
                        word_count = len(operation_part.split())
                        score += word_count * 50
                        
                        # 4. Taxa mais alta tem ligeira prioridade (desempate)
                        taxa = details.get('taxa_storm', '0%').replace('%', '').replace(',', '.')
                        try:
                            taxa_float = float(taxa)
                            score += taxa_float
                        except:
                            pass
                        
                        # Log detalhado para AVERBAI
                        if bank_normalized == "AVERBAI":
                            logging.info(f"🏆 Candidato: '{detail_key}' | Score={score} | Código={details.get('codigo_tabela')} | Taxa={details.get('taxa_storm')}")
                        
                        if score > best_score:
                            best_score = score
                            best_candidate = (detail_key, details)
            
            if best_candidate:
                detail_key, details = best_candidate
                logging.info(f"✅ MELHOR CANDIDATO (score={best_score}): {detail_key} -> Codigo={details['codigo_tabela']} | Taxa={details['taxa_storm']}")
                return details
        
        # PRIORIDADE 3: Busca genérica por BANCO + ORGÃO (fallback mais amplo)
        bank_organ_key = f"{bank_normalized}|{organ_normalized}"
        if bank_organ_key in BANK_ORGAN_MAPPING:
            options = BANK_ORGAN_MAPPING[bank_organ_key]
            if options:
                # Tentar encontrar a operação mais compatível
                best_option = None
                best_op_score = 0
                
                for option in options:
                    op_storm = option.get('operacao_storm', '').upper()
                    # Calcular compatibilidade da operação com priorização inteligente
                    if operation_normalized == op_storm:
                        op_score = 100  # Match exato - máxima prioridade
                    elif operation_normalized in op_storm:
                        # Operação buscada está contida na operação do Storm
                        # Dar prioridade a operações mais específicas (mais palavras)
                        word_count_bonus = len(op_storm.split()) * 5
                        op_score = 50 + word_count_bonus  # Substring match + bonus por especificidade
                    elif op_storm in operation_normalized:
                        # Operação Storm está contida na operação buscada
                        op_score = 40  # Substring match reverso
                    elif any(word in op_storm for word in operation_normalized.split()) or any(word in operation_normalized for word in op_storm.split()):
                        # Palavras em comum
                        common_words = len(set(operation_normalized.split()) & set(op_storm.split()))
                        op_score = 10 + (common_words * 2)  # Base + bonus por palavra comum
                    else:
                        op_score = 0
                    
                    # Log detalhado para AVERBAI debug
                    if bank_normalized == "AVERBAI" and operation_normalized and op_score > 0:
                        logging.info(f"🔍 AVERBAI Score: '{operation_normalized}' vs '{op_storm}' = {op_score} (Código: {option.get('codigo_tabela', 'N/A')})")
                    
                    if op_score > best_op_score:
                        best_op_score = op_score
                        best_option = option
                
                if best_option:
                    logging.info(f"✅ Mapeamento GENÉRICO por BANCO+ORGAO: Codigo={best_option['codigo_tabela']} | Taxa={best_option['taxa_storm']} | Operacao={best_option['operacao_storm']}")
                    return best_option
                else:
                    # Se não encontrou por operação, usar a primeira opção
                    first_option = options[0]
                    logging.warning(f"⚠️ Usando primeira opção genérica para {bank_normalized}+{organ_normalized}: Codigo={first_option['codigo_tabela']} | Taxa={first_option['taxa_storm']}")
                    return first_option
        
        # Se chegou até aqui, não encontrou nenhum mapeamento
        logging.error(f"❌ NENHUM mapeamento encontrado para: {bank_normalized} -> {organ_normalized} -> {operation_normalized}")
        return {}
        
    except Exception as e:
        logging.error(f"❌ Erro no mapeamento: {str(e)}")
        return {}

def normalize_bank_data(df: pd.DataFrame, bank_type: str) -> pd.DataFrame:
    """Normaliza dados do banco para estrutura padrão usando mapeamento correto baseado no arquivo"""
    # Garantir acesso às variáveis globais
    global ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING
    
    normalized_data = []
    
    logging.info(f"🔧 INICIANDO normalize_bank_data para {bank_type} com {len(df)} registros")
    logging.info(f"Colunas disponíveis: {list(df.columns)}")
    
    # VALIDAÇÃO: Remover linhas completamente vazias
    df = df.dropna(how='all')
    
    # VALIDAÇÃO: Verificar se ainda tem dados
    if df.empty:
        logging.error(f"❌ {bank_type}: DataFrame vazio após remover linhas vazias")
        return pd.DataFrame()
    
    # VALIDAÇÃO: Verificar se tem pelo menos 3 colunas
    if len(df.columns) < 3:
        logging.error(f"❌ {bank_type}: Muito poucas colunas ({len(df.columns)}) - Colunas: {list(df.columns)}")
        return pd.DataFrame()
    
    logging.info(f"✅ DataFrame passou validações - {len(df)} registros, {len(df.columns)} colunas")
    
    logging.info(f"Após limpeza: {len(df)} registros válidos com {len(df.columns)} colunas")
    
    for idx, row in df.iterrows():
        logging.info(f"🔍 PROCESSANDO linha {idx}: {dict(row)}")
        
        # Pular linhas que são claramente cabeçalhos ou metadados
        row_str = ' '.join([str(val).lower() for val in row.values if pd.notna(val)])
        
        # Detectar linhas de metadados/cabeçalho
        metadata_indicators = [
            'relatório', 'relatorio', 'total de registros', 'total:', 'página',
            'data de emissão', 'data de extração', 'banco:', 'período',
            'nome do banco', 'agencia:', 'conta:', 'saldo:'
        ]
        
        # Detectar linhas de cabeçalho específicas do BANCO PAULISTA
        paulista_header_indicators = [
            'nº proposta', 'numero proposta', 'data captura', 'banco paulista',
            'cpf/cnpj proponente', 'nome do proponente', 'valor solicitado',
            'quant. parcelas', 'usuário digitador', 'usuario digitador'
        ]
        
        if any(indicator in row_str for indicator in metadata_indicators + paulista_header_indicators):
            logging.debug(f"Pulando linha de cabeçalho/metadados: {row_str[:100]}")
            continue
        
        normalized_row = {}
        
        logging.debug(f"🔧 Normalizando linha {idx} para banco: {bank_type}")
        
        if bank_type == "AVERBAI":
            # Mapeamento AVERBAI - Baseado na estrutura REAL do map_relat_atualizados.txt
            # Detectar tipo de operação do campo TipoProduto ou outro campo
            tipo_produto = str(row.get('TipoProduto', '')).strip()
            tipo_operacao_averbai = "Margem Livre (Novo)"  # padrão
            orgao_averbai = ""
            
            # Identificar ORGAO e tipo de operação baseado nos campos do arquivo
            tipo_produto_upper = tipo_produto.upper()
            
            # Detectar tipo de operação PRIMEIRO (isso afeta o órgão)
            if 'PORTABILIDADE' in tipo_produto_upper and 'REFIN' in tipo_produto_upper:
                tipo_operacao_averbai = "Refinanciamento Da Portabilidade"  # ✅ Corrigido para maiúsculo "Da"
            elif 'PORTABILIDADE' in tipo_produto_upper:
                tipo_operacao_averbai = "Portabilidade"
            elif 'REFIN' in tipo_produto_upper:
                tipo_operacao_averbai = "Refinanciamento"
            else:
                tipo_operacao_averbai = "Margem Livre (Novo)"
            
            # Detectar ORGAO - CRÍTICO: Portabilidade/Refinanciamento são sempre INSS no CSV!
            if tipo_operacao_averbai in ["Portabilidade", "Refinanciamento Da Portabilidade", "Refinanciamento"]:
                # Portabilidade e Refinanciamento estão cadastrados como INSS no CSV
                orgao_averbai = 'INSS'
            elif 'INSS' in tipo_produto_upper or 'SAQUE INSS' in tipo_produto_upper:
                orgao_averbai = 'INSS'
            elif 'FGTS' in tipo_produto_upper or 'SAQUE FGTS' in tipo_produto_upper:
                orgao_averbai = 'FGTS'
            else:
                orgao_averbai = 'FGTS'  # Default
            
            # Normalizar nome da tabela AVERBAI removendo espaços extras e variações
            tabela_raw = str(row.get('Tabela', '')).strip()
            # Normalizar: remover espaços extras no início/fim e múltiplos espaços internos
            tabela_normalizada = ' '.join(tabela_raw.split()) if tabela_raw else ""
            
            # 🎯 SOLUÇÃO DEFINITIVA: Usar código direto do arquivo AVERBAI!
            # Campo IdTableComissao já tem o código correto (1005, 1016, 994, 992, etc)
            codigo_tabela_direto = str(row.get('IdTableComissao', '')).strip()
            cpf_cliente = str(row.get('CpfCliente', '')).strip()
            
            # 💰 FUNÇÃO para formatar valores no padrão brasileiro
            def format_brazilian_currency(value_str):
                """Converte valores para formato brasileiro: 1.500,39 ou 87,58"""
                if not value_str or str(value_str).strip() in ['', 'nan', 'None', '0']:
                    return "0,00"
                
                try:
                    # Limpar o valor (remover espaços, moeda, etc.)
                    clean_value = str(value_str).strip().replace('R$', '').replace(' ', '')
                    
                    # Se já está no formato brasileiro, manter
                    if ',' in clean_value and clean_value.count(',') == 1:
                        parts = clean_value.split(',')
                        if len(parts[1]) == 2:  # Duas casas decimais após vírgula
                            return clean_value
                    
                    # Converter do formato americano (ponto decimal)
                    if '.' in clean_value:
                        # Separar parte inteira e decimal
                        parts = clean_value.split('.')
                        integer_part = parts[0]
                        decimal_part = parts[1][:2] if len(parts) > 1 else "00"  # Max 2 decimais
                    else:
                        # Sem decimal, assumir valor inteiro
                        integer_part = clean_value
                        decimal_part = "00"
                    
                    # Garantir que decimal tenha 2 dígitos
                    if len(decimal_part) == 1:
                        decimal_part += "0"
                    elif len(decimal_part) == 0:
                        decimal_part = "00"
                    
                    # Converter para float para formatar
                    float_value = float(f"{integer_part}.{decimal_part}")
                    
                    # Formatar no padrão brasileiro
                    if float_value >= 1000:
                        # Valores altos: 1.500,39
                        formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        # Valores baixos: 87,58
                        formatted = f"{float_value:.2f}".replace('.', ',')
                    
                    return formatted
                    
                except (ValueError, TypeError) as e:
                    logging.warning(f"⚠️ AVERBAI: Erro ao formatar valor '{value_str}': {e}")
                    return str(value_str)  # Retornar original se houver erro
            
            # 🔍 LOG DEBUG: Campos importantes do AVERBAI
            logging.info(f"🔍 AVERBAI Debug - Id: {row.get('Id', 'N/A')}, IdTableComissao: '{codigo_tabela_direto}', CpfCliente: '{cpf_cliente}', NomeCliente: '{row.get('NomeCliente', 'N/A')}'")
            
            # Buscar dados do código no CSV para pegar órgão e taxa corretos
            orgao_final = orgao_averbai  # Default baseado no TipoProduto
            taxa_final = ""
            operacao_final = tipo_operacao_averbai
            
            if codigo_tabela_direto and codigo_tabela_direto.isdigit():
                # Procurar informações do código no CSV
                for key, details in TABELA_MAPPING.items():
                    if details.get('codigo_tabela', '') == codigo_tabela_direto:
                        # Usar dados oficiais do CSV
                        orgao_csv = details.get('orgao_storm', '')
                        taxa_csv = details.get('taxa_storm', '')
                        operacao_csv = details.get('operacao_storm', '')
                        
                        if orgao_csv:
                            orgao_final = orgao_csv
                        if taxa_csv:
                            taxa_final = taxa_csv
                        if operacao_csv:
                            operacao_final = operacao_csv
                            
                        logging.info(f"✅ AVERBAI código {codigo_tabela_direto}: {orgao_final} | {operacao_final} | {taxa_final} | CPF: {cpf_cliente}")
                        break
                else:
                    # Código não encontrado no CSV - usar detecção automática
                    logging.warning(f"⚠️ AVERBAI código {codigo_tabela_direto}: Não encontrado no CSV, usando detecção automática")
            else:
                # Sem código - usar nome da tabela como antes
                codigo_tabela_direto = tabela_normalizada
                logging.warning(f"⚠️ AVERBAI sem IdTableComissao, usando nome da tabela: '{tabela_normalizada}'")
            
            # 💰 Formatar valores no padrão brasileiro
            valor_operacao_br = format_brazilian_currency(row.get('ValorOperacao', ''))
            valor_liberado_br = format_brazilian_currency(row.get('ValorLiquido', ''))
            valor_parcela_br = format_brazilian_currency(row.get('ValorParcela', ''))
            
            # 📊 Organizar taxa conforme tabela (garantir formato percentual)
            taxa_formatada = taxa_final
            if taxa_formatada and '%' not in taxa_formatada:
                # Se não tem %, adicionar
                try:
                    # Tentar converter para float e formatar
                    taxa_num = float(taxa_formatada.replace(',', '.'))
                    taxa_formatada = f"{taxa_num:.2f}%".replace('.', ',')
                except:
                    taxa_formatada = f"{taxa_formatada}%"
            
            logging.info(f"💰 AVERBAI Proposta {row.get('Id', 'N/A')}: Valores formatados - OPERAÇÃO: {valor_operacao_br}, LIBERADO: {valor_liberado_br}, PARCELA: {valor_parcela_br}, TAXA: {taxa_formatada}")
            
            normalized_row = {
                "PROPOSTA": str(row.get('Id', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data', '')).strip(),
                "BANCO": "AVERBAI",
                "ORGAO": orgao_final,  # Órgão correto do CSV ou detectado
                "TIPO_OPERACAO": operacao_final,  # Operação correta do CSV ou detectada
                "NUMERO_PARCELAS": str(row.get('Prazo', '')).strip(),
                "VALOR_OPERACAO": valor_operacao_br,  # 💰 FORMATO BRASILEIRO
                "VALOR_LIBERADO": valor_liberado_br,  # 💰 FORMATO BRASILEIRO
                "USUARIO_BANCO": str(row.get('LoginConsultor', '')).strip(),
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('DataFinalização', '')).strip() if 'DataFinalização' in df.columns else "",
                "CPF": cpf_cliente,  # CPF já extraído e validado
                "NOME": str(row.get('NomeCliente', '')).strip(),
                "DATA_NASCIMENTO": str(row.get('DataNascimento', '')).strip() if 'DataNascimento' in df.columns else "",
                "VALOR_PARCELAS": valor_parcela_br,  # 💰 FORMATO BRASILEIRO
                "CODIGO_TABELA": codigo_tabela_direto,  # 🎯 CÓDIGO DIRETO DO ARQUIVO!
                "TAXA": taxa_formatada,  # 📊 TAXA ORGANIZADA CONFORME TABELA
                "OBSERVACOES": str(row.get('Observações', row.get('Observacoes', row.get('Obs', '')))).strip()
            }
            
        elif bank_type == "DIGIO":
            # Mapeamento BANCO DIGIO S.A. - Estrutura com muitas colunas "Unnamed"
            # Baseado em map_relat_atualizados.txt - 104 colunas no total
            proposta = str(row.get('Unnamed: 3', '')).strip()
            tipo_operacao = str(row.get('Unnamed: 4', '')).strip()
            data_cadastro = str(row.get('Unnamed: 8', '')).strip()
            situacao = str(row.get('Unnamed: 9', '')).strip()
            data_lancamento = str(row.get('Unnamed: 13', '')).strip()
            nome_orgao_raw = str(row.get('Unnamed: 25', '')).strip()
            usuario_digitador = str(row.get('Unnamed: 29', '')).strip()
            cpf_cliente = str(row.get('Unnamed: 31', '')).strip()
            nome_cliente = str(row.get('Unnamed: 32', '')).strip()
            data_nascimento = str(row.get('Unnamed: 33', '')).strip()
            qtd_parcelas = str(row.get('Unnamed: 48', '')).strip()
            vlr_parcela = str(row.get('Unnamed: 49', '')).strip()  # Valor da parcela
            vlr_financiado = str(row.get('Unnamed: 50', '')).strip()
            nome_convenio = str(row.get('Unnamed: 54', '')).strip()
            vlr_lib1 = str(row.get('Unnamed: 59', '')).strip()
            
            # DIGIO: Usar NOME_CONVENIO (Unnamed: 54) como tabela - baseado em map_relat_atualizados.txt
            # Exemplos: "PORT+REFIN VINCULADO-1-96X-1,39 A 1,85-T", "REFIN DA PORT VINCULADO-96X-1,75 A 1,85-"
            nome_tabela_completo = nome_convenio.strip() if nome_convenio else ""
            
            # Se nome_convenio estiver vazio, tentar COD_CONVENIO (Unnamed: 53)
            if not nome_tabela_completo:
                cod_convenio = str(row.get('Unnamed: 53', '')).strip()
                nome_tabela_completo = cod_convenio
            
            # Log para debug do DIGIO
            logging.info(f"🔍 DIGIO campos principais: Proposta={proposta}, TipoOp='{tipo_operacao}', Orgao='{nome_orgao_raw}', Convenio='{nome_convenio}', QtdParc={qtd_parcelas}")
            logging.info(f"🔍 DIGIO tabela final: '{nome_tabela_completo}'")
            
            # MELHORADO: Detecção inteligente de ORGAO DIGIO baseada no map_relat_atualizados.txt
            def detect_digio_organ(nome_orgao, nome_empregador="", cod_empregador=""):
                """Detecta órgão do DIGIO baseado nos campos NOME_ORGAO, NOME_EMPREGADOR"""
                orgao_upper = nome_orgao.upper() if nome_orgao else ""
                empregador_upper = nome_empregador.upper() if nome_empregador else ""
                
                # Log para debug
                logging.info(f"🏛️ DIGIO detectando órgão: NOME_ORGAO='{orgao_upper}' | NOME_EMPREGADOR='{empregador_upper}' | COD_EMP='{cod_empregador}'")
                
                # Baseado nos exemplos do mapeamento:
                # NOME_ORGAO: INSS, PREFEITURA DE B, PREFEITURA DE L, PREFEITURA DE S
                # NOME_EMPREGADOR: INSS, PREF BAURU SP, PREF LINS - SP, PREF SERTAOZINH
                
                # Prioridade 1: INSS (mais comum)
                if 'INSS' in orgao_upper or 'INSS' in empregador_upper:
                    return 'INSS'
                
                # Prioridade 2: Prefeituras específicas (usar formato do empregador que é mais específico)
                if 'BAURU' in empregador_upper:
                    return 'PREF BAURU SP'
                elif 'LINS' in empregador_upper:
                    return 'PREF LINS - SP'
                elif 'SERTAOZINHO' in empregador_upper or 'SERTAOZINH' in empregador_upper:
                    return 'PREF SERTAOZINHO - SP'
                elif 'PREFEITURA DE B' in orgao_upper:
                    return 'PREF BAURU SP'  # B = BAURU
                elif 'PREFEITURA DE L' in orgao_upper:
                    return 'PREF LINS - SP'  # L = LINS
                elif 'PREFEITURA DE S' in orgao_upper:
                    return 'PREF SERTAOZINHO - SP'  # S = SERTAOZINHO
                elif 'PREF' in empregador_upper or 'PREFEITURA' in orgao_upper:
                    # Prefeitura genérica - usar formato do empregador
                    return empregador_upper if empregador_upper else orgao_upper.replace('PREFEITURA', 'PREF').strip()
                
                # Default: INSS
                return 'INSS'
            
            nome_orgao = detect_digio_organ(nome_orgao_raw, row.get('NOME_EMPREGADOR', ''), row.get('COD_EMPREGADOR', ''))
            
            # MELHORADO: Detecção inteligente de tipo de operação DIGIO
            def detect_digio_operation(tipo_op, tabela_nome=""):
                """Detecta tipo de operação do DIGIO de forma inteligente"""
                tipo_upper = tipo_op.upper() if tipo_op else ""
                tabela_upper = tabela_nome.upper() if tabela_nome else ""
                
                logging.info(f"🔧 DIGIO detectando operação: tipo='{tipo_upper}' | tabela='{tabela_upper[:50]}...'")
                
                # Analisar tanto o tipo quanto o nome da tabela
                combined_text = f"{tipo_upper} {tabela_upper}"
                
                # Prioridade 1: Refinanciamento + Portabilidade (mais específico primeiro)
                if any(x in combined_text for x in ['REFIN DA PORT', 'REFINANCIAMENTO DA PORTABILIDADE', 'REFIN PORT', 'REFIN PORTABILIDADE']):
                    return "Refinanciamento da Portabilidade"
                
                # Prioridade 2: Portabilidade + Refin (diferente do anterior)
                elif any(x in combined_text for x in ['PORT+REFIN', 'PAGTO SALDO PORTAB']):
                    return "Portabilidade"
                
                # Prioridade 2.5: Portabilidade simples
                elif 'PORTABILIDADE' in combined_text and 'REFIN' not in combined_text:
                    return "Portabilidade"
                
                # Prioridade 3: Refinanciamento simples
                elif 'REFIN' in combined_text and 'PORT' not in combined_text:
                    return "Refinanciamento"
                
                # Prioridade 4: Margem Livre (mais comum)
                else:
                    return "Margem Livre (Novo)"
            
            tipo_operacao_norm = detect_digio_operation(tipo_operacao, nome_tabela_completo)
                
            normalized_row = {
                "PROPOSTA": proposta,
                "DATA_CADASTRO": data_cadastro,
                "BANCO": "BANCO DIGIO S.A.",  # Nome completo como no relat_orgaos.csv
                "ORGAO": nome_orgao,
                "TIPO_OPERACAO": tipo_operacao_norm,
                "NUMERO_PARCELAS": qtd_parcelas,
                "VALOR_OPERACAO": vlr_financiado,
                "VALOR_LIBERADO": vlr_lib1 if vlr_lib1 else vlr_financiado,
                "USUARIO_BANCO": usuario_digitador,
                "SITUACAO": situacao,
                "DATA_PAGAMENTO": data_lancamento,
                "CPF": cpf_cliente,
                "NOME": nome_cliente,
                "DATA_NASCIMENTO": data_nascimento,
                "VALOR_PARCELAS": vlr_parcela,
                "CODIGO_TABELA": nome_tabela_completo,  # NOME_CONVENIO do DIGIO (campo real)
                "TAXA": "",  # Será preenchida pelo mapeamento
                "OBSERVACOES": str(row.get('Unnamed: 11', row.get('Observações', ''))).strip()  # NOME_ATIVIDADE como observação
            }
            
            # NOVO: Aplicar mapeamento automático DIGIO (similar ao AVERBAI) 
            # para corrigir códigos de tabela e taxas erradas
            logging.info(f"🔍 DIGIO aplicando mapeamento automático: BANCO={normalized_row['BANCO']}, ORGAO={normalized_row['ORGAO']}, OPERACAO={normalized_row['TIPO_OPERACAO']}")
            
            digio_mapping = apply_mapping(
                bank_name=normalized_row['BANCO'],
                organ=normalized_row['ORGAO'], 
                operation_type=normalized_row['TIPO_OPERACAO'],
                tabela=nome_tabela_completo
            )
            
            # Se encontrou mapeamento, substituir dados incorretos do arquivo por dados corretos do CSV
            if digio_mapping:
                original_codigo = normalized_row.get('CODIGO_TABELA', '')
                original_taxa = normalized_row.get('TAXA', '')
                
                # Substituir código da tabela
                if digio_mapping.get('codigo_tabela'):
                    normalized_row['CODIGO_TABELA'] = digio_mapping['codigo_tabela']
                    
                # Substituir taxa 
                if digio_mapping.get('taxa_storm'):
                    normalized_row['TAXA'] = digio_mapping['taxa_storm']
                
                # Garantir órgão correto
                if digio_mapping.get('orgao_storm'):
                    normalized_row['ORGAO'] = digio_mapping['orgao_storm']
                
                # Garantir operação correta
                if digio_mapping.get('operacao_storm'):
                    normalized_row['TIPO_OPERACAO'] = digio_mapping['operacao_storm']
                
                logging.info(f"✅ DIGIO mapeamento aplicado: Código='{normalized_row['CODIGO_TABELA']}' | Taxa='{normalized_row['TAXA']}' | Órgão='{normalized_row['ORGAO']}' | Operação='{normalized_row['TIPO_OPERACAO']}'")
                
                if original_codigo != normalized_row['CODIGO_TABELA']:
                    logging.warning(f"🔄 DIGIO código corrigido: '{original_codigo}' → '{normalized_row['CODIGO_TABELA']}'")
                    
            else:
                logging.warning(f"⚠️ DIGIO: Nenhum mapeamento encontrado para {normalized_row['ORGAO']} + {normalized_row['TIPO_OPERACAO']}")
            
        elif bank_type == "PRATA":
            # Mapeamento baseado na estrutura real do Prata
            # PRATA usa prazo em MESES, precisa dividir por 12
            prazo = str(row.get('Prazo proposta', '')).strip()
            numero_parcelas = ""
            if prazo and prazo.isdigit():
                numero_parcelas = str(int(prazo) // 12) if int(prazo) >= 12 else prazo
            
            # PRATA: Pegar campo Usuario e limpar (remover nome entre parênteses)
            usuario_prata = str(row.get('Nome do Vendedor', '')).strip()
            if not usuario_prata:
                usuario_prata = str(row.get('Usuário (acesso login)', '')).strip()
            
            # Limpar: remover tudo após o email (ex: "lprodrigues@q-faz.com (LARIANA PITON RODRIGUES)" → "lprodrigues@q-faz.com")
            if '(' in usuario_prata:
                usuario_prata = usuario_prata.split('(')[0].strip()
            
            normalized_row = {
                "PROPOSTA": str(row.get('Número da Proposta', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data da operação', '')).strip(),
                "BANCO": "BANCO PRATA DIGITAL",
                "ORGAO": "FGTS",
                "TIPO_OPERACAO": "Margem Livre (Novo)",
                "NUMERO_PARCELAS": numero_parcelas,
                "VALOR_OPERACAO": str(row.get('Valor da Emissão', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Desembolso', '')).strip(),
                "USUARIO_BANCO": usuario_prata,
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Data do Desembolso', '')).strip(),
                "CPF": str(row.get('CPF do Cliente', '')).strip(),
                "NOME": str(row.get('Nome do Cliente', '')).strip(),
                "DATA_NASCIMENTO": "",
                "VALOR_PARCELAS": "",  # PRATA não fornece valor da parcela
                "CODIGO_TABELA": str(row.get('Tabela', '')).strip(),  # Nome da tabela do banco
                "TAXA": "",  # Vazio para buscar no relat_orgaos.csv
                "OBSERVACOES": str(row.get('Observações', row.get('Observacoes', row.get('Obs', '')))).strip()
            }
            
        elif bank_type == "VCTEX":
            # Mapeamento BANCO VCTEX - Estrutura REAL dos arquivos
            # VCTEX usa prazo em MESES, precisa dividir por 12
            prazo_vctex = str(row.get('Prazo proposta', '')).strip()
            numero_parcelas_vctex = ""
            if prazo_vctex and prazo_vctex.isdigit():
                numero_parcelas_vctex = str(int(prazo_vctex) // 12) if int(prazo_vctex) >= 12 else prazo_vctex
            
            # Função para busca flexível de datas VCTEX - CORRIGIDA
            def get_vctex_date_field(row, date_type='cadastro'):
                """Busca flexível por campo de data no VCTEX - prioridade corrigida"""
                
                logging.debug(f"🔍 VCTEX buscando campo de data tipo '{date_type}' nas colunas disponíveis")
                
                if date_type == 'cadastro':
                    # Prioridade ALTA para campos específicos de criação/operação
                    cadastro_high_priority = [
                        'Data da operação', 'Data da operacao', 'Data operacao', 'Data Operacao',
                        'Data de criacao', 'Data de criação', 'Data criacao', 'Data criação',
                        'Data contrato', 'Data Contrato', 'Data do contrato', 'Data do Contrato',
                        'Data inclusao', 'Data inclusão', 'Data de inclusao', 'Data de inclusão'
                    ]
                    
                    # Prioridade MÉDIA para campos de cadastro genéricos  
                    cadastro_medium_priority = [
                        'Data cadastro', 'Data Cadastro', 'Data de cadastro', 'Data de Cadastro',
                        'Data assinatura', 'Data Assinatura', 'DT_OPERACAO', 'DT_CADASTRO', 'DT_CRIACAO'
                    ]
                    
                    # Buscar por prioridade
                    for field_list in [cadastro_high_priority, cadastro_medium_priority]:
                        for field in field_list:
                            if field in row and str(row.get(field, '')).strip() and str(row.get(field, '')).strip() != 'nan':
                                found_date = str(row.get(field, '')).strip()
                                logging.info(f"✅ VCTEX DATA_CADASTRO encontrada em '{field}': {found_date}")
                                return found_date
                            
                elif date_type == 'pagamento':
                    # Prioridade ALTA para campos específicos de pagamento/finalização
                    pagamento_high_priority = [
                        'Data pagamento Operação', 'Data pagamento Operacao', 'Data pagamento',
                        'Data de pagamento', 'Data Pagamento', 'Data liquidacao', 'Data liquidação',
                        'Data liberacao', 'Data liberação', 'Data credito', 'Data crédito'
                    ]
                    
                    # Prioridade MÉDIA para campos de finalização/vencimento
                    pagamento_medium_priority = [
                        'Data finalizacao', 'Data finalização', 'Data vencimento', 'Data Vencimento',
                        'Data de vencimento', 'Data de Vencimento', 'DT_PAGAMENTO', 'DT_FINALIZACAO', 'DT_LIQUIDACAO'
                    ]
                    
                    # Buscar por prioridade
                    for field_list in [pagamento_high_priority, pagamento_medium_priority]:
                        for field in field_list:
                            if field in row and str(row.get(field, '')).strip() and str(row.get(field, '')).strip() != 'nan':
                                found_date = str(row.get(field, '')).strip()
                                logging.info(f"✅ VCTEX DATA_PAGAMENTO encontrada em '{field}': {found_date}")
                                return found_date
                
                # 🚫 EVITAR campos genéricos que causam confusão entre cadastro e pagamento
                # Vamos ser mais restritivos para evitar pegar campos errados
                logging.warning(f"⚠️ VCTEX: Nenhum campo específico de {date_type} encontrado!")
                
                # Log das colunas disponíveis para debug
                available_columns = [col for col in row.index if 'data' in col.lower() or 'date' in col.lower()]
                if available_columns:
                    logging.info(f"🔍 VCTEX: Colunas relacionadas a datas disponíveis: {available_columns}")
                
                return ""  # Retornar vazio ao invés de tentar campo genérico
            
            # Função para validar e normalizar formato de data - MELHORADA
            def validate_and_normalize_date(date_str, field_name=""):
                """Valida, normaliza e detecta problemas em datas do VCTEX"""
                if not date_str or date_str.strip() == "" or str(date_str).strip().lower() in ['nan', 'none', 'null']:
                    logging.debug(f"🔍 VCTEX {field_name}: Campo vazio ou inválido")
                    return ""
                
                date_clean = str(date_str).strip()
                
                # Verificar padrões de data válidos com regex mais rigoroso
                import re
                from datetime import datetime
                
                # Padrões aceitos com validação mais rigorosa
                date_patterns = [
                    (r'^\d{1,2}/\d{1,2}/\d{4}$', '%d/%m/%Y'),     # DD/MM/YYYY
                    (r'^\d{1,2}/\d{1,2}/\d{2}$', '%d/%m/%y'),     # DD/MM/YY  
                    (r'^\d{1,2}-\d{1,2}-\d{4}$', '%d-%m-%Y'),     # DD-MM-YYYY
                    (r'^\d{1,2}-\d{1,2}-\d{2}$', '%d-%m-%y'),     # DD-MM-YY
                    (r'^\d{4}-\d{1,2}-\d{1,2}$', '%Y-%m-%d'),     # YYYY-MM-DD
                    (r'^\d{1,2}\.\d{1,2}\.\d{4}$', '%d.%m.%Y'),   # DD.MM.YYYY
                    (r'^\d{4}/\d{1,2}/\d{1,2}$', '%Y/%m/%d')      # YYYY/MM/DD
                ]
                
                # Tentar validar com cada padrão
                for pattern, date_format in date_patterns:
                    if re.match(pattern, date_clean):
                        try:
                            # Tentar fazer o parse da data para validar se é real
                            parsed_date = datetime.strptime(date_clean, date_format)
                            
                            # Verificar se a data faz sentido (não muito antiga nem futura)
                            current_year = datetime.now().year
                            if parsed_date.year < 1990 or parsed_date.year > current_year + 1:
                                logging.warning(f"⚠️ VCTEX {field_name}: Ano suspeito ({parsed_date.year}) na data '{date_clean}'")
                            
                            logging.info(f"✅ VCTEX {field_name}: Data válida '{date_clean}' (formato: {date_format})")
                            return date_clean
                            
                        except ValueError as ve:
                            logging.warning(f"⚠️ VCTEX {field_name}: Data inválida '{date_clean}' - erro: {ve}")
                            continue
                
                # 🔧 MODO FLEXÍVEL: Se validação rigorosa falhou, aceitar formatos razoáveis
                logging.warning(f"⚠️ VCTEX {field_name}: Formato não padrão: '{date_clean}' - aplicando modo flexível")
                
                # 🔧 CORREÇÃO ESPECÍFICA: Tratar timestamps (DD/MM/YYYY HH:MM:SS)
                if len(date_clean) > 10:  # Possível timestamp/datetime
                    logging.info(f"🔧 VCTEX {field_name}: Detectado timestamp: '{date_clean}'")
                    
                    # Padrão brasileiro: DD/MM/YYYY HH:MM:SS
                    timestamp_br_match = re.match(r'^(\d{1,2}/\d{1,2}/\d{4})\s+\d{1,2}:\d{2}', date_clean)
                    if timestamp_br_match:
                        date_only = timestamp_br_match.group(1)
                        logging.info(f"✅ VCTEX {field_name}: Extraído data brasileira: '{date_only}'")
                        return date_only
                    
                    # Padrão ISO: YYYY-MM-DD HH:MM:SS
                    timestamp_iso_match = re.match(r'^(\d{4}-\d{2}-\d{2})\s+\d{1,2}:\d{2}', date_clean) 
                    if timestamp_iso_match:
                        date_only = timestamp_iso_match.group(1)
                        logging.info(f"✅ VCTEX {field_name}: Extraído data ISO: '{date_only}'")
                        return date_only
                    
                    # Tentar extrair primeiros 10 caracteres se parecer data
                    if re.match(r'^\d{4}-\d{2}-\d{2}', date_clean):
                        date_part = date_clean[:10]
                        logging.info(f"🔧 VCTEX {field_name}: Extraindo primeiros 10 chars: '{date_part}'")
                        return date_part
                
                # 🆘 MODO EMERGÊNCIA: Se tem qualquer padrão de data, ACEITAR!
                # Formatos que podem existir no mundo real
                flexible_patterns = [
                    r'\d{1,4}[/.-]\d{1,2}[/.-]\d{1,4}',  # Qualquer separador com números
                    r'\d{8}',  # DDMMYYYY ou YYYYMMDD
                    r'\d{6}',  # DDMMYY ou YYMMDD
                ]
                
                for pattern in flexible_patterns:
                    if re.search(pattern, date_clean):
                        logging.warning(f"⚠️ VCTEX {field_name}: ACEITANDO formato flexível: '{date_clean}'")
                        return date_clean  # Aceitar como está
                
                # Se realmente não parece data de jeito nenhum
                logging.error(f"❌ VCTEX {field_name}: Realmente não parece data: '{date_clean}' - retornando vazio")
                return ""
            
            # Pegar campos brutos
            convenio_raw = str(row.get('Convênio', row.get('Nome da entidade consignataria', ''))).strip().upper()
            tabela_raw = str(row.get('Tabela', row.get('Nome tabela juros', ''))).strip()
            taxa_raw = str(row.get('Taxa Juros Aplicada', row.get('Taxa de juros', ''))).strip()
            
            # 🔧 CORREÇÃO VCTEX: Garantir formato correto da tabela para mapeamento
            if tabela_raw and not tabela_raw.upper().startswith('TABELA'):
                # Se não começa com "Tabela", adicionar prefixo para match com relat_orgaos.csv
                tabela_formatted = f"Tabela {tabela_raw}"
                logging.info(f"🔄 VCTEX: Formatando tabela '{tabela_raw}' → '{tabela_formatted}' para mapeamento")
                tabela_raw = tabela_formatted
            
            # Normalizar ORGAO usando CONVENIO e TABELA como indicadores
            orgao_vctex = ""
            
            # Primeiro, tentar pelo campo Convênio
            if 'FGTS' in convenio_raw or 'FUNDO' in convenio_raw:
                orgao_vctex = 'FGTS'
            elif 'INSS' in convenio_raw or 'PREVID' in convenio_raw:
                orgao_vctex = 'INSS'
            # Se Convênio não ajudou, usar a TABELA como indicador
            elif 'INSS' in tabela_raw.upper():
                orgao_vctex = 'INSS'
            elif 'FGTS' in tabela_raw.upper():
                orgao_vctex = 'FGTS'
            # Detectar por nome de tabela típicas
            elif any(x in tabela_raw.upper() for x in ['VAMO', 'EXPONENCIAL', 'RELAX', 'VCT', 'EXP']):
                # Se tem tabela típica de FGTS e não mencionou INSS
                orgao_vctex = 'FGTS'
            else:
                # Default para INSS se não conseguiu determinar
                orgao_vctex = 'INSS'
            
            # Garantir que TAXA tenha valor, mesmo que seja 0,00%
            if not taxa_raw or taxa_raw == 'nan':
                taxa_raw = '0,00%'
            elif '%' not in taxa_raw:
                taxa_raw = taxa_raw + '%' if taxa_raw else '0,00%'
            
            # 🔍 DEBUG: Log das colunas de data disponíveis
            date_columns = [col for col in row.index if any(word in col.lower() for word in ['data', 'date'])]
            logging.info(f"🔍 VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: Colunas de data disponíveis: {date_columns}")
            
            # Buscar datas usando função flexível
            data_cadastro_raw = get_vctex_date_field(row, 'cadastro')
            data_pagamento_raw = get_vctex_date_field(row, 'pagamento')
            
            # 🔍 DEBUG: Log das datas brutas encontradas
            logging.info(f"🔍 VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: Datas brutas - CADASTRO_RAW: '{data_cadastro_raw}' | PAGAMENTO_RAW: '{data_pagamento_raw}'")
            
            # Validar e normalizar datas
            data_cadastro_vctex = validate_and_normalize_date(data_cadastro_raw, "DATA_CADASTRO")
            data_pagamento_vctex = validate_and_normalize_date(data_pagamento_raw, "DATA_PAGAMENTO")
            
            # 🔍 DEBUG: Log das datas processadas
            logging.info(f"🔍 VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: Datas processadas - CADASTRO_FINAL: '{data_cadastro_vctex}' | PAGAMENTO_FINAL: '{data_pagamento_vctex}'")
            
            # 🔧 CORREÇÃO ROBUSTA: Verificar e corrigir datas trocadas do VCTEX
            if data_cadastro_vctex and data_pagamento_vctex:
                try:
                    from datetime import datetime
                    cadastro_dt = None
                    pagamento_dt = None
                    
                    # Tentar formatos comuns de data brasileira e internacional
                    date_formats = [
                        '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d.%m.%Y',  # Formatos básicos
                        '%d/%m/%y', '%d-%m-%y', '%y-%m-%d', '%d.%m.%y',  # Ano de 2 dígitos
                        '%Y/%m/%d', '%Y.%m.%d'  # Formatos internacionais
                    ]
                    
                    # Tentar converter CADASTRO
                    for fmt in date_formats:
                        try:
                            cadastro_dt = datetime.strptime(data_cadastro_vctex, fmt)
                            break
                        except:
                            continue
                    
                    # Tentar converter PAGAMENTO  
                    for fmt in date_formats:
                        try:
                            pagamento_dt = datetime.strptime(data_pagamento_vctex, fmt)
                            break
                        except:
                            continue
                    
                    # ✅ VALIDAÇÃO: Se conseguiu converter ambas, verificar ordem lógica
                    if cadastro_dt and pagamento_dt:
                        # Calcular diferença em dias
                        diferenca_dias = (pagamento_dt - cadastro_dt).days
                        
                        if diferenca_dias < 0:
                            # Pagamento anterior ao cadastro = ERRO LÓGICO!
                            logging.error(f"🔄 VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: DATAS LOGICAMENTE INCORRETAS!")
                            logging.error(f"   ❌ CADASTRO: {data_cadastro_vctex} ({cadastro_dt.strftime('%d/%m/%Y')})")
                            logging.error(f"   ❌ PAGAMENTO: {data_pagamento_vctex} ({pagamento_dt.strftime('%d/%m/%Y')})")
                            logging.error(f"   ❌ Diferença: {diferenca_dias} dias (IMPOSSÍVEL!)")
                            
                            # CORREÇÃO AUTOMÁTICA: Trocar as datas
                            data_cadastro_vctex, data_pagamento_vctex = data_pagamento_vctex, data_cadastro_vctex
                            logging.warning(f"   🔧 CORRIGIDO - CADASTRO: {data_cadastro_vctex} | PAGAMENTO: {data_pagamento_vctex}")
                            
                        elif diferenca_dias > 365:
                            # Muito tempo entre cadastro e pagamento = suspeito
                            logging.warning(f"⚠️ VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: Diferença suspeita de {diferenca_dias} dias entre cadastro e pagamento")
                        else:
                            # Datas em ordem lógica
                            logging.info(f"✅ VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: Datas em ordem correta ({diferenca_dias} dias)")
                    
                    else:
                        logging.warning(f"⚠️ VCTEX: Não foi possível validar formato das datas - CADASTRO: '{data_cadastro_vctex}' | PAGAMENTO: '{data_pagamento_vctex}'")
                        
                except Exception as e:
                    logging.error(f"❌ VCTEX: Erro ao validar datas: {e}")
            
            # 📊 LOG COMPLETO das datas VCTEX para debug
            logging.info(f"� VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: DATAS ORIGINAIS DO ARQUIVO")
            logging.info(f"   ✅ DATA_CADASTRO_FINAL: '{data_cadastro_vctex}'")
            logging.info(f"   ✅ DATA_PAGAMENTO_FINAL: '{data_pagamento_vctex}'")
            logging.info(f"   🏦 BANCO: VCTEX | ÓRGÃO: {orgao_vctex} | TAXA: {taxa_raw}")
            
            normalized_row = {
                "PROPOSTA": str(row.get('Número do Contrato', row.get('Identificacao da operacao', ''))).strip(),
                "DATA_CADASTRO": data_cadastro_vctex,
                "BANCO": "BANCO VCTEX",
                "ORGAO": orgao_vctex,
                "TIPO_OPERACAO": "Margem Livre (Novo)",  # VCTEX normalmente só tem esse tipo
                "NUMERO_PARCELAS": numero_parcelas_vctex,
                "VALOR_OPERACAO": str(row.get('Valor da operacao', str(row.get('Valor Liberado', '')))).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Liberado', '')).strip(),
                "USUARIO_BANCO": str(row.get('Usuário (acesso login)', row.get('CPF Usuario', ''))).strip(),
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": data_pagamento_vctex,
                "CPF": str(row.get('CPF', '')).strip(),
                "NOME": str(row.get('Nome do Cliente', row.get('Nome', ''))).strip(),
                "DATA_NASCIMENTO": str(row.get('Data de nascimento', '')).strip() if 'Data de nascimento' in df.columns else "",
                "VALOR_PARCELAS": str(row.get('Parcela', row.get('Valor parcela', ''))).strip(),
                "CODIGO_TABELA": tabela_raw,  # Nome COMPLETO da tabela (usado para buscar no dicionário)
                "TAXA": taxa_raw,  # Taxa do arquivo (mas será substituída pelo mapeamento se encontrar)
                "OBSERVACOES": str(row.get('Observação', row.get('Observações', row.get('Observacoes', row.get('Obs', ''))))).strip()  # Campo observações do VCTEX
            }
            
        elif bank_type == "DAYCOVAL":
            # 🔧 DAYCOVAL - Mapeamento Melhorado (não tem código direto como AVERBAI)
            # DAYCOVAL não tem campo direto com código da tabela, então usamos mapeamento tradicional
            # Unnamed: 0 = NR.PROP., Unnamed: 1 = Tp. Operação
            # Unnamed: 2 = CLIENTE, Unnamed: 3 = CPF/CNPJ
            # Unnamed: 12 = TX.AM (taxa), Unnamed: 23 = DESCRIÇÃO EMPREGADOR
            
            cpf_cliente = str(row.get('Unnamed: 3', '')).strip()
            taxa_arquivo = str(row.get('Unnamed: 12', '')).strip()
            
            # Detectar órgão e operação dos campos do arquivo
            tipo_op = str(row.get('Unnamed: 1', '')).strip().upper()
            orgao_descricao = str(row.get('Unnamed: 23', '')).strip().upper()  # DESCRIÇÃO EMPREGADOR
            
            # 🔍 LOG DEBUG: Campos importantes do DAYCOVAL  
            logging.info(f"🔍 DAYCOVAL Debug - Proposta: {row.get('Unnamed: 0', 'N/A')}, TipoOp: '{tipo_op}', Orgao: '{orgao_descricao}', CPF: '{cpf_cliente}', Taxa: '{taxa_arquivo}'")
            
            # 🔍 LOG DEBUG: Validação individual dos campos críticos
            proposta_debug = str(row.get('Unnamed: 0', '')).strip()
            nome_debug = str(row.get('Unnamed: 2', '')).strip()
            cpf_debug = str(row.get('Unnamed: 3', '')).strip()
            
            logging.info(f"🔍 DAYCOVAL Validação - Proposta: '{proposta_debug}' (len={len(proposta_debug)}), Nome: '{nome_debug}' (len={len(nome_debug)}), CPF: '{cpf_debug}' (len={len(cpf_debug)})")
            
            # Órgão baseado na descrição
            if 'INSS' in orgao_descricao:
                orgao_final = "INSS"
            elif 'SPPREV' in orgao_descricao:
                orgao_final = "SPPREV"  
            elif 'EDUC' in orgao_descricao or 'SEC EDU' in orgao_descricao:
                orgao_final = "EDUCACAO"
            else:
                orgao_final = "INSS"  # Default
                
            # Operação baseada no tipo
            if 'PORTABILIDADE' in tipo_op and 'REFIN' in tipo_op:
                operacao_final = "Refinanciamento da Portabilidade"
            elif 'PORTABILIDADE' in tipo_op:
                operacao_final = "Portabilidade + Refin"  # DAYCOVAL usa esse padrão
            elif 'REFIN' in tipo_op:
                operacao_final = "Refinanciamento"  
            elif 'NOVA' in tipo_op:
                operacao_final = "Margem Livre (Novo)"
            else:
                operacao_final = "Margem Livre (Novo)"
            
            # Extrair dados principais para validação
            proposta_daycoval = str(row.get('Unnamed: 0', '')).strip()
            nome_daycoval = str(row.get('Unnamed: 2', '')).strip()
            
            # 🔧 DAYCOVAL FIX: Se proposta vazia, tentar outros campos
            if not proposta_daycoval or proposta_daycoval in ['nan', 'None', '']:
                # Tentar campo alternativo ou gerar proposta sintética
                proposta_daycoval = f"DAYC_{row.name if hasattr(row, 'name') else 'AUTO'}"
                logging.warning(f"⚠️ DAYCOVAL: Proposta vazia, usando sintética: {proposta_daycoval}")
                
            # 🔧 DAYCOVAL FIX: Garantir que tem pelo menos CPF válido para identificação
            if not cpf_cliente or len(cpf_cliente) < 11:
                # Se CPF inválido, usar nome como identificador
                if nome_daycoval and len(nome_daycoval) > 3:
                    cpf_cliente = "00000000000"  # CPF sintético para permitir processamento
                    logging.warning(f"⚠️ DAYCOVAL: CPF inválido, usando nome como identificador: {nome_daycoval[:20]}")
                
            normalized_row = {
                "PROPOSTA": proposta_daycoval,
                "DATA_CADASTRO": str(row.get('Unnamed: 5', '')).strip(),
                "BANCO": "BANCO DAYCOVAL", 
                "ORGAO": orgao_final,  # Órgão detectado do arquivo
                "TIPO_OPERACAO": operacao_final,  # Operação detectada do arquivo
                "NUMERO_PARCELAS": str(row.get('Unnamed: 11', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Unnamed: 16', '')).strip(),  # VLR.OPER
                "VALOR_LIBERADO": str(row.get('Unnamed: 13', '')).strip(),  # VLR.LIQ
                "USUARIO_BANCO": "",  # Não disponível
                "SITUACAO": str(row.get('Unnamed: 27', '')).strip(),  # Situação_Atual_da_Proposta
                "DATA_PAGAMENTO": str(row.get('Unnamed: 6', '')).strip(),  # DT.BASE
                "CPF": cpf_cliente,  # CPF já extraído e validado
                "NOME": nome_daycoval,
                "DATA_NASCIMENTO": "",  # Não disponível
                "CODIGO_TABELA": "",  # Será preenchido pelo mapeamento
                "VALOR_PARCELAS": str(row.get('Unnamed: 18', '')).strip(),  # VLR.PARC
                "TAXA": taxa_arquivo,  # Taxa do arquivo, será substituída pelo mapeamento
                "OBSERVACOES": str(row.get('Unnamed: 29', '')).strip()  # Motivo de reprovação
            }
            
        elif bank_type == "SANTANDER":
            # 🏦 MAPEAMENTO BANCO SANTANDER - Baseado no map_relat_atualizados.txt
            # Campos reais: COD, COD. BANCO, CPF, CLIENTE, CONVENIO, PRODUTO, QTDE PARCELAS, VALOR BRUTO, VALOR LIQUIDO, etc.
            
            # Mapear campos reais do arquivo SANTANDER
            proposta_santander = str(row.get('COD. BANCO', row.get('COD', row.get('PROPOSTA', '')))).strip()
            cliente_santander = str(row.get('CLIENTE', row.get('NOME', ''))).strip()
            cpf_santander = str(row.get('CPF', '')).strip()
            convenio_santander = str(row.get('CONVENIO', '')).strip()
            produto_santander = str(row.get('PRODUTO', '')).strip()
            parcelas_santander = str(row.get('QTDE PARCELAS', row.get('NUMERO PARCELAS', '96'))).strip()
            valor_bruto = str(row.get('VALOR BRUTO', row.get('VALOR', row.get('VALOR OPERACAO', '0')))).strip()
            valor_liquido = str(row.get('VALOR LIQUIDO', row.get('VALOR BRUTO', '0'))).strip()
            valor_parcela = str(row.get('VALOR PARCELA', row.get('VALOR PARCELAS', '0'))).strip()
            data_cadastro = str(row.get('DATA', row.get('DATA CADASTRO', ''))).strip()
            status_santander = str(row.get('STATUS', row.get('SITUACAO', 'AGUARDANDO'))).strip()
            data_averbacao = str(row.get('DATA AVERBACAO', row.get('DATA DE PAGAMENTO', ''))).strip()
            cod_digitador = str(row.get('COD DIGITADOR NO BANCO', row.get('USUARIO BANCO', ''))).strip()
            
            # Extrair código tabela do PRODUTO (formato: "21387 - 810021387 - 1 OFERTA NOVO COM SEGURO")
            codigo_tabela_santander = ""
            if produto_santander:
                parts = produto_santander.split(' - ')
                if len(parts) >= 2 and parts[1].strip().isdigit():
                    codigo_tabela_santander = parts[1].strip()
                else:
                    # Buscar primeiro número longo no produto
                    import re
                    numbers = re.findall(r'\d{6,}', produto_santander)
                    if numbers:
                        codigo_tabela_santander = numbers[0]
            
            # Determinar órgão baseado no convênio
            if 'PREF' in convenio_santander.upper() or 'AGUDOS' in convenio_santander.upper():
                orgao_santander = 'PREF. DE AGUDOS - SP'
            elif 'RANCHARIA' in convenio_santander.upper():
                orgao_santander = 'PREF. DE RANCHARIA - SP'
            else:
                orgao_santander = 'INSS'
            
            # Determinar tipo de operação baseado no produto
            if 'REFIN' in produto_santander.upper():
                operacao_santander = 'REFINANCIAMENTO'
            elif 'NOVO' in produto_santander.upper():
                operacao_santander = 'MARGEM LIVRE (NOVO)'
            elif 'PORTABILIDADE' in produto_santander.upper():
                operacao_santander = 'PORTABILIDADE'
            else:
                operacao_santander = 'MARGEM LIVRE (NOVO)'
            
            # 🔧 FIX: Normalização de status SANTANDER (AGUARDANDO/PAGO/CANCELADO)
            status_santander = str(row.get('SITUACAO', '')).strip().upper()
            
            # Normalizar status para padrão Storm
            if status_santander in ['PAGO', 'AVERBADO', 'AVERBADA', 'LIBERADO', 'DESEMBOLSADO', 'APROVADO']:
                status_santander = 'PAGO'
            elif status_santander in ['CANCELADO', 'REPROVADO', 'REJEITADO', 'NEGADO', 'CANCELADA']:
                status_santander = 'CANCELADO'
            elif status_santander in ['AGUARDANDO', 'EM ANALISE', 'EM ANÁLISE', 'PENDENTE', 'ABERTO', 'PROCESSANDO']:
                status_santander = 'AGUARDANDO'
            else:
                # Manter original se não conseguir mapear
                logging.warning(f"⚠️ SANTANDER: Status não reconhecido '{status_santander}', mantendo original")
                status_santander = str(row.get('SITUACAO', 'AGUARDANDO')).strip()
            
            logging.info(f"📋 SANTANDER: Proposta {row.get('PROPOSTA')} - Status: {status_santander}, ADE: {ade_santander}, CPF Digitador: {cpf_digitador_limpo}")
            # Problemas resolvidos:
            # 1. ADE errada (era do COD.BANCO, agora correto)
            # 2. Código tabela com nome junto (extração limpa)
            # 3. Usuário digitador com números extras (CPF padronizado)
            # 4. Status normalizado como AVERBAI/VCTEX
            # 5. Valores formatados corretamente
            # 6. Propostas SEGURO (11111111) removidas
            
            # 🚫 FILTRO SANTANDER: Remover propostas SEGURO (mais robusto)
            codigo_tabela_check = str(row.get('CODIGO TABELA', row.get('PRODUTO', ''))).strip()
            produto_check = str(row.get('PRODUTO', '')).upper()
            tipo_operacao_check = str(row.get('TIPO DE OPERACAO', '')).upper()
            
            # Verificar múltiplos critérios para filtrar SEGURO
            is_seguro = (
                '11111111' in codigo_tabela_check or 
                'SEGURO' in produto_check or
                'SEGURO' in tipo_operacao_check or
                'TODOS OS CONVENIOS' in produto_check
            )
            
            if is_seguro:
                logging.info(f"🚫 SANTANDER FILTRO: Removendo proposta SEGURO - Código: {codigo_tabela_check}, Produto: {produto_check[:50]}")
                return None  # Retornar None para indicar que deve ser pulado
            
            def extract_santander_codigo_tabela(produto_str):
                """Extrai código tabela limpo do Santander (ex: '810021387' de '21387 - 810021387 - 1 OFERTA NOVO COM SEGURO')"""
                if not produto_str:
                    return ""
                
                produto_str = str(produto_str).strip()
                
                # Padrão: "21387 - 810021387 - 1 OFERTA NOVO COM SEGURO"
                # Queremos extrair o código do meio (810021387)
                parts = produto_str.split(' - ')
                if len(parts) >= 2:
                    # Segundo elemento é o código que queremos
                    codigo = parts[1].strip()
                    # Verificar se é numérico
                    if codigo.isdigit():
                        return codigo
                
                # Se não conseguir extrair, usar o primeiro número encontrado
                import re
                numbers = re.findall(r'\d+', produto_str)
                if numbers:
                    # Pegar o maior número (provavelmente o código)
                    return max(numbers, key=len)
                
                return produto_str
            
            def extract_cpf_from_user(user_field):
                """Extrai CPF do campo usuário que pode ter números extras"""
                if not user_field:
                    return ""
                
                user_str = str(user_field).strip()
                
                # Procurar padrão de CPF (11 dígitos)
                import re
                cpf_match = re.search(r'\d{11}', user_str)
                if cpf_match:
                    return cpf_match.group()
                
                # Se não encontrar CPF completo, retornar apenas números
                numbers = re.sub(r'\D', '', user_str)
                return numbers if len(numbers) >= 11 else user_str
            
            # Detecção de órgão melhorada
            convenio = str(row.get('CONVENIO', '')).strip().upper()
            cod_banco = str(row.get('COD. BANCO', '')).strip().upper()
            
            # Usar múltiplas fontes para detectar órgão
            orgao = 'INSS'  # Default
            if 'INSS' in convenio or 'PREF' in convenio:
                orgao = 'INSS'
            elif 'FGTS' in convenio:
                orgao = 'FGTS'
            elif 'SEGURO' in convenio:
                orgao = 'INSS'  # Seguro vinculado ao INSS
            elif 'PREFEITURA' in cod_banco or 'PREF' in cod_banco:
                orgao = 'INSS'  # Prefeituras geralmente INSS
            
            # FIX: ADE correta - usar 'DATA AVERBACAO' em vez de 'COD. BANCO'
            data_averbacao = str(row.get('DATA AVERBACAO', row.get('DATA DE AVERBACAO', ''))).strip()
            
            # FIX: Código tabela limpo
            codigo_tabela_bruto = str(row.get('PRODUTO', '')).strip()
            codigo_tabela = extract_santander_codigo_tabela(codigo_tabela_bruto)
            
            # FIX: CPF do usuário padronizado
            usuario_bruto = str(row.get('USUARIO DIGITADOR', row.get('GERENTE', ''))).strip()
            usuario_cpf = extract_cpf_from_user(usuario_bruto)
            
            # 🔧 SANTANDER FIX: Usar campos corretos baseados no arquivo manual
            # Campos do arquivo Santander real:
            # PROPOSTA;DATA CADASTRO;BANCO;ORGAO;CODIGO TABELA;TIPO DE OPERACAO;
            # NUMERO PARCELAS;VALOR PARCELAS;VALOR OPERACAO;VALOR LIBERADO;VALOR QUITAR;
            # USUARIO BANCO;CODIGO LOJA;SITUACAO;DATA DE PAGAMENTO;CPF;NOME
            
            # Campo PROPOSTA correto (não é COD!)
            proposta_santander = str(row.get('PROPOSTA', row.get('COD', ''))).strip()
            
            # Campo USUARIO BANCO já é CPF (não precisa extrair!)
            usuario_banco_original = str(row.get('USUARIO BANCO', row.get('USUARIO DIGITADOR', ''))).strip()
            
            # Se USUARIO BANCO já tem formato CPF, manter; senão extrair
            if re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', usuario_banco_original):
                usuario_cpf_final = usuario_banco_original  # Já está formatado
            else:
                usuario_cpf_final = extract_cpf_from_user(usuario_banco_original)
            
            # DATA DE PAGAMENTO correta (não é DATA AVERBACAO!)
            data_pagamento_original = str(row.get('DATA DE PAGAMENTO', row.get('DATA AVERBACAO', ''))).strip()
            
            # SITUACAO original (não mapear para outros valores!)
            situacao_original = str(row.get('SITUACAO', row.get('STATUS', ''))).strip()
            
            # ORGAO direto do arquivo (não detectar!)
            orgao_arquivo = str(row.get('ORGAO', row.get('CONVENIO', ''))).strip().upper()
            if not orgao_arquivo or orgao_arquivo == 'NAN':
                # Só se não vier no arquivo, detectar
                if 'PREF' in convenio or 'PREFEITURA' in convenio:
                    orgao_arquivo = 'PREF. DE AGUDOS - SP'  # Padrão Santander
                else:
                    orgao_arquivo = 'INSS'
            
            # CODIGO TABELA direto do arquivo
            codigo_tabela_arquivo = str(row.get('CODIGO TABELA', row.get('PRODUTO', ''))).strip()
            if not codigo_tabela_arquivo or codigo_tabela_arquivo == 'NAN':
                # Só se não vier, extrair do PRODUTO
                codigo_tabela_arquivo = extract_santander_codigo_tabela(codigo_tabela_bruto)
            
            # 🔧 SANTANDER: Normalização de STATUS como AVERBAI/VCTEX
            def normalize_santander_status(status_original):
                """Normaliza status do Santander para padrão Storm"""
                if not status_original:
                    return "AGUARDANDO"
                
                status_upper = str(status_original).strip().upper()
                
                # Mapeamento específico Santander
                if status_upper in ['PAGO', 'AVERBADO', 'AVERBADA', 'LIBERADO', 'DESEMBOLSADO']:
                    return "PAGO"
                elif status_upper in ['CANCELADO', 'REPROVADO', 'REJEITADO', 'NEGADO']:
                    return "CANCELADO" 
                elif status_upper in ['AGUARDANDO', 'EM ANALISE', 'EM ANÁLISE', 'PENDENTE', 'ABERTO']:
                    return "AGUARDANDO"
                else:
                    return status_original  # Manter original se não reconhecer
            
            # 💰 SANTANDER: Formatação brasileira de valores
            def format_santander_value(value_str):
                """Formata valores do Santander no padrão brasileiro"""
                if not value_str or str(value_str).strip() in ['', 'nan', 'NaN', 'None']:
                    return "0,00"
                
                try:
                    # Converter para float e formatar
                    value_clean = str(value_str).replace(',', '.')
                    value_float = float(value_clean)
                    
                    # Formato brasileiro: 1.234,56
                    if value_float >= 1000:
                        return f"{value_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        return f"{value_float:.2f}".replace('.', ',')
                        
                except (ValueError, TypeError):
                    return str(value_str)  # Retornar original se não conseguir converter
            
            # 🏛️ SANTANDER: Correção de ÓRGÃO
            def correct_santander_orgao(orgao_original, codigo_tabela):
                """Corrige órgão baseado no código da tabela"""
                if not orgao_original or str(orgao_original).strip().upper() == 'INSS':
                    # Se código começar com 810, é prefeitura
                    if codigo_tabela and codigo_tabela.startswith('810'):
                        return "PREF. DE AGUDOS - SP"  # Padrão Santander prefeitura
                    elif codigo_tabela and codigo_tabela.startswith('827'):
                        return "PREF. DE AGUDOS - SP"  # Refinanciamento prefeitura
                    else:
                        return "INSS"  # Default
                else:
                    return str(orgao_original).strip()
            
            # Aplicar correções
            status_normalizado = normalize_santander_status(situacao_original)
            orgao_corrigido = correct_santander_orgao(orgao_arquivo, codigo_tabela_arquivo)
            
            # Garantir USUARIO_BANCO válido
            if not usuario_cpf_final or usuario_cpf_final == 'NAN':
                # Tentar campo alternativo ou usar CPF do cliente
                cpf_cliente = str(row.get('CPF', '')).strip().replace('.', '').replace('-', '')
                if len(cpf_cliente) == 11:
                    usuario_cpf_final = cpf_cliente
                else:
                    usuario_cpf_final = "00000000000"  # CPF sintético
                    logging.warning(f"⚠️ SANTANDER: USUARIO_BANCO vazio, usando CPF sintético")
            
            # 🔧 FIX: Mapear campos do arquivo original SANTANDER (baseado no mapeamento)
            # Campos originais: COD, COD. BANCO, COD DIGITADOR NO BANCO, STATUS, etc.
            
            def _detect_santander_orgao(row):
                """Detecta órgão do SANTANDER baseado no convênio"""
                convenio = str(row.get('CONVENIO', '')).strip().upper()
                if 'PREF' in convenio or 'AGUDOS' in convenio:
                    return 'PREF. DE AGUDOS - SP'
                elif 'RANCHARIA' in convenio:
                    return 'PREF. DE RANCHARIA - SP'
                else:
                    return 'INSS'
            
            def _get_santander_operation_type(row):
                """Extrai tipo de operação do SANTANDER baseado no produto"""
                produto = str(row.get('PRODUTO', '')).strip().upper()
                if 'REFIN' in produto:
                    return 'REFINANCIAMENTO'
                elif 'NOVO' in produto:
                    return 'MARGEM LIVRE (NOVO)'
                elif 'PORTABILIDADE' in produto:
                    return 'PORTABILIDADE'
                else:
                    return 'MARGEM LIVRE (NOVO)'
            
            def _extract_santander_codigo_tabela(produto_str):
                """Extrai código tabela do produto SANTANDER"""
                if not produto_str:
                    return ""
                
                import re
                # Procurar padrão: "21387 - 810021387 - 1 OFERTA NOVO COM SEGURO"
                # Queremos o segundo número (810021387)
                parts = str(produto_str).split(' - ')
                if len(parts) >= 2 and parts[1].strip().isdigit():
                    return parts[1].strip()
                
                # Se não encontrar, buscar número longo
                numbers = re.findall(r'\d{6,}', str(produto_str))
                return numbers[0] if numbers else ""
            
            normalized_row = {
                "PROPOSTA": proposta_santander,
                "DATA_CADASTRO": data_cadastro,
                "BANCO": "BANCO SANTANDER",
                "ORGAO": orgao_santander,
                "TIPO_OPERACAO": operacao_santander,
                "NUMERO_PARCELAS": parcelas_santander,
                "VALOR_OPERACAO": format_santander_value(valor_bruto),
                "VALOR_LIBERADO": format_santander_value(valor_liquido),
                "USUARIO_BANCO": cod_digitador,
                "SITUACAO": status_santander.upper(),
                "DATA_PAGAMENTO": data_averbacao,
                "CPF": cpf_santander,
                "NOME": cliente_santander.upper(),
                "DATA_NASCIMENTO": "",
                "CODIGO_TABELA": codigo_tabela_santander,
                "VALOR_PARCELAS": format_santander_value(valor_parcela),
                "TAXA": "0,00%",
                "OBSERVACOES": ""
            }
            
            # 🔧 FIX: ADE deve usar COD.BANCO (não PROPOSTA)
            # No relatório final, ADE = PROPOSTA, mas deve vir do COD.BANCO original
            ade_original = str(row.get('COD. BANCO', row.get('COD.BANCO', ''))).strip()
            if ade_original:
                # Usar COD.BANCO como base para PROPOSTA no relatório final 
                # (mantendo o mapeamento correto ADE = COD.BANCO)
                pass  # Por enquanto manter a PROPOSTA original, mas o ADE é COD.BANCO
            
            # 🔄 SANTANDER: Aplicar mapeamento após normalização para garantir CODIGO_TABELA e OPERACAO corretos
            if codigo_tabela_arquivo and codigo_tabela_arquivo.isdigit():
                logging.info(f"🔍 SANTANDER: Aplicando mapeamento para código {codigo_tabela_arquivo}")
                
                # Buscar mapeamento direto
                for key, details in TABELA_MAPPING.items():
                    if details.get('codigo_tabela') == codigo_tabela_arquivo and 'BANCO SANTANDER' in key:
                        # Atualizar com dados oficiais do mapeamento
                        orgao_mapeado = details.get('orgao_storm', '')
                        operacao_mapeada = details.get('operacao_storm', '')
                        taxa_mapeada = details.get('taxa_storm', '')
                        
                        if orgao_mapeado:
                            normalized_row["ORGAO"] = orgao_mapeado
                        if operacao_mapeada:
                            normalized_row["TIPO_OPERACAO"] = operacao_mapeada
                        if taxa_mapeada:
                            normalized_row["TAXA"] = taxa_mapeada
                            
                        logging.info(f"✅ SANTANDER MAPEADO: {codigo_tabela_arquivo} → {operacao_mapeada} ({orgao_mapeado}) [{taxa_mapeada}]")
                        break
                else:
                    logging.warning(f"⚠️ SANTANDER: Código {codigo_tabela_arquivo} não encontrado no mapeamento oficial")
            
        elif bank_type == "CREFAZ":
            # Mapeamento BANCO CREFAZ - Campos reais baseados no mapeamento
            # Colunas reais: Data Cadastro, Número da Proposta, CPF, Cliente, Cidade, Status, Agente, etc.
            
            normalized_row = {
                "PROPOSTA": str(row.get('Número da Proposta', row.get('Proposta', ''))).strip(),
                "DATA_CADASTRO": str(row.get('Data Cadastro', '')).strip(),
                "BANCO": "BANCO CREFAZ",
                "ORGAO": "INSS",  # CREFAZ é sempre INSS (energia/boleto)
                "TIPO_OPERACAO": str(row.get('Produto', 'Margem Livre (Novo)')).strip(),
                "NUMERO_PARCELAS": str(row.get('Prazo', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor Liberado', row.get('Valor Solicitado', ''))).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Liberado', '')).strip(),
                "USUARIO_BANCO": str(row.get('Agente', row.get('Login Agente', ''))).strip(),
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Alteração', row.get('Data Pagamento', ''))).strip(),
                "CPF": str(row.get('CPF', '')).strip(),
                "NOME": str(row.get('Cliente', row.get('Nome', ''))).strip(),
                "DATA_NASCIMENTO": "",
                "CODIGO_TABELA": str(row.get('Cod Operação', row.get('Tabela', ''))).strip(),
                "VALOR_PARCELAS": str(row.get('Valor da Parcela', row.get('Parcela', ''))).strip(),
                "TAXA": "",
                "OBSERVACOES": str(row.get('Motivos', row.get('Observacoes', ''))).strip()
            }
        
        elif bank_type == "QUERO_MAIS":
            # Mapeamento BANCO QUERO MAIS CREDITO - ESTRUTURA REAL IDENTIFICADA
            
            # Log para debug das colunas disponíveis
            logging.info(f"🏦 QUERO MAIS - Colunas disponíveis: {list(row.keys())[:15]}...")
            
            # ESTRUTURA REAL baseada no map_relat_atualizados.txt:
            # Unnamed: 11 = CPF Cliente (213.651.558-62, 141.255.778-03)
            # Unnamed: 19 = Data Cadastro (03/09/2025, 05/09/2025) 
            # Unnamed: 20 = Data Nasc. (10/12/1969, 24/10/1958)
            # Unnamed: 22 = Descr. Tabela (INSS CARTÃO BENEFÍCIO_LOAS_CCC, INSS_RMC_ QUERO MAIS_CCC)
            # Unnamed: 24 = Descr. Empregador (INSS BENEFICIO, INSS RMC, GOV SÃO PAULO)
            # Unnamed: 25 = Descr. Orgao (INSS BENEFICIO, INSS RMC, GOV SÃO PAULO)
            # Unnamed: 33 = Proposta (601967573, 601972997)
            # Unnamed: 37 = Nome do Agente (GRUPO QFZ)
            # Unnamed: 38 = Cliente (ADRIANA NATALINA RANCURA)
            # Unnamed: 40 = Nome usu. cad. Proposta (02579846158_901064) - USUÁRIO COM _
            # Unnamed: 42 = Qtd Parcelas (96)
            # Unnamed: 46 = Tabela utilizada (004713, 006640) - CÓDIGO DA TABELA!
            # Unnamed: 48 = Vlr.da parcela (53.13, 194.36)
            # Unnamed: 49 = Valor liberacao 1 (1829.79, 1717.23)
            
            # Detecção de órgão pela descrição correta
            descr_orgao = str(row.get('Unnamed: 25', '')).strip().upper()  # Descr. Orgao
            descr_empregador = str(row.get('Unnamed: 24', '')).strip().upper()  # Descr. Empregador
            
            orgao_text = f"{descr_orgao} {descr_empregador}"
            if 'INSS' in orgao_text:
                orgao = 'INSS'
            elif 'GOV' in orgao_text or 'SÃO PAULO' in orgao_text or 'SP' in orgao_text:
                orgao = 'SIAPE'
            elif 'FGTS' in orgao_text:
                orgao = 'FGTS'
            else:
                orgao = 'INSS'  # Default
            
            # Campos mapeados corretamente
            proposta = str(row.get('Unnamed: 33', '')).strip()  # Proposta
            cpf_cliente = str(row.get('Unnamed: 11', '')).strip()  # CPF Cliente
            nome_cliente = str(row.get('Unnamed: 38', '')).strip()  # Cliente
            data_cadastro = str(row.get('Unnamed: 19', '')).strip()  # Data Cadastro
            data_nascimento = str(row.get('Unnamed: 20', '')).strip()  # Data Nasc.
            qtd_parcelas = str(row.get('Unnamed: 42', '')).strip()  # Qtd Parcelas
            codigo_tabela_raw = str(row.get('Unnamed: 46', '')).strip()  # Tabela utilizada (CÓDIGO!)
            # Formatar código de tabela com zeros à esquerda (6 dígitos)
            codigo_tabela = codigo_tabela_raw.zfill(6) if codigo_tabela_raw.isdigit() else codigo_tabela_raw
            valor_parcela = str(row.get('Unnamed: 48', '')).strip()  # Vlr.da parcela
            valor_liberado = str(row.get('Unnamed: 49', '')).strip()  # Valor liberacao 1
            descr_tabela = str(row.get('Unnamed: 22', '')).strip()  # Descr. Tabela
            usuario_cadastro = str(row.get('Unnamed: 40', '')).strip()  # Nome usu. cad. Proposta (com _)
            
            # Determinação do tipo de operação baseado na descrição da tabela
            tipo_operacao = "Margem Livre (Novo)"  # Default
            if descr_tabela:
                descr_upper = descr_tabela.upper()
                if "CARTAO" in descr_upper or "CARTÃO" in descr_upper:
                    if "SAQUE" in descr_upper:
                        tipo_operacao = "Cartao c/ saque"  # Sem acentos para evitar corrupção
                    else:
                        tipo_operacao = "Cartao s/ saque"  # Sem acentos para evitar corrupção
                elif "RMC" in descr_upper:
                    tipo_operacao = "RMC"
                elif "LOAS" in descr_upper:
                    tipo_operacao = "Margem Livre (LOAS)"
            
            # Remover zeros à esquerda do código de tabela (004717 → 4717)
            codigo_tabela_original = str(row.get('Unnamed: 46', '')).strip()
            codigo_tabela_final = codigo_tabela_original.lstrip('0') if codigo_tabela_original else ''
            # Se ficou vazio após remover zeros, manter o original
            if not codigo_tabela_final:
                codigo_tabela_final = codigo_tabela_original
            
            # Manter formato original do usuário (já vem correto do banco com underscore)
            usuario_final = usuario_cadastro  # Manter formato original: 36057733894_901064
            
            normalized_row = {
                "PROPOSTA": proposta,
                "DATA_CADASTRO": data_cadastro,
                "BANCO": "BANCO QUERO MAIS CREDITO",
                "ORGAO": orgao,
                "TIPO_OPERACAO": tipo_operacao,  # Determinado pela descrição da tabela
                "NUMERO_PARCELAS": qtd_parcelas,
                "VALOR_OPERACAO": valor_liberado,  # Usar valor liberado como operação
                "VALOR_LIBERADO": valor_liberado,
                "USUARIO_BANCO": usuario_final,  # Usuário com formato correto (com _)
                "SITUACAO": "DIGITADA",  # ✅ MANUAL conforme solicitado 
                "DATA_PAGAMENTO": "",   # ✅ MANUAL conforme solicitado (sempre vazio)
                "CPF": cpf_cliente,
                "NOME": nome_cliente,
                "DATA_NASCIMENTO": data_nascimento,
                "CODIGO_TABELA": codigo_tabela_final,  # Código sem zeros à esquerda (4717)
                "VALOR_PARCELAS": valor_parcela,
                "TAXA": "0,00%",  # Taxa fixa para QUERO MAIS
                "OBSERVACOES": descr_tabela  # Descrição da tabela como observação
            }
            
            # Log para debug dos valores mapeados
            logging.info(f"✅ QUERO MAIS mapeado: PROPOSTA={proposta}, ORGAO={orgao}, CPF={cpf_cliente}, TIPO_OP={tipo_operacao}")
        
        elif bank_type == "PAN":
            # Mapeamento BANCO PAN - Estrutura de cartão e saque
            normalized_row = {
                "PROPOSTA": str(row.get('Nº Proposta', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data do Cadastro', '')).strip(),
                "BANCO": "BANCO PAN",
                "ORGAO": str(row.get('Nome do Órgão', row.get('Nome do Empregador', 'INSS'))).strip(),
                "TIPO_OPERACAO": str(row.get('Tipo de Operação', 'Cartão')).strip(),
                "NUMERO_PARCELAS": str(row.get('Quantidade de Parcelas', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor Financiado', '')).strip(),
                "VALOR_LIBERADO": str(row.get('VLR_LIB1', row.get('Valor Financiado', ''))).strip(),
                "USUARIO_BANCO": str(row.get('Nome do Usuário Digitador', '')).strip(),
                "SITUACAO": str(row.get('Nome da Atividade', row.get('Situação da Proposta', ''))).strip(),
                "DATA_PAGAMENTO": str(row.get('Data do Lançamento', '')).strip(),
                "CPF": str(row.get('CPF do Cliente', '')).strip(),
                "NOME": str(row.get('Nome do Cliente', '')).strip(),
                "DATA_NASCIMENTO": str(row.get('Data de Nascimento', '')).strip(),
                "CODIGO_TABELA": str(row.get('Nome do Convênio', row.get('Código do Convênio', ''))).strip(),
                "VALOR_PARCELAS": str(row.get('Valor da Parcela', '')).strip(),
                "TAXA": "",
                "OBSERVACOES": str(row.get('Observações', row.get('Observacoes', row.get('Obs', '')))).strip()
            }
        
        elif bank_type == "C6":
            # Mapeamento BANCO C6 BANK - Campos reais do mapeamento
            # Colunas reais: Nome Entidade, Numero do Contrato, Proposta, Data da operacao, etc.
            
            # Detectar órgão pelo Nome Entidade
            nome_entidade = str(row.get('Nome Entidade', '')).strip().upper()
            if 'INSS' in nome_entidade:
                orgao = 'INSS'
            elif 'FGTS' in nome_entidade:
                orgao = 'FGTS'
            else:
                orgao = 'INSS'  # Default
            
            normalized_row = {
                "PROPOSTA": str(row.get('Número do Contrato', row.get('Proposta', row.get('Numero do Contrato', '')))).strip(),
                "DATA_CADASTRO": str(row.get('Data da operação', row.get('Data da operacao', row.get('Data Cadastro', '')))).strip(),
                "BANCO": "BANCO C6 BANK",
                "ORGAO": orgao,
                "TIPO_OPERACAO": str(row.get('Produto', 'Margem Livre (Novo)')).strip(),
                "NUMERO_PARCELAS": str(row.get('Prazo proposta', row.get('Parcelas', ''))).strip(),
                "VALOR_OPERACAO": str(row.get('Valor Liberado', row.get('Valor', ''))).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Liberado', '')).strip(),
                "USUARIO_BANCO": str(row.get('Usuário (acesso login)', row.get('Usuario', ''))).strip(),
                "SITUACAO": str(row.get('Status', row.get('Situacao', ''))).strip(),
                "DATA_PAGAMENTO": str(row.get('Data pagamento Operação', row.get('Data Pagamento', ''))).strip(),
                "CPF": str(row.get('CPF', '')).strip(),
                "NOME": str(row.get('Nome do Cliente', row.get('Nome', ''))).strip(),
                "DATA_NASCIMENTO": str(row.get('Data Nascimento', '')).strip(),
                "CODIGO_TABELA": str(row.get('Tabela', '')).strip(),
                "VALOR_PARCELAS": str(row.get('Parcela', row.get('Valor Parcela', ''))).strip(),
                "TAXA": str(row.get('Taxa Juros Aplicada', '')).strip(),
                "OBSERVACOES": str(row.get('Observação', row.get('Observacoes', ''))).strip()
            }
        
        elif bank_type == "FACTA92":
            # Mapeamento FACTA92 - Estrutura REAL baseada em map_relat_atualizados.txt
            # Colunas principais: CODIGO, NM_CLIENT, CPF, VL_LIQUIDO, VL_BRUTO, NUMEROPRESTACAO, DS_TABCOM, CORRETOR
            
            # Proposta pode estar em CODIGO, PROPOSTA ou NUMERO_CONTRATO
            proposta = str(row.get('CODIGO', row.get('PROPOSTA', row.get('NUMERO_CONTRATO', '')))).strip()
            
            # Nome do cliente em NM_CLIENT
            nome = str(row.get('NM_CLIENT', row.get('NOME', row.get('CLIENTE', '')))).strip()
            
            # CPF
            cpf = str(row.get('CPF', '')).strip()
            
            # Valores (mapeamento melhorado baseado no arquivo real)
            vl_liquido = str(row.get('VL_LIQUIDO', row.get('VALOR_LIBERADO', row.get('VLR_LIBERADO', '')))).strip()
            vl_bruto = str(row.get('VL_BRUTO', row.get('VALOR_OPERACAO', row.get('VLR_FINANCIADO', '')))).strip()
            vl_parcela = str(row.get('VL_PARCELA', row.get('VALOR_PARCELA', row.get('VLR_PRESTACAO', '')))).strip()
            
            # Parcelas
            num_parcelas = str(row.get('NUMEROPRESTACAO', row.get('NUMERO_PARCELAS', row.get('PARCELAS', row.get('QTD_PARCELAS', ''))))).strip()
            
            # Data de nascimento (se disponível)
            data_nascimento = str(row.get('DATA_NASCIMENTO', row.get('DT_NASCIMENTO', ''))).strip()
            
            # Status/Situação
            situacao = str(row.get('STATUS', row.get('SITUACAO', row.get('SITUACAO_PROPOSTA', '')))).strip()
            if not situacao:
                situacao = "PAGO"  # FACTA92 default para pagos
            
            # Tabela - DS_TABCOM tem formato: "60186 - INSS NOVO GOLD MAX PN-S"
            tabela_completa = str(row.get('DS_TABCOM', row.get('TABELA', row.get('TIPO_TABELA', '')))).strip()
            
            # Função para detectar tipo de operação baseado na tabela
            def detect_facta_operation_type(tabela_descricao):
                """Detecta tipo de operação FACTA92 baseado na descrição da tabela"""
                if not tabela_descricao:
                    return "Margem Livre (Novo)"
                    
                descricao_upper = tabela_descricao.upper()
                logging.info(f"🔧 FACTA92 detectando operação: '{descricao_upper[:50]}...'")
                
                # Baseado nos códigos vistos no relatório
                if 'FGTS' in descricao_upper:
                    return "Margem Livre (Novo)"  # FGTS é margem livre
                elif 'CLT' in descricao_upper and 'NOVO' in descricao_upper:
                    return "Margem Livre (Novo)"
                elif 'PORTABILIDADE' in descricao_upper or 'PORT' in descricao_upper:
                    return "Portabilidade"
                elif 'REFINANCIAMENTO' in descricao_upper or 'REFIN' in descricao_upper:
                    return "Refinanciamento"
                else:
                    return "Margem Livre (Novo)"  # Default
            
            # CORRIGIDO: Extrair apenas código numérico da tabela
            codigo_tabela = ""
            if tabela_completa:
                # Procurar por código numérico no início
                import re
                match = re.match(r'^(\d+)', tabela_completa)
                if match:
                    codigo_tabela = match.group(1)
                    logging.info(f"✅ FACTA92 código extraído: '{tabela_completa}' → '{codigo_tabela}'")
                else:
                    codigo_tabela = tabela_completa  # Fallback
                    logging.warning(f"⚠️ FACTA92 não conseguiu extrair código de: '{tabela_completa}'")
            
            # Usuário/Corretor
            usuario = str(row.get('LOGIN_CORRETOR', row.get('CORRETOR', row.get('USUARIO', '')))).strip()
            
            # Data
            data_cadastro = str(row.get('DATA_CADASTRO', row.get('DATA_REGISTRO', row.get('DATA', '')))).strip()
            data_pagamento = str(row.get('DATAEFETIVACAO', row.get('DATA_PAGAMENTO_CLIENTE', row.get('DATA_PAGAMENTO', '')))).strip()
            
            # Convênio e detecção de órgão melhorada
            convenio = str(row.get('CONVENIO', '')).strip()
            if convenio == '3':
                orgao = 'INSS'
            else:
                # Detectar órgão baseado na tabela completa
                if tabela_completa:
                    tabela_upper = tabela_completa.upper()
                    if 'FGTS' in tabela_upper:
                        orgao = 'INSS'  # FGTS usa margem INSS
                    elif 'CLT' in tabela_upper or 'INSS' in tabela_upper:
                        orgao = 'INSS'
                    elif 'SIAPE' in tabela_upper:
                        orgao = 'SIAPE'
                    elif 'PREFEITURA' in tabela_upper or 'PREF' in tabela_upper:
                        orgao = 'PREFEITURA'
                    else:
                        orgao = 'INSS'  # Default
                else:
                    orgao = 'INSS'  # Default
            
            # Log para debug
            logging.info(f"✅ FACTA92 processado: PROPOSTA={proposta}, TABELA={tabela_completa} → CODIGO={codigo_tabela}, VL_BRUTO={vl_bruto}, VL_LIQ={vl_liquido}")
            
            normalized_row = {
                "PROPOSTA": proposta,
                "DATA_CADASTRO": data_cadastro,
                "BANCO": "FACTA92",
                "ORGAO": orgao,
                "TIPO_OPERACAO": detect_facta_operation_type(tabela_completa),
                "NUMERO_PARCELAS": num_parcelas,
                "VALOR_OPERACAO": vl_bruto if vl_bruto else vl_liquido,
                "VALOR_LIBERADO": vl_liquido,
                "USUARIO_BANCO": usuario,
                "SITUACAO": situacao if situacao else "PAGO",  # Status melhorado
                "DATA_PAGAMENTO": data_pagamento,
                "CPF": cpf,
                "NOME": nome,
                "DATA_NASCIMENTO": data_nascimento,  # Agora mapeado
                "CODIGO_TABELA": codigo_tabela,  # CORRIGIDO: Só código numérico
                "VALOR_PARCELAS": vl_parcela,  # CORRIGIDO: Agora mapeado
                "TAXA": str(row.get('TAXA', '')).strip(),  # FACTA92 tem TAXA em formato decimal (1.85)
                "OBSERVACOES": ""
            }
        
        elif bank_type == "PAULISTA":
            def detect_paulista_organ(especies_beneficio, produto, proposta=""):
                """Detecta órgão do Paulista de forma inteligente"""
                especies_upper = especies_beneficio.upper() if especies_beneficio else ""
                produto_upper = produto.upper() if produto else ""
                proposta_upper = proposta.upper() if proposta else ""
                
                logging.info(f"🏛️ PAULISTA detectando órgão: espécie='{especies_upper[:30]}...' | produto='{produto_upper[:30]}...'")
                
                # Análise combinada de espécie + produto
                combined_text = f"{especies_upper} {produto_upper} {proposta_upper}"
                
                # INSS - mais comum no Paulista
                if any(x in combined_text for x in ['INSS', 'APOSENT', 'PENSÃO', 'PENSAO', 'BENEFICI', 'PREVIDENC']):
                    return "INSS"
                
                # FGTS
                elif any(x in combined_text for x in ['FGTS', 'TRABALHADOR', 'SAQUE']):
                    return "FGTS"
                
                # Prefeituras ou outros órgãos
                elif any(x in combined_text for x in ['PREFEIT', 'MUNICIPAL', 'SERVIDOR']):
                    return "PREFEITURA"
                
                # Padrão: INSS (Paulista é principalmente INSS)
                else:
                    return "INSS"
            
            def detect_paulista_operation(produto, especies_beneficio="", status=""):
                """Detecta tipo de operação do Paulista"""
                produto_upper = produto.upper() if produto else ""
                especies_upper = especies_beneficio.upper() if especies_beneficio else ""
                status_upper = status.upper() if status else ""
                
                logging.info(f"🔧 PAULISTA detectando operação: produto='{produto_upper[:30]}...' | espécie='{especies_upper[:20]}...'")
                
                combined_text = f"{produto_upper} {especies_upper} {status_upper}"
                
                # Refinanciamento
                if any(x in combined_text for x in ['REFIN', 'REFINANCIAMENTO']):
                    return "Refinanciamento"
                
                # Portabilidade
                elif any(x in combined_text for x in ['PORT', 'PORTABILIDADE']):
                    return "Portabilidade"
                
                # Margem Livre (mais comum)
                elif any(x in combined_text for x in ['MARGEM', 'LIVRE', 'CONSIGNADO', 'NOVO']):
                    return "Margem Livre (Novo)"
                
                # Padrão
                else:
                    return "Margem Livre (Novo)"
            
            # Mapeamento BANCO PAULISTA - Colunas corretas (Unnamed)
            # Unnamed: 0 = Nº Proposta, Unnamed: 1 = Contrato
            # Unnamed: 2 = Data Captura, Unnamed: 3 = Dt Atividade  
            # Unnamed: 4 = CPF, Unnamed: 5 = Nome do Proponente
            # Unnamed: 7 = Espécie Benefício (indica INSS)
            # Unnamed: 14 = Valor Empréstimo, Unnamed: 15 = Prazo
            # Unnamed: 18 = Produto, Unnamed: 19 = Fase, Unnamed: 20 = Status
            # Unnamed: 21 = Dta. Integração, Unnamed: 24 = Nome Digitador
            
            proposta = str(row.get('Unnamed: 0', row.get('Unnamed: 1', ''))).strip()
            especies_beneficio = str(row.get('Unnamed: 7', '')).strip()
            produto = str(row.get('Unnamed: 18', '')).strip()
            status = str(row.get('Unnamed: 20', '')).strip()
            
            # Detectar órgão e operação
            orgao_detectado = detect_paulista_organ(especies_beneficio, produto, proposta)
            operacao_detectada = detect_paulista_operation(produto, especies_beneficio, status)
            
            normalized_row = {
                "PROPOSTA": proposta,  # ADE/PROPOSTA (Unnamed: 0)
                "ADE": proposta,  # Campo ADE explícito = mesma proposta
                "DATA_CADASTRO": str(row.get('Unnamed: 2', '')).strip(),
                "BANCO": "BANCO PAULISTA",
                "ORGAO": orgao_detectado,
                "TIPO_OPERACAO": operacao_detectada,
                "NUMERO_PARCELAS": str(row.get('Unnamed: 15', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Unnamed: 14', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Unnamed: 14', '')).strip(),
                "USUARIO_BANCO": str(row.get('Unnamed: 24', '')).strip(),
                "SITUACAO": status,  # STATUS direto (será normalizado depois)
                "DATA_PAGAMENTO": str(row.get('Unnamed: 21', '')).strip(),
                "CPF": str(row.get('Unnamed: 4', '')).strip(),  # CPF (Unnamed: 4)
                "NOME": str(row.get('Unnamed: 5', '')).strip(),
                "DATA_NASCIMENTO": "",  # Não disponível
                "CODIGO_TABELA": str(row.get('Unnamed: 16', '')).strip(),  # Será mapeado pelo Storm depois
                "VALOR_PARCELAS": str(row.get('Unnamed: 11', '')).strip(),
                "TAXA": "",  # Será mapeado pelo Storm depois
                "OBSERVACOES": f"Contrato: {str(row.get('Unnamed: 1', '')).strip()} | Fase: {str(row.get('Unnamed: 19', '')).strip()}"
            }
        
        elif bank_type == "BRB":
            # Mapeamento BRB (Banco de Brasília) - Baseado em map_relat_atualizados.txt
            normalized_row = {
                "PROPOSTA": str(row.get('ID Card', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data da Proposta', '')).strip(),
                "BANCO": "BRB",
                "ORGAO": str(row.get('ORGÃO', 'INSS')).strip(),
                "TIPO_OPERACAO": str(row.get('OPERAÇÃO', 'Margem Livre (Novo)')).strip(),
                "NUMERO_PARCELAS": str(row.get('Qtd. Parcelas', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor da Proposta', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Valor da Proposta', '')).strip(),
                "USUARIO_BANCO": str(row.get('Agente Responsável', '')).strip(),
                "SITUACAO": str(row.get('Status da Proposta', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Data da PAGAMENTO', '')).strip(),
                "CPF": str(row.get('CPF do Beneficiário', '')).strip(),
                "NOME": str(row.get('Nome do cliente', '')).strip(),
                "DATA_NASCIMENTO": "",  # Não disponível
                "CODIGO_TABELA": str(row.get('TABELA', '')).strip(),
                "VALOR_PARCELAS": str(row.get('Valor da Parcela', '')).strip(),
                "TAXA": str(row.get('TAXA', '')).strip(),
                "OBSERVACOES": str(row.get('Observações', '')).strip()
            }
        
        elif bank_type == "QUALIBANKING":
            # Mapeamento QUALIBANKING - Baseado em map_relat_atualizados.txt
            normalized_row = {
                "PROPOSTA": str(row.get('Número do Contrato', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data da Proposta', '')).strip(),
                "BANCO": "QUALIBANKING",
                "ORGAO": str(row.get('Tipo de Produto', 'INSS')).strip(),
                "TIPO_OPERACAO": str(row.get('Tipo de Operação', 'Margem Livre (Novo)')).strip(),
                "NUMERO_PARCELAS": str(row.get('Prazo', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor do Empréstimo', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Líquido ao Cliente', '')).strip(),
                "USUARIO_BANCO": str(row.get('Login', '')).strip(),
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Data do Crédito ao Cliente', '')).strip(),
                "CPF": str(row.get('CPF', '')).strip(),
                "NOME": str(row.get('Nome', '')).strip(),
                "DATA_NASCIMENTO": "",  # Não disponível
                "CODIGO_TABELA": str(row.get('Nome da Tabela', '')).strip(),
                "VALOR_PARCELAS": str(row.get('Valor da Parcela', '')).strip(),
                "TAXA": str(row.get('Taxa', '')).strip(),
                "OBSERVACOES": str(row.get('Motivo do Status', '')).strip()
            }
        
        elif bank_type == "MERCANTIL":
            # Mapeamento BANCO MERCANTIL - Baseado em map_relat_atualizados.txt
            # Detectar órgão pelo nome do convênio
            nome_convenio = str(row.get('NomeConvenio', '')).upper()
            if 'FGTS' in nome_convenio or 'F.G.T.S' in nome_convenio:
                orgao = 'FGTS'
            elif 'INSS' in nome_convenio:
                orgao = 'INSS'
            else:
                orgao = 'INSS'  # Default
            
            # Detectar tipo de operação
            modalidade = str(row.get('ModalidadeCredito', '')).upper()
            if 'FGTS' in modalidade or 'SAQUEANIVERSARIOFGTS' in modalidade:
                tipo_operacao = 'Margem Livre (Novo)'
            elif 'CREDITOPESSOAL' in modalidade:
                tipo_operacao = 'Margem Livre (Novo)'
            else:
                tipo_operacao = 'Margem Livre (Novo)'
            
            normalized_row = {
                "PROPOSTA": str(row.get('NumeroProposta', '')).strip(),
                "DATA_CADASTRO": str(row.get('DataCadastro', '')).strip(),
                "BANCO": "BANCO MERCANTIL",
                "ORGAO": orgao,
                "TIPO_OPERACAO": tipo_operacao,
                "NUMERO_PARCELAS": str(row.get('QuantidadeParcelas', '')).strip(),
                "VALOR_OPERACAO": str(row.get('ValorFinanciado', '')).strip(),
                "VALOR_LIBERADO": str(row.get('ValorEmprestimo', '')).strip(),
                "USUARIO_BANCO": str(row.get('LoginUsuarioDigitador', '')).strip(),
                "SITUACAO": str(row.get('SituacaoProposta', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('DataPagamentoCliente', '')).strip(),
                "CPF": str(row.get('Cpf', '')).strip(),
                "NOME": str(row.get('Nome', '')).strip(),
                "DATA_NASCIMENTO": str(row.get('DataNascimento', '')).strip(),
                "CODIGO_TABELA": str(row.get('NomeProduto', '')).strip(),
                "VALOR_PARCELAS": str(row.get('ValorParcela', '')).strip(),
                "TAXA": str(row.get('TaxaJurosMes', '')).strip(),
                "OBSERVACOES": ""
            }
        
        elif bank_type == "AMIGOZ":
            # Mapeamento BANCO AMIGOZ - Baseado em map_relat_atualizados.txt
            normalized_row = {
                "PROPOSTA": str(row.get('Nr Proposta', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data Cadastro', '')).strip(),
                "BANCO": "BANCO AMIGOZ",
                "ORGAO": str(row.get('Convenio', 'INSS')).strip(),
                "TIPO_OPERACAO": str(row.get('Produto', 'Cartão Consignado')).strip(),
                "NUMERO_PARCELAS": str(row.get('Qtd Parcelas', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor Proposta', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Liberado Cliente', '')).strip(),
                "USUARIO_BANCO": str(row.get('Usuário Digitador', '')).strip(),
                "SITUACAO": str(row.get('Status Proposta', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Data Integração', '')).strip(),
                "CPF": str(row.get('CPF Cliente', '')).strip(),
                "NOME": str(row.get('Nome Cliente', '')).strip(),
                "DATA_NASCIMENTO": "",  # Não disponível diretamente
                "CODIGO_TABELA": str(row.get('Tipo de Cartão', '')).strip(),
                "VALOR_PARCELAS": "",  # Não disponível
                "TAXA": str(row.get('Taxa da Operação', '')).strip(),
                "OBSERVACOES": str(row.get('Restricoes', '')).strip()
            }
        
        elif bank_type == "TOTALCASH":
            # Mapeamento BANCO TOTALCASH - Colunas corretas
            convenio = str(row.get('Convenio', '')).strip()
            if 'INSS' in convenio:
                orgao = 'INSS'
            elif 'FGTS' in convenio:
                orgao = 'FGTS'
            else:
                orgao = 'INSS'  # Default
            
            normalized_row = {
                "PROPOSTA": str(row.get('Nr Proposta', '')).strip(),
                "DATA_CADASTRO": str(row.get('Data Cadastro', '')).strip(),
                "BANCO": "BANCO TOTALCASH",
                "ORGAO": orgao,
                "TIPO_OPERACAO": str(row.get('Produto', 'Margem Livre (Novo)')).strip(),
                "NUMERO_PARCELAS": str(row.get('Qtd Parcelas', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor Proposta', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Valor Liberado Cliente', '')).strip(),
                "USUARIO_BANCO": str(row.get('Usuário Digitador', '')).strip(),
                "SITUACAO": str(row.get('Status Proposta', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Data Integração', '')).strip(),
                "CPF": str(row.get('CPF Cliente', '')).strip(),
                "NOME": str(row.get('Nome Cliente', '')).strip(),
                "DATA_NASCIMENTO": "",  # Não disponível
                "CODIGO_TABELA": "",  # Não disponível
                "VALOR_PARCELAS": str(row.get('Valor Parcela', '')).strip(),
                "TAXA": str(row.get('Taxa da Operação', '')).strip(),
                "OBSERVACOES": str(row.get('Observações', row.get('Observacoes', row.get('Obs', '')))).strip()
            }
        
        else:  # GENERICO
            # Tentar mapear colunas automaticamente
            normalized_row = {
                "PROPOSTA": "",
                "DATA_CADASTRO": "",
                "BANCO": bank_type,
                "ORGAO": "",
                "TIPO_OPERACAO": "MARGEM LIVRE (NOVO)",
                "NUMERO_PARCELAS": "",
                "VALOR_OPERACAO": "",
                "VALOR_LIBERADO": "",
                "USUARIO_BANCO": "",
                "SITUACAO": "",
                "DATA_PAGAMENTO": "",
                "CPF": "",
                "NOME": "",
                "DATA_NASCIMENTO": "",
                "TAXA": ""
            }
            
            # Tentar mapear automaticamente baseado em nomes de colunas
            for col in df.columns:
                col_lower = str(col).lower()
                if 'proposta' in col_lower or 'id' in col_lower:
                    normalized_row["PROPOSTA"] = str(row.get(col, '')).strip()
                elif 'data' in col_lower and 'cadastro' in col_lower:
                    normalized_row["DATA_CADASTRO"] = str(row.get(col, '')).strip()
                elif 'nome' in col_lower and 'cliente' in col_lower:
                    normalized_row["NOME"] = str(row.get(col, '')).strip()
                elif 'cpf' in col_lower:
                    normalized_row["CPF"] = str(row.get(col, '')).strip()
                elif 'status' in col_lower or 'situacao' in col_lower:
                    normalized_row["SITUACAO"] = str(row.get(col, '')).strip()
                elif 'valor' in col_lower and ('operacao' in col_lower or 'liberado' in col_lower):
                    normalized_row["VALOR_LIBERADO"] = str(row.get(col, '')).strip()
                    if not normalized_row["VALOR_OPERACAO"]:
                        normalized_row["VALOR_OPERACAO"] = str(row.get(col, '')).strip()
        
        # Aplicar mapeamento de status (normalização completa)
        if normalized_row.get("SITUACAO"):
            situacao_original = str(normalized_row["SITUACAO"]).strip()
            situacao_lower = situacao_original.lower()
            
            # Tentar encontrar no mapeamento
            situacao_normalizada = STATUS_MAPPING.get(situacao_lower, None)
            
            # Se não encontrou exato, tentar normalizar caracteres especiais e espaços
            if not situacao_normalizada:
                # Remover acentos e caracteres especiais para busca mais flexível
                import unicodedata
                situacao_clean = ''.join(
                    c for c in unicodedata.normalize('NFD', situacao_lower)
                    if unicodedata.category(c) != 'Mn'
                )
                situacao_clean = situacao_clean.replace('/', ' ').replace('-', ' ').strip()
                situacao_clean = ' '.join(situacao_clean.split())  # Remove espaços múltiplos
                
                # Tentar encontrar novamente
                situacao_normalizada = STATUS_MAPPING.get(situacao_clean, None)
            
            # Se ainda não encontrou, fazer busca por palavras-chave
            if not situacao_normalizada:
                situacao_palavras = situacao_lower.lower()
                if any(word in situacao_palavras for word in ['pag', 'integra', 'finaliz', 'quitad', 'liberad', 'desembolsa', 'aprovad']):
                    situacao_normalizada = "PAGO"
                elif any(word in situacao_palavras for word in ['cancel', 'reprov', 'rejeit', 'negad', 'expirad', 'invalid', 'recus', 'desist']):
                    situacao_normalizada = "CANCELADO"
                elif any(word in situacao_palavras for word in ['aguard', 'pendent', 'aberto', 'digital', 'andament', 'analise', 'process', 'formal', 'cadastr', 'enviad']):
                    situacao_normalizada = "AGUARDANDO"
            
            # Aplicar a normalização (ou manter original se não encontrou)
            normalized_row["SITUACAO"] = situacao_normalizada if situacao_normalizada else situacao_original
            
            # Log para debug (apenas se não encontrou mapeamento)
            if not situacao_normalizada:
                logging.warning(f"⚠ Status não mapeado: '{situacao_original}' - mantido como está")
        
        # Aplicar mapeamento de código de tabela (sem dependência de usuário para maior estabilidade)
        # EXCETO para DIGIO, AVERBAI e DAYCOVAL que já fizeram mapeamento específico
        if bank_type == "DIGIO":
            # DIGIO já aplicou mapeamento específico, pular mapeamento geral
            logging.info(f"📊 PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: DIGIO já mapeado, pulando mapeamento geral")
            mapping_result = None
        elif bank_type == "AVERBAI" and normalized_row.get("CODIGO_TABELA", "").isdigit():
            # 🎯 AVERBAI com código direto do arquivo - não precisa mapeamento complexo!
            codigo_direto = normalized_row.get("CODIGO_TABELA", "")
            logging.info(f"✅ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: AVERBAI código direto {codigo_direto}, pulando mapeamento complexo")
            mapping_result = None
        elif bank_type == "DAYCOVAL" and normalized_row.get("CODIGO_TABELA", "").isdigit():
            # 🎯 DAYCOVAL com código direto do arquivo - mesma lógica do AVERBAI!
            codigo_direto = normalized_row.get("CODIGO_TABELA", "")
            logging.info(f"✅ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: DAYCOVAL código direto {codigo_direto}, pulando mapeamento complexo")
            mapping_result = None
        elif bank_type == "QUERO_MAIS":
            # 🎯 QUERO MAIS - preservar códigos originais, não aplicar mapeamento automático
            codigo_direto = normalized_row.get("CODIGO_TABELA", "")
            logging.info(f"✅ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: QUERO MAIS código direto {codigo_direto}, pulando mapeamento automático")
            mapping_result = None
        else:
            banco_para_mapeamento = normalized_row.get("BANCO", "")
            orgao_para_mapeamento = normalized_row.get("ORGAO", "")
            operacao_para_mapeamento = normalized_row.get("TIPO_OPERACAO", "")
            tabela_para_mapeamento = normalized_row.get("CODIGO_TABELA", "")
            
            logging.info(f"📊 PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: Aplicando mapeamento com BANCO={banco_para_mapeamento}, ORGAO={orgao_para_mapeamento}, OPERACAO={operacao_para_mapeamento}, TABELA={tabela_para_mapeamento}")
            
            mapping_result = apply_mapping(
                banco_para_mapeamento,
                orgao_para_mapeamento,
                operacao_para_mapeamento,
                "",  # usuario vazio - não mais usado para evitar problemas futuros
                tabela_para_mapeamento
            )
        
        # SEMPRE usar dados do relat_orgaos.csv (formato Storm) quando disponível
        # Os dados do banco são apenas para valores financeiros
        
        # Log ANTES do mapeamento
        logging.info(f"📋 ANTES do mapeamento - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: ORGAO={normalized_row.get('ORGAO', '')}, CODIGO_TABELA={normalized_row.get('CODIGO_TABELA', '')}, TAXA={normalized_row.get('TAXA', '')}, OPERACAO={normalized_row.get('TIPO_OPERACAO', '')}")
        
        # Se encontrou mapeamento, aplicar TODOS os campos do Storm
        if mapping_result:
            # 1. ORGÃO padronizado (Storm)
            if mapping_result.get('orgao_storm'):
                normalized_row["ORGAO"] = mapping_result.get('orgao_storm', '')
            
            # 2. CODIGO TABELA (Storm) - SEMPRE substituir se encontrou mapeamento
            if mapping_result.get('codigo_tabela'):
                normalized_row["CODIGO_TABELA"] = mapping_result.get('codigo_tabela', '')
            
            # 3. TAXA (Storm) - SEMPRE substituir se encontrou mapeamento
            if mapping_result.get('taxa_storm'):
                taxa_mapeada = mapping_result.get('taxa_storm', "0,00%")
                # Garantir que tem formato percentual
                if taxa_mapeada and '%' not in taxa_mapeada:
                    taxa_mapeada = taxa_mapeada + '%'
                normalized_row["TAXA"] = taxa_mapeada if taxa_mapeada else "0,00%"
            
            # 4. TIPO DE OPERACAO (Storm) - SEMPRE substituir se encontrou mapeamento
            if mapping_result.get('operacao_storm'):
                normalized_row["TIPO_OPERACAO"] = mapping_result.get('operacao_storm', "")
        else:
            # Se NÃO encontrou mapeamento, manter valores do banco mas garantir que TAXA existe
            logging.warning(f"⚠️ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: Mapeamento NÃO encontrado! Usando valores do banco")
            # Garantir que TAXA tenha valor mesmo sem mapeamento
            if not normalized_row.get("TAXA") or normalized_row.get("TAXA") == "":
                normalized_row["TAXA"] = "0,00%"
            elif '%' not in normalized_row.get("TAXA", ""):
                normalized_row["TAXA"] = normalized_row.get("TAXA") + '%'
        
        # VALIDAÇÃO FINAL: Garantir que TAXA e CODIGO_TABELA nunca fiquem vazios
        if not normalized_row.get("TAXA") or normalized_row.get("TAXA").strip() == "":
            normalized_row["TAXA"] = "0,00%"
            logging.warning(f"⚠️ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: TAXA vazia, definida como 0,00%")
        
        if not normalized_row.get("CODIGO_TABELA") or normalized_row.get("CODIGO_TABELA").strip() == "":
            normalized_row["CODIGO_TABELA"] = "SEM_CODIGO"
            logging.warning(f"⚠️ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: CODIGO_TABELA vazio, definido como SEM_CODIGO")
        
        # 🔍 PRESERVAR DATAS ORIGINAIS - não deixar o mapeamento alterar
        data_cadastro_original = normalized_row.get('DATA_CADASTRO', '')
        data_pagamento_original = normalized_row.get('DATA_PAGAMENTO', '')
        
        # Log DEPOIS do mapeamento
        logging.info(f"📗 DEPOIS do mapeamento - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: ORGAO={normalized_row.get('ORGAO', '')}, CODIGO_TABELA={normalized_row.get('CODIGO_TABELA', '')}, TAXA={normalized_row.get('TAXA', '')}, OPERACAO={normalized_row.get('TIPO_OPERACAO', '')}")
        
        # ✅ GARANTIR que as datas originais sejam mantidas
        if data_cadastro_original:
            normalized_row['DATA_CADASTRO'] = data_cadastro_original
        if data_pagamento_original: 
            normalized_row['DATA_PAGAMENTO'] = data_pagamento_original
            
        logging.info(f"📅 DATAS FINAIS PRESERVADAS - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: CADASTRO='{normalized_row.get('DATA_CADASTRO')}' | PAGAMENTO='{normalized_row.get('DATA_PAGAMENTO')}'")

        
        # VALIDAÇÃO MELHORADA: Só adicionar se tiver dados essenciais válidos
        proposta = str(normalized_row.get("PROPOSTA", "")).strip()
        nome = str(normalized_row.get("NOME", "")).strip()
        cpf = str(normalized_row.get("CPF", "")).strip()
        
        # Palavras-chave que indicam linha inválida (EXATAS, não substring)
        invalid_exact_keywords = [
            "nan", "none", "null", "unnamed", "relatório", "relatorio",
            "total", "página", "pagina"
        ]
        
        # Palavras que só são inválidas se forem a palavra COMPLETA
        invalid_whole_words = [
            "proposta", "nome", "cliente", "cpf", "banco", "código", "codigo", "data"
        ]
        
        # Verificar se proposta é válida
        proposta_lower = proposta.lower()
        
        # Verificação melhorada: não rejeitar se é uma proposta real que contém essas palavras
        has_invalid_exact = any(keyword == proposta_lower for keyword in invalid_exact_keywords)
        has_invalid_whole = any(proposta_lower == keyword for keyword in invalid_whole_words)
        
        # Validação mais leniente para diagnóstico
        is_valid_proposta = (
            proposta and 
            proposta.strip() not in ["", "nan", "None", "NULL", "NaN"] and
            not has_invalid_exact and
            not has_invalid_whole and
            len(proposta.strip()) >= 1  # Qualquer proposta com pelo menos 1 caractere
        )
        
        # Verificar se tem pelo menos nome OU cpf válido
        nome_lower = nome.lower() if nome else ""
        nome_is_invalid = any(nome_lower == keyword for keyword in invalid_whole_words + invalid_exact_keywords)
        
        # Relaxar validação de CPF para aceitar formatados (XXX.XXX.XXX-XX)
        cpf_clean = ''.join(filter(str.isdigit, cpf)) if cpf else ""
        cpf_valid = len(cpf_clean) >= 11 or (cpf and len(cpf) >= 11)
        
        has_valid_data = (
            (nome and len(nome) > 3 and not nome_is_invalid) or
            cpf_valid or
            proposta  # Se tem proposta, já é válido
        )
        
        # ✅ Verificar se normalized_row não é None (filtrado pelo SANTANDER)
        if normalized_row is None:
            logging.info(f"🚫 SANTANDER: Linha filtrada (proposta SEGURO removida)")
            continue
            
        if is_valid_proposta and has_valid_data:
            normalized_data.append(normalized_row)
            logging.info(f"✅ Linha válida adicionada: Proposta={proposta}, Nome={nome[:20] if nome else 'N/A'}, CPF={cpf[:6] if cpf else 'N/A'}...")
        else:
            logging.warning(f"❌ Linha IGNORADA [{bank_type}] - Proposta='{proposta}' (len={len(proposta)}), Nome='{nome[:20] if nome else 'N/A'}' (len={len(nome)}), CPF='{cpf}' (len={len(cpf)}), is_valid_proposta={is_valid_proposta}, has_valid_data={has_valid_data}")
            # Log detalhado para debug
            if not is_valid_proposta:
                logging.warning(f"  🔍 Proposta inválida: has_invalid_exact={has_invalid_exact}, has_invalid_whole={has_invalid_whole}")
            if not has_valid_data:
                logging.warning(f"  🔍 Dados inválidos: nome_valid={nome and len(nome) > 3 and not nome_is_invalid}, cpf_valid={cpf_valid}")
    
    logging.info(f"📊 [{bank_type}] RESUMO: {len(normalized_data)} registros válidos de {len(df)} linhas processadas")
    
    # Log detalhado se não temos dados
    if len(normalized_data) == 0:
        logging.error(f"❌ [{bank_type}] NENHUM dado válido foi extraído!")
        logging.error(f"   📋 Colunas do DataFrame: {list(df.columns)[:10]}...")
        if not df.empty:
            logging.error(f"   📄 Primeira linha: {dict(df.iloc[0])}") 
        return pd.DataFrame()
    
    return pd.DataFrame(normalized_data)

def _get_daycoval_operation_type(table_description: str) -> str:
    """Determina o tipo de operação baseado na descrição da tabela do Daycoval"""
    table_lower = table_description.lower()
    if 'rfn' in table_lower or 'refin' in table_lower:
        if 'portab' in table_lower:
            return "REFINANCIAMENTO DA PORTABILIDADE"
        else:
            return "REFINANCIAMENTO"
    elif 'portab' in table_lower:
        return "PORTABILIDADE + REFIN"
    else:
        return "MARGEM LIVRE (NOVO)"

def map_to_final_format(df: pd.DataFrame, bank_type: str) -> tuple[pd.DataFrame, int]:
    """Mapear dados para o formato final de 24 colunas com estatísticas de mapeamento"""
    try:
        # Primeiro normalizar os dados
        normalized_df = normalize_bank_data(df, bank_type)
        
        if normalized_df.empty:
            logging.warning(f"Dados normalizados vazios para banco {bank_type}")
            return pd.DataFrame(), 0
        
        # Remover duplicatas específicas para QUERO MAIS (propostas duplicadas)
        if bank_type == "QUERO_MAIS":
            original_count = len(normalized_df)
            # Remover duplicatas baseado na PROPOSTA (campo único) mantendo o primeiro registro
            normalized_df = normalized_df.drop_duplicates(subset=['PROPOSTA'], keep='first')
            removed_count = original_count - len(normalized_df)
            if removed_count > 0:
                logging.info(f"🧹 QUERO MAIS: Removidas {removed_count} propostas duplicadas ({original_count} → {len(normalized_df)})")
        
        final_data = []
        mapped_count = 0
        
        for _, row in normalized_df.iterrows():
            situacao = row.get("SITUACAO", "")
            data_pagamento = row.get("DATA_PAGAMENTO", "")
            
            # DATA DE PAGAMENTO só deve ter valor se STATUS for exatamente PAGO (após normalização)
            if situacao.upper() != "PAGO":
                data_pagamento = ""
            
            final_row = {
                "PROPOSTA": row.get("PROPOSTA", ""),
                "DATA CADASTRO": row.get("DATA_CADASTRO", ""),
                "BANCO": row.get("BANCO", ""),
                "ORGAO": row.get("ORGAO", ""),
                "CODIGO TABELA": row.get("CODIGO_TABELA", ""),
                "TIPO DE OPERACAO": row.get("TIPO_OPERACAO", ""),
                "NUMERO PARCELAS": row.get("NUMERO_PARCELAS", ""),
                "VALOR PARCELAS": row.get("VALOR_PARCELAS", ""),
                "VALOR OPERACAO": row.get("VALOR_OPERACAO", ""),
                "VALOR LIBERADO": row.get("VALOR_LIBERADO", ""),
                "VALOR QUITAR": "",
                "USUARIO BANCO": row.get("USUARIO_BANCO", ""),
                "CODIGO LOJA": "",
                "SITUACAO": situacao,
                "DATA DE PAGAMENTO": data_pagamento,
                "CPF": row.get("CPF", ""),
                "NOME": row.get("NOME", ""),
                "DATA DE NASCIMENTO": row.get("DATA_NASCIMENTO", ""),
                "TIPO DE CONTA": "",
                "TIPO DE PAGAMENTO": "",
                "AGENCIA CLIENTE": "",
                "CONTA CLIENTE": "",
                "FORMALIZACAO DIGITAL": "SIM",
                "TAXA": row.get("TAXA", ""),  # TAXA já vem do relat_orgaos.csv (aplicada em normalize_bank_data)
                "OBSERVACOES": row.get("OBSERVACOES", "")  # Campo de observações (principalmente VCTEX)
            }
            
            # Contar se foi mapeado o código de tabela
            if final_row["CODIGO TABELA"]:
                mapped_count += 1
            
            # Limpar valores 'nan'
            for key, value in final_row.items():
                if str(value).lower() in ['nan', 'none', 'null', '']:
                    final_row[key] = ""
            
            final_data.append(final_row)
        
        result_df = pd.DataFrame(final_data)
        logging.info(f"Mapeamento concluído para {bank_type}: {len(result_df)} registros, {mapped_count} mapeados")
        return result_df, mapped_count
        
    except Exception as e:
        logging.error(f"Erro no mapeamento para {bank_type}: {str(e)}")
        return pd.DataFrame(), 0

def remove_duplicates_enhanced(df: pd.DataFrame, storm_data: Dict[str, str]) -> pd.DataFrame:
    """Remoção aprimorada de duplicatas baseada na Storm"""
    if df.empty:
        return df
    
    filtered_data = []
    removed_count = 0
    
    for _, row in df.iterrows():
        proposta = str(row.get('PROPOSTA', '')).strip()
        
        if not proposta or proposta.lower() in ['nan', 'null', '']:
            continue
        
        # Verificar se proposta existe na Storm
        skip_record = False
        for storm_proposta, storm_status in storm_data.items():
            if proposta == storm_proposta or proposta in storm_proposta or storm_proposta in proposta:
                if storm_status in ["PAGO", "CANCELADO"]:
                    skip_record = True
                    removed_count += 1
                    break
        
        if not skip_record:
            filtered_data.append(row.to_dict())
    
    logging.info(f"Duplicatas removidas: {removed_count}")
    return pd.DataFrame(filtered_data)

def format_csv_for_storm(df: pd.DataFrame) -> str:
    """Formatar CSV otimizado para importação na Storm com separador ';'"""
    if df.empty:
        return ""
    
    # Garantir que todas as colunas estão presentes na ordem correta
    required_columns = [
        "PROPOSTA", "DATA CADASTRO", "BANCO", "ORGAO", "CODIGO TABELA",
        "TIPO DE OPERACAO", "NUMERO PARCELAS", "VALOR PARCELAS", "VALOR OPERACAO",
        "VALOR LIBERADO", "VALOR QUITAR", "USUARIO BANCO", "CODIGO LOJA",
        "SITUACAO", "DATA DE PAGAMENTO", "CPF", "NOME", "DATA DE NASCIMENTO",
        "TIPO DE CONTA", "TIPO DE PAGAMENTO", "AGENCIA CLIENTE", "CONTA CLIENTE",
        "FORMALIZACAO DIGITAL", "TAXA", "OBSERVACOES"
    ]
    
    # Reordenar colunas
    df_ordered = df.reindex(columns=required_columns, fill_value="")
    
    # Limpar dados e garantir formatação consistente
    for col in df_ordered.columns:
        df_ordered[col] = df_ordered[col].astype(str).str.strip()
        df_ordered[col] = df_ordered[col].replace(['nan', 'None', 'null', 'NaN'], '')
    
    # 🔧 FIX: Corrigir formatação do CPF digitador (USUARIO BANCO) no relatório final
    if "USUARIO BANCO" in df_ordered.columns:
        def format_cpf_usuario_banco(cpf_str):
            """Formatar CPF do digitador no padrão XXX.XXX.XXX-XX"""
            if not cpf_str or cpf_str in ['', '0', '000.000.000-00']:
                return '000.000.000-00'
            
            # Remover qualquer formatação existente e extrair apenas números
            cpf_digits = ''.join(filter(str.isdigit, str(cpf_str)))
            
            # Se tem mais de 11 dígitos (caso SANTANDER), pegar apenas os primeiros 11
            if len(cpf_digits) >= 11:
                cpf_clean = cpf_digits[:11]
                # Formatar no padrão brasileiro
                return f"{cpf_clean[:3]}.{cpf_clean[3:6]}.{cpf_clean[6:9]}-{cpf_clean[9:11]}"
            elif len(cpf_digits) == 11:
                # CPF já tem 11 dígitos, apenas formatar
                return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:11]}"
            else:
                # CPF inválido, retornar original
                return str(cpf_str)
        
        df_ordered["USUARIO BANCO"] = df_ordered["USUARIO BANCO"].apply(format_cpf_usuario_banco)
    
    # Formatar datas para DD/MM/YYYY (padrão brasileiro)
    date_columns = ["DATA CADASTRO", "DATA DE PAGAMENTO", "DATA DE NASCIMENTO"]
    for date_col in date_columns:
        if date_col in df_ordered.columns:
            df_ordered[date_col] = df_ordered[date_col].apply(lambda x: format_date_to_brazilian(x))
    
    # Usar separador ';' como solicitado
    return df_ordered.to_csv(index=False, sep=';', encoding='utf-8', lineterminator='\n')

def format_date_to_brazilian(date_str: str) -> str:
    """Converte data para formato DD/MM/YYYY"""
    if not date_str or date_str in ['', 'nan', 'None', 'null']:
        return ""
    
    date_str = str(date_str).strip()
    
    # Já está no formato DD/MM/YYYY
    if '/' in date_str and len(date_str.split('/')) == 3:
        parts = date_str.split('/')
        if len(parts[0]) == 2 and len(parts[2]) == 4:  # DD/MM/YYYY
            return date_str
    
    # Tentar converter de outros formatos comuns
    try:
        # Formato YYYY-MM-DD
        if '-' in date_str:
            date_obj = pd.to_datetime(date_str, format='%Y-%m-%d', errors='coerce')
            if pd.notna(date_obj):
                return date_obj.strftime('%d/%m/%Y')
        
        # Formato DD/MM/YY (ano com 2 dígitos)
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3 and len(parts[2]) == 2:
                day, month, year = parts
                year = '20' + year if int(year) < 50 else '19' + year
                return f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        # Tentar parsing automático do pandas
        date_obj = pd.to_datetime(date_str, errors='coerce', dayfirst=True)
        if pd.notna(date_obj):
            return date_obj.strftime('%d/%m/%Y')
    except:
        pass
    
    return date_str  # Retorna original se não conseguir converter

@api_router.post("/upload-storm")
async def upload_storm_report(file: UploadFile = File(...)):
    """Upload e processamento do relatório da Storm"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Nome do arquivo é obrigatório")
        
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Arquivo está vazio")
        
        df = read_file_optimized(content, file.filename)
        
        # Detectar tipo de banco
        bank_type = detect_bank_type_enhanced(df, file.filename)
        if bank_type != "STORM":
            raise HTTPException(status_code=400, detail="Este não é um arquivo da Storm válido")
        
        # Processar dados da Storm
        storm_proposals = process_storm_data_enhanced(df)
        
        # Armazenar globalmente
        global storm_data_global
        storm_data_global = storm_proposals
        
        return {
            "message": "Arquivo da Storm processado com sucesso",
            "total_proposals": len(storm_proposals),
            "paid_cancelled": sum(1 for status in storm_proposals.values() if status in ["PAGO", "CANCELADO"]),
            "filename": file.filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro ao processar Storm: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.post("/process-banks")
async def process_bank_reports(files: List[UploadFile] = File(...)):
    """Processamento aprimorado de múltiplos relatórios de bancos"""
    try:
        if not storm_data_global:
            raise HTTPException(status_code=400, detail="Primeiro faça upload do relatório da Storm")
        
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="Nenhum arquivo de banco foi enviado")
        
        job_id = str(uuid.uuid4())
        job = ProcessingJob(id=job_id, total_records=0, processed_records=0)
        processing_jobs[job_id] = job
        
        all_final_data = []
        bank_summaries = []
        
        for file in files:
            try:
                if not file.filename:
                    continue
                
                content = await file.read()
                if len(content) == 0:
                    continue
                
                logging.info(f"Processando arquivo: {file.filename}")
                
                # Ler arquivo com tratamento de erros melhorado
                try:
                    df = read_file_optimized(content, file.filename)
                except Exception as read_error:
                    logging.error(f"❌ Erro ao ler arquivo {file.filename}: {str(read_error)}")
                    continue
                
                # Validar DataFrame
                if df is None or df.empty:
                    logging.warning(f"⚠️ Arquivo {file.filename} resultou em DataFrame vazio")
                    continue
                
                # Limpar DataFrame - remover linhas completamente vazias
                df = df.dropna(how='all')
                
                if df.empty:
                    logging.warning(f"⚠️ Arquivo {file.filename} não contém dados válidos após limpeza")
                    continue
                
                # Detectar tipo de banco
                try:
                    bank_type = detect_bank_type_enhanced(df, file.filename)
                except Exception as detect_error:
                    logging.error(f"❌ Erro ao detectar banco em {file.filename}: {str(detect_error)}")
                    continue
                
                if bank_type == "STORM":
                    continue  # Pular arquivos da Storm
                
                logging.info(f"✅ Banco detectado: {bank_type}, Registros originais: {len(df)}, Colunas: {len(df.columns)}")
                
                # Mapear para formato final
                mapped_df, mapped_count = map_to_final_format(df, bank_type)
                
                if mapped_df.empty:
                    logging.warning(f"Nenhum dado mapeado para {file.filename}")
                    continue
                
                # Remover duplicatas baseado na Storm
                original_count = len(mapped_df)
                filtered_df = remove_duplicates_enhanced(mapped_df, storm_data_global)
                duplicates_removed = original_count - len(filtered_df)
                
                logging.info(f"Após remoção de duplicatas: {len(filtered_df)} registros")
                
                if not filtered_df.empty:
                    all_final_data.append(filtered_df)
                
                # Criar resumo
                status_dist = {}
                if not filtered_df.empty and "SITUACAO" in filtered_df.columns:
                    status_dist = filtered_df["SITUACAO"].value_counts().to_dict()
                
                bank_summaries.append(ReportSummary(
                    bank_name=bank_type,
                    total_records=len(filtered_df),
                    duplicates_removed=duplicates_removed,
                    status_distribution=status_dist,
                    mapped_records=mapped_count,
                    unmapped_records=original_count - mapped_count
                ))
                
            except Exception as e:
                logging.error(f"Erro ao processar arquivo {file.filename}: {str(e)}")
                continue
        
        # Combinar todos os dados
        if not all_final_data:
            logging.error("🚫 ERRO CRÍTICO: Nenhum DataFrame válido foi processado!")
            for i, file in enumerate(files):
                logging.error(f"   📂 Arquivo {i+1}: {file.filename}")
            raise HTTPException(status_code=400, detail="Nenhum dado válido foi processado. Verifique se os arquivos têm o formato correto e contêm dados válidos.")
        
        final_df = pd.concat(all_final_data, ignore_index=True)
        
        # **FORMATAÇÃO OTIMIZADA PARA STORM COM SEPARADOR ';'**
        csv_content = format_csv_for_storm(final_df)
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8')
        temp_file.write(csv_content)
        temp_file.close()
        
        # Atualizar job
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.message = f"Processamento concluído: {len(final_df)} registros"
        job.total_records = len(final_df)
        job.result_file = temp_file.name
        
        return {
            "job_id": job_id,
            "message": "Processamento concluído com sucesso",
            "total_records": len(final_df),
            "bank_summaries": [summary.dict() for summary in bank_summaries],
            "download_url": f"/api/download-result/{job_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Erro no processamento: {str(e)}")
        if 'job' in locals():
            job.status = "failed"
            job.message = str(e)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.get("/download-result/{job_id}")
async def download_result(job_id: str):
    """Download do resultado processado"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = processing_jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Processamento ainda não concluído")
    
    if not hasattr(job, 'result_file') or not os.path.exists(job.result_file):
        raise HTTPException(status_code=404, detail="Arquivo de resultado não encontrado")
    
    return FileResponse(
        path=job.result_file,
        filename=f"relatorio_final_storm_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        media_type='text/csv'
    )

@api_router.get("/processing-status/{job_id}")
async def get_processing_status(job_id: str):
    """Status do processamento"""
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    
    job = processing_jobs[job_id]
    return job.dict()

@api_router.get("/")
async def root():
    return {"message": "Sistema de Processamento de Relatórios Financeiros - V6.6.0 Melhorias Completas DIGIO, VCTEX e AVERBAI"}

@api_router.post("/reload-mapping")
async def reload_mapping():
    """Endpoint para recarregar o mapeamento de órgãos quando novos códigos são adicionados"""
    try:
        success = reload_organ_mapping()
        if success:
            return {
                "message": "✅ Mapeamento recarregado com sucesso!",
                "total_bancos": len(ORGAN_MAPPING),
                "total_combinacoes": len(DETAILED_MAPPING),
                "total_tabelas": len(TABELA_MAPPING),
                "total_fallback": len(BANK_ORGAN_MAPPING)
            }
        else:
            raise HTTPException(status_code=500, detail="Erro ao recarregar mapeamento")
    except Exception as e:
        logging.error(f"Erro no reload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.get("/averbai-codes")
async def get_averbai_codes():
    """Endpoint para listar todos os códigos AVERBAI reconhecidos pelo sistema"""
    try:
        averbai_codes = {
            "FGTS": [],
            "INSS": [],
            "CREDITO_DO_TRABALHADOR": []
        }
        
        # Buscar todos os códigos AVERBAI no mapeamento
        for key, details in TABELA_MAPPING.items():
            parts = key.split('|')
            if len(parts) >= 2 and parts[0] == "AVERBAI":
                orgao = parts[1]
                codigo = details.get('codigo_tabela', '')
                tabela = details.get('tabela_banco', '')
                taxa = details.get('taxa_storm', '')
                
                code_info = {
                    "codigo": codigo,
                    "tabela": tabela,
                    "taxa": taxa,
                    "operacao": details.get('operacao_storm', '')
                }
                
                if orgao == "FGTS":
                    averbai_codes["FGTS"].append(code_info)
                elif orgao == "INSS":
                    averbai_codes["INSS"].append(code_info)
                elif orgao == "CRÉDITO DO TRABALHADOR":
                    averbai_codes["CREDITO_DO_TRABALHADOR"].append(code_info)
        
        # Ordenar por código
        for orgao in averbai_codes:
            averbai_codes[orgao] = sorted(averbai_codes[orgao], key=lambda x: int(x["codigo"]) if x["codigo"].isdigit() else 9999)
        
        return {
            "message": "Códigos AVERBAI reconhecidos pelo sistema",
            "total_fgts": len(averbai_codes["FGTS"]),
            "total_inss": len(averbai_codes["INSS"]), 
            "total_clt": len(averbai_codes["CREDITO_DO_TRABALHADOR"]),
            "codes": averbai_codes
        }
        
    except Exception as e:
        logging.error(f"Erro ao listar códigos AVERBAI: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

@api_router.post("/debug-file")
async def debug_file(file: UploadFile = File(...)):
    """Endpoint de debug para testar leitura e detecção de arquivos"""
    try:
        content = await file.read()
        
        # Tentar ler arquivo
        try:
            df = read_file_optimized(content, file.filename)
            
            debug_info = {
                "filename": file.filename,
                "file_size": len(content),
                "success": True,
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": list(df.columns)[:20],  # Primeiras 20 colunas
                "first_row_sample": {}
            }
            
            # Pegar primeira linha como exemplo
            if not df.empty:
                first_row = df.iloc[0]
                for col in list(df.columns)[:10]:  # Primeiras 10 colunas
                    debug_info["first_row_sample"][col] = str(first_row[col])[:100]
            
            # Tentar detectar banco
            try:
                bank_type = detect_bank_type_enhanced(df, file.filename)
                debug_info["detected_bank"] = bank_type
            except Exception as detect_error:
                debug_info["detected_bank"] = f"ERRO: {str(detect_error)}"
            
            return debug_info
            
        except Exception as read_error:
            return {
                "filename": file.filename,
                "file_size": len(content),
                "success": False,
                "error": str(read_error),
                "error_type": type(read_error).__name__
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no debug: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()