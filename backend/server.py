from fastapi import FastAPI, APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
# from motor.motor_asyncio import AsyncIOMotorClient  # Comentado para deploy mais rápido
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

# MongoDB connection (comentado para deploy mais rápido)
# mongo_url = os.environ.get('MONGO_URL', '')
# client = AsyncIOMotorClient(mongo_url) if mongo_url else None
# db = client[os.environ.get('DB_NAME', '')] if client else None

# Create the main app without a prefix
app = FastAPI()

# Health check endpoint for Docker
@app.get("/health")
async def health_check():
    """Health check endpoint para verificar se a aplicação está funcionando"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Q-FAZ Backend",
        "version": "1.0.0"
    }

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

# ✅ MAPEAMENTO PADRONIZADO STORM - SEM ACENTOS (baseado em relat_orgaos.csv)
STORM_OPERATIONS_MAPPING = {
    # Operações SEM ACENTOS para evitar caracteres quebrados
    "MARGEM LIVRE (NOVO)": "Margem Livre (Novo)",
    "MARGEM LIVRE NOVO": "Margem Livre (Novo)", 
    "CARTAO C/ SAQUE": "CARTAO C/ SAQUE",
    "CARTAO C/ SAQUE COMPLEMENTAR A VISTA": "CARTAO C/ SAQUE COMPLEMENTAR A VISTA",
    "PORTABILIDADE": "PORTABILIDADE",
    "PORTABILIDADE + REFIN": "PORTABILIDADE",  # 🚨 CORREÇÃO: + Refin vira simples
    "PORTABILIDADE + REFINANCIAMENTO": "PORTABILIDADE",  # 🚨 CORREÇÃO
    "PORTABILIDADE E REFINANCIAMENTO": "PORTABILIDADE",  # 🚨 CORREÇÃO
    "REFINANCIAMENTO": "Refinanciamento",
    "REFINANCIAMENTO DA PORTABILIDADE": "Refinanciamento da Portabilidade",
    "ATIVACAO - PRE SAQUE": "Ativacao - Pre Saque",
    # Variações com acentos → sem acentos
    "Portabilidade": "PORTABILIDADE",
    "Portabilidade + Refin": "PORTABILIDADE",
    "Portabilidade + Refinanciamento": "PORTABILIDADE", 
    "Portabilidade e Refinanciamento": "PORTABILIDADE",
    "Portabilidade +Refin": "PORTABILIDADE",
    "Refinanciamento da Portabilidade": "Refinanciamento da Portabilidade",
    "Refinanciamento Da Portabilidade": "Refinanciamento da Portabilidade",
    "Cartão c/ Saque": "CARTAO C/ SAQUE",
    "Cartao C/ Saque": "CARTAO C/ SAQUE",
    "Cartão C/ Saque": "CARTAO C/ SAQUE",
    "Margem Livre (Novo)": "Margem Livre (Novo)",
    # Casos especiais
    "Rentabilidade": "PORTABILIDADE",  # Erro de digitação comum
    "Saque FGTS": "Margem Livre (Novo)",
    "Consignado FGTS": "Margem Livre (Novo)",
    "Consignado INSS": "Margem Livre (Novo)",
    "Emprestimo Complementar": "Margem Livre (Novo)",
    "Credito Do Trabalhador": "Margem Livre (Novo)"
}

# ✅ MAPEAMENTO PADRONIZADO ÓRGÃOS STORM - SEM ACENTOS
STORM_ORGANS_MAPPING = {
    # Órgãos SEM ACENTOS para evitar caracteres quebrados
    "INSS": "INSS",
    "FGTS": "FGTS", 
    "SIAPE FEDERAL": "FEDERAL",  # SIAPE FEDERAL → FEDERAL no relatório final
    "SIAPE CONSIG": "SIAPE CONSIG",
    "SIAPE BENEFICIO": "SIAPE BENEFICIO",
    "CREDITO DO TRABALHADOR": "CREDITO DO TRABALHADOR",
    "SPPREV": "SPPREV",
    "GOV. SAO PAULO": "GOV. SAO PAULO",
    "EDUCACAO": "EDUCACAO",
    "SEFAZ": "SEFAZ",
    "SAUDE": "SAUDE",
    "PREF. DE BAURU": "PREF. DE BAURU",
    "PREF. DE LINS - SP": "PREF. DE LINS - SP",
    "PREF. DE AGUDOS - SP": "PREF. DE AGUDOS - SP",
    "MINISTERIO DO TRABALHO E EMPREGO MTE": "MINISTERIO DO TRABALHO E EMPREGO MTE",
    # Variações com acentos → sem acentos
    "CRÉDITO DO TRABALHADOR": "CREDITO DO TRABALHADOR",
    "EDUCAÇÃO": "EDUCACAO",
    "SAÚDE": "SAUDE",
    "SEFAZ - AOL": "SEFAZ - AOL",
    "TJ SERVIDORES": "TJ SERVIDORES",
    "PMESP": "PMESP",
    "OBRAS": "OBRAS",
    "CULTURA": "CULTURA",
    "ENERGIA": "ENERGIA",
    "ADMINISTRACAO": "ADMINISTRACAO",
    "LOAS": "LOAS"
}

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
    "PORTABILIDADE": "PORTABILIDADE",  # 🚨 CORREÇÃO: Mapeamento simples
    "PORTABILIDADE + REFIN": "PORTABILIDADE",  # 🚨 CORREÇÃO: + Refin vira simples Portabilidade
    "REFINANCIAMENTO": "REFINANCIAMENTO",
    "REFINANCIAMENTO DA PORTABILIDADE": "REFINANCIAMENTO DA PORTABILIDADE",
    "EMPRÉSTIMO COMPLEMENTAR": "EMPRÉSTIMO COMPLEMENTAR",
    "Saque FGTS": "MARGEM LIVRE (NOVO)",
    "Consignado FGTS": "MARGEM LIVRE (NOVO)",
    "Consignado INSS": "MARGEM LIVRE (NOVO)",
    "Portabilidade + Refin": "PORTABILIDADE",  # 🚨 CORREÇÃO: + Refin vira simples Portabilidade
    "Portabilidade": "PORTABILIDADE",  # 🚨 ADICIONADO: Mapeamento direto
    "Refinanciamento": "REFINANCIAMENTO",
    "Cartão c/ saque": "CARTÃO C/ SAQUE",
    "Cartão c/ saque complementar à vista": "CARTÃO C/ SAQUE COMPLEMENTAR À VISTA"
}

# Global storage for processing state
processing_jobs = {}
storm_data_global = {}

# 🌍 FUNÇÕES GLOBAIS DE FORMATAÇÃO (aplicadas a TODOS os bancos)

def format_cpf_global(cpf_str):
    """Formata CPF para o padrão brasileiro: 000.000.000-00
    IMPORTANTE: NÃO formata códigos de usuário que contêm underscore!
    """
    if not cpf_str:
        return ""
    
    cpf_clean = str(cpf_str).strip()
    
    # 🚫 NÃO FORMATAR códigos de usuário que contêm underscore!
    # Ex: "39891947807_901064" deve manter formato original sem underscore
    if '_' in cpf_clean:
        # É um código de usuário, não CPF - remover underscore e retornar
        return cpf_clean.replace('_', '')
    
    # Remover tudo que não é número
    cpf_numbers = ''.join(filter(str.isdigit, cpf_clean))
    
    # Verificar se tem 11 dígitos
    if len(cpf_numbers) != 11:
        # Se não tem 11 dígitos, retornar original
        return cpf_clean
    
    # Formatar: 000.000.000-00
    cpf_formatted = f"{cpf_numbers[0:3]}.{cpf_numbers[3:6]}.{cpf_numbers[6:9]}-{cpf_numbers[9:11]}"
    return cpf_formatted

def format_value_brazilian(value_str):
    """Formata valores monetários para o padrão brasileiro: 1.255,00"""
    if not value_str or str(value_str).strip() in ['', 'nan', 'None', 'null', 'NaN']:
        return "0,00"
    
    try:
        # Limpar o valor (remover espaços, moeda, etc.)
        clean_value = str(value_str).strip().replace('R$', '').replace(' ', '').replace('\xa0', '')
        
        # Se está vazio após limpeza
        if not clean_value or clean_value == '0':
            return "0,00"
        
        # Se já está no formato brasileiro correto (X.XXX,XX), manter
        if ',' in clean_value:
            parts = clean_value.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Verificar se parte inteira tem pontos como separador de milhar
                if '.' in parts[0] or parts[0].isdigit():
                    return clean_value
        
        # Remover pontos que são separadores de milhar no formato brasileiro
        # mas manter o último ponto se for decimal
        if ',' not in clean_value and '.' in clean_value:
            # Formato americano: 1234.56 ou 1,234.56
            clean_value = clean_value.replace(',', '')  # Remove vírgulas (separador de milhar americano)
            parts = clean_value.split('.')
            integer_part = parts[0]
            decimal_part = parts[1][:2] if len(parts) > 1 else "00"
        elif ',' in clean_value:
            # Formato brasileiro: 1.234,56 ou já está com vírgula decimal
            parts = clean_value.replace('.', '').split(',')  # Remove pontos, split por vírgula
            integer_part = parts[0]
            decimal_part = parts[1][:2] if len(parts) > 1 else "00"
        else:
            # Sem decimal, assumir valor inteiro
            integer_part = clean_value.replace('.', '').replace(',', '')
            decimal_part = "00"
        
        # Garantir que decimal tenha 2 dígitos
        if len(decimal_part) == 1:
            decimal_part += "0"
        elif len(decimal_part) == 0:
            decimal_part = "00"
        
        # Converter para float
        float_value = float(f"{integer_part}.{decimal_part}")
        
        # Formatar no padrão brasileiro: 1.255,00
        if float_value >= 1000:
            # Valores >= 1000: usar ponto para milhar
            formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        else:
            # Valores < 1000: apenas vírgula decimal
            formatted = f"{float_value:.2f}".replace('.', ',')
        
        return formatted
        
    except (ValueError, TypeError) as e:
        logging.warning(f"⚠️ Erro ao formatar valor '{value_str}': {e}")
        return str(value_str).strip()  # Retornar original se houver erro

def format_percentage_brazilian(percentage_str):
    """Formata percentuais para o padrão brasileiro: 1,85%"""
    if not percentage_str or str(percentage_str).strip() in ['', 'nan', 'None', 'null', 'NaN']:
        return "0,00%"
    
    try:
        # Limpar o valor (remover %, espaços, etc.)
        clean_value = str(percentage_str).strip().replace('%', '').replace(' ', '')
        
        if not clean_value or clean_value == '0':
            return "0,00%"
        
        # Converter para float
        percentage_float = float(clean_value.replace(',', '.'))
        
        # Formatar no padrão brasileiro: X,XX%
        formatted = f"{percentage_float:.2f}".replace('.', ',')
        return f"{formatted}%"
        
    except (ValueError, TypeError) as e:
        logging.warning(f"⚠️ Erro ao formatar percentual '{percentage_str}': {e}")
        return f"{str(percentage_str).strip()}%"

def clean_special_characters(text):
    """
    Remove ou substitui caracteres especiais problemáticos que quebram o processamento
    Versão simplificada para evitar corrupção de dados
    """
    if not text or pd.isna(text):
        return ""
    
    text_str = str(text).strip()

    # CORREÇÕES DIRETAS E SEGURAS APENAS
    # Mapeamento direto para casos problemáticos conhecidos
    direct_fixes = {
        # Casos de mojibake comuns
            'CRÃ‰DITO': 'CRÉDITO',
            'CRÃ©DITO': 'CRÉDITO', 
            'CRÃDITO': 'CRÉDITO',
            'CRDITO': 'CRÉDITO',
            'ï¿½': '',  # Remove replacement characters
            'Ã¡': 'á',
            'Ã©': 'é',
            'Ã­': 'í',
            'Ã³': 'ó',
            'Ãº': 'ú',
            'Ã§': 'ç',
            # 🚨 CORREÇÃO ESPECÍFICA: Typos e normalização 
            'Portabilidae': 'Portabilidade',
            'PORTABILIDAE': 'PORTABILIDADE',
            'portabilidae': 'portabilidade',
            # Remoção de acentos para evitar caracteres quebrados
            'Cartão': 'Cartao',
            'CARTÃO': 'CARTAO', 
            'cartão': 'cartao',
            'Crédito': 'Credito',
            'CRÉDITO': 'CREDITO',
            'crédito': 'credito',
            'Saque': 'Saque',  # mantém
            'Trabalhador': 'Trabalhador',  # mantém
            'ç': 'c',
            'ã': 'a',
            'á': 'a',
            'é': 'e',
            'í': 'i',
            'ó': 'o',
            'ú': 'u',
            'ô': 'o',
            'â': 'a',
            'ê': 'e',
            'Ç': 'C',
            'Ã': 'A',
            'Á': 'A',
            'É': 'E',
            'Í': 'I', 
            'Ó': 'O',
            'Ú': 'U',
            'Ô': 'O',
            'Â': 'A',
            'Ê': 'E',
            'Ã£': 'ã',
            'Ãµ': 'õ',
            'Ãª': 'ê',
            'Ã´': 'ô',
            'Ã ': 'à',
            # Caracteres especiais seguros
            '–': '-',
            '—': '-', 
            '•': '-',
            '…': '...',
            '\u00A0': ' ',  # non-breaking space
            '\t': ' ',
            '\r': '',
            '\n': ' '
        }
    
    # Aplicar correções
    result = text_str
    for broken, fixed in direct_fixes.items():
        result = result.replace(broken, fixed)
    
    # Normalizar espaços múltiplos e limpar caracteres de replacement
    result = re.sub(r'\s+', ' ', result).strip()
    result = result.replace('\ufffd', '')  # Remove replacement chars
    
    return result

def clean_contact_field(value, field_name=""):
    """
    Limpa e valida campos de contato, retornando string vazia para valores inválidos
    """
    if not value:
        return ""
    
    # Converter para string e limpar
    clean_value = str(value).strip()
    
    # Lista de valores inválidos
    invalid_values = ['nan', 'none', 'null', '', 'n/a', 'na', 'não informado', 'nao informado']
    
    # Verificar se é valor inválido
    if clean_value.lower() in invalid_values:
        return ""
    
    # Se passou na validação, retornar valor limpo
    return clean_value

def fix_daycoval_date(date_str, field_name=""):
    """
    CORRECAO ESPECIFICA DAYCOVAL: 
    Converte múltiplos formatos para DD/MM/YYYY (formato brasileiro)
    Aceita: YYYY-MM-DD HH:MM:SS, MM/DD/YYYY, DD/MM/YYYY
    MESMA LÓGICA DO VCTEX QUE FUNCIONOU
    """
    if not date_str or pd.isna(date_str) or str(date_str).strip() == "" or str(date_str).strip().lower() == 'nan':
        logging.warning(f"DAYCOVAL {field_name}: Formato não reconhecido: '{date_str}'")
        return ""
    
    import re
    from datetime import datetime
    
    date_clean = str(date_str).strip()
    
    # Se for 'nan', retornar vazio
    if date_clean.lower() == 'nan':
        logging.warning(f"DAYCOVAL {field_name}: Formato não reconhecido: '{date_clean}'")
        return ""
    
    logging.info(f"🔧 DAYCOVAL {field_name}: PROCESSANDO DATA '{date_clean}' - CORRIGIR FORMATO!")
    
    try:
        # 🔥 PRIORIDADE 1: Formato YYYY-MM-DD HH:MM:SS (como '2025-10-01 00:00:00')
        iso_pattern = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})(\s+\d{2}:\d{2}:\d{2})?$', date_clean)
        if iso_pattern:
            year, month, day = iso_pattern.groups()[:3]
            # Converter para DD/MM/YYYY brasileiro
            fixed_date = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
            logging.info(f"✅ DAYCOVAL {field_name}: '{date_clean}' → '{fixed_date}' (ISO→BR convertido)")
            return fixed_date
        
        # Formato XX/YY/YYYY (lógica original)
        us_date_pattern = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', date_clean)
        if us_date_pattern:
            first_num, second_num, year = us_date_pattern.groups()
            
            first_int = int(first_num)
            second_int = int(second_num)
            
            # Se primeiro numero > 12, entao esta no formato DD/MM (brasileiro) - MANTER
            if first_int > 12:
                logging.info(f"DAYCOVAL {field_name}: '{date_clean}' mantido (já DD/MM/YYYY)")
                return date_clean
            
            # Se segundo numero > 12, entao esta no formato MM/DD (americano) - TROCAR
            elif second_int > 12:
                fixed_date = f"{second_num}/{first_num}/{year}"  # DD/MM/YYYY
                logging.info(f"DAYCOVAL {field_name}: '{date_clean}' -> '{fixed_date}' (MM/DD convertido)")
                return fixed_date
            
            # Caso ambiguo (ambos <= 12): assumir formato americano MM/DD e converter para DD/MM
            elif first_int <= 12 and second_int <= 12:
                fixed_date = f"{second_num}/{first_num}/{year}"  # DD/MM/YYYY
                logging.info(f"DAYCOVAL {field_name}: '{date_clean}' -> '{fixed_date}' (assumido MM/DD)")
                return fixed_date
    
    except Exception as e:
        logging.error(f"DAYCOVAL {field_name}: Erro ao processar '{date_clean}': {e}")
    
    # Se nao reconhecer nenhum formato, retornar vazio 
    logging.warning(f"DAYCOVAL {field_name}: Formato não reconhecido: '{date_clean}'")
    return ""

def map_daycoval_columns(row):
    """
    PARSER ESPECÍFICO DAYCOVAL: Mapeia colunas 'Unnamed: X' para campos reais
    Baseado na estrutura real dos arquivos DAYCOVAL que não têm headers normais
    """
    logging.info(f"🔍 DAYCOVAL PARSER: Mapeando colunas para estrutura real")
    
    # Primeira coluna pode ser 'BANCO DAYCOVAL S/A - Consignado' ou 'Unnamed: 0'
    primeira_coluna = None
    if 'BANCO DAYCOVAL S/A - Consignado' in row.keys():
        primeira_coluna = 'BANCO DAYCOVAL S/A - Consignado'
    else:
        primeira_coluna = 'Unnamed: 0'
    
    # Mapeamento baseado na análise dos logs de debug
    mapped_data = {
        'PROPOSTA': str(row.get(primeira_coluna, '')).strip(),  # Coluna 0
        'TIPO_OPERACAO': str(row.get('Unnamed: 1', '')).strip(),  # Coluna 1
        'CLIENTE': str(row.get('Unnamed: 2', '')).strip(),  # Coluna 2  
        'CPF': str(row.get('Unnamed: 3', '')).strip(),  # Coluna 3
        'MATRICULA': str(row.get('Unnamed: 4', '')).strip(),  # Coluna 4
        'DATA_CADASTRO_RAW': str(row.get('Unnamed: 5', '')).strip(),  # Coluna 5
        'DATA_BASE': str(row.get('Unnamed: 6', '')).strip(),  # Coluna 6
        'PRAZO_MESES': str(row.get('Unnamed: 11', '')).strip(),  # Coluna 11
        'TAXA': str(row.get('Unnamed: 12', '')).strip(),  # Coluna 12
        'VALOR_LIQUIDO': str(row.get('Unnamed: 13', '')).strip(),  # Coluna 13
        'VALOR_OPERACAO': str(row.get('Unnamed: 16', '')).strip(),  # Coluna 16
        'VALOR_PARCELA': str(row.get('Unnamed: 18', '')).strip(),  # Coluna 18
        'EMPREGADOR': str(row.get('Unnamed: 23', '')).strip(),  # Coluna 23
        'SITUACAO': str(row.get('Unnamed: 27', '')).strip(),  # Coluna 27
        'DATA_PAGAMENTO_RAW': str(row.get('Unnamed: 36', '')).strip(),  # Coluna 36
        'USUARIO': str(row.get('Unnamed: 40', '')).strip(),  # Coluna 40
        # Campos de contato - vamos tentar diferentes colunas
        'TELEFONE_RAW': str(row.get('Unnamed: 7', '')).strip(),  # Tentativa coluna 7
        'ENDERECO_RAW': str(row.get('Unnamed: 8', '')).strip(),  # Tentativa coluna 8
        'BAIRRO_RAW': str(row.get('Unnamed: 9', '')).strip(),  # Tentativa coluna 9
        'CEP_RAW': str(row.get('Unnamed: 10', '')).strip(),  # Tentativa coluna 10
        'UF_RAW': str(row.get('Unnamed: 14', '')).strip(),  # Tentativa coluna 14
    }
    
    # Log do mapeamento para debug
    logging.info(f"📋 DAYCOVAL MAPEADO: PROPOSTA={mapped_data['PROPOSTA'][:20]}...")
    logging.info(f"📋 DAYCOVAL MAPEADO: CLIENTE={mapped_data['CLIENTE'][:30]}...")  
    logging.info(f"📋 DAYCOVAL MAPEADO: DATA_CAD_RAW={mapped_data['DATA_CADASTRO_RAW']}")
    logging.info(f"📋 DAYCOVAL MAPEADO: DATA_PAG_RAW={mapped_data['DATA_PAGAMENTO_RAW']}")
    logging.info(f"📋 DAYCOVAL MAPEADO: TEL={mapped_data['TELEFONE_RAW'][:15]}...")
    logging.info(f"📋 DAYCOVAL MAPEADO: END={mapped_data['ENDERECO_RAW'][:30]}...")
    
    return mapped_data

def normalize_storm_operation(operation_str):
    """
    🚨 NORMALIZAÇÃO STORM: Operações padronizadas SEM ACENTOS
    """
    if not operation_str:
        return ""
    
    operation_clean = str(operation_str).strip()
    
    # Primeiro remover acentos
    operation_clean = clean_special_characters(operation_clean)
    
    # Depois aplicar mapeamento Storm
    return STORM_OPERATIONS_MAPPING.get(operation_clean.upper(), operation_clean)

def normalize_storm_organ(organ_str):
    """
    🚨 NORMALIZAÇÃO STORM: Órgãos padronizados SEM ACENTOS
    """
    if not organ_str:
        return ""
    
    organ_clean = str(organ_str).strip()
    
    # Primeiro remover acentos
    organ_clean = clean_special_characters(organ_clean)
    
    # Depois aplicar mapeamento Storm
    return STORM_ORGANS_MAPPING.get(organ_clean.upper(), organ_clean)

def extract_contact_data(row, bank_type: str = "") -> dict:
    """
    � FUNÇÃO INTELIGENTE PARA EXTRAIR DADOS DE CONTATO
    Tenta múltiplas estratégias para encontrar telefone, endereço, etc.
    """
    
    # 🔍 LOG SIMPLIFICADO: Mostrar apenas colunas que podem ter dados úteis
    if bank_type in ["DIGIO", "QUERO_MAIS", "PAN"]:
        colunas_todas = list(row.keys())
        # Filtrar colunas que podem ter dados (não vazias e com texto)
        colunas_com_dados = []
        for col in colunas_todas:
            valor = str(row.get(col, '')).strip()
            if valor and valor not in ['nan', 'NaN', '', '0', '0.0']:
                if len(valor) > 3:  # Valores com pelo menos 4 caracteres
                    colunas_com_dados.append(f"{col}='{valor[:20]}'")
        
        logging.error(f"🔍 {bank_type} COLUNAS COM DADOS: {len(colunas_com_dados)} de {len(colunas_todas)}")
        for i, col_data in enumerate(colunas_com_dados[:8]):  # Primeiras 8 colunas úteis
            logging.error(f"   {i}: {col_data}")
    
    # 📞 BUSCA INTELIGENTE DE TELEFONE
    telefone = ""
    telefone_patterns = [
        # Nomes específicos
        'telefone', 'tel', 'fone', 'phone', 'celular', 'cel', 'contato',
        # Para DIGIO - testar colunas específicas que podem ter telefone
        'unnamed: 42', 'unnamed: 43', 'unnamed: 20', 'unnamed: 29',
        # Para QUERO_MAIS
        'fone cel.', 'unnamed: 29'
    ]
    
    for col_name, valor in row.items():
        col_lower = str(col_name).lower().strip()
        valor_str = str(valor).strip()
        
        # Se o nome da coluna contém padrão de telefone
        if any(pattern in col_lower for pattern in telefone_patterns):
            if valor_str and valor_str not in ['nan', '', '0']:
                # Verificar se parece com telefone (só números e tem tamanho certo)
                digits_only = ''.join(filter(str.isdigit, valor_str))
                if len(digits_only) >= 8:  # Pelo menos 8 dígitos para ser telefone
                    telefone = valor_str
                    logging.info(f"📞 {bank_type} TELEFONE encontrado na coluna '{col_name}': {telefone}")
                    break
    
    # 🏠 BUSCA INTELIGENTE DE ENDEREÇO
    endereco = ""
    endereco_patterns = [
        'endereco', 'endereço', 'end', 'address', 'rua', 'avenida', 'av', 'logradouro',
        # Para DIGIO
        'unnamed: 35', 'unnamed: 26', 'unnamed: 34',
        # Para QUERO_MAIS
        'endereco cliente', 'unnamed: 26'
    ]
    
    for col_name, valor in row.items():
        col_lower = str(col_name).lower().strip()
        valor_str = str(valor).strip()
        
        if any(pattern in col_lower for pattern in endereco_patterns):
            if valor_str and valor_str not in ['nan', '', '0']:
                # Verificar se parece com endereço (tem letras e é relativamente longo)
                if len(valor_str) > 5 and any(c.isalpha() for c in valor_str):
                    endereco = valor_str
                    logging.info(f"🏠 {bank_type} ENDERECO encontrado na coluna '{col_name}': {endereco[:30]}...")
                    break
    
    # 📍 BUSCA INTELIGENTE DE CEP
    cep = ""
    cep_patterns = ['cep', 'codigo postal', 'postal', 'unnamed: 12', 'unnamed: 41']
    
    for col_name, valor in row.items():
        col_lower = str(col_name).lower().strip()
        valor_str = str(valor).strip()
        
        if any(pattern in col_lower for pattern in cep_patterns):
            if valor_str and valor_str not in ['nan', '', '0']:
                # Verificar se parece com CEP (8 dígitos ou formato XX.XXX-XXX)
                digits_only = ''.join(filter(str.isdigit, valor_str))
                if len(digits_only) == 8:
                    cep = valor_str
                    logging.info(f"📍 {bank_type} CEP encontrado na coluna '{col_name}': {cep}")
                    break
    
    # 🌎 BUSCA INTELIGENTE DE UF
    uf = ""
    uf_patterns = ['uf', 'estado', 'state', 'unnamed: 27', 'unnamed: 40']
    
    for col_name, valor in row.items():
        col_lower = str(col_name).lower().strip()
        valor_str = str(valor).strip().upper()
        
        if any(pattern in col_lower for pattern in uf_patterns):
            if valor_str and valor_str not in ['NAN', '', '0']:
                # Verificar se parece com UF (2 letras)
                if len(valor_str) == 2 and valor_str.isalpha():
                    uf = valor_str
                    logging.info(f"🌎 {bank_type} UF encontrado na coluna '{col_name}': {uf}")
                    break
    
    # 🏘️ BUSCA INTELIGENTE DE BAIRRO
    bairro = ""
    bairro_patterns = ['bairro', 'neighborhood', 'distrito', 'unnamed: 2', 'unnamed: 38']
    
    for col_name, valor in row.items():
        col_lower = str(col_name).lower().strip()
        valor_str = str(valor).strip()
        
        if any(pattern in col_lower for pattern in bairro_patterns):
            if valor_str and valor_str not in ['nan', '', '0']:
                if len(valor_str) > 2 and any(c.isalpha() for c in valor_str):
                    bairro = valor_str
                    logging.info(f"🏘️ {bank_type} BAIRRO encontrado na coluna '{col_name}': {bairro}")
                    break
    
    # 📊 RESULTADO FINAL
    campos_encontrados = []
    if telefone: campos_encontrados.append("TEL")
    if endereco: campos_encontrados.append("END")
    if cep: campos_encontrados.append("CEP")
    if uf: campos_encontrados.append("UF")
    if bairro: campos_encontrados.append("BAI")
    
    if campos_encontrados:
        logging.info(f"✅ {bank_type} CONTATO SUCESSO: {' + '.join(campos_encontrados)}")
    else:
        logging.warning(f"❌ {bank_type} CONTATO VAZIO: Nenhum campo encontrado")
    
    return {
        'TELEFONE': telefone,
        'ENDERECO': endereco,
        'BAIRRO': bairro,
        'CEP': cep,
        'UF': uf,
        'CIDADE': ""  # Deixar vazio por enquanto
    }

def apply_character_cleaning_to_dataframe(df: pd.DataFrame, filename: str = "") -> pd.DataFrame:
    """
    Aplica limpeza de caracteres especiais em todas as colunas de texto do DataFrame
    """
    if df.empty:
        return df
    
    cleaned_columns = 0
    for column in df.columns:
        if df[column].dtype == 'object':  # Colunas de texto
            df[column] = df[column].astype(str).apply(clean_special_characters)
            cleaned_columns += 1
    
    if cleaned_columns > 0 and filename:
        logging.info(f"✅ Limpeza aplicada ao arquivo {filename}: {cleaned_columns} colunas processadas")
    
    return df

def load_organ_mapping():
    """Carrega o mapeamento de órgãos do arquivo CSV atualizado - MELHORADO sem dependência de usuário"""
    try:
        # Ler o arquivo de mapeamento atualizado usando caminho relativo
        csv_path = os.path.join(os.path.dirname(__file__), 'relat_orgaos.csv')
        
        # Verificar se arquivo existe antes de tentar ler
        if not os.path.exists(csv_path):
            logging.warning(f"Arquivo relat_orgaos.csv não encontrado em: {csv_path}")
            logging.warning(f"Diretório atual: {os.getcwd()}")
            logging.warning(f"Arquivos no diretório backend: {os.listdir(os.path.dirname(__file__))}")
            return {}, {}, {}, {}
            
        # Tentar diferentes encodings com tratamento robusto de caracteres especiais
        # CORREÇÃO: Priorizar encodings que lidam melhor com caracteres portugueses
        encodings_to_try = ['utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-8', 'utf-16']
        df = None
        
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(csv_path, encoding=encoding, sep=';')
                logging.info(f"✅ Arquivo CSV carregado com encoding: {encoding}")
                break
            except Exception as e:
                logging.warning(f"⚠️ Erro ao ler CSV com encoding {encoding}: {e}")
                continue
        
        if df is None:
            # Fallback final 
            try:
                df = pd.read_csv(csv_path, encoding='utf-8', sep=';')
                logging.warning("⚠️ Arquivo CSV carregado com encoding UTF-8 como fallback")
            except Exception as e:
                logging.error(f"❌ Erro crítico ao ler CSV: {e}")
                return {}, {}, {}, {}
        
        # Formato REAL do arquivo: BANCO;ORGÃO STORM;TABELA BANCO;CODIGO TABELA STORM;OPERAÇÃO STORM;TAXA STORM
        # NOTA: Campo USUARIO DIGITADOR STORM foi removido para evitar problemas futuros com mudanças de usuário
        mapping = {}
        detailed_mapping = {}  # Mapeamento por BANCO|ORGÃO|OPERAÇÃO (múltiplas opções)
        tabela_mapping = {}     # Mapeamento por BANCO|ORGÃO|OPERAÇÃO|TABELA (mais específico)
        bank_organ_mapping = {} # Mapeamento por BANCO|ORGÃO (mais genérico para fallback)
        
        for _, row in df.iterrows():
            banco = ' '.join(str(row.get('BANCO', '')).strip().upper().split())
            # FIX ENCODING: Usar ÍNDICE em vez de nome da coluna para evitar problemas de encoding
            # Coluna 0: BANCO
            # Coluna 1: ORGÃO
            # Coluna 2: TABELA BANCO
            # Coluna 3: CODIGO TABELA STORM
            # Coluna 4: OPERAÇÃO STORM
            # Coluna 5: TAXA STORM
            orgao = ' '.join(str(row.iloc[1] if len(row) > 1 else '').strip().upper().split())
            # CRÍTICO: Normalizar tabela removendo TODOS os espaços extras (incluindo espaços iniciais)
            tabela_banco_raw = str(row.iloc[2] if len(row) > 2 else '').strip()
            tabela_banco = ' '.join(tabela_banco_raw.split())  # Remove espaços extras completamente
            codigo_tabela = str(row.iloc[3] if len(row) > 3 else '').strip()
            operacao_storm = str(row.iloc[4] if len(row) > 4 else '').strip()
            taxa_storm = str(row.iloc[5] if len(row) > 5 else '').strip()
            
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
                key = f"{banco}|{orgao}|{operacao_storm.upper()}"
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
                    tabela_key = f"{banco}|{orgao}|{operacao_storm.upper()}|{tabela_banco.upper()}"
                    tabela_mapping[tabela_key] = {
                        'codigo_tabela': codigo_tabela,
                        'tabela_banco': tabela_banco,  # Manter original para exibição
                        'orgao_storm': orgao,  # ORGÃO padronizado Storm
                        'operacao_storm': operacao_storm,
                        'taxa_storm': taxa_storm
                    }
                    
                    # 🔍 DEBUG: Log primeiras 3 linhas FACTA
                    if 'FACTA' in banco and len([k for k in tabela_mapping.keys() if 'FACTA' in k]) <= 3:
                        logging.info(f"🔍 DEBUG TABELA_MAPPING FACTA: Chave='{tabela_key}'")
                        logging.info(f"   Valores: codigo={codigo_tabela}, orgao={orgao}, operacao={operacao_storm}, taxa={taxa_storm}")
                
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
        
        # 🔍 DEBUG: Mostrar primeiras chaves FACTA no TABELA_MAPPING
        facta_keys = [k for k in tabela_mapping.keys() if 'FACTA' in k]
        if facta_keys:
            logging.info(f"🔍 DEBUG: Primeiras {min(3, len(facta_keys))} chaves FACTA no TABELA_MAPPING:")
            for key in facta_keys[:3]:
                logging.info(f"   Chave: '{key}'")
                logging.info(f"   Dados: {tabela_mapping[key]}")
        
        return mapping, detailed_mapping, tabela_mapping, bank_organ_mapping
    except Exception as e:
        logging.error(f"Erro ao carregar mapeamento de órgãos: {str(e)}")
        return {}, {}, {}, {}

# Carregar mapeamento global - ATUALIZADO sem dependência de usuário
try:
    ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING = load_organ_mapping()
    logging.info("✅ Mapeamento de órgãos carregado com sucesso!")
except Exception as e:
    logging.error(f"❌ Erro ao carregar mapeamento: {e}")
    ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING = {}, {}, {}, {}

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
            # Tentar diferentes encodings e separadores com tratamento robusto
            encodings_to_try = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252', 'utf-16']
            for encoding in encodings_to_try:
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
                            return apply_character_cleaning_to_dataframe(df, filename)
                            
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
            # Verificar se é arquivo PAULISTA - precisa pular primeiras linhas
            filename_lower = filename.lower()
            is_paulista = any(indicator in filename_lower for indicator in ['paulista', 'af5eebb7'])
            
            logging.info(f"🔍 Arquivo: {filename_lower}, É PAULISTA? {is_paulista}")
            
            if is_paulista:
                logging.info(f"🏦 Detectado arquivo PAULISTA: {filename}, aplicando leitura especial...")
                try:
                    # PAULISTA: pular primeiras 2 linhas, usar linha 3 como cabeçalho
                    df = pd.read_excel(
                        io.BytesIO(file_content),
                        skiprows=2,  # Pula logo e linha vazia
                        na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                        dtype=str
                    )
                    logging.info(f"🏦 PAULISTA lido com skip=2: {len(df.columns)} colunas, primeiras: {list(df.columns)[:5]}")
                    return apply_character_cleaning_to_dataframe(df, filename)
                except Exception as e:
                    logging.error(f"❌ Erro na leitura especial PAULISTA: {str(e)}")
                    # Fallback para leitura normal
            
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
                
                # PAULISTA DETECTION: Verificar se tem "Relação de Propostas" nas primeiras linhas
                if not df.empty and len(df) > 0:
                    first_few_rows = df.head(3).astype(str)
                    content_text = ' '.join(first_few_rows.values.flatten()).lower()
                    
                    if 'relação de propostas' in content_text or 'analítico' in content_text:
                        logging.info(f"🏦 PAULISTA detectado por conteúdo! Aplicando leitura especial...")
                        try:
                            # Recarregar pulando primeiras linhas
                            df_paulista = pd.read_excel(
                                io.BytesIO(file_content),
                                skiprows=2,  # Pula logo e "Relação de Propostas"
                                na_values=['', 'NaN', 'NULL', 'null', 'N/A', 'n/a'],
                                dtype=str
                            )
                            logging.info(f"🏦 PAULISTA relido: {len(df_paulista.columns)} colunas: {list(df_paulista.columns)[:5]}")
                            return apply_character_cleaning_to_dataframe(df_paulista, filename)
                        except Exception as e:
                            logging.error(f"❌ Erro na releitura PAULISTA: {str(e)}")
                
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
                                        return apply_character_cleaning_to_dataframe(df_attempt, filename)
                            except:
                                continue
                
                # Se chegou aqui, usar o DataFrame original
                logging.info(f"Excel lido normalmente, {len(df.columns)} colunas")
                return apply_character_cleaning_to_dataframe(df, filename)
                
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
                                return apply_character_cleaning_to_dataframe(df, filename)
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
    
    logging.warning(f"🏦 INICIANDO DETECÇÃO para arquivo: {filename}")
    logging.warning(f"📊 {len(df.columns)} colunas encontradas: {df_columns[:10]}...")  # Mostrar apenas primeiras 10
    logging.warning(f"📋 Filename lower: {filename_lower}")
    
    # Detecção por nome do arquivo - mais confiável
    if any(indicator in filename_lower for indicator in ['storm', 'contratos', 'digitados']):
        logging.warning(f"🎯 STORM detectado por nome: {filename}")
        return "STORM"
    elif 'averbai' in filename_lower:
        logging.warning(f"🎯 AVERBAI detectado por nome: {filename}")
        return "AVERBAI"
    elif any(indicator in filename_lower for indicator in ['digio', 'wfsic', 'wfi']):
        logging.warning(f"🎯 DIGIO detectado por nome: {filename}")
        return "DIGIO"
    elif 'prata' in filename_lower:
        logging.warning(f"🎯 PRATA detectado por nome: {filename}")
        return "PRATA"
    elif 'vctex' in filename_lower:
        logging.warning(f"🎯 VCTEX detectado por nome: {filename}")
        return "VCTEX"
    elif 'daycoval' in filename_lower:
        logging.warning(f"🎯 DAYCOVAL detectado por nome: {filename}")
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
            
            # Indicadores únicos do DIGIO (expandidos para melhor detecção)
            digio_unique_indicators = [
                'banco digio', 'digio s.a', 'digio s/a', 'digio bank', 'digio',
                'propostas cadastradas', 'relatório de propostas', 'relatorio de propostas',
                'sic - v.', 'mprlprcd', 'proc.:', 'sist.:', 'cont.:',
                'tipo: por data', 'por data de liberação', 'periodo:',
                'tkt', 'ticket', 'ativo', 'cancelado', 'pago', 'liberado'
            ]
            found_digio_indicators = [ind for ind in digio_unique_indicators if ind in all_data]
            
            # Verificar também na estrutura de colunas
            digio_column_patterns = ['unnamed:', 'proposta', 'tipo_operacao', 'data_cadastro', 'situacao', 'cpf_cliente']
            digio_col_count = sum(1 for pattern in digio_column_patterns if any(pattern in str(col).lower() for col in df_columns))
            
            if found_digio_indicators:
                logging.info(f"✅ DIGIO detectado por indicadores: {found_digio_indicators}")
                return "DIGIO"
                
            # Verificar estrutura típica do DIGIO (muitas colunas Unnamed)
            unnamed_count = sum(1 for col in df_columns if 'unnamed:' in str(col).lower())
            if unnamed_count >= 50:  # DIGIO tem ~105 colunas Unnamed
                # Verificar se NÃO é DAYCOVAL
                daycoval_exclusive_indicators = ['banco daycoval', 'qfz solucoes', 'tp. operação', 'daycoval']
                found_daycoval_indicators = [ind for ind in daycoval_exclusive_indicators if ind in all_data]
                
                if not found_daycoval_indicators:
                    logging.info(f"✅ DIGIO detectado por estrutura ({unnamed_count} colunas Unnamed)")
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
        logging.info(f"✅ DAYCOVAL detectado por nome do arquivo: {filename}")
        return "DAYCOVAL"
    
    # 2. Por estrutura de colunas específicas - FORMATO CSV CORRETO
    daycoval_csv_indicators = ['proposta', 'data cadastro', 'banco', 'orgao', 'codigo tabela', 'tipo de operacao', 'numero parcelas']
    daycoval_csv_matches = sum(1 for indicator in daycoval_csv_indicators if any(indicator in col for col in df_columns))
    if daycoval_csv_matches >= 5:
        logging.info(f"✅ DAYCOVAL detectado por colunas CSV: {daycoval_csv_matches} matches")
        return "DAYCOVAL"
    
    # 3. Por estrutura de colunas antigas (Unnamed)
    daycoval_column_indicators = ['cliente', 'cpf/cnpj', 'matrícula', 'dt.cad.', 'dt.base', 'vlr.oper', 'prz. em meses', 'tx.am']
    daycoval_col_matches = sum(1 for indicator in daycoval_column_indicators if any(indicator in col for col in df_columns))
    if daycoval_col_matches >= 5:
        logging.info(f"✅ DAYCOVAL detectado por colunas antigas: {daycoval_col_matches} matches")
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
    
    # Detecção por nome do arquivo SANTANDER (prioridade)
    if 'santander' in filename_lower:
        logging.info(f"✅ SANTANDER detectado por nome do arquivo")
        return "SANTANDER"
    
    # Verificar se é SANTANDER por colunas específicas
    # Colunas reais do SANTANDER: COD, COD. BANCO, CPF, CLIENTE, CONVENIO, PRODUTO, STATUS, etc.
    santander_column_indicators = ['cod. banco', 'convenio', 'produto', 'qtde parcelas', 'valor bruto', 'valor liquido', 'cod digitador']
    santander_col_matches = sum(1 for indicator in santander_column_indicators if any(indicator in col for col in df_columns))
    
    if santander_col_matches >= 4:
        logging.info(f"✅ SANTANDER detectado por colunas ({santander_col_matches} matches)")
        return "SANTANDER"
    
    # Verificar se tem "SANTANDER" nos dados (formato relatório final)
    if not df.empty:
        banco_col = next((col for col in df.columns if 'banco' in str(col).lower()), None)
        if banco_col and any('SANTANDER' in str(val).upper() for val in df[banco_col].dropna().head(10)):
            logging.info(f"✅ SANTANDER detectado por conteúdo da coluna BANCO")
            return "SANTANDER"
    
    # Verificar se é CREFAZ (PRIORIDADE ALTA - antes do MERCANTIL)
    # 1. Por nome do arquivo
    if 'crefaz' in filename_lower:
        logging.info(f"✅ CREFAZ detectado por nome do arquivo: {filename}")
        return "CREFAZ"
    
    # 2. Por colunas específicas do CREFAZ
    crefaz_column_indicators = ['data cadastro', 'número da proposta', 'cpf', 'cliente', 'cidade', 'valor liberado', 'prazo', 'status', 'agente', 'cod operação', 'produto']
    crefaz_col_matches = sum(1 for indicator in crefaz_column_indicators if any(indicator in col for col in df_columns))
    if crefaz_col_matches >= 5:
        logging.info(f"✅ CREFAZ detectado por colunas ({crefaz_col_matches} matches)")
        return "CREFAZ"
    
    # 3. Por conteúdo específico (indicadores únicos de energia/boleto)
    if not df.empty:
        # Verificar nas primeiras 3 linhas para indicadores específicos do CREFAZ
        all_data = ""
        for i in range(min(3, len(df))):
            row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
            all_data += " " + row_data
        
        # Indicadores únicos do CREFAZ (energia, boleto, etc.)
        crefaz_unique_indicators = ['crefaz', 'energia', 'boleto', 'cpfl', 'cosern', 'celpe', 'enel', 'ener', 'bol', 'luz', 'fatura']
        found_crefaz_indicators = [ind for ind in crefaz_unique_indicators if ind in all_data]
        
        # Verificar se NÃO tem indicadores exclusivos do MERCANTIL
        mercantil_exclusive_indicators = ['banco mercantil do brasil', 'credfranco', 'bmb', 'codigocorrespondente', 'nomecorrespondente']
        found_mercantil_indicators = [ind for ind in mercantil_exclusive_indicators if ind in all_data]
        
        if found_crefaz_indicators and not found_mercantil_indicators:
            logging.info(f"✅ CREFAZ detectado por conteúdo único: {found_crefaz_indicators}")
            return "CREFAZ"

    # Verificar se é MERCANTIL (Banco Mercantil do Brasil) - APÓS CREFAZ
    # 1. Por nome do arquivo
    if 'mercantil' in filename_lower or 'bmb' in filename_lower or 'credfranco' in filename_lower:
        logging.info(f"✅ MERCANTIL detectado por nome do arquivo: {filename}")
        return "MERCANTIL"
    
    # 2. Por estrutura de colunas específicas (FORMATO REAL DO MERCANTIL)
    # Indicadores principais do formato real
    mercantil_indicators = ['numeroproposta', 'codigoconvenio', 'nomeconvenio', 'codigoproduto', 'nomeproduto', 'modalidadecredito', 'situacaoproposta']
    mercantil_matches = sum(1 for indicator in mercantil_indicators if any(indicator in col for col in df_columns))
    
    # Indicadores específicos únicos do Mercantil (baseado no arquivo real)
    mercantil_unique = ['codigocorrespondente', 'nomecorrespondente', 'cnpjcorrespondente', 'codigosubstabelecido', 'nomesubstabelecido', 'cpfagentecertificado']
    mercantil_unique_matches = sum(1 for indicator in mercantil_unique if any(indicator in col for col in df_columns))
    
    # Indicadores de campos extensos típicos do Mercantil
    mercantil_extended = ['valorliberacaosimulado', 'bancoliberacaocliente', 'agencialiberacaocliente', 'contaliberacaocliente', 'digitacontaliberacaocliente']
    mercantil_extended_matches = sum(1 for indicator in mercantil_extended if any(indicator in col for col in df_columns))
    
    if mercantil_matches >= 4:
        logging.info(f"✅ MERCANTIL detectado por colunas principais ({mercantil_matches}/7 matches)")
        return "MERCANTIL"
    elif mercantil_unique_matches >= 3:
        logging.info(f"✅ MERCANTIL detectado por colunas únicas ({mercantil_unique_matches}/6 matches)")
        return "MERCANTIL"
    elif mercantil_extended_matches >= 2:
        logging.info(f"✅ MERCANTIL detectado por colunas extensas ({mercantil_extended_matches}/5 matches)")
        return "MERCANTIL"
    
    # 3. Por conteúdo específico do MERCANTIL (mais restrito)
    if not df.empty:
        # Verificar nas primeiras 5 linhas por indicadores específicos do Mercantil
        all_data = ""
        for i in range(min(5, len(df))):
            row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
            all_data += " " + row_data
        
        # Indicadores específicos do MERCANTIL (removido 'qfz solucoes' para evitar conflito)
        mercantil_content_indicators = ['banco mercantil do brasil', 'credfranco', 'bmb', 'mercantil']
        found_content_indicators = [ind for ind in mercantil_content_indicators if ind in all_data]
        
        # Verificar se NÃO tem indicadores do CREFAZ
        crefaz_conflict_indicators = ['crefaz', 'energia', 'boleto', 'cpfl', 'enel', 'ener', 'bol']
        found_crefaz_conflicts = [ind for ind in crefaz_conflict_indicators if ind in all_data]
        
        if found_content_indicators and not found_crefaz_conflicts:
            logging.info(f"✅ MERCANTIL detectado por conteúdo específico: {found_content_indicators}")
            return "MERCANTIL"
    
    # Verificar se é QUERO MAIS CREDITO (PRIORIDADE ALTA - antes do Paulista)
    # 1. Por nome do arquivo
    if 'quero' in filename_lower and 'mais' in filename_lower:
        logging.warning(f"🎯 QUERO MAIS detectado por nome do arquivo: {filename}")
        return "QUERO_MAIS"
    
    # 1.5 Por palavras-chave específicas no nome (NOVO)
    quero_mais_filename_indicators = ['promotora', 'capital consig', 'grupo qfz', 'relatório de produção', 'relatorio de producao']
    for indicator in quero_mais_filename_indicators:
        if indicator in filename_lower:
            logging.warning(f"🎯 QUERO MAIS detectado por indicador no nome '{indicator}' em arquivo: {filename}")
            return "QUERO_MAIS"
    
    # 2. Por estrutura de colunas Unnamed específicas
    total_cols = len(df.columns)
    unnamed_cols = sum(1 for col in df_columns if 'unnamed:' in col)
    logging.warning(f"🔍 QUERO MAIS check estrutura: {total_cols} colunas totais, {unnamed_cols} Unnamed, arquivo: {filename}")
    
    # 🔧 CRITÉRIO MELHORADO: Se tem 40+ colunas e 30+ Unnamed (ou ratio > 80%)
    unnamed_ratio = (unnamed_cols / total_cols * 100) if total_cols > 0 else 0
    structure_matches = (total_cols > 40 and unnamed_cols > 30) or unnamed_ratio > 80
    
    logging.warning(f"🔍 QUERO MAIS estrutura - ratio Unnamed: {unnamed_ratio:.1f}%, match: {structure_matches}")
    
    if structure_matches:
        # Verificar indicadores específicos do QUERO MAIS (ANTES do Paulista!)
        quero_mais_indicators = ['capital consig', 'quero mais credito', 'quero mais crédito', 'relatório de produção', 'relatório de produção', 'promotora', 'grupo qfz', 'cpf correspondente', 'convênio correspondente', 'quero mais', 'queromais', 'qmais', 'capital consignado']
        logging.warning(f"🔍 QUERO MAIS estrutura OK - verificando conteúdo...")
        if not df.empty:
            # Verificar nas primeiras 5 linhas para maior precisão
            all_data = ""
            for i in range(min(5, len(df))):
                row_data = ' '.join([str(val).lower() for val in df.iloc[i].values if pd.notna(val)])
                all_data += " " + row_data
            
            logging.info(f"🔍 QUERO MAIS check - dados: {all_data[:200]}...")
            
            # Indicadores únicos do QUERO MAIS (não confundem com PAULISTA)
            quero_mais_unique = ['capital consig', 'quero mais', 'queromais', 'qmais', 'promotora', 'grupo qfz', 'cpf correspondente', 'capital consignado']
            found_quero_indicators = [ind for ind in quero_mais_unique if ind in all_data]
            
            # Verificar se NÃO tem indicadores do PAULISTA
            paulista_exclusive = ['banco paulista', 'relação de propostas', 'espécie benefício', 'analítico']
            found_paulista_indicators = [ind for ind in paulista_exclusive if ind in all_data]
            
            if found_quero_indicators and not found_paulista_indicators:
                logging.warning(f"✅ QUERO MAIS detectado! Indicadores únicos: {found_quero_indicators}")
                return "QUERO_MAIS"
            else:
                logging.error(f"❌ QUERO MAIS não detectado - indicadores QUERO: {found_quero_indicators}, PAULISTA: {found_paulista_indicators}")
                logging.error(f"   📄 Conteúdo analisado: {all_data[:300]}...")
    
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
            quero_mais_exclusive = ['capital consig', 'quero mais', 'queromais', 'qmais', 'promotora', 'grupo qfz', 'cpf correspondente', 'capital consignado']
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
    
    logging.error(f"❌ CRÍTICO: Tipo de banco NÃO RECONHECIDO para: {filename}")
    logging.error(f"   📊 Estrutura: {len(df.columns)} colunas, {sum(1 for col in df_columns if 'unnamed:' in col)} colunas 'Unnamed'")
    logging.error(f"   📋 Primeiras colunas: {df_columns[:5]}")
    
    raise HTTPException(status_code=400, detail=f"Tipo de banco não reconhecido para: {filename}. Estrutura: {len(df.columns)} colunas, {sum(1 for col in df_columns if 'unnamed:' in col)} colunas 'Unnamed'. Primeiras colunas: {df_columns[:5]}")

def process_storm_data_enhanced(df: pd.DataFrame) -> Dict[str, str]:
    """Processamento aprimorado dos dados da Storm - usa ADE e Status do Contrato"""
    storm_proposals = {}
    
    logging.info(f"Processando Storm com {len(df)} linhas e colunas: {list(df.columns)}")
    
    # Identificar colunas corretas
    ade_col = None
    status_col = None
    
    # Buscar colunas ADE e Status do Contrato
    for col in df.columns:
        col_lower = str(col).lower().strip()
        if col_lower == 'ade':
            ade_col = col
            logging.info(f"Coluna ADE encontrada: '{col}'")
        elif 'status do contrato' in col_lower or col_lower == 'status do contrato':
            status_col = col
            logging.info(f"Coluna Status encontrada: '{col}'")
    
    # Fallback para posições fixas baseadas na estrutura padrão Storm
    if ade_col is None:
        # ADE é geralmente a coluna 28 (índice 28)
        if len(df.columns) > 28:
            ade_col = df.columns[28]
            logging.info(f"Usando coluna ADE por posição [28]: '{ade_col}'")
    
    if status_col is None:
        # Status do Contrato é geralmente a coluna 40 (índice 40)  
        if len(df.columns) > 40:
            status_col = df.columns[40]
            logging.info(f"Usando coluna Status por posição [40]: '{status_col}'")
        elif len(df.columns) > 39:
            status_col = df.columns[39]
            logging.info(f"Usando coluna Status por posição [39]: '{status_col}'")
    
    if not ade_col or not status_col:
        logging.warning(f"Colunas não encontradas - ADE: {ade_col}, Status: {status_col}")
        # Tentar busca flexível
        for idx, col in enumerate(df.columns):
            col_lower = str(col).lower()
            if not ade_col and ('ade' in col_lower or 'proposta' in col_lower):
                ade_col = col
            if not status_col and ('status' in col_lower or 'situacao' in col_lower):
                status_col = col
    
    processed_count = 0
    pago_cancelado_count = 0
    
    for _, row in df.iterrows():
        try:
            # Extrair ADE
            ade_value = str(row[ade_col]).strip() if ade_col else ""
            
            # Extrair Status
            status_value = str(row[status_col]).strip().lower() if status_col else ""
            
            # Limpar e validar ADE
            if ade_value and ade_value not in ['nan', 'NaN', '', 'ADE']:
                # Manter apenas números
                ade_clean = ''.join(c for c in ade_value if c.isdigit())
                
                if ade_clean and len(ade_clean) >= 6:  # ADEs têm pelo menos 6 dígitos
                    # Normalizar status
                    normalized_status = STATUS_MAPPING.get(status_value, status_value.upper())
                    
                    storm_proposals[ade_clean] = normalized_status
                    processed_count += 1
                    
                    # Contar quantos estão PAGO/CANCELADO para estatística
                    if normalized_status in ['PAGO', 'CANCELADO']:
                        pago_cancelado_count += 1
                    
                    if processed_count <= 5:  # Log apenas os primeiros 5 para debug
                        logging.info(f"Proposta Storm: ADE={ade_clean} Status={normalized_status}")
                        
        except Exception as e:
            logging.error(f"Erro ao processar linha da Storm: {e}")
            continue
    
    logging.info(f"Storm processada: {processed_count} propostas válidas")
    logging.info(f"Propostas PAGO/CANCELADO (serão filtradas): {pago_cancelado_count}")
    logging.info(f"Propostas disponíveis para processamento: {processed_count - pago_cancelado_count}")
    
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
        
        # Normalizar tabela (UPPER para matching consistente com chaves do CSV)
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
        
            # Log básico para VCTEX
            if bank_normalized == "BANCO VCTEX":
                print(f"🔍 VCTEX: BANCO={bank_normalized} | ORGAO={organ_normalized} | OPERACAO={operation_normalized} | TABELA={tabela_normalized}")
                logging.warning(f"🔍 VCTEX: BANCO={bank_normalized} | ORGAO={organ_normalized} | OPERACAO={operation_normalized} | TABELA={tabela_normalized}")
        
        logging.info(f"🔍 Buscando mapeamento: BANCO={bank_normalized} | ORGAO={organ_normalized} | OPERACAO={operation_normalized} | TABELA={tabela_normalized}")
        
        # PRIORIDADE 1: Busca EXATA por BANCO + ORGÃO + OPERAÇÃO + TABELA (mais específico e confiável)
        if tabela_normalized:
            best_match = None
            best_match_score = 0
            
            # Log detalhado para AVERBAI e VCTEX
            is_averbai = bank_normalized == "AVERBAI"
            is_vctex = bank_normalized == "BANCO VCTEX"
            if is_averbai:
                logging.info(f"🔎 AVERBAI - Iniciando busca por tabela: '{tabela_normalized}' (len={len(tabela_normalized)})")
            elif is_vctex:
                print(f"🔎 VCTEX: '{tabela_normalized}'")
                logging.warning(f"🔎 VCTEX: '{tabela_normalized}'")
            
            for key, details in TABELA_MAPPING.items():
                parts = key.split('|')
                if len(parts) == 4:
                    key_banco, key_orgao, key_operacao, key_tabela = parts
                    # Normalizar keys removendo espaços extras
                    key_banco_norm = ' '.join(key_banco.upper().split())
                    key_orgao_norm = ' '.join(key_orgao.upper().split())
                    key_operacao_norm = ' '.join(key_operacao.upper().split())
                    key_tabela_norm = ' '.join(key_tabela.upper().split())
                    
                    # Debug para VCTEX
                    if is_vctex and 'VCTEX' in key:
                        print(f"🔎🔥 VCTEX - Testando chave: '{key}'")
                        print(f"   🔥 Key Tabela: '{key_tabela_norm}' vs Busca: '{tabela_normalized}'")
                        logging.warning(f"🔎🔥 VCTEX - Testando chave: '{key}'")
                        logging.warning(f"   🔥 Key Tabela: '{key_tabela_norm}' vs Busca: '{tabela_normalized}'")
                    
                    # Busca EXATA para banco
                    if bank_normalized != key_banco_norm:
                        if is_vctex and 'VCTEX' in key:
                            print(f"   ❌🔥 BANCO não match: '{bank_normalized}' != '{key_banco_norm}'")
                            logging.warning(f"   ❌🔥 BANCO não match: '{bank_normalized}' != '{key_banco_norm}'")
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
                    
                    # 🔢 PRIORIDADE MÁXIMA: Match exato de CÓDIGO NUMÉRICO no início
                    # Ex: busca "61700" deve bater EXATO em "61700 - CLT..." e não em "60763 - CLT..."
                    if tabela_normalized.isdigit() and key_tabela_norm.startswith(tabela_normalized + ' '):
                        match_score = 10  # Match de código exato (MÁXIMA PRIORIDADE)
                    elif tabela_normalized == key_tabela_norm:
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
    
    logging.info(f"=" * 100)
    logging.info(f"🔧 INICIANDO normalize_bank_data para {bank_type} com {len(df)} registros")
    logging.info(f"   Colunas disponíveis: {list(df.columns)}")
    
    # Debug específico para PAULISTA
    if bank_type == "PAULISTA":
        logging.error(f"🏦 NORMALIZE_BANK_DATA: PAULISTA com {len(df)} linhas")
        for i in range(min(3, len(df))):
            row_data = df.iloc[i].to_dict()
            logging.error(f"   Linha {i}: Unnamed:0='{row_data.get('Unnamed: 0', 'N/A')}'")
    
    logging.info(f"=" * 100)
    
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
    
    # 🧹 LIMPEZA DE CARACTERES ESPECIAIS: Aplicar em todas as colunas de texto
    logging.info(f"🧹 {bank_type}: Iniciando limpeza de caracteres especiais...")
    text_columns_cleaned = 0
    
    for column in df.columns:
        if df[column].dtype == 'object':  # Colunas de texto
            original_values = df[column].astype(str)
            df[column] = df[column].astype(str).apply(clean_special_characters)
            
            # Contar quantas células foram alteradas
            changes_count = sum(1 for old, new in zip(original_values, df[column]) if old != new)
            if changes_count > 0:
                text_columns_cleaned += 1
                logging.info(f"🧹 {bank_type}: Coluna '{column}' - {changes_count} células limpas")
    
    if text_columns_cleaned > 0:
        logging.info(f"🧹 {bank_type}: Limpeza concluída - {text_columns_cleaned} colunas processadas")
    else:
        logging.info(f"🧹 {bank_type}: Nenhum caractere especial problemático encontrado")
    

    logging.info(f"✅ DataFrame passou validações - {len(df)} registros, {len(df.columns)} colunas")
    
    logging.info(f"Após limpeza: {len(df)} registros válidos com {len(df.columns)} colunas")
    
    for idx, row in df.iterrows():
        logging.info(f"🔍 PROCESSANDO linha {idx}: {dict(row)}")
        
        # Pular linhas que são claramente cabeçalhos ou metadados
        row_str = ' '.join([str(val).lower() for val in row.values if pd.notna(val)])
        
        # DEBUG: Log para PAULISTA mostrando a row_str construída
        if bank_type == "PAULISTA":
            logging.info(f"🔍 PAULISTA linha {idx}: row_str = '{row_str[:100]}...'")
        
        # ✅ MELHORADO: Detectar linhas de metadados/cabeçalho com mais precisão
        metadata_indicators = [
            'relatório', 'relatorio', 'total de registros', 'total:', 'página',
            'data de emissão', 'data de extração', 'banco:', 'período',
            'nome do banco', 'agencia:', 'conta:', 'saldo:'
        ]
        
        # Detectar linhas de cabeçalho específicas do BANCO PAULISTA
        paulista_header_indicators = [
            'nº proposta', 'numero proposta', 'data captura', 'banco paulista',
            'cpf/cnpj proponente', 'nome do proponente', 'valor solicitado',
            'quant. parcelas', 'usuário digitador', 'usuario digitador',
            'relação de propostas', 'analítico', 'relatório', 'relatorio'
        ]
        
        # ✅ CORREÇÃO: Não pular linhas que podem ter dados válidos
        # Verificar se é REALMENTE cabeçalho (ter múltiplos indicadores OU ser linha muito curta)
        header_matches = sum(1 for indicator in metadata_indicators + paulista_header_indicators if indicator in row_str)
        is_likely_data = len([val for val in row.values if pd.notna(val) and str(val).strip()]) >= 3  # Pelo menos 3 campos preenchidos
        
        # É cabeçalho se: tem múltiplos indicadores OU poucos campos preenchidos com palavras de cabeçalho
        is_header = (header_matches >= 2) or (header_matches >= 1 and not is_likely_data)
        
        if bank_type == "PAULISTA":
            # Log bem detalhado para PAULISTA
            primeira_col = row.get('Unnamed: 0', '')
            logging.error(f"🔍 PAULISTA linha {idx}: Primeira coluna = '{primeira_col}'")
            logging.error(f"🔍 PAULISTA linha {idx}: row_str = '{row_str[:50]}...'")
            logging.error(f"🔍 PAULISTA linha {idx}: É cabeçalho? {is_header}")
            if is_header:
                matched_indicators = [ind for ind in metadata_indicators + paulista_header_indicators if ind in row_str]
                logging.error(f"📋 PAULISTA: Indicadores encontrados: {matched_indicators}")
        
        if is_header:
            if bank_type == "PAULISTA":
                logging.error(f"📋 PAULISTA: Pulando linha de cabeçalho: {row_str[:50]}...")
            else:
                logging.debug(f"Pulando linha de cabeçalho/metadados: {row_str[:100]}")
            continue
        else:
            # Esta linha NÃO é cabeçalho - vai processar
            if bank_type == "PAULISTA":
                logging.error(f"✅ PAULISTA linha {idx}: VAI PROCESSAR - Primeira coluna: '{row.get('Unnamed: 0', '')}')")
        
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
            
            # � FUNÇÃO para formatar CPF no padrão brasileiro
            def format_cpf(cpf_str):
                """Formata CPF para o padrão 000.000.000-00"""
                if not cpf_str:
                    return ""
                
                # Remover tudo que não é número
                cpf_numbers = ''.join(filter(str.isdigit, str(cpf_str)))
                
                # Verificar se tem 11 dígitos
                if len(cpf_numbers) != 11:
                    logging.warning(f"⚠️ CPF inválido (não tem 11 dígitos): '{cpf_str}' -> '{cpf_numbers}'")
                    return cpf_str  # Retornar original se inválido
                
                # Formatar: 000.000.000-00
                cpf_formatted = f"{cpf_numbers[0:3]}.{cpf_numbers[3:6]}.{cpf_numbers[6:9]}-{cpf_numbers[9:11]}"
                return cpf_formatted
            
            # Formatar CPF
            cpf_cliente = format_cpf(cpf_cliente)
            
            # �💰 FUNÇÃO para formatar valores no padrão brasileiro
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
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal
            contact_data = extract_contact_data(row, "AVERBAI")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"],
                "ENDERECO": contact_data["ENDERECO"],
                "BAIRRO": contact_data["BAIRRO"],
                "CEP": contact_data["CEP"],
                "UF": contact_data["UF"]
            })
            
            # Continuar com os outros campos
            normalized_row.update({
                "VALOR_PARCELAS": valor_parcela_br,  # 💰 FORMATO BRASILEIRO
                "CODIGO_TABELA": codigo_tabela_direto,  # 🎯 CÓDIGO DIRETO DO ARQUIVO!
                "TAXA": taxa_formatada,  # 📊 TAXA ORGANIZADA CONFORME TABELA
                "OBSERVACOES": ""  # AVERBAI não deve ter observações - somente VCTEX
            })
            
        elif bank_type == "DIGIO":
            # Mapeamento BANCO DIGIO S.A. - Suporte para duas estruturas:
            # 1. Estrutura com colunas Unnamed (arquivo XLS original do banco)
            # 2. Estrutura com cabeçalhos nomeados (arquivo CSV exportado)
            
            # Verificar se é estrutura com Unnamed ou com cabeçalhos nomeados
            # Checar se a maioria das colunas são Unnamed
            unnamed_count = sum(1 for col in row.index if 'unnamed:' in str(col).lower())
            total_count = len(row.index)
            has_unnamed_structure = unnamed_count > (total_count * 0.5)  # Mais de 50% Unnamed
            
            logging.info(f"🔍 DIGIO estrutura: {unnamed_count} Unnamed de {total_count} colunas ({unnamed_count/total_count*100:.1f}%)")
            
            # 🔍 DIGIO: Se tem 100+ colunas Unnamed, aceitar - é a estrutura normal
            if unnamed_count == total_count and total_count >= 100:
                logging.info(f"✅ DIGIO: Estrutura normal detectada - {total_count} colunas Unnamed")
            
            if not has_unnamed_structure:
                # Estrutura com cabeçalhos nomeados (CSV exportado do banco)
                logging.info("🔍 DIGIO: Detectada estrutura CSV com cabeçalhos nomeados")
                
                # Mapeamento baseado na estrutura real do CSV DIGIO
                proposta = str(row.get('PROPOSTA', '')).strip()
                tipo_operacao = str(row.get('TIPO_OPERACAO', '')).strip()
                data_cadastro = str(row.get('DATA_CADASTRO', '')).strip()
                situacao = str(row.get('SITUACAO_PROPOSTA', '')).strip()
                data_lancamento = str(row.get('DATA_LANCAMENTO', '')).strip()
                nome_orgao_raw = str(row.get('NOME_ORGAO', '')).strip()
                usuario_digitador_raw = str(row.get('DESCR_USU_DIGITADOR', '')).strip()
                cpf_cliente = str(row.get('CPF_CLIENTE', '')).strip()
                
                # 🔍 DIGIO: Pular linhas de cabeçalho (identificar pelo conteúdo)
                row_values = ' '.join([str(val) for val in row.values if pd.notna(val)]).upper()
                if ('BANCO DIGIO' in row_values or 'RELATÓRIO' in row_values or 'RELATORIO' in row_values or
                    'PROPOSTAS CADASTRADAS' in row_values or 'PROC.:' in row_values or
                    proposta == 'PROPOSTA' or  # Header da tabela
                    not proposta or proposta.upper() in ['PROPOSTA', 'NAN']):
                    logging.info(f"⏭️ DIGIO: Pulando linha de cabeçalho - Conteúdo: {row_values[:100]}")
                    continue
                
                # ✅ DIGIO: Validar se proposta é número válido 
                if (not proposta or not proposta.replace('.', '').isdigit()):
                    logging.debug(f"⏭️ DIGIO: Pulando linha - proposta inválida: '{proposta}'")
                    continue
                
                logging.info(f"✅ DIGIO: Proposta válida encontrada: {proposta}")
                
                # 🔧 DIGIO: Extrair campos da estrutura CSV real
                usuario_digitador = usuario_digitador_raw if usuario_digitador_raw else ""
                nome_cliente = str(row.get('NOMECLI', '')).strip()
                data_nascimento = str(row.get('DATA_NASCIMENTO', '')).strip()
                qtd_parcelas = str(row.get('QTD_PARCELAS', '')).strip()
                vlr_parcela = str(row.get('VALOR_PARCELA', '')).strip()
                vlr_financiado = str(row.get('VLR FINANCIADO', '')).strip()
                vlr_lib1 = str(row.get('VLR_LIB1', '')).strip()
                
                # Código e nome de convênio
                cod_convenio = str(row.get('COD_CONVENIO', '')).strip()
                nome_convenio = str(row.get('NOME_CONVENIO', '')).strip()
                
                nome_tabela_para_busca = cod_convenio
                
            else:
                # Estrutura com Unnamed (XLS original do banco)
                logging.info("🔍 DIGIO: Detectada estrutura com colunas Unnamed (XLS original)")
                proposta = str(row.get('Unnamed: 3', '')).strip()
                tipo_operacao = str(row.get('Unnamed: 4', '')).strip()
                data_cadastro = str(row.get('Unnamed: 8', '')).strip()
                situacao = str(row.get('Unnamed: 9', '')).strip()
                data_lancamento = str(row.get('Unnamed: 13', '')).strip()
                nome_orgao_raw = str(row.get('Unnamed: 25', '')).strip()
                usuario_digitador_raw = str(row.get('Unnamed: 29', '')).strip()
                cpf_cliente = str(row.get('Unnamed: 31', '')).strip()
                
                # 🔍 DIGIO: Pular linhas de cabeçalho baseado no MAP
                # Verificar se tem "BANCO DIGIO", "RELATÓRIO", "PROPOSTA" (como header), etc.
                row_values = ' '.join([str(val) for val in row.values if pd.notna(val)]).upper()
                
                # Linha é cabeçalho se:
                # 1. Contém "BANCO DIGIO", "RELATÓRIO" 
                # 2. Proposta = "PROPOSTA" (header da tabela de dados)
                # 3. Campos são nomes de colunas
                if ('BANCO DIGIO' in row_values or 'RELATÓRIO' in row_values or 'RELATORIO' in row_values or
                    proposta == 'PROPOSTA' or  # Header da tabela de dados
                    usuario_digitador_raw in ['DESCR_USU_DIGITADOR'] or
                    cpf_cliente in ['CPF_CLIENTE'] or
                    nome_orgao_raw in ['NOME_ORGAO']):
                    logging.info(f"⏭️ DIGIO: Pulando linha de cabeçalho detectada - Proposta='{proposta}', Conteúdo: {row_values[:100]}...")
                    continue
                
                # ✅ DIGIO: Validar se proposta é número válido (estrutura Unnamed)
                proposta_str = str(proposta).strip()
                if (not proposta_str or proposta_str.lower() in ['nan', 'none', ''] or 
                    not proposta_str.replace('.', '').isdigit()):
                    logging.debug(f"⏭️ DIGIO: Pulando linha - proposta inválida: '{proposta}' (não é número)")
                    continue
                
                logging.info(f"✅ DIGIO: Proposta válida encontrada: {proposta}")
                
                # 🔧 DIGIO: Manter underscore do usuário digitador no formato original
                # Exemplo: "02579846158_202902" (manter como está)
                usuario_digitador = usuario_digitador_raw if usuario_digitador_raw else ""
                nome_cliente = str(row.get('Unnamed: 32', '')).strip()
                data_nascimento = str(row.get('Unnamed: 33', '')).strip()
                qtd_parcelas = str(row.get('Unnamed: 48', '')).strip()
                vlr_parcela = str(row.get('Unnamed: 49', '')).strip()
                vlr_financiado = str(row.get('Unnamed: 50', '')).strip()
                
                # DIGIO: Extrair códigos e nomes de convênio (Unnamed: 53 e 54)
                cod_convenio = str(row.get('Unnamed: 53', '')).strip()  # Ex: 002035, 001717
                nome_convenio = str(row.get('Unnamed: 54', '')).strip()  # Ex: "PORT+REFIN VINCULADO-1-96X-1,39 A 1,85-T"
                
                vlr_lib1 = str(row.get('Unnamed: 59', '')).strip()
                
                # DIGIO: Manter COD_CONVENIO original (ex: 002035 mantém como 002035)
                # NÃO remover zeros à esquerda - usar código exato do arquivo
                # cod_convenio já está correto como string original
                
                nome_tabela_para_busca = nome_convenio if nome_convenio else cod_convenio
            
            # Log para debug do DIGIO - EXPANDIDO
            logging.info(f"🔍 DIGIO campos principais: Proposta='{proposta}', TipoOp='{tipo_operacao}', Orgao='{nome_orgao_raw}'")
            logging.info(f"🔍 DIGIO tabela: COD_CONVENIO='{cod_convenio}' | NOME_CONVENIO='{nome_convenio}'")
            logging.info(f"🔍 DIGIO valores: QtdParc={qtd_parcelas}, VlrFinanc={vlr_financiado}, VlrLib={vlr_lib1}")
            logging.info(f"🔍 DIGIO cliente: CPF='{cpf_cliente}', Nome='{nome_cliente}', Usuario='{usuario_digitador}'")
            logging.info(f"🔍 DIGIO estrutura: has_unnamed={has_unnamed_structure}, unnamed_count={unnamed_count}/{total_count}")
            
            # ✅ DIGIO: Validações mínimas para prosseguir com o processamento
            if not proposta or len(str(proposta).strip()) == 0:
                logging.error(f"❌ DIGIO: Proposta vazia ou inválida - pulando linha")
                continue
                
            # Log final antes de prosseguir
            logging.info(f"✅ DIGIO: Linha válida encontrada - prosseguindo com processamento")

            
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
                elif 'AGUDOS' in empregador_upper:
                    return 'PREF AGUDOS - S'
                elif 'JABOTICABA' in empregador_upper:
                    return 'PREF JABOTICABA'
                elif 'SERTAOZINHO' in empregador_upper or 'SERTAOZINH' in empregador_upper:
                    return 'PREF SERTAOZINHO - SP'
                elif 'PREFEITURA DE B' in orgao_upper:
                    return 'PREF BAURU SP'  # B = BAURU
                elif 'PREFEITURA DE L' in orgao_upper:
                    return 'PREF LINS - SP'  # L = LINS
                elif 'PREFEITURA DE S' in orgao_upper:
                    return 'PREF SERTAOZINHO - SP'  # S = SERTAOZINHO
                elif 'PREFEITURA DE A' in orgao_upper:
                    return 'PREF AGUDOS - S'  # A = AGUDOS
                elif 'PREF' in empregador_upper or 'PREFEITURA' in orgao_upper:
                    # Prefeitura genérica - usar formato do empregador
                    return empregador_upper if empregador_upper else orgao_upper.replace('PREFEITURA', 'PREF').strip()
                
                # Default: INSS
                return 'INSS'
            
            # Se tem estrutura nomeada, usar o campo ORGAO diretamente, senão detectar
            if not has_unnamed_structure:
                # Já temos o órgão normalizado no CSV
                nome_orgao = nome_orgao_raw if nome_orgao_raw else 'INSS'
            else:
                # Detectar órgão a partir dos campos Unnamed
                nome_empregador = str(row.get('Unnamed: 23', '')).strip()
                cod_empregador = str(row.get('Unnamed: 17', '')).strip()
                nome_orgao = detect_digio_organ(nome_orgao_raw, nome_empregador, cod_empregador)
            
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
                elif any(x in combined_text for x in ['PORT+REFIN', 'PORTABILIDADE + REFIN', 'PORT REFIN']):
                    return "Portabilidade + Refin"
                
                # Prioridade 2.5: Portabilidade simples
                elif 'PORTABILIDADE' in combined_text and 'REFIN' not in combined_text:
                    return "Portabilidade"
                
                # Prioridade 3: Refinanciamento simples
                elif 'REFIN' in combined_text and 'PORT' not in combined_text:
                    return "Refinanciamento"
                
                # Prioridade 4: Margem Livre (mais comum)
                else:
                    return "Margem Livre (Novo)"
            
            # ✅ CORRIGIDO: Se estrutura nomeada, usar TIPO DE OPERACAO do arquivo diretamente
            if not has_unnamed_structure:
                # Arquivo já processado tem tipo correto
                tipo_operacao_norm = tipo_operacao if tipo_operacao else "Margem Livre (Novo)"
                logging.info(f"✅ DIGIO usando tipo de operação do arquivo: '{tipo_operacao_norm}'")
            else:
                # Estrutura XLS original - detectar tipo
                tipo_operacao_norm = detect_digio_operation(tipo_operacao, nome_convenio)
                logging.info(f"🔍 DIGIO tipo detectado: '{tipo_operacao_norm}'")
                
            # 📞 DIGIO: Extrair dados de contato e endereço (se disponível)
            telefone = ""
            if not has_unnamed_structure:
                # Estrutura CSV nomeada
                tel_cliente = str(row.get('TEL_CLIENTE', '')).strip()
                cel_cliente = str(row.get('CEL_CLIENTE', '')).strip()
                telefone = cel_cliente if cel_cliente else tel_cliente
                
                endereco = str(row.get('END_CLIENTE', '')).strip()
                num_endereco = str(row.get('NUM_END_CLIENTE', '')).strip()
                complemento = str(row.get('COMPLEMENTO', '')).strip()
                endereco_completo = f"{endereco}, {num_endereco}".strip(", ")
                if complemento:
                    endereco_completo += f", {complemento}"
                
                bairro = str(row.get('BAIRRO', '')).strip()
                cep = str(row.get('CEP_CLIENTE', '')).strip()
                uf = str(row.get('UF_CLIENTE', '')).strip()
            else:
                # Estrutura XLS com Unnamed (baseado no MAP)
                tel_cliente = str(row.get('Unnamed: 42', '')).strip()  # TEL_CLIENTE
                cel_cliente = str(row.get('Unnamed: 43', '')).strip()  # CEL_CLIENTE
                telefone = cel_cliente if cel_cliente else tel_cliente
                
                endereco = str(row.get('Unnamed: 37', '')).strip()  # END_CLIENTE
                num_endereco = str(row.get('Unnamed: 38', '')).strip()  # NUM_END_CLIENTE
                complemento = str(row.get('Unnamed: 39', '')).strip()  # COMPLEMENTO
                endereco_completo = f"{endereco}, {num_endereco}".strip(", ")
                if complemento and complemento not in ['nan', '']:
                    endereco_completo += f", {complemento}"
                
                bairro = str(row.get('Unnamed: 40', '')).strip()  # BAIRRO
                cep = str(row.get('Unnamed: 42', '')).strip()  # CEP_CLIENTE  
                uf = str(row.get('Unnamed: 41', '')).strip()  # UF_CLIENTE
            
            # 📞📍 DIGIO: Log dos dados de contato para debug
            logging.info(f"📞 DIGIO contato: telefone='{telefone}', endereco='{endereco_completo.strip(', ')}', bairro='{bairro}', cep='{cep}', uf='{uf}'")
            
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
                "CODIGO_TABELA": cod_convenio,  # ✅ DIGIO: Usar COD_CONVENIO direto (5076, 5077, 1720, etc)
                "TAXA": "",  # Taxa deve vir do arquivo ou ser buscada depois
                "OBSERVACOES": ""  # DIGIO não deve ter observações - somente VCTEX
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal (substituir lógica manual)
            contact_data = extract_contact_data(row, "DIGIO")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"] if contact_data["TELEFONE"] else clean_contact_field(telefone, "TELEFONE"),
                "ENDERECO": contact_data["ENDERECO"] if contact_data["ENDERECO"] else clean_contact_field(endereco_completo.strip(", "), "ENDERECO"),
                "BAIRRO": contact_data["BAIRRO"] if contact_data["BAIRRO"] else clean_contact_field(bairro, "BAIRRO"),
                "CEP": contact_data["CEP"] if contact_data["CEP"] else clean_contact_field(cep, "CEP"),
                "UF": contact_data["UF"] if contact_data["UF"] else clean_contact_field(uf, "UF")
            })
            
            # ✅ DIGIO: NÃO aplicar mapeamento! 
            # O arquivo DIGIO já vem com códigos corretos (5076, 5077, 1720, 2055, etc)
            # Diferente de VCTEX que precisa converter "Tabela EXP" → "TabelaEXP"
            logging.info(f"✅ DIGIO FINAL: Proposta={proposta} | Código='{cod_convenio}' | Órgão='{normalized_row['ORGAO']}' | Operação='{normalized_row['TIPO_OPERACAO']}'")
            logging.info(f"   └─ Usando código direto do arquivo (SEM mapeamento)")
            
            
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
                "OBSERVACOES": ""  # PRATA não deve ter observações - somente VCTEX
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal
            contact_data = extract_contact_data(row, "PRATA")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"],
                "ENDERECO": contact_data["ENDERECO"],
                "BAIRRO": contact_data["BAIRRO"],
                "CEP": contact_data["CEP"],
                "UF": contact_data["UF"]
            })
            
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
            
            # 🎯 VCTEX: Normalizar nome da tabela para fazer matching correto no relat_orgaos.csv
            # O relat_orgaos.csv tem: "TABELA BANCO" (ex: "Tabela Exponencial") → "CODIGO TABELA STORM" (ex: "TabelaExponencial")
            # Normalizar tabela_raw para garantir prefixo "Tabela" quando necessário
            def normalize_vctex_table_name(table_name):
                """Normaliza nome da tabela VCTEX para matching no mapeamento
                REGRAS:
                - "Tabela EXP" → "TabelaEXP"  
                - "Tabela Exponencial" → "TabelaExponencial"
                - "EXP" → "TabelaEXP"
                - "Exponencial" → "TabelaExponencial"
                """
                if not table_name:
                    return ""
                
                table_clean = str(table_name).strip()
                
                # 🎯 CASOS ESPECÍFICOS COMPLETOS (com "Tabela" no nome)
                # EXP e Exponencial são DIFERENTES!
                if table_clean.upper() == "TABELA EXP":
                    logging.info(f"🔧 VCTEX: 'Tabela EXP' → 'TabelaEXP' (EXP é diferente de Exponencial)")
                    return "TabelaEXP"
                elif table_clean.upper() == "TABELA EXPONENCIAL":
                    logging.info(f"🔧 VCTEX: 'Tabela Exponencial' → 'TabelaExponencial' (Exponencial é diferente de EXP)")
                    return "TabelaExponencial"
                elif table_clean.upper() == "TABELA LINEAR":
                    return "TabelaLinear"
                elif table_clean.upper() == "TABELA VCT":
                    return "TabelaVCT"
                elif table_clean.upper() == "TABELA RELAX":
                    return "TabelaRelax"
                elif table_clean.upper() == "TABELA VAMO":
                    return "TabelaVamo"
                
                # Se já começa com "Tabela" e não foi tratado acima, manter como está
                if table_clean.startswith("Tabela"):
                    return table_clean
                
                # 🎯 CASOS SEM PREFIXO "Tabela"
                table_upper = table_clean.upper()
                
                # EXP e Exponencial são DIFERENTES - tratar separadamente
                if table_upper == "EXP":
                    logging.info(f"🔧 VCTEX: 'EXP' → 'TabelaEXP' (mantém EXP, não confundir com Exponencial)")
                    return "TabelaEXP"
                elif table_upper == "EXPONENCIAL":
                    logging.info(f"🔧 VCTEX: 'Exponencial' → 'TabelaExponencial' (mantém Exponencial, não confundir com EXP)")
                    return "TabelaExponencial"
                
                # Outros casos específicos
                elif table_upper == "VCT":
                    return "TabelaVCT"
                elif table_upper == "RELAX":
                    return "TabelaRelax" 
                elif table_upper == "VAMO":
                    return "TabelaVamo"
                elif table_upper == "LINEAR":
                    return "TabelaLinear"
                elif table_upper in ["DIFERENCIADA", "ESPECIAL", "PADRÃO", "PADRAO"]:
                    return f"Tabela{table_clean}"
                
                # Para outros casos, adicionar prefixo Tabela mantendo nome original
                normalized = f"Tabela{table_clean}"
                logging.info(f"🔧 VCTEX: Tabela genérica '{table_clean}' → '{normalized}'")
                return normalized
            
            tabela_normalized = normalize_vctex_table_name(tabela_raw)
            logging.info(f"📋 VCTEX: Tabela original: '{tabela_raw}' → Normalizada: '{tabela_normalized}' (será usada para buscar CODIGO TABELA STORM no CSV)")
            logging.info(f"🔍 VCTEX DEBUG: tabela_raw='{tabela_raw}' | tabela_normalized='{tabela_normalized}' | EXP≠Exponencial")
            
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
            logging.info(f"📅 VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: DATAS ORIGINAIS DO ARQUIVO")
            logging.info(f"   ✅ DATA_CADASTRO_FINAL: '{data_cadastro_vctex}'")
            logging.info(f"   ✅ DATA_PAGAMENTO_FINAL: '{data_pagamento_vctex}'")
            logging.info(f"   🏦 BANCO: VCTEX | ÓRGÃO: {orgao_vctex} | TAXA: {taxa_raw}")
            
            # 💰 VCTEX: Formatação de valores no padrão brasileiro (1.234,56)
            def format_vctex_value(value_str):
                """Formata valores do VCTEX no padrão brasileiro com ponto e vírgula"""
                if not value_str or str(value_str).strip() in ['', 'nan', 'NaN', 'None', '0']:
                    return "0,00"
                
                try:
                    # Limpar o valor (remover R$, espaços, etc.)
                    clean_value = str(value_str).strip().replace('R$', '').replace(' ', '')
                    
                    # Se já está no formato brasileiro, verificar se está correto
                    if ',' in clean_value:
                        # Formato brasileiro: 1.234,56 ou 87,58
                        parts = clean_value.split(',')
                        if len(parts) == 2 and len(parts[1]) == 2:
                            # Já está formatado corretamente
                            return clean_value
                        else:
                            # Tem vírgula mas não está formatado corretamente
                            # Converter para ponto e processar
                            clean_value = clean_value.replace('.', '').replace(',', '.')
                    
                    # Converter para float
                    value_float = float(clean_value)
                    
                    # Formatar no padrão brasileiro
                    if value_float >= 1000:
                        # Valores >= 1000: usar ponto como separador de milhar
                        # Ex: 1.234,56
                        formatted = f"{value_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        # Valores < 1000: só vírgula decimal
                        # Ex: 87,58
                        formatted = f"{value_float:.2f}".replace('.', ',')
                    
                    return formatted
                    
                except (ValueError, TypeError) as e:
                    logging.warning(f"⚠️ VCTEX: Erro ao formatar valor '{value_str}': {e}")
                    return str(value_str)  # Retornar original se houver erro
            
            # Formatar valores antes de adicionar ao normalized_row
            valor_operacao_raw = str(row.get('Valor da operacao', str(row.get('Valor Liberado', '')))).strip()
            valor_liberado_raw = str(row.get('Valor Liberado', '')).strip()
            valor_parcela_raw = str(row.get('Parcela', row.get('Valor parcela', ''))).strip()
            
            valor_operacao_formatado = format_vctex_value(valor_operacao_raw)
            valor_liberado_formatado = format_vctex_value(valor_liberado_raw)
            valor_parcela_formatado = format_vctex_value(valor_parcela_raw)
            
            logging.info(f"💰 VCTEX Proposta {row.get('Número do Contrato', 'N/A')}: Valores formatados - OP: {valor_operacao_formatado}, LIB: {valor_liberado_formatado}, PARC: {valor_parcela_formatado}")
            
            normalized_row = {
                "PROPOSTA": str(row.get('Número do Contrato', row.get('Identificacao da operacao', ''))).strip(),
                "DATA_CADASTRO": data_cadastro_vctex,
                "BANCO": "BANCO VCTEX",
                "ORGAO": orgao_vctex,
                "TIPO_OPERACAO": "Margem Livre (Novo)",  # VCTEX normalmente só tem esse tipo
                "NUMERO_PARCELAS": numero_parcelas_vctex,
                "VALOR_OPERACAO": valor_operacao_formatado,  # 💰 FORMATADO
                "VALOR_LIBERADO": valor_liberado_formatado,  # 💰 FORMATADO
                "USUARIO_BANCO": str(row.get('Usuário (acesso login)', row.get('CPF Usuario', ''))).strip(),
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": data_pagamento_vctex,
                "CPF": str(row.get('CPF', '')).strip(),
                "NOME": str(row.get('Nome do Cliente', row.get('Nome', ''))).strip(),
                "DATA_NASCIMENTO": str(row.get('Data de nascimento', '')).strip() if 'Data de nascimento' in df.columns else "",

                "VALOR_PARCELAS": valor_parcela_formatado,  # 💰 FORMATADO
                "CODIGO_TABELA": tabela_normalized,  # Nome NORMALIZADO da tabela (usado para buscar no dicionário)
                "TAXA": taxa_raw,  # Taxa do arquivo (mas será substituída pelo mapeamento se encontrar)
                "OBSERVACOES": str(row.get('Observação', row.get('Observações', row.get('Observacoes', row.get('Obs', ''))))).strip()  # Campo observações do VCTEX
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal
            contact_data = extract_contact_data(row, "VCTEX")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"],
                "ENDERECO": contact_data["ENDERECO"],
                "BAIRRO": contact_data["BAIRRO"],
                "CEP": contact_data["CEP"],
                "UF": contact_data["UF"]
            })
            
        elif bank_type == "DAYCOVAL":
            # 🔧 DAYCOVAL - Detectar formato (CSV correto vs Unnamed)
            
            # Verificar se já está no formato CSV correto
            has_correct_columns = any(col in ['PROPOSTA', 'DATA CADASTRO', 'BANCO', 'ORGAO'] for col in row.keys())
            
            if has_correct_columns:
                # ✅ FORMATO CSV CORRETO - Mapear diretamente
                logging.info(f"✅ DAYCOVAL linha {idx}: FORMATO CSV CORRETO DETECTADO")
                
                normalized_row = {
                    "PROPOSTA": str(row.get('PROPOSTA', '')).strip(),
                    "ADE": str(row.get('PROPOSTA', '')).strip(),  # ADE = mesma proposta
                    "DATA_CADASTRO": fix_daycoval_date(str(row.get('DATA CADASTRO', '')).strip(), "DATA_CADASTRO"),
                    "BANCO": "BANCO DAYCOVAL",
                    "ORGAO": clean_special_characters(str(row.get('ORGAO', '')).strip()),
                    "TIPO_OPERACAO": clean_special_characters(str(row.get('TIPO DE OPERACAO', '')).strip()),
                    "NUMERO_PARCELAS": str(row.get('NUMERO PARCELAS', '')).strip(),
                    "VALOR_OPERACAO": str(row.get('VALOR OPERACAO', '')).strip(),
                    "VALOR_LIBERADO": str(row.get('VALOR LIBERADO', '')).strip(),
                    "USUARIO_BANCO": str(row.get('USUARIO BANCO', '')).strip(),
                    "SITUACAO": str(row.get('SITUACAO', '')).strip(),
                    "DATA_PAGAMENTO": fix_daycoval_date(str(row.get('DATA DE PAGAMENTO', '')).strip(), "DATA_PAGAMENTO"),
                    "CPF": str(row.get('CPF', '')).strip(),
                    "NOME": str(row.get('NOME', '')).strip().upper(),
                    "DATA_NASCIMENTO": str(row.get('DATA DE NASCIMENTO', '')).strip(),
                    "TELEFONE": "",  # DAYCOVAL não possui campos de contato
                    "ENDERECO": "",  # DAYCOVAL não possui campos de contato
                    "BAIRRO": "",   # DAYCOVAL não possui campos de contato
                    "CEP": "",      # DAYCOVAL não possui campos de contato
                    "UF": str(row.get('UF', '')).strip(),
                    "CODIGO_TABELA": str(row.get('CODIGO TABELA', '')).strip(),
                    "VALOR_PARCELAS": str(row.get('VALOR PARCELAS', '')).strip(),
                    "TAXA": str(row.get('TAXA', '')).strip(),
                    "OBSERVACOES": ""  # DAYCOVAL não deve ter observações - somente VCTEX
                }
                
                # ✅ ADICIONAR DADOS DE CONTATO usando função universal (substituir hardcoded)
                contact_data = extract_contact_data(row, "DAYCOVAL")
                normalized_row.update({
                    "TELEFONE": contact_data["TELEFONE"] if contact_data["TELEFONE"] else normalized_row["TELEFONE"],
                    "ENDERECO": contact_data["ENDERECO"] if contact_data["ENDERECO"] else normalized_row["ENDERECO"],
                    "BAIRRO": contact_data["BAIRRO"] if contact_data["BAIRRO"] else normalized_row["BAIRRO"],
                    "CEP": contact_data["CEP"] if contact_data["CEP"] else normalized_row["CEP"],
                    "UF": contact_data["UF"] if contact_data["UF"] else normalized_row["UF"]
                })
                
                logging.info(f"✅ DAYCOVAL CSV: {normalized_row['PROPOSTA']} | {normalized_row['NOME']} | {normalized_row['SITUACAO']}")
                
            else:
                # FORMATO ANTIGO COM "Unnamed:" - PARSER ESPECÍFICO DAYCOVAL MELHORADO
                logging.info(f"=" * 80)
                logging.info(f"DAYCOVAL linha {idx}: FORMATO ANTIGO DETECTADO - USANDO PARSER ESPECÍFICO")
                logging.info(f"   Colunas disponíveis: {list(row.keys())[:10]}")
                logging.info(f"=" * 80)
                
                # ✅ USAR NOVO PARSER ESPECÍFICO DAYCOVAL
                mapped_data = map_daycoval_columns(row)
                
                # Extrair dados mapeados
                proposta_raw = mapped_data['PROPOSTA']
                tipo_operacao_raw = mapped_data['TIPO_OPERACAO']
                cliente_raw = mapped_data['CLIENTE']
                cpf_raw = mapped_data['CPF']
                matricula_raw = mapped_data['MATRICULA']
                data_cadastro_raw = mapped_data['DATA_CADASTRO_RAW']
                data_base_raw = mapped_data['DATA_BASE']
                prazo_meses_raw = mapped_data['PRAZO_MESES']
                taxa_raw = mapped_data['TAXA']
                valor_liquido_raw = mapped_data['VALOR_LIQUIDO']
                valor_operacao_raw = mapped_data['VALOR_OPERACAO']
                valor_parcela_raw = mapped_data['VALOR_PARCELA']
                descricao_empregador_raw = mapped_data['EMPREGADOR']
                situacao_raw = mapped_data['SITUACAO']
                data_liberacao_raw = mapped_data['DATA_PAGAMENTO_RAW']
            
            # Normalizar campos para detecção
            tipo_op = tipo_operacao_raw.upper()
            orgao_descricao = descricao_empregador_raw.upper()
            
            # DEBUG COMPLETO: Mostrar TODAS as colunas disponíveis e seus valores
            logging.error(f"DAYCOVAL DEBUG COMPLETO - Todas as colunas:")
            all_columns = list(row.keys())
            for i, col in enumerate(all_columns[:20]):  # Primeiras 20 colunas
                valor = str(row.get(col, 'N/A'))[:50]  # Limitar valor a 50 caracteres
                logging.error(f"   [{i:2d}] {col}: '{valor}'")
            
            # Logs detalhados para debug
            logging.info(f"DAYCOVAL extraído:")
            logging.info(f"   Proposta: {proposta_raw}")
            logging.info(f"   Tipo Operacao: {tipo_operacao_raw}")
            logging.info(f"   Cliente: {cliente_raw[:30] if cliente_raw else 'N/A'}...")
            logging.info(f"   CPF: {cpf_raw}")
            logging.info(f"   Situacao: {situacao_raw}")
            logging.info(f"   Orgao: {descricao_empregador_raw}")
            logging.info(f"   Valor Operacao: {valor_operacao_raw}")
            logging.info(f"   Data Cadastro Raw: '{data_cadastro_raw}' (Unnamed: 5)")
            logging.info(f"   Data Pagamento Raw: '{data_liberacao_raw}' (Unnamed: 36)")
            logging.info(f"   Data Cadastro RAW: {data_cadastro_raw}")
            logging.info(f"   Data Liberacao RAW: {data_liberacao_raw}")
            
            # Função para detectar órgão do DAYCOVAL
            def detect_daycoval_orgao(descricao_empregador):
                """Detecta órgão baseado na descrição do empregador"""
                desc_upper = descricao_empregador.upper()
                
                if 'INSS' in desc_upper:
                    orgao = "INSS"
                elif 'SPPREV' in desc_upper:
                    orgao = "SPPREV"
                elif 'EDUC' in desc_upper or 'SEC EDU' in desc_upper:
                    orgao = "EDUCACAO"
                elif 'SEFAZ' in desc_upper:
                    orgao = "SEFAZ"
                else:
                    orgao = "INSS"  # Default
                
                # 🚨 APLICAR NORMALIZAÇÃO STORM
                return normalize_storm_organ(orgao)
            
            # Função para detectar operação do DAYCOVAL  
            def detect_daycoval_operacao(tipo_operacao):
                """Detecta tipo de operação baseado no campo Tp. Operação"""
                tipo_upper = tipo_operacao.upper()
                
                if 'PORTABILIDADE' in tipo_upper and 'REFINANCIAMENTO' in tipo_upper:
                    operacao = "Refinanciamento da Portabilidade"
                elif 'PORTABILIDADE' in tipo_upper:
                    operacao = "PORTABILIDADE"  # 🚨 CORREÇÃO: Sem "+ Refin"
                elif 'REFINANCIAMENTO' in tipo_upper:
                    operacao = "Refinanciamento"
                elif 'NOVA' in tipo_upper:
                    operacao = "Margem Livre (Novo)"
                else:
                    operacao = "Margem Livre (Novo)"  # Default
                
                # 🚨 APLICAR NORMALIZAÇÃO STORM
                return normalize_storm_operation(operacao)
            
            # Detectar órgão e operação usando as funções
            orgao_detectado = detect_daycoval_orgao(descricao_empregador_raw)
            operacao_detectada = detect_daycoval_operacao(tipo_operacao_raw)
            
            # Verificar se não são cabeçalhos óbvios (menos restritivo)
            if (proposta_raw.upper() in ['PROPOSTAS CADASTRADAS', 'DETALHADO', 'NR.PROP.'] or
                'PROPOSTAS CADASTRADAS' in proposta_raw.upper()):
                logging.info(f"⏭️ DAYCOVAL linha {idx}: Detectado cabeçalho - pulando")
                normalized_row = None
            else:
                # Aplicar formatação brasileira
                cpf_formatted = format_cpf_global(cpf_raw)
                valor_operacao_formatted = format_value_brazilian(valor_operacao_raw)
                valor_liberado_formatted = format_value_brazilian(valor_liquido_raw)
                valor_parcela_formatted = format_value_brazilian(valor_parcela_raw)
                taxa_formatted = format_percentage_brazilian(taxa_raw)
            
                logging.info(f"✅ DAYCOVAL formatado:")
                logging.info(f"   CPF: {cpf_formatted}")
                logging.info(f"   Valor Operação: {valor_operacao_formatted}")
                logging.info(f"   Valor Liberado: {valor_liberado_formatted}")
                logging.info(f"   Órgão: {orgao_detectado}")
                logging.info(f"   Operação: {operacao_detectada}")
                
                # ✅ SEMPRE CRIAR normalized_row - Deixar validação final decidir
                logging.info(f"✅ DAYCOVAL linha {idx}: Processando proposta {proposta_raw}")
                
                # ✅ VALIDAÇÃO RIGOROSA: NÃO gerar dados falsos se não temos dados reais
                proposta_final = str(proposta_raw).strip() if proposta_raw and str(proposta_raw).strip() not in ['nan', 'None', ''] else ""
                nome_final = str(cliente_raw).strip().upper() if cliente_raw and str(cliente_raw).strip() not in ['nan', 'None', ''] else ""
                cpf_final = cpf_formatted if cpf_formatted and cpf_formatted != "000.000.000-00" else ""
                
                # ✅ CRÍTICO: Se não temos dados mínimos (proposta OU nome OU cpf), PULAR a linha
                # Isso evita gerar "DAYC_1", "NOME NAO INFORMADO", "000.000.000-00"
                if not proposta_final and not nome_final and not cpf_final:
                    logging.info(f"DAYCOVAL linha {idx}: Sem dados minimos (proposta/nome/cpf vazios), pulando para evitar dados falsos")
                    continue
                
                # APLICAR FIX DE DATAS COM LOGS DETALHADOS
                data_cadastro_fixed = fix_daycoval_date(str(data_cadastro_raw) if data_cadastro_raw else "", "DATA_CADASTRO")
                data_pagamento_fixed = fix_daycoval_date(str(data_liberacao_raw) if data_liberacao_raw else "", "DATA_PAGAMENTO")
                
                logging.info(f"DAYCOVAL DATAS - ANTES: cadastro='{data_cadastro_raw}', pagamento='{data_liberacao_raw}'")
                logging.info(f"DAYCOVAL DATAS - DEPOIS: cadastro='{data_cadastro_fixed}', pagamento='{data_pagamento_fixed}'")
                
                normalized_row = {
                    "PROPOSTA": proposta_final,  # Unnamed: 0
                    "ADE": proposta_final,  # Campo ADE = mesma proposta
                    "DATA_CADASTRO": data_cadastro_fixed,  # Unnamed: 5 - DT.CAD. - CORRIGIDA
                    "BANCO": "BANCO DAYCOVAL",
                    "ORGAO": clean_special_characters(orgao_detectado),  # Detectado do arquivo + limpo
                    "TIPO_OPERACAO": clean_special_characters(operacao_detectada),  # Detectado do arquivo + limpo
                    "NUMERO_PARCELAS": str(prazo_meses_raw) if prazo_meses_raw else "0",  # Unnamed: 11 - Prz. em Meses
                    "VALOR_OPERACAO": valor_operacao_formatted,  # Formatado brasileiro
                    "VALOR_LIBERADO": valor_liberado_formatted,  # Formatado brasileiro
                    "USUARIO_BANCO": str(row.get('Unnamed: 40', '')).strip(),  # Usuário_Digitador
                    "SITUACAO": str(situacao_raw) if situacao_raw else "",  # Unnamed: 27 - Situação_Atual_da_Proposta
                    "DATA_PAGAMENTO": data_pagamento_fixed,  # Unnamed: 36 - Data da liberação - CORRIGIDA
                    "CPF": cpf_final,  # ✅ Formatado brasileiro (XXX.XXX.XXX-XX)
                    "NOME": nome_final,  # ✅ Maiúsculas
                    "DATA_NASCIMENTO": "",  # Não disponível no DAYCOVAL
                }
                
                # ✅ ADICIONAR DADOS DE CONTATO usando função universal
                contact_data = extract_contact_data(row, "DAYCOVAL")
                normalized_row.update({
                    "TELEFONE": contact_data["TELEFONE"],
                    "ENDERECO": contact_data["ENDERECO"],
                    "BAIRRO": contact_data["BAIRRO"],
                    "CEP": contact_data["CEP"],
                    "UF": contact_data["UF"]
                })
                
                # Continuar com os outros campos
                normalized_row.update({
                    "CODIGO_TABELA": str(row.get('Unnamed: 38', '')).strip() if row.get('Unnamed: 38') else "",  # Código da tabela
                    "VALOR_PARCELAS": valor_parcela_formatted,  # ✅ Formatado brasileiro
                    "TAXA": taxa_formatted,  # ✅ Formatado brasileiro (X,XX%)
                    "OBSERVACOES": ""  # DAYCOVAL não deve ter observações - somente VCTEX
                })
                
                logging.info(f"✅✅✅ DAYCOVAL normalized_row criado com sucesso para proposta: {proposta_final}")
                logging.info(f"✅✅✅ DAYCOVAL normalized_row: PROPOSTA={proposta_final}, NOME={nome_final}, CPF={cpf_final}")
            
        elif bank_type == "SANTANDER":
            # 🏦 BANCO SANTANDER - Processamento simplificado
            # Campos reais: COD, COD. BANCO, CPF, CLIENTE, CONVENIO, PRODUTO, QTDE PARCELAS, 
            #               VALOR BRUTO, VALOR LIQUIDO, STATUS, DATA, DATA AVERBACAO, COD DIGITADOR
            
            logging.info(f"=" * 80)
            logging.info(f"🏦 SANTANDER linha {idx}: INICIANDO PROCESSAMENTO")
            logging.info(f"   Colunas disponíveis: {list(row.keys())[:15]}")
            logging.info(f"=" * 80)
            
            import re
            
            # 🔧 Funções auxiliares
            def extract_santander_codigo_tabela(produto_str):
                """Extrai código tabela do produto (ex: '810021387' de '21387 - 810021387 - OFERTA')"""
                if not produto_str:
                    return ""
                
                parts = str(produto_str).split(' - ')
                if len(parts) >= 2 and parts[1].strip().isdigit():
                    return parts[1].strip()
                
                # Buscar número longo
                numbers = re.findall(r'\d{6,}', str(produto_str))
                return numbers[0] if numbers else ""
            
            def format_santander_value(value_str):
                """Formata valores no padrão brasileiro - VERSÃO ROBUSTA"""
                if not value_str or str(value_str).strip() in ['', 'nan', 'NaN', 'None', '0']:
                    return "0,00"
                
                try:
                    # Limpeza mais cuidadosa
                    clean_value = str(value_str).strip()
                    clean_value = clean_value.replace('R$', '').replace(' ', '').replace('\xa0', '').replace('\u00a0', '')
                    
                    # Se está vazio após limpeza
                    if not clean_value or clean_value == '0':
                        return "0,00"
                        
                    # Tratar formatos comuns
                    if ',' in clean_value and '.' in clean_value:
                        # Formato: 1.234,56 (brasileiro) ou 1,234.56 (americano)
                        if clean_value.rfind(',') > clean_value.rfind('.'):
                            # Formato brasileiro: 1.234,56
                            clean_value = clean_value.replace('.', '').replace(',', '.')
                        else:
                            # Formato americano: 1,234.56
                            clean_value = clean_value.replace(',', '')
                    elif ',' in clean_value:
                        # Apenas vírgula - formato brasileiro
                        clean_value = clean_value.replace(',', '.')
                        
                    value_float = float(clean_value)
                    
                    # Formatar no padrão brasileiro
                    if value_float >= 1000:
                        formatted = f"{value_float:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        formatted = f"{value_float:.2f}".replace('.', ',')
                        
                    return formatted
                    
                except (ValueError, TypeError) as e:
                    logging.warning(f"⚠️ SANTANDER: Erro ao formatar valor '{value_str}': {e}")
                    # Retornar valor original limpo ao invés de erro
                    clean_fallback = str(value_str).replace('R$', '').replace('  ', ' ').strip()
                    return clean_fallback if clean_fallback else "0,00"
            
            def normalize_santander_status(status_str):
                """Normaliza status para padrão Storm - VERSÃO ROBUSTA"""
                if not status_str:
                    return "AGUARDANDO"
                
                try:
                    # Conversão segura para string
                    status_clean = str(status_str).strip().upper()
                    
                    # Remover apenas caracteres problemáticos específicos, preservar texto
                    status_clean = status_clean.replace('�', '').replace('\x00', '').replace('\ufffd', '')
                    
                    # Remover acentos de forma mais segura
                    import unicodedata
                    status_clean = unicodedata.normalize('NFKD', status_clean)
                    status_clean = ''.join(c for c in status_clean if not unicodedata.combining(c))
                    
                    logging.info(f"🔍 SANTANDER status original: '{status_str}' → normalizado: '{status_clean}'")
                    
                    # Verificar palavras-chave SANTANDER - ORDEM ESPECÍFICA
                    # 1. PAGO: Operações finalizadas/averbadas
                    if any(palavra in status_clean for palavra in ['PAGO', 'LIBERADO', 'DESEMBOLSADO', 'FINALIZADO', 'LIQUIDADO']):
                        return "PAGO"
                    elif 'AVERBADA' in status_clean and 'ANALISE' not in status_clean:
                        # "AVERBADA" sozinha = PAGO, mas "AVERBADA EM ANALISE" = AGUARDANDO  
                        return "PAGO"
                    elif ('AVERBADA' in status_clean and 'ANALISE' in status_clean) or ('AVERBACAO' in status_clean and 'ANALISE' in status_clean):
                        # "AVERBADA EM ANALISE" ou "AVERBACAO EM ANALISE" = ainda em processamento
                        return "AGUARDANDO"
                    # 2. CANCELADO: Operações rejeitadas/negadas
                    elif any(palavra in status_clean for palavra in ['CANCELADO', 'CANCELADA', 'REPROVADO', 'REPROVADA', 'REJEITADO', 'REJEITADA', 'NEGADO', 'NEGADA', 'RECUSADO', 'RECUSADA']):
                        return "CANCELADO"
                    # 3. AGUARDANDO: Operações em processamento/análise
                    elif any(palavra in status_clean for palavra in ['AGUARDANDO', 'ANALISE', 'PENDENTE', 'ABERTO', 'ABERTA', 'DIGITACAO', 'PROCESSAMENTO', 'EM PROCESSAMENTO']):
                        return "AGUARDANDO"
                    else:
                        # Se não reconhecer nenhuma palavra-chave, retornar AGUARDANDO
                        logging.info(f"🔍 SANTANDER: Status não reconhecido '{status_clean}' → AGUARDANDO")
                        return "AGUARDANDO"
                        
                except Exception as e:
                    logging.warning(f"⚠️ SANTANDER: Erro ao normalizar status '{status_str}': {e}")
                    return "AGUARDANDO"
            
            # Função para limpar texto "quebrado" do SANTANDER
            def clean_santander_text(text_str):
                """Limpa texto quebrado/corrompido do relatório SANTANDER"""
                if not text_str:
                    return ""
                
                try:
                    # Converter para string e limpar
                    clean_text = str(text_str).strip()
                    
                    # Remover caracteres problemáticos comuns
                    clean_text = clean_text.replace('�', '').replace('\ufffd', '').replace('\x00', '')
                    clean_text = clean_text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                    
                    # Remover espaços múltiplos
                    while '  ' in clean_text:
                        clean_text = clean_text.replace('  ', ' ')
                    
                    return clean_text.strip()
                except:
                    return str(text_str).strip() if text_str else ""
            
            # Extrair campos do arquivo com limpeza
            proposta = clean_santander_text(row.get('COD. BANCO', row.get('COD', row.get('PROPOSTA', ''))))
            cliente = clean_santander_text(row.get('CLIENTE', row.get('NOME', '')))
            cpf = clean_santander_text(row.get('CPF', ''))
            convenio = clean_santander_text(row.get('CONVENIO', '')).upper()
            produto = clean_santander_text(row.get('PRODUTO', ''))
            parcelas = clean_santander_text(row.get('QTDE PARCELAS', row.get('NUMERO PARCELAS', '96')))
            valor_bruto = clean_santander_text(row.get('VALOR BRUTO', row.get('VALOR OPERACAO', '0')))
            valor_liquido = clean_santander_text(row.get('VALOR LIQUIDO', row.get('VALOR LIBERADO', '0')))
            valor_parcela = clean_santander_text(row.get('VALOR PARCELA', row.get('VALOR PARCELAS', '0')))
            data_cadastro = clean_santander_text(row.get('DATA', row.get('DATA CADASTRO', '')))
            status = clean_santander_text(row.get('STATUS', row.get('SITUACAO', 'AGUARDANDO')))
            data_averbacao = clean_santander_text(row.get('DATA AVERBACAO', row.get('DATA DE PAGAMENTO', '')))
            cod_digitador = str(row.get('COD DIGITADOR NO BANCO', row.get('USUARIO BANCO', ''))).strip()
            
            # 🎯 SANTANDER: Extrair CPF do campo "COD DIGITADOR NO BANCO" 
            def format_santander_usuario_from_cod(cod_digitador_raw):
                """Extrair CPF dos primeiros 11 dígitos do COD DIGITADOR NO BANCO
                Ex: '37375205850030700' → '373.752.058-50'
                """
                if not cod_digitador_raw or cod_digitador_raw in ['', 'nan', 'NaN']:
                    return "000.000.000-00"
                
                # Limpar e usar apenas dígitos
                digits_only = ''.join(filter(str.isdigit, str(cod_digitador_raw)))
                
                if len(digits_only) >= 11:
                    # Pegar apenas os primeiros 11 dígitos (CPF)
                    cpf_digits = digits_only[:11]
                    return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:11]}"
                else:
                    return cod_digitador_raw  # Manter original se não conseguir formatar
            
            usuario_digitador_formatado = format_santander_usuario_from_cod(cod_digitador)
            
            logging.info(f"📋 SANTANDER extraído: Proposta={proposta}, Cliente={cliente[:20] if cliente else 'N/A'}, CPF={cpf[:6] if cpf else 'N/A'}...")
            logging.info(f"👤 SANTANDER COD DIGITADOR: '{cod_digitador}' → CPF: '{usuario_digitador_formatado}'")
            logging.info(f"🔍 SANTANDER validações: proposta='{proposta}', convenio='{convenio[:30] if convenio else 'N/A'}', produto='{produto[:50] if produto else 'N/A'}'")
            
            # ✅ VALIDAÇÃO: Verificar se linha deve ser processada
            should_process = True
            
            if not proposta or proposta.upper() in ['NAN', 'NONE', '', 'COD. BANCO']:
                logging.info(f"⏭️ SANTANDER linha {idx}: Pulando - proposta vazia ou cabeçalho")
                should_process = False
                normalized_row = None
            
            # 🚫 FILTRO ESPECIAL: Propostas SEGURO têm 'S' no final do COD. BANCO
            elif proposta.upper().endswith('S') and len(proposta) > 5:
                # Verificar se é realmente SEGURO (não um código normal que termina com S)
                if 'SEGURO' in convenio or 'SEGURO' in produto.upper():
                    logging.info(f"🚫 SANTANDER linha {idx}: Filtrando - proposta SEGURO com 'S' no final ({proposta})")
                    should_process = False
                    normalized_row = None
                else:
                    logging.info(f"✓ SANTANDER linha {idx}: Proposta termina com 'S' mas NÃO é SEGURO - vai processar")
            
            logging.info(f"📊 SANTANDER linha {idx}: should_process = {should_process}")
            
            # Processar apenas se não foi filtrado
            if should_process:
                # Extrair código tabela
                codigo_tabela = extract_santander_codigo_tabela(produto)
                
                logging.info(f"🔍 SANTANDER linha {idx}: código extraído = '{codigo_tabela}' de produto: {produto[:50] if produto else 'N/A'}...")
                
                # Detectar órgão
                if 'PREF' in convenio or 'AGUDOS' in convenio or 'RANCHARIA' in convenio:
                    orgao = 'PREF. DE AGUDOS - SP' if 'AGUDOS' in convenio else 'PREF. DE RANCHARIA - SP'
                elif 'LINS' in convenio:
                    orgao = 'PREF. DE LINS - SP'
                else:
                    orgao = 'INSS'
                
                logging.info(f"🏛️ SANTANDER linha {idx}: órgão = {orgao} (convênio: {convenio[:30] if convenio else 'N/A'}...)")
                
                # Detectar tipo de operação
                produto_upper = produto.upper()
                if 'REFIN' in produto_upper:
                    tipo_operacao = 'REFINANCIAMENTO'
                elif 'PORT' in produto_upper:
                    tipo_operacao = 'PORTABILIDADE'
                else:
                    tipo_operacao = 'MARGEM LIVRE (NOVO)'
                
                logging.info(f"🔧 SANTANDER linha {idx}: tipo_operacao = {tipo_operacao}")
                
                # 🚫 FILTRO: Remover propostas SEGURO (11111111)
                has_seguro_codigo = codigo_tabela and '11111111' in codigo_tabela
                has_seguro_produto = False  # Desativado - estava filtrando tudo
                is_pure_seguro = 'SEGURO' in produto_upper and not any(p in produto_upper for p in ['OFERTA', 'REFIN', 'PORT'])
                has_todos_convenios = 'TODOS OS CONVENIOS' in produto_upper
                
                logging.info(f"� SANTANDER linha {idx}: Verificando SEGURO - has_seguro_codigo={has_seguro_codigo}, has_seguro_produto={has_seguro_produto}, has_todos_convenios={has_todos_convenios}")
                
                if codigo_tabela and (has_seguro_codigo or is_pure_seguro or has_todos_convenios):
                    logging.info(f"FILTRADO por SEGURO - proposta {proposta}")
                    normalized_row = None
                else:
                    logging.info(f"PASSOU nos filtros - vai criar normalized_row")
                    
                    # Criar registro normalizado apenas se passou nos filtros
                    normalized_row = {
                        "PROPOSTA": proposta,
                        "DATA_CADASTRO": data_cadastro,
                        "BANCO": "BANCO SANTANDER",
                        "ORGAO": orgao,
                        "TIPO_OPERACAO": tipo_operacao,
                        "NUMERO_PARCELAS": parcelas,
                        "VALOR_OPERACAO": format_santander_value(valor_bruto),
                        "VALOR_LIBERADO": format_santander_value(valor_liquido),
                        "USUARIO_BANCO": usuario_digitador_formatado,
                        "SITUACAO": normalize_santander_status(status),
                        "DATA_PAGAMENTO": data_averbacao if normalize_santander_status(status) == "PAGO" else "",
                        "CPF": cpf,
                        "NOME": cliente.upper(),
                        "DATA_NASCIMENTO": "",

                        "CODIGO_TABELA": codigo_tabela,
                        "VALOR_PARCELAS": format_santander_value(valor_parcela),
                        "TAXA": "0,00%",
                        "OBSERVACOES": ""
                    }
                    
                    # ✅ ADICIONAR DADOS DE CONTATO usando função universal
                    contact_data = extract_contact_data(row, "SANTANDER")
                    normalized_row.update({
                        "TELEFONE": contact_data["TELEFONE"],
                        "ENDERECO": contact_data["ENDERECO"],
                        "BAIRRO": contact_data["BAIRRO"],
                        "CEP": contact_data["CEP"],
                        "UF": contact_data["UF"]
                    })
                    
                    logging.info(f"✅✅✅ SANTANDER linha {idx}: normalized_row CRIADO! Proposta={proposta} | Código={codigo_tabela} | Órgão={orgao} | Status={normalize_santander_status(status)}")
                    logging.info(f"📦 SANTANDER linha {idx}: normalized_row pronto para validação comum")
            else:
                # Se should_process=False, garantir que normalized_row=None já foi definido
                logging.info(f"⏭️ SANTANDER linha {idx}: should_process=False, normalized_row=None")
                if 'normalized_row' not in locals():
                    normalized_row = None
        
        elif bank_type == "CREFAZ":
            # 🔍 CREFAZ: Log das colunas disponíveis para debug
            logging.info(f"🏦 CREFAZ - Colunas disponíveis: {list(row.keys())}")
            
            # Mapeamento BANCO CREFAZ - Campos reais baseados no mapeamento
            # Colunas reais: Data Cadastro, Número da Proposta, CPF, Cliente, Cidade, Status, Agente, etc.
            
            # 💰 FUNÇÃO para formatar valores no padrão brasileiro
            def format_crefaz_value(value_str):
                """Converte valores para formato brasileiro: 1.255,00"""
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
                        decimal_part = parts[1][:2] if len(parts) > 1 else "00"
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
                    
                    # Formatar no padrão brasileiro: 1.255,00
                    if float_value >= 1000:
                        # Valores >= 1000: usar ponto para milhar
                        formatted = f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    else:
                        # Valores < 1000: apenas vírgula decimal
                        formatted = f"{float_value:.2f}".replace('.', ',')
                    
                    return formatted
                    
                except (ValueError, TypeError) as e:
                    logging.warning(f"⚠️ CREFAZ: Erro ao formatar valor '{value_str}': {e}")
                    return str(value_str)  # Retornar original se houver erro
            
            # 🔧 CREFAZ: CORREÇÃO - ADE deve vir da coluna "Cod Operação" (ex: 3915740)
            # O ADE correto está em "Cod Operação", não em "Número da Proposta"
            proposta = str(row.get('Cod Operação', '')).strip()
            
            # Fallback: tentar outras variações da coluna se não encontrar
            if not proposta or proposta in ['nan', 'None', '', 'NaN', '0']:
                proposta = str(row.get('Cod Operacao', row.get('COD_OPERACAO', ''))).strip()
            
            # ✅ FILTRAR LINHAS VAZIAS - Validações mais robustas
            if not proposta or proposta in ['nan', 'None', '', 'NaN', '0']:
                logging.info(f"⏭️ CREFAZ: Pulando linha - ADE vazio na coluna 'Cod Operação': '{proposta}'")
                continue
            
            # Validar campos essenciais antes de prosseguir
            cpf_cliente = str(row.get('CPF', '')).strip()
            nome_cliente = str(row.get('Cliente', row.get('Nome', ''))).strip()
            
            # Pular linhas com campos críticos vazios
            if not cpf_cliente or cpf_cliente in ['nan', 'None', '', 'NaN']:
                logging.info(f"⏭️ CREFAZ: Pulando linha - CPF vazio (ADE: {proposta})")
                continue
                
            if not nome_cliente or nome_cliente in ['nan', 'None', '', 'NaN']:
                logging.info(f"⏭️ CREFAZ: Pulando linha - Nome vazio (ADE: {proposta})")
                continue
                
            logging.info(f"🎯 CREFAZ: ADE correto encontrado em 'Cod Operação': {proposta}")
            
            # 🔧 CREFAZ: CÓDIGO DE TABELA - gerar baseado no produto
            produto_raw = str(row.get('Produto', '')).strip().upper()
            
            # Validar se produto não está vazio
            if not produto_raw or produto_raw in ['NAN', 'NONE', '']:
                logging.info(f"⏭️ CREFAZ: Pulando linha - Produto vazio (ADE: {proposta})")
                continue
            
            if 'ENERGIA' in produto_raw or 'LUZ' in produto_raw:
                cod_operacao = "ENER"
            elif 'BOLETO' in produto_raw:
                cod_operacao = "BOL" 
            elif 'VEICULO' in produto_raw or 'AUTO' in produto_raw:
                cod_operacao = "CPAUTO"
            elif 'TRABALHADOR' in produto_raw or 'CLT' in produto_raw:
                cod_operacao = "CSD"
            else:
                cod_operacao = "ENER"  # Default para energia
                
            logging.info(f"🎯 CREFAZ: Código gerado do produto '{produto_raw}': {cod_operacao}")
            produto = str(row.get('Produto', '')).strip()
            
            # ✅ VALIDAÇÃO: Pular linhas com código de operação vazio
            if not cod_operacao or cod_operacao.upper() in ['NAN', 'NONE', '']:
                logging.info(f"⏭️ CREFAZ: Pulando proposta {proposta} - código de operação vazio")
                continue
            
            # 🔧 CREFAZ: Extrair usuário digitador - tentar múltiplas colunas
            usuario_candidates = [
                'Login Agente', 'login agente', 'LOGIN_AGENTE',
                'Agente', 'agente', 'AGENTE',
                'Código Digitador', 'Codigo Digitador', 'COD_DIGITADOR',
                'Usuario', 'USUARIO', 'usuario',
                'Digitador', 'DIGITADOR', 'digitador'
            ]
            
            usuario_banco = ""
            col_usuario_usada = ""
            for col_name in usuario_candidates:
                temp_usuario = str(row.get(col_name, '')).strip()
                if temp_usuario and temp_usuario not in ['nan', 'None', '', 'NaN']:
                    usuario_banco = temp_usuario
                    col_usuario_usada = col_name
                    break
            
            # Se não encontrou usuário válido, usar valor padrão
            if not usuario_banco:
                usuario_banco = "SISTEMA"
                col_usuario_usada = "DEFAULT"
            
            logging.info(f"🎯 CREFAZ: Usuário digitador: '{usuario_banco}' (coluna: '{col_usuario_usada}')")
            
            # 🔍 CREFAZ: Detectar ÓRGÃO baseado no CÓDIGO (não no produto)
            # Os códigos já vêm corretos do arquivo: ENER, CPAUTO, LUZ, BOL, CSD
            cod_upper = cod_operacao.upper()
            
            # Mapear órgão baseado no código
            if cod_upper in ['ENER', 'LUZ']:
                orgao = 'ENERGIA'
            elif cod_upper in ['BOL', 'BOLETO']:
                orgao = 'BOLETO'
            elif cod_upper in ['CPAUTO', 'AUTO', 'VEICULO']:
                orgao = 'VEICULOS'
            elif cod_upper in ['CSD', 'CLT', 'TRABALHADOR']:
                orgao = 'CRÉDITO DO TRABALHADOR'
            else:
                # Se código desconhecido, tentar detectar pelo produto
                produto_upper = produto.upper()
                if 'ENERGIA' in produto_upper or 'LUZ' in produto_upper or 'FATURA' in produto_upper:
                    orgao = 'ENERGIA'
                elif 'BOLETO' in produto_upper:
                    orgao = 'BOLETO'
                elif 'VEICULO' in produto_upper or 'AUTO' in produto_upper or 'CARRO' in produto_upper:
                    orgao = 'VEICULOS'
                elif 'TRABALHADOR' in produto_upper or 'CLT' in produto_upper or 'PRIVADO' in produto_upper:
                    orgao = 'CRÉDITO DO TRABALHADOR'
                else:
                    orgao = 'ENERGIA'  # Default
            
            tipo_operacao = 'Margem Livre (Novo)'  # CREFAZ sempre é margem livre
            
            # 💰 Formatar valores no padrão brasileiro
            valor_operacao_br = format_crefaz_value(row.get('Valor Liberado', row.get('Valor Solicitado', '')))
            valor_liberado_br = format_crefaz_value(row.get('Valor Liberado', ''))
            valor_parcela_br = format_crefaz_value(row.get('Valor da Parcela', row.get('Parcela', '')))
            
            # Criar registro normalizado
            normalized_row = {
                "PROPOSTA": proposta,
                "DATA_CADASTRO": str(row.get('Data Cadastro', '')).strip(),
                "BANCO": "BANCO CREFAZ",
                "ORGAO": orgao,
                "TIPO_OPERACAO": tipo_operacao,
                "NUMERO_PARCELAS": str(row.get('Prazo', '')).strip(),
                "VALOR_OPERACAO": valor_operacao_br,  # 💰 FORMATO BRASILEIRO
                "VALOR_LIBERADO": valor_liberado_br,  # 💰 FORMATO BRASILEIRO
                "USUARIO_BANCO": usuario_banco,
                "SITUACAO": str(row.get('Status', '')).strip(),
                "DATA_PAGAMENTO": str(row.get('Alteração', row.get('Data Pagamento', ''))).strip(),
                "CPF": str(row.get('CPF', '')).strip(),
                "NOME": str(row.get('Cliente', row.get('Nome', ''))).strip(),
                "DATA_NASCIMENTO": "",

                "CODIGO_TABELA": cod_operacao,  # ✅ Usar código diretamente do arquivo (ENER, CPAUTO, LUZ, BOL, CSD)
                "VALOR_PARCELAS": valor_parcela_br,  # 💰 FORMATO BRASILEIRO
                "TAXA": "0,00%",  # CREFAZ não tem taxa no relat_orgaos (sempre 0,00%)
                "OBSERVACOES": str(row.get('Motivos', row.get('Observacoes', ''))).strip()
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal
            contact_data = extract_contact_data(row, "CREFAZ")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"],
                "ENDERECO": contact_data["ENDERECO"],
                "BAIRRO": contact_data["BAIRRO"],
                "CEP": contact_data["CEP"],
                "UF": contact_data["UF"]
            })
            
            logging.info(f"✅ CREFAZ processado: Proposta={proposta} | Código='{cod_operacao}' | Órgão='{orgao}'")

        
        elif bank_type == "QUERO_MAIS":
            # Mapeamento BANCO QUERO MAIS CREDITO - ESTRUTURA REAL IDENTIFICADA
            
            # ⚠️ VALIDAÇÃO: Pular linhas de cabeçalho  
            primeira_coluna = str(list(row.values())[0] if row.values() else "").strip()
            if any(header in primeira_coluna.upper() for header in [
                'RELATÓRIO DE PRODUÇÃO', 'CAPITAL CONSIG', 'COMISSIONADO', 'AGENCIA', 'CNPJ', 
                'CODIGO PROMOTORA', 'PG.', 'PROC.', 'SIST.', 'VERSÃO'
            ]):
                logging.info(f"🚫 QUERO MAIS - Pulando linha de cabeçalho: '{primeira_coluna[:50]}...'")
                continue
            
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
            
            # Detecção de órgão INTELIGENTE - usando múltiplas fontes
            descr_orgao = str(row.get('Unnamed: 25', '')).strip().upper()  # Descr. Orgao
            descr_empregador = str(row.get('Unnamed: 24', '')).strip().upper()  # Descr. Empregador
            descr_tabela = str(row.get('Unnamed: 22', '')).strip().upper()  # Descr. Tabela
            codigo_tabela_raw = str(row.get('Unnamed: 46', '')).strip()  # Código da tabela
            
            # Combinar todas as informações para análise
            todas_descricoes = f"{descr_orgao} {descr_empregador} {descr_tabela}".strip()
            logging.info(f"🏛️ QUERO MAIS análise completa:")
            logging.info(f"   descr_orgao: '{descr_orgao}'")
            logging.info(f"   descr_empregador: '{descr_empregador}'")  
            logging.info(f"   descr_tabela: '{descr_tabela}'")
            logging.info(f"   codigo_tabela: '{codigo_tabela_raw}'")
            
            # 🚨 LÓGICA INTELIGENTE: Análise por prioridade
            if 'INSS' in todas_descricoes and ('BENEFICIO' in todas_descricoes or 'BENEFÍCIO' in todas_descricoes or 'RMC' in todas_descricoes or 'CART' in todas_descricoes):
                # Se menciona INSS + (benefício OU RMC OU cartão) = realmente INSS
                orgao = 'INSS'
                logging.info(f"✅ QUERO MAIS → INSS (detectado: INSS + benefício/RMC/cartão)")
            elif 'SIAPE' in todas_descricoes or 'FEDERAL' in todas_descricoes:
                # Se menciona SIAPE ou FEDERAL explicitamente
                orgao = 'SIAPE FEDERAL'
                logging.info(f"✅ QUERO MAIS → SIAPE FEDERAL (detectado: SIAPE/FEDERAL explícito)")
            elif 'GOV' in todas_descricoes or 'GOVERNO' in todas_descricoes or 'ESTADO' in todas_descricoes:
                # Se menciona governo/estado = SIAPE
                orgao = 'SIAPE FEDERAL'
                logging.info(f"✅ QUERO MAIS → SIAPE FEDERAL (detectado: governo/estado)")
            elif 'SÃO PAULO' in todas_descricoes or 'SP' in todas_descricoes:
                # Estado de São Paulo = SIAPE
                orgao = 'SIAPE FEDERAL'
                logging.info(f"✅ QUERO MAIS → SIAPE FEDERAL (detectado: São Paulo/SP)")
            elif 'PREFEITURA' in todas_descricoes or 'MUNICIPAL' in todas_descricoes:
                # Prefeituras = SIAPE CONSIG
                orgao = 'SIAPE CONSIG'
                logging.info(f"✅ QUERO MAIS → SIAPE CONSIG (detectado: prefeitura/municipal)")
            elif 'FGTS' in todas_descricoes:
                # FGTS = FGTS
                orgao = 'FGTS'
                logging.info(f"✅ QUERO MAIS → FGTS (detectado: FGTS)")
            else:
                # 🚨 DECISÃO INTELIGENTE BASEADA NO CÓDIGO DA TABELA
                # Códigos 4xxx geralmente são INSS, códigos 49xx podem ser SIAPE
                if codigo_tabela_raw:
                    codigo_num = codigo_tabela_raw.lstrip('0')
                    if codigo_num.startswith('46') or codigo_num.startswith('47'):
                        # Códigos 46xx, 47xx = tipicamente INSS cartão
                        orgao = 'INSS'
                        logging.info(f"✅ QUERO MAIS → INSS (código {codigo_num} = padrão INSS cartão)")
                    elif codigo_num.startswith('49'):
                        # Códigos 49xx = tipicamente SIAPE
                        orgao = 'SIAPE FEDERAL'
                        logging.info(f"✅ QUERO MAIS → SIAPE FEDERAL (código {codigo_num} = padrão SIAPE)")
                    else:
                        # Outros códigos: defaultar para INSS (mais comum no QUERO MAIS)
                        orgao = 'INSS'
                        logging.info(f"✅ QUERO MAIS → INSS (código {codigo_num} = default INSS)")
                else:
                    # Sem código: defaultar para INSS
                    orgao = 'INSS'
                    logging.info(f"✅ QUERO MAIS → INSS (sem código = default INSS)")
                
            # 🚨 APLICAR NORMALIZAÇÃO STORM NO ÓRGÃO
            orgao = normalize_storm_organ(orgao)
            logging.info(f"🎯 QUERO MAIS órgão FINAL: '{orgao}'")
            
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
                logging.info(f"🔍 QUERO MAIS tipo operação - descr_tabela: '{descr_tabela}' -> '{descr_upper}'")
                
                if "CARTAO" in descr_upper or "CARTÃO" in descr_upper or "CCC" in descr_upper:
                    # 🚨 CORREÇÃO: Sempre "c/ Saque" para cartão
                    tipo_operacao = "CARTAO C/ SAQUE"  # 🚨 SEM ACENTOS
                elif "RMC" in descr_upper:
                    tipo_operacao = "Margem Livre (Novo)"  # RMC = Margem Livre
                elif "LOAS" in descr_upper:
                    tipo_operacao = "Margem Livre (Novo)"  # LOAS = Margem Livre
                elif "BENEFICIO" in descr_upper or "BENEFÍCIO" in descr_upper:
                    tipo_operacao = "Margem Livre (Novo)"
                    
                # 🚨 APLICAR NORMALIZAÇÃO STORM
                tipo_operacao = normalize_storm_operation(tipo_operacao)
                logging.info(f"✅ QUERO MAIS tipo operação determinado: '{tipo_operacao}' (de '{descr_tabela}')")
            
            # Remover zeros à esquerda do código de tabela (004717 → 4717)
            codigo_tabela_original = str(row.get('Unnamed: 46', '')).strip()
            codigo_tabela_final = codigo_tabela_original.lstrip('0') if codigo_tabela_original else ''
            # Se ficou vazio após remover zeros, manter o original
            if not codigo_tabela_final:
                codigo_tabela_final = codigo_tabela_original
            
            # 🔧 QUERO_MAIS: Manter usuário digitador no formato original com underscore
            # Exemplo: "39891947807_901064" (manter como está)
            usuario_final = usuario_cadastro  # Manter formato original: 39891947807_901064
            
            # 📞📍 QUERO MAIS: Extrair dados de contato baseado no mapeamento real
            endereco_rua = str(row.get('Unnamed: 26', '')).strip()  # Endereco Cliente
            numero_endereco = str(row.get('Unnamed: 34', '')).strip()  # Numero Endereco  
            bairro_cliente = str(row.get('Unnamed: 2', '')).strip()  # Bairro
            cep_cliente = str(row.get('Unnamed: 12', '')).strip()  # Cep
            uf_cliente = str(row.get('Unnamed: 27', '')).strip()  # Estado
            fone_cel = str(row.get('Unnamed: 29', '')).strip()  # Fone Cel.
            fone_res = str(row.get('Unnamed: 31', '')).strip()  # Fone Res.
            
            # Montar endereço completo
            endereco_completo = f"{endereco_rua}, {numero_endereco}".strip(", ") if endereco_rua else ""
            
            # Priorizar celular, senão telefone residencial
            telefone_final = fone_cel if fone_cel else fone_res
            
            normalized_row = {
                "PROPOSTA": proposta,
                "DATA_CADASTRO": data_cadastro,
                "BANCO": "BANCO QUERO MAIS CREDITO",
                "ORGAO": orgao,
                "TIPO_OPERACAO": tipo_operacao,  # Determinado pela descrição da tabela
                "NUMERO_PARCELAS": qtd_parcelas,
                "VALOR_OPERACAO": valor_liberado,  # Usar valor liberado como operação
                "VALOR_LIBERADO": valor_liberado,
                "USUARIO_BANCO": usuario_final,  # Usuário no formato original completo (com underscore)
                "SITUACAO": "DIGITADA",  # ✅ MANUAL conforme solicitado 
                "DATA_PAGAMENTO": "",   # ✅ MANUAL conforme solicitado (sempre vazio)
                "CPF": cpf_cliente,
                "NOME": nome_cliente,
                "DATA_NASCIMENTO": data_nascimento,
                "CODIGO_TABELA": codigo_tabela_final,  # Código sem zeros à esquerda (4717)
                "VALOR_PARCELAS": valor_parcela,
                "TAXA": "0,00%",  # Taxa fixa para QUERO MAIS
                "OBSERVACOES": ""  # QUERO MAIS não deve ter observações - somente VCTEX
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal (manter fallback manual se necessário)
            contact_data = extract_contact_data(row, "QUERO_MAIS")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"] if contact_data["TELEFONE"] else clean_contact_field(telefone_final, "TELEFONE"),
                "ENDERECO": contact_data["ENDERECO"] if contact_data["ENDERECO"] else clean_contact_field(endereco_completo, "ENDERECO"),
                "BAIRRO": contact_data["BAIRRO"] if contact_data["BAIRRO"] else clean_contact_field(bairro_cliente, "BAIRRO"),
                "CEP": contact_data["CEP"] if contact_data["CEP"] else clean_contact_field(cep_cliente, "CEP"),
                "UF": contact_data["UF"] if contact_data["UF"] else clean_contact_field(uf_cliente, "UF")
            })
            
            # Log para debug dos valores mapeados
            logging.info(f"✅ QUERO MAIS mapeado: PROPOSTA={proposta}, ORGAO={orgao}, CPF={cpf_cliente}, TIPO_OP={tipo_operacao}")
        
        elif bank_type == "PAN":
            # Mapeamento BANCO PAN - Estrutura de cartão e saque
            
            # 📞📍 PAN: Extrair dados de contato baseado no mapeamento real
            telefone_pan = str(row.get('Telefone', '')).strip()  # Telefone
            celular_pan = str(row.get('Celular', '')).strip()   # Celular
            endereco_pan = str(row.get('Endereço do Cliente', '')).strip()  # Endereço do Cliente
            num_endereco_pan = str(row.get('Nº Endereço', '')).strip()  # Nº Endereço
            cidade_pan = str(row.get('Cidade', '')).strip()   # Cidade
            uf_pan = str(row.get('UF', '')).strip()           # UF
            cep_pan = str(row.get('CEP', '')).strip()         # CEP
            
            # Montar endereço completo
            endereco_completo_pan = f"{endereco_pan}, {num_endereco_pan}".strip(", ") if endereco_pan else ""
            
            # Priorizar celular, senão telefone fixo  
            telefone_final_pan = celular_pan if celular_pan else telefone_pan
            
            # 📍 PAN: Log dos dados de contato para debug
            logging.info(f"📞 PAN contato: telefone='{telefone_final_pan}', endereco='{endereco_completo_pan}', cidade='{cidade_pan}', cep='{cep_pan}', uf='{uf_pan}'")
            
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
                "TELEFONE": clean_contact_field(telefone_final_pan, "TELEFONE"),
                "ENDERECO": clean_contact_field(endereco_completo_pan, "ENDERECO"),
                "BAIRRO": clean_contact_field(cidade_pan, "BAIRRO"),  # PAN usa Cidade como Bairro
                "CEP": clean_contact_field(cep_pan, "CEP"),
                "UF": clean_contact_field(uf_pan, "UF"),
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
            # NR_TABCOM tem o código numérico: 60186
            tabela_completa = str(row.get('DS_TABCOM', row.get('TABELA', row.get('TIPO_TABELA', '')))).strip()
            nr_tabcom = str(row.get('NR_TABCOM', '')).strip()
            
            # ✅ CORREÇÃO: Extrair código da tabela (priorizar NR_TABCOM)
            codigo_tabela = ""
            if nr_tabcom:
                # Usar NR_TABCOM diretamente (mais confiável)
                codigo_tabela = nr_tabcom
                logging.info(f"✅ FACTA92 código de NR_TABCOM: {codigo_tabela}")
            elif tabela_completa:
                # Fallback: extrair do DS_TABCOM
                import re
                match = re.match(r'^(\d+)', tabela_completa)
                if match:
                    codigo_tabela = match.group(1)
                    logging.info(f"✅ FACTA92 código extraído de DS_TABCOM: '{tabela_completa}' → '{codigo_tabela}'")
                else:
                    codigo_tabela = tabela_completa
                    logging.warning(f"⚠️ FACTA92 não conseguiu extrair código de: '{tabela_completa}'")
            
            # Usuário/Corretor
            usuario = str(row.get('LOGIN_CORRETOR', row.get('CORRETOR', row.get('USUARIO', '')))).strip()
            
            # Data
            data_cadastro = str(row.get('DATA_CADASTRO', row.get('DATA_REGISTRO', row.get('DATA', '')))).strip()
            data_pagamento = str(row.get('DATAEFETIVACAO', row.get('DATA_PAGAMENTO_CLIENTE', row.get('DATA_PAGAMENTO', '')))).strip()
            
            # Convênio e detecção de órgão melhorada
            convenio = str(row.get('CONVENIO', '')).strip()
            
            # ✅ CORREÇÃO: Detectar órgão baseado no DS_TABCOM
            orgao = 'INSS'  # Default
            if tabela_completa:
                tabela_upper = tabela_completa.upper()
                if 'FGTS' in tabela_upper:
                    orgao = 'FGTS'  # ✅ FGTS é órgão próprio
                elif 'CLT' in tabela_upper:
                    orgao = 'CRÉDITO DO TRABALHADOR'  # ✅ CLT é crédito do trabalhador
                elif 'INSS' in tabela_upper:
                    orgao = 'INSS'
                elif 'SIAPE' in tabela_upper:
                    orgao = 'SIAPE'
                elif 'PREFEITURA' in tabela_upper or 'PREF' in tabela_upper:
                    orgao = 'PREFEITURA'
                else:
                    orgao = 'INSS'
            
            # ❌ NÃO buscar TAXA do arquivo - deixar vazio para o mapeamento preencher com 0,00%
            # O relat_orgaos.csv tem a taxa correta (0,00% para FACTA)
            taxa_formatada = ""  # Sempre vazio - será preenchido pelo apply_mapping()
            
            # Log para debug
            logging.info(f"✅ FACTA92 processado: PROPOSTA={proposta}, CODIGO_TABELA={codigo_tabela}, ORGAO={orgao}, TAXA={taxa_formatada}")
            
            normalized_row = {
                "PROPOSTA": proposta,
                "DATA_CADASTRO": data_cadastro,
                "BANCO": "FACTA FINANCEIRA",  # ✅ Nome correto
                "ORGAO": orgao,
                "TIPO_OPERACAO": "",  # ✅ Será buscado em relat_orgaos.csv pelo CODIGO_TABELA
                "NUMERO_PARCELAS": num_parcelas,
                "VALOR_OPERACAO": vl_bruto if vl_bruto else vl_liquido,
                "VALOR_LIBERADO": vl_liquido,
                "USUARIO_BANCO": usuario,
                "SITUACAO": situacao if situacao else "PAGO",
                "DATA_PAGAMENTO": data_pagamento,
                "CPF": cpf,
                "NOME": nome,
                "DATA_NASCIMENTO": data_nascimento,
                "CODIGO_TABELA": codigo_tabela,  # ✅ Código da tabela (ex: 61700)
                "VALOR_PARCELAS": vl_parcela,
                "TAXA": taxa_formatada,  # ✅ Vazia - será preenchida pelo mapeamento
                "OBSERVACOES": ""
            }
            
            # ✅ ADICIONAR DADOS DE CONTATO usando função universal
            contact_data = extract_contact_data(row, "FACTA92")
            normalized_row.update({
                "TELEFONE": contact_data["TELEFONE"],
                "ENDERECO": contact_data["ENDERECO"], 
                "BAIRRO": contact_data["BAIRRO"],
                "CEP": contact_data["CEP"],
                "UF": contact_data["UF"]
            })
        
        elif bank_type == "PAULISTA":
            logging.error(f"🎯 CHEGOU NO BLOCO PAULISTA! Linha {idx}: '{row.get('Unnamed: 0', '')}'")
            logging.error(f"💥 INICIO DO PROCESSAMENTO PAULISTA - ANTES DE QUALQUER LÓGICA")
            logging.info(f"=" * 80)
            logging.info(f"🏦 PAULISTA linha {idx}: INICIANDO PROCESSAMENTO")
            logging.info(f"   Colunas disponíveis: {list(row.keys())[:10]}")
            
            # 🔧 CORREÇÃO PAULISTA: Verificar se primeira linha contém cabeçalhos
            primeira_celula = row.get('Unnamed: 0', '')
            logging.error(f"🔧 PAULISTA: Verificando primeira_celula = '{primeira_celula}'")
            if str(primeira_celula) == 'Nº Proposta':
                logging.info(f"� PAULISTA: Primeira linha é cabeçalho! Pulando...")
                continue  # Pular linha de cabeçalho
            
            logging.error(f"🎉 PAULISTA: Passou da verificação de cabeçalho! Continuando processamento...")
            
            # Debug da linha atual - log detalhado para ver o que está vindo
            logging.error(f"🔍 PAULISTA: Iniciando debug da linha atual...")
            logging.info(f"   🔍 Proposta bruta: '{primeira_celula}' (tipo: {type(primeira_celula)})")
            logging.info(f"   🔍 Segunda coluna (Contrato): '{row.get('Unnamed: 1', '')}'")
            logging.info(f"   🔍 CPF: '{row.get('Unnamed: 4', '')}'")
            logging.info(f"   🔍 Nome: '{row.get('Unnamed: 5', '')}'")
            
            logging.error(f"🔍 PAULISTA: Após logs básicos - continuando...")
            logging.info(f"=" * 80)
            
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
            
            # Mapeamento BANCO PAULISTA - Colunas NOMEADAS (não Unnamed!)
            # Baseado no arquivo real: Nº Proposta | Contrato | Data Captura | etc.
            
            # Mapeamento PAULISTA corrigido baseado em map_relat_atualizados.txt
            # Unnamed: 0='Nº Proposta', 1='Contrato', 2='Data Captura', 3='Dt Atividade'  
            # Unnamed: 4='CPF/CNPJ Proponente', 5='Nome do Proponente', 6='Matrícula', 7='Espécie Benefício'
            # Unnamed: 8='Banco', 9='Agência', 10='Conta', 11='Valor Solicitado'
            # Unnamed: 12='Vl. Liberado', 13='Vl. Troco', 14='Quant. Parcelas', 15='Valor Parcela'
            # Unnamed: 16='Plano', 17='1º Vencimento', 18='Produto', 19='Fase', 20='Status'
            # Unnamed: 21='Dta. Integração', 22='Loja/Sub', 23='Lojista/Master', 24='Usuário Digitador'
            
            proposta = str(row.get('Unnamed: 0', '')).strip()  # Nº Proposta
            especies_beneficio = str(row.get('Unnamed: 7', '')).strip()  # Espécie Benefício
            produto = str(row.get('Unnamed: 18', '')).strip()  # Produto
            status = str(row.get('Unnamed: 20', '')).strip()  # Status
            
            # Logs detalhados para debug
            logging.info(f"📋 PAULISTA extraído: Proposta={proposta}, Produto={produto[:30] if produto else 'N/A'}")
            logging.info(f"📋 PAULISTA status='{status}', espécie='{especies_beneficio[:20] if especies_beneficio else 'N/A'}'")
            
            logging.error(f"🔍 PAULISTA: Chegou na validação! Proposta extraída: '{proposta}'")
            
            # ✅ VALIDAÇÃO: Verificar se linha deve ser processada
            if not proposta or proposta.upper() in ['NAN', 'NONE', '', 'UNNAMED: 0', 'Nº PROPOSTA', 'PROPOSTA']:
                logging.info(f"⏭️ PAULISTA linha {idx}: Pulando - proposta vazia ou cabeçalho ({proposta})")
                normalized_row = None
            else:
                logging.info(f"✅ PAULISTA linha {idx}: Proposta válida - vai processar")
                
                # Detectar órgão e operação
                orgao_detectado = detect_paulista_organ(especies_beneficio, produto, proposta)
                operacao_detectada = detect_paulista_operation(produto, especies_beneficio, status)
                
                # Aplicar formatação brasileira usando posições Unnamed corretas do mapeamento
                valor_operacao_raw = str(row.get('Unnamed: 11', '')).strip()  # Valor Solicitado
                valor_parcela_raw = str(row.get('Unnamed: 15', '')).strip()   # Valor Parcela  
                valor_liberado_raw = str(row.get('Unnamed: 12', '')).strip()  # Vl. Liberado
                cpf_raw = str(row.get('Unnamed: 4', '')).strip()             # CPF/CNPJ Proponente
                
                # Usar as funções globais de formatação
                valor_operacao_formatted = format_value_brazilian(valor_operacao_raw)
                valor_liberado_formatted = format_value_brazilian(valor_liberado_raw)
                valor_parcela_formatted = format_value_brazilian(valor_parcela_raw)
                cpf_formatted = format_cpf_global(cpf_raw)
                
                logging.info(f"✅ PAULISTA formatado: CPF={cpf_formatted}, Valor={valor_operacao_formatted}, Órgão={orgao_detectado}")
                
                normalized_row = {
                    "PROPOSTA": proposta,  # Unnamed: 0 = Nº Proposta
                    "ADE": proposta,  # Campo ADE explícito = mesma proposta
                    "DATA_CADASTRO": str(row.get('Unnamed: 2', '')).strip(),  # Data Captura
                    "BANCO": "BANCO PAULISTA",
                    "ORGAO": orgao_detectado,
                    "TIPO_OPERACAO": operacao_detectada,
                    "NUMERO_PARCELAS": str(row.get('Unnamed: 14', '')).strip(),  # Quant. Parcelas
                    "VALOR_OPERACAO": valor_operacao_formatted,  # ✅ Formatado brasileiro
                    "VALOR_LIBERADO": valor_liberado_formatted,  # ✅ Formatado brasileiro
                    "USUARIO_BANCO": str(row.get('Unnamed: 24', '')).strip(),   # Usuário Digitador
                    "SITUACAO": status,  # STATUS direto (será normalizado depois)
                    "DATA_PAGAMENTO": str(row.get('Unnamed: 21', '')).strip(),  # Dta. Integração
                    "CPF": cpf_formatted,  # ✅ Formatado brasileiro (XXX.XXX.XXX-XX)
                    "NOME": str(row.get('Unnamed: 5', '')).strip().upper(),     # Nome do Proponente ✅ Maiúsculas
                    "DATA_NASCIMENTO": "",  # Não disponível no PAULISTA
                    "CODIGO_TABELA": str(row.get('Unnamed: 16', '')).strip(),   # Plano - será mapeado pelo Storm depois
                    "VALOR_PARCELAS": valor_parcela_formatted,  # ✅ Formatado brasileiro
                    "TAXA": "0,00%",  # Padrão brasileiro
                    "OBSERVACOES": f"Contrato: {str(row.get('Unnamed: 1', '')).strip()} | Banco: {str(row.get('Unnamed: 8', '')).strip()} | Agência: {str(row.get('Unnamed: 9', '')).strip()}"
                }
                
                logging.info(f"✅✅✅ PAULISTA normalized_row criado com sucesso!")
                logging.info(f"✅✅✅ PAULISTA normalized_row final: {normalized_row}")
        
        elif bank_type == "BRB":
            # Mapeamento BRB (Banco de Brasília) - Estrutura REAL do arquivo
            # Colunas REAIS do arquivo BRB (Propostas-202593.csv):
            # - ID Card: ID interno Q-FAZ (2579370)
            # - Nº Contrato: Número da proposta BRB (1901615764) ✅ USAR ESTE!
            # - Nome do cliente
            # - CPF do Beneficiário (sem formatação)
            # - Data da Proposta
            # - Qtd. Parcelas
            # - Valor da Parcela (formato: 294,30)
            # - Valor da Proposta (formato: 13082,34)
            # - Tabela: TAXA em decimal (1.85, 1.79, 1) ✅ NÃO é código!
            # - Produto: Tipo operação (Refinanciamento, Novo, Portabilidade e Refinanciamento)
            # - Status da Proposta (Nova proposta, Pago, Perdido, etc)
            # - Sub-Status (opcional)
            # - Observações (opcional)
            # - E-mail Agente Responsável
            # - Parceiro: "70-BRB - Banco de Brasília S.A."
            
            normalized_row = {
                "PROPOSTA": str(row.get('Nº Contrato', '')).strip(),  # ✅ CORRIGIDO: Nº Contrato, não ID Card!
                "DATA_CADASTRO": str(row.get('Data da Proposta', '')).strip(),
                "BANCO": "BRB - CRÉDITO, FINANCIAMENTO E INVESTIMENTO",  # ✅ Nome completo
                "ORGAO": "INSS",  # ✅ Todos BRB são INSS (arquivo não tem coluna ORGÃO)
                "TIPO_OPERACAO": str(row.get('Produto', 'Margem Livre (Novo)')).strip(),  # ✅ CORRIGIDO: Produto, não OPERAÇÃO!
                "NUMERO_PARCELAS": str(row.get('Qtd. Parcelas', '')).strip(),
                "VALOR_OPERACAO": str(row.get('Valor da Proposta', '')).strip(),
                "VALOR_LIBERADO": str(row.get('Valor da Proposta', '')).strip(),
                "USUARIO_BANCO": str(row.get('E-mail Agente Responsável', '')).strip(),
                "SITUACAO": str(row.get('Status da Proposta', '')).strip(),
                "DATA_PAGAMENTO": "",  # ✅ Arquivo não tem Data da PAGAMENTO, será vazio
                "CPF": str(row.get('CPF do Beneficiário', '')).strip(),
                "NOME": str(row.get('Nome do cliente', '')).strip().upper(),
                "DATA_NASCIMENTO": "",  # Não disponível
                "CODIGO_TABELA": str(row.get('Tabela', '')).strip(),  # ✅ Tabela = TAXA que vira código (1.85 → 185)
                "VALOR_PARCELAS": str(row.get('Valor da Parcela', '')).strip(),
                "TAXA": str(row.get('Tabela', '')).strip(),  # ✅ CORRIGIDO: Tabela contém TAXA!
                "OBSERVACOES": str(row.get('Observações', '')).strip()
            }
            
            # ✅ FORMATAÇÃO BRASILEIRA para BRB
            # Converter valores para formato brasileiro COM R$
            valor_operacao = normalized_row.get("VALOR_OPERACAO", "")
            if valor_operacao:
                valor_formatado = format_value_brazilian(valor_operacao)
                normalized_row["VALOR_OPERACAO"] = f"R$ {valor_formatado}"
            
            valor_liberado = normalized_row.get("VALOR_LIBERADO", "")
            if valor_liberado:
                valor_formatado = format_value_brazilian(valor_liberado)
                normalized_row["VALOR_LIBERADO"] = f"R$ {valor_formatado}"
            
            valor_parcelas = normalized_row.get("VALOR_PARCELAS", "")
            if valor_parcelas:
                valor_formatado = format_value_brazilian(valor_parcelas)
                normalized_row["VALOR_PARCELAS"] = f"R$ {valor_formatado}"
            
            # Formatar CPF para padrão brasileiro (vem sem formatação: 13097582800)
            normalized_row["CPF"] = format_cpf_global(normalized_row.get("CPF", ""))
            
            # Converter CODIGO_TABELA de taxa decimal para código inteiro
            # BRB: Tabela = 1.85 → CODIGO_TABELA = 185
            #      Tabela = 1.79 → CODIGO_TABELA = 179
            #      Tabela = 1 → CODIGO_TABELA = 100
            codigo_tabela_raw = normalized_row.get("CODIGO_TABELA", "")
            if codigo_tabela_raw:
                try:
                    taxa_str = str(codigo_tabela_raw).replace(',', '.')
                    taxa_float = float(taxa_str)
                    # Multiplicar por 100 para obter código
                    codigo_int = int(taxa_float * 100)
                    normalized_row["CODIGO_TABELA"] = str(codigo_int)
                    logging.info(f"  🔢 CODIGO_TABELA: {codigo_tabela_raw} → {codigo_int}")
                except (ValueError, TypeError):
                    normalized_row["CODIGO_TABELA"] = str(codigo_tabela_raw)
            
            # Formatar TAXA para percentual brasileiro
            # BRB vem como decimal COM PONTO: 1.85 → deve virar 1,85%
            taxa_raw = normalized_row.get("TAXA", "")
            if taxa_raw:
                try:
                    taxa_str = str(taxa_raw).replace(',', '.')
                    taxa_float = float(taxa_str)
                    
                    if taxa_float < 10:
                        normalized_row["TAXA"] = f"{taxa_float:.2f}%".replace('.', ',')
                    else:
                        taxa_percentual = taxa_float / 100
                        normalized_row["TAXA"] = f"{taxa_percentual:.2f}%".replace('.', ',')
                except (ValueError, TypeError):
                    normalized_row["TAXA"] = format_percentage_brazilian(taxa_raw)
            
            logging.info(f"✅ BRB formatado: PROPOSTA={normalized_row.get('PROPOSTA')}, TAXA={normalized_row.get('TAXA')}, CODIGO={normalized_row.get('CODIGO_TABELA')}")
            
            # 🔧 NORMALIZAÇÃO DE STATUS BRB
            # Nova proposta → AGUARDANDO
            # Ag. aprovação do convênio → AGUARDANDO
            # Formalização cliente → AGUARDANDO
            # Pendente de documentação → AGUARDANDO
            # (vazio) → AGUARDANDO
            # Perdido → CANCELADO
            # PAGO → PAGO
            situacao_original = normalized_row.get('SITUACAO', '').strip()
            situacao_upper = situacao_original.upper()
            
            if not situacao_original or situacao_original == '':
                normalized_row['SITUACAO'] = 'AGUARDANDO'
                logging.info(f"  📊 STATUS: (vazio) → AGUARDANDO")
            elif 'NOVA PROPOSTA' in situacao_upper:
                normalized_row['SITUACAO'] = 'AGUARDANDO'
                logging.info(f"  📊 STATUS: {situacao_original} → AGUARDANDO")
            elif 'APROVAÇÃO' in situacao_upper or 'CONVÊNIO' in situacao_upper or 'CONVENIO' in situacao_upper:
                normalized_row['SITUACAO'] = 'AGUARDANDO'
                logging.info(f"  📊 STATUS: {situacao_original} → AGUARDANDO")
            elif 'FORMALIZAÇÃO' in situacao_upper or 'FORMALIZACAO' in situacao_upper:
                normalized_row['SITUACAO'] = 'AGUARDANDO'
                logging.info(f"  📊 STATUS: {situacao_original} → AGUARDANDO")
            elif 'PENDENTE' in situacao_upper or 'DOCUMENTAÇÃO' in situacao_upper or 'DOCUMENTACAO' in situacao_upper:
                normalized_row['SITUACAO'] = 'AGUARDANDO'
                logging.info(f"  📊 STATUS: {situacao_original} → AGUARDANDO")
            elif 'PERDIDO' in situacao_upper:
                normalized_row['SITUACAO'] = 'CANCELADO'
                logging.info(f"  📊 STATUS: {situacao_original} → CANCELADO")
            elif 'PAGO' in situacao_upper:
                normalized_row['SITUACAO'] = 'PAGO'
                logging.info(f"  📊 STATUS: {situacao_original} → PAGO")
            elif 'CANCELAD' in situacao_upper:
                normalized_row['SITUACAO'] = 'CANCELADO'
                logging.info(f"  📊 STATUS: {situacao_original} → CANCELADO")
            else:
                # Manter original se não reconhecer
                normalized_row['SITUACAO'] = 'AGUARDANDO'
                logging.info(f"  📊 STATUS: {situacao_original} → AGUARDANDO (padrão)")
            
            # 🔧 REGRAS ESPECÍFICAS BRB - Portabilidade e Refinanciamento
            try:
                tipo_operacao = normalized_row.get('TIPO_OPERACAO', '').upper()
                observacoes = normalized_row.get('OBSERVACOES', '').upper()
                
                # Produtos BRB que são Portabilidade/Refin:
                # - "Portabilidade e Refinanciamento" (campo Produto)
                # - "Refinanciamento" (campo Produto)
                # Estes NÃO devem esvaziar CODIGO_TABELA (código deve vir da taxa)
                
                if 'PORTABILIDADE' in tipo_operacao:
                    # Portabilidade: manter CODIGO_TABELA e DATA_PAGAMENTO vazios
                    normalized_row['DATA_PAGAMENTO'] = ''
                    
                    # Adicionar marcador nas observações
                    obs_atual = normalized_row.get('OBSERVACOES', '')
                    if obs_atual:
                        normalized_row['OBSERVACOES'] = f"{obs_atual} | MANUAL: Portabilidade/Refin"
                    else:
                        normalized_row['OBSERVACOES'] = "MANUAL: Portabilidade/Refin"
                    
                    logging.info(f"🔧 BRB PROPOSTA {normalized_row.get('PROPOSTA')}: {tipo_operacao} - DATA_PAGAMENTO vazio, CODIGO_TABELA mantido")
            except Exception as e:
                logging.warning(f"⚠️ Erro aplicando regras específicas BRB: {e}")
        
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
                "CODIGO_TABELA": str(row.get('CodigoProduto', '')).strip(),
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
        
        # ✅ VERIFICAÇÃO CRÍTICA: Pular linhas filtradas (normalized_row = None)
        # DEVE VIR ANTES de qualquer acesso a normalized_row.get() ou normalized_row[]
        if normalized_row is None:
            logging.info(f"⏭️ [{bank_type}] Linha filtrada (normalized_row=None), pulando mapeamento e validação")
            continue
        
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
        
        # 🔧 REGRA GERAL: Se SITUACAO vier vazia, definir como AGUARDANDO
        if not normalized_row.get("SITUACAO") or str(normalized_row.get("SITUACAO", "")).strip() == "":
            normalized_row["SITUACAO"] = "AGUARDANDO"
            logging.info(f"📋 Status vazio detectado - definido como AGUARDANDO para PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}")
        
        # Aplicar mapeamento de código de tabela (sem dependência de usuário para maior estabilidade)
        # EXCETO para DIGIO, AVERBAI, DAYCOVAL, QUERO_MAIS e SANTANDER que já têm códigos corretos
        # VCTEX PRECISA de mapeamento: "Tabela EXP" (banco) → "TabelaEXP" (storm)
        if bank_type == "DIGIO":
            # DIGIO já aplicou mapeamento específico, pular mapeamento geral
            logging.info(f"📊 PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: DIGIO já mapeado, pulando mapeamento geral")
            mapping_result = None
        elif bank_type == "SANTANDER":
            # 🏦 SANTANDER: Códigos já extraídos corretamente (810021387, 82721387, etc.)
            codigo_direto = normalized_row.get("CODIGO_TABELA", "")
            logging.info(f"✅ PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: SANTANDER código direto {codigo_direto}, pulando mapeamento automático")
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
            orgao_quero = normalized_row.get("ORGAO", "")
            tipo_op_quero = normalized_row.get("TIPO_OPERACAO", "")
            logging.warning(f"🏆 PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: QUERO MAIS processado - ORGAO={orgao_quero}, TIPO_OP={tipo_op_quero}, CODIGO={codigo_direto}")
            mapping_result = None
        elif bank_type == "VCTEX":
            # 🎯 VCTEX - Processamento com mapeamento direto (BYPASS DO SISTEMA CSV)
            tabela_original = normalized_row.get("CODIGO_TABELA", "").strip()
            
            # Mapeamento direto VCTEX - EXPANDIDO para cobrir mais casos INSS
            vctex_map = {
                "Tabela Vamo Com Tudo": "TabelaVamoComTudo",
                "Tabela Vamo com tudo com Seguro": "TabelaVamoComTudoComSeg", 
                "Tabela Exponencial": "TabelaExponencial",
                "Tabela Relax": "TabelaRelax",
                "Tabela VCT": "TabelaVCT",
                "Tabela EXP": "TabelaEXP",
                "Tabela INSS Exponencial TX 1,85 - com Seguro Hot": "TabelaExponencialHot",
                "TabelaVamoComTudoComSeg": "TabelaVamoComTudoComSeg",
                # 🔥 EXPANSÃO INSS: Mais variações comuns
                "EXP": "TabelaEXP",
                "Exponencial": "TabelaExponencial", 
                "TABELA EXP": "TabelaEXP",
                "TABELA EXPONENCIAL": "TabelaExponencial",
                "Tabela Exp": "TabelaEXP",
                "tabela exp": "TabelaEXP",
                "tabela exponencial": "TabelaExponencial",
                "INSS Exponencial": "TabelaExponencial",
                "INSS EXP": "TabelaEXP",
                "Vamo Com Tudo": "TabelaVamoComTudo",
                "VAMO COM TUDO": "TabelaVamoComTudo",
                "VCT": "TabelaVCT",
                "Relax": "TabelaRelax",
                "RELAX": "TabelaRelax"
            }
            
            # Aplicar mapeamento direto se encontrar
            if tabela_original in vctex_map:
                codigo_novo = vctex_map[tabela_original]
                normalized_row["CODIGO_TABELA"] = codigo_novo
                normalized_row["TAXA"] = "1,83%"
                normalized_row["TIPO_OPERACAO"] = "Margem Livre (Novo)"
                print(f"✅🎯 VCTEX MAPEAMENTO DIRETO: '{tabela_original}' → '{codigo_novo}'")
                logging.warning(f"✅🎯 VCTEX MAPEAMENTO DIRETO: '{tabela_original}' → '{codigo_novo}'")
            else:
                print(f"⚠️🎯 VCTEX SEM MAPEAMENTO: mantendo '{tabela_original}'")
                logging.warning(f"⚠️🎯 VCTEX SEM MAPEAMENTO: mantendo '{tabela_original}'")
            
            # SKIP o sistema de mapeamento CSV para VCTEX - usar None para evitar sobrescrita
            mapping_result = None
        elif bank_type == "FACTA92":
            # 🎯 FACTA92 - código vem correto do arquivo (NR_TABCOM), buscar por BANCO + CODIGO apenas
            codigo_direto = normalized_row.get("CODIGO_TABELA", "")
            banco_para_mapeamento = normalized_row.get("BANCO", "")
            
            print(f"🚨🚨🚨 FACTA92 INICIOU - Proposta {normalized_row.get('PROPOSTA', 'N/A')}, Codigo {codigo_direto}")
            logging.warning(f"� FACTA92 PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: Código {codigo_direto}, buscando mapeamento por BANCO + CODIGO")
            
            # 🔍 Buscar no TABELA_MAPPING usando apenas BANCO e CODIGO (ignorar ORGAO e OPERACAO)
            mapping_result = None
            codigo_norm = ' '.join(str(codigo_direto).strip().upper().split()) if codigo_direto else ""
            banco_norm = ' '.join(str(banco_para_mapeamento).strip().upper().split())
            
            logging.info(f"🔍 FACTA92 Debug INICIAL: banco_norm='{banco_norm}', codigo_norm='{codigo_norm}', codigo_isdigit={codigo_norm.isdigit()}")
            logging.info(f"🔍 FACTA92 TABELA_MAPPING type: {type(TABELA_MAPPING)}, len: {len(TABELA_MAPPING) if TABELA_MAPPING else 0}")
            
            # DEBUG: Mostrar TODAS as chaves FACTA que contém 61700 ou CLT
            if TABELA_MAPPING:
                facta_keys = [k for k in TABELA_MAPPING.keys() if 'FACTA' in k]
                logging.warning(f"🔍 FACTA92 Total de chaves FACTA no mapping: {len(facta_keys)}")
                
                # Procurar especificamente 61700
                keys_61700 = [k for k in facta_keys if '61700' in k]
                logging.warning(f"🔍 FACTA92 Chaves com 61700: {len(keys_61700)}")
                for k in keys_61700:
                    logging.warning(f"   -> '{k}'")
                    
                # Mostrar todas as chaves CLT
                keys_clt = [k for k in facta_keys if 'CLT' in k or 'CRÉDITO DO TRABALHADOR' in k or 'CREDITO DO TRABALHADOR' in k]
                logging.warning(f"🔍 FACTA92 Total chaves CLT/CREDITO: {len(keys_clt)}")
                for i, k in enumerate(keys_clt[:5]):
                    logging.warning(f"   CLT #{i+1}: '{k}'")
            
            if codigo_norm and TABELA_MAPPING:
                matches_found = 0
                banco_matches = 0
                for key, details in TABELA_MAPPING.items():
                    parts = key.split('|')
                    if len(parts) == 4:
                        key_banco, key_orgao, key_operacao, key_tabela = parts
                        key_banco_norm = ' '.join(key_banco.upper().split())
                        key_tabela_norm = ' '.join(key_tabela.upper().split())
                        
                        # Contar quantos matches de banco temos
                        if banco_norm == key_banco_norm:
                            banco_matches += 1
                            
                            # Debug: Log primeiras 3 chaves do CSV que batem com BANCO
                            if matches_found < 3:
                                logging.info(f"🔍 FACTA92 Exemplo chave CSV #{matches_found+1}: '{key}' → banco='{key_banco_norm}', tabela='{key_tabela_norm}'")
                                matches_found += 1
                        
                        # Match EXATO por BANCO e código numérico no início da tabela
                        if banco_norm == key_banco_norm:
                            # 🔧 CORREÇÃO: Tabela vem como "61700 - CLT NOVO GOLD PN-S", então verificar se começa com "61700 " OU "61700-"
                            codigo_match = False
                            if codigo_norm.isdigit():
                                # Aceitar tanto "61700 -" quanto "61700 " quanto "61700-"
                                if (key_tabela_norm.startswith(codigo_norm + ' ') or 
                                    key_tabela_norm.startswith(codigo_norm + '-') or
                                    key_tabela_norm == codigo_norm):
                                    codigo_match = True
                                    
                            # Log TODOS os testes de código para 61700
                            if codigo_norm == '61700':
                                logging.info(f"🎯 FACTA92 Testando 61700: key_tabela_norm='{key_tabela_norm}', codigo_match={codigo_match}")
                            
                            if codigo_match:
                                # Encontrou! Usar esse mapeamento mas SEM sobrescrever o código
                                mapping_result = {
                                    'orgao_storm': details.get('orgao_storm', ''),
                                    'operacao_storm': details.get('operacao_storm', ''),
                                    'taxa_storm': details.get('taxa_storm', '0,00%')
                                }
                                logging.info(f"✅ FACTA92: Encontrou mapeamento para código {codigo_direto}: ORGAO={mapping_result['orgao_storm']}, OPERACAO={mapping_result['operacao_storm']}, TAXA={mapping_result['taxa_storm']}")
                                break
                
                # Log resumo da busca
                logging.info(f"🔍 FACTA92 Resumo busca código {codigo_norm}: {banco_matches} chaves com BANCO match, mapping_result={'ENCONTRADO' if mapping_result else 'NÃO ENCONTRADO'}")
            
            if not mapping_result:
                logging.warning(f"⚠️ FACTA92 PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: Mapeamento NÃO encontrado para código {codigo_direto}")
                logging.warning(f"⚠️ FACTA92 Debug: banco_norm='{banco_norm}', codigo_norm='{codigo_norm}', TABELA_MAPPING tem {len(TABELA_MAPPING)} entradas")
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
                codigo_anterior = normalized_row.get("CODIGO_TABELA", "")
                codigo_novo = mapping_result.get('codigo_tabela', '')
                normalized_row["CODIGO_TABELA"] = codigo_novo
                
                # Log específico para VCTEX
                if bank_type == "VCTEX":
                    print(f"🔄🔥 VCTEX APLICANDO MAPEAMENTO: '{codigo_anterior}' → '{codigo_novo}'")
                    logging.warning(f"🔄🔥 VCTEX APLICANDO MAPEAMENTO: '{codigo_anterior}' → '{codigo_novo}'")
                    print(f"🔥 VCTEX CODIGO_TABELA FINAL: '{normalized_row.get('CODIGO_TABELA', '')}'")
                    logging.warning(f"🔥 VCTEX CODIGO_TABELA FINAL: '{normalized_row.get('CODIGO_TABELA', '')}'")
            elif bank_type == "VCTEX":
                # Se é VCTEX mas não tem mapping_result, manter original e avisar
                print(f"⚠️🔥 VCTEX SEM MAPEAMENTO: mantendo '{normalized_row.get('CODIGO_TABELA', '')}'")
                logging.warning(f"⚠️🔥 VCTEX SEM MAPEAMENTO: mantendo '{normalized_row.get('CODIGO_TABELA', '')}')")
            
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
            # 🔧 CORREÇÃO FACTA92: SEMPRE definir TAXA como 0,00% se não encontrou mapeamento
            if bank_type == "FACTA92":
                normalized_row["TAXA"] = "0,00%"
                logging.info(f"✅ FACTA92: Sem mapeamento, TAXA definida como 0,00%")
            elif not normalized_row.get("TAXA") or normalized_row.get("TAXA") == "":
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
        # EXCETO para DAYCOVAL que já foram corrigidas pelo fix_daycoval_date()
        data_cadastro_original = normalized_row.get('DATA_CADASTRO', '')
        data_pagamento_original = normalized_row.get('DATA_PAGAMENTO', '')
        banco_atual = normalized_row.get('BANCO', '').upper()
        
        # Log DEPOIS do mapeamento
        logging.info(f"📗 DEPOIS do mapeamento - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: ORGAO={normalized_row.get('ORGAO', '')}, CODIGO_TABELA={normalized_row.get('CODIGO_TABELA', '')}, TAXA={normalized_row.get('TAXA', '')}, OPERACAO={normalized_row.get('TIPO_OPERACAO', '')}")
        
        # ✅ GARANTIR que as datas originais sejam mantidas
        # ⚠️  EXCETO para DAYCOVAL que precisa manter as datas corrigidas pelo fix_daycoval_date()
        if data_cadastro_original and 'DAYCOVAL' not in banco_atual:
            normalized_row['DATA_CADASTRO'] = data_cadastro_original
        if data_pagamento_original and 'DAYCOVAL' not in banco_atual: 
            normalized_row['DATA_PAGAMENTO'] = data_pagamento_original
            
        if 'DAYCOVAL' in banco_atual:
            logging.info(f"🔧 DAYCOVAL - MANTENDO datas corrigidas pelo fix_daycoval_date(): CADASTRO='{normalized_row.get('DATA_CADASTRO')}' | PAGAMENTO='{normalized_row.get('DATA_PAGAMENTO')}'")
        else:
            logging.info(f"📅 DATAS FINAIS PRESERVADAS - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: CADASTRO='{normalized_row.get('DATA_CADASTRO')}' | PAGAMENTO='{normalized_row.get('DATA_PAGAMENTO')}'")

        # 📞 LOG FINAL DOS CAMPOS DE CONTATO
        contato_campos = []
        if normalized_row.get('TELEFONE') and normalized_row.get('TELEFONE').strip() != "":
            contato_campos.append(f"TEL:{normalized_row.get('TELEFONE')}")
        if normalized_row.get('ENDERECO') and normalized_row.get('ENDERECO').strip() != "":
            contato_campos.append(f"END:{normalized_row.get('ENDERECO')[:15]}...")
        if normalized_row.get('BAIRRO') and normalized_row.get('BAIRRO').strip() != "":
            contato_campos.append(f"BAI:{normalized_row.get('BAIRRO')}")
        if normalized_row.get('CIDADE') and normalized_row.get('CIDADE').strip() != "":
            contato_campos.append(f"CID:{normalized_row.get('CIDADE')}")
        if normalized_row.get('UF') and normalized_row.get('UF').strip() != "":
            contato_campos.append(f"UF:{normalized_row.get('UF')}")
        if normalized_row.get('CEP') and normalized_row.get('CEP').strip() != "":
            contato_campos.append(f"CEP:{normalized_row.get('CEP')}")
        
        if contato_campos:
            logging.info(f"📞 CONTATO FINAL {banco_atual} - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: {' | '.join(contato_campos)}")
        else:
            logging.info(f"📞 CONTATO FINAL {banco_atual} - PROPOSTA {normalized_row.get('PROPOSTA', 'N/A')}: SEM DADOS DE CONTATO")

        
        # ✅ VALIDAÇÃO RIGOROSA: Filtrar cabeçalhos e linhas vazias
        proposta = str(normalized_row.get("PROPOSTA", "")).strip()
        nome = str(normalized_row.get("NOME", "")).strip()
        cpf = str(normalized_row.get("CPF", "")).strip()
        banco = str(normalized_row.get("BANCO", "")).strip()
        
        logging.info(f"🔍 VALIDAÇÃO FINAL - Proposta: '{proposta}', Nome: '{nome[:20] if nome else 'N/A'}', CPF: '{cpf}', Banco: '{banco}'")
        
        # ❌ REJEITAR linhas problemáticas específicas
        problematic_indicators = [
            # Cabeçalhos óbvios
            "proposta", "data cadastro", "tabela utilizada", "qtd parcelas", "valor liberacao",
            # Linhas vazias/numéricas sem contexto
            proposta in ["51", ""],
            # Linhas com apenas "nan" ou valores vazios em campos críticos
            "matrícula: nan" in str(normalized_row.get("OBSERVACOES", "")).lower(),
            # Cabeçalho do VCTEX
            "tabela inss exponencial" in proposta.lower() or "com seguro hot" in proposta.lower(),
            # Linhas só com banco sem proposta válida
            not proposta and banco and not nome and not cpf,
        ]
        
        # ❌ Se tem indicadores problemáticos, REJEITAR
        has_problematic = any(problematic_indicators) or proposta.lower() in ["nan", "none", "null", ""]
        
        # ✅ CRITÉRIO MAIS FLEXÍVEL: Aceitar dados reais dos bancos
        has_valid_proposta = (
            proposta and 
            len(proposta) >= 2 and  # ✅ Reduzido: mínimo 2 chars
            not has_problematic and
            not proposta.lower().startswith(("tabela", "data", "valor", "cliente"))
        )
        
        has_valid_nome = nome and len(nome) >= 3 and nome.upper() not in ["CLIENTE", "NOME", "NOME DO CLIENTE"]  # ✅ Reduzido: 3+ chars
        has_valid_cpf = cpf and len(cpf) >= 8   # ✅ Mais flexível: 8+ chars (pode ser formatado ou não)
        
        # ✅ CRITÉRIO RELAXADO: Aceitar se tem proposta válida OU pelo menos nome e CPF 
        is_valid_record = has_valid_proposta or (has_valid_nome and has_valid_cpf)
        
        logging.info(f"   ✅ VALIDAÇÃO: proposta_valid={has_valid_proposta}, nome_valid={has_valid_nome}, cpf_valid={has_valid_cpf}, problematic={has_problematic}, RESULTADO={is_valid_record}")
        
        if is_valid_record:
            normalized_data.append(normalized_row)
            logging.info(f"✅✅✅ Linha ACEITA: Proposta='{proposta}', Nome='{nome[:15] if nome else 'N/A'}', CPF='{cpf[:8] if cpf else 'N/A'}'")
        else:
            logging.warning(f"❌ Linha REJEITADA (rigorosa): Proposta='{proposta}', Nome='{nome}', CPF='{cpf}', Problematic={has_problematic}")
    
    logging.info(f"📊 [{bank_type}] RESUMO: {len(normalized_data)} registros válidos de {len(df)} linhas processadas")
    
    # Log detalhado se não temos dados
    if len(normalized_data) == 0:
        logging.error(f"❌ [{bank_type}] NENHUM dado válido foi extraído!")
        logging.error(f"   📋 Colunas do DataFrame: {list(df.columns)[:10]}...")
        if not df.empty:
            logging.error(f"   📄 Primeira linha: {dict(df.iloc[0])}") 
        return pd.DataFrame()
    
    # 🧹 FILTRO DE SEGURANÇA: Remover qualquer None que possa ter escapado
    normalized_data_clean = [row for row in normalized_data if row is not None and isinstance(row, dict)]
    
    if len(normalized_data_clean) != len(normalized_data):
        logging.warning(f"⚠️ [{bank_type}] Removidos {len(normalized_data) - len(normalized_data_clean)} registros None da lista")
    
    if len(normalized_data_clean) == 0:
        logging.error(f"❌ [{bank_type}] Após filtrar None, nenhum dado restou!")
        return pd.DataFrame()
    
    return pd.DataFrame(normalized_data_clean)

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
        # Debug específico para PAULISTA
        if bank_type == "PAULISTA":
            logging.info(f"🏦 map_to_final_format: PAULISTA com {len(df)} linhas")
            logging.info(f"🏦 Primeiras 3 linhas do DF:")
            for i, (idx, row) in enumerate(df.head(3).iterrows()):
                logging.info(f"   Linha {idx}: Unnamed:0='{row.get('Unnamed: 0', 'N/A')}'")
        
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
            
            # 🌎 APLICAR FORMATAÇÃO GLOBAL BRASILEIRA (CPF + Valores Monetários)
            cpf_raw = row.get("CPF", "")
            cpf_formatted = format_cpf_global(cpf_raw)
            
            valor_parcelas_raw = row.get("VALOR_PARCELAS", "")
            valor_parcelas_formatted = format_value_brazilian(valor_parcelas_raw)
            
            valor_operacao_raw = row.get("VALOR_OPERACAO", "")
            valor_operacao_formatted = format_value_brazilian(valor_operacao_raw)
            
            valor_liberado_raw = row.get("VALOR_LIBERADO", "")
            valor_liberado_formatted = format_value_brazilian(valor_liberado_raw)
            
            final_row = {
                "PROPOSTA": row.get("PROPOSTA", ""),
                "DATA CADASTRO": row.get("DATA_CADASTRO", ""),
                "BANCO": row.get("BANCO", ""),
                "ORGAO": row.get("ORGAO", ""),
                "CODIGO TABELA": row.get("CODIGO_TABELA", ""),
                "TIPO DE OPERACAO": row.get("TIPO_OPERACAO", ""),
                "NUMERO PARCELAS": row.get("NUMERO_PARCELAS", ""),
                "VALOR PARCELAS": valor_parcelas_formatted,  # ✅ Formatado em padrão brasileiro
                "VALOR OPERACAO": valor_operacao_formatted,  # ✅ Formatado em padrão brasileiro
                "VALOR LIBERADO": valor_liberado_formatted,  # ✅ Formatado em padrão brasileiro
                "VALOR QUITAR": "",
                "USUARIO BANCO": row.get("USUARIO_BANCO", ""),
                "CODIGO LOJA": "",
                "SITUACAO": situacao,
                "DATA DE PAGAMENTO": data_pagamento,
                "CPF": cpf_formatted,  # ✅ Formatado em padrão brasileiro (XXX.XXX.XXX-XX)
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
    """Remoção aprimorada de duplicatas baseada na Storm - usa ADE para comparação precisa"""
    if df.empty:
        return df
    
    filtered_data = []
    removed_count = 0
    pago_removido = 0
    cancelado_removido = 0
    
    logging.info(f"🔍 Verificando {len(df)} registros contra {len(storm_data)} ADEs da Storm")
    
    for _, row in df.iterrows():
        proposta = str(row.get('PROPOSTA', '')).strip()
        
        if not proposta or proposta.lower() in ['nan', 'null', '']:
            # Se não tem proposta válida, incluir mesmo assim
            filtered_data.append(row.to_dict())
            continue
        
        # Limpar proposta para comparar com ADEs da Storm (apenas números)
        proposta_clean = ''.join(c for c in proposta if c.isdigit())
        
        # Verificar se ADE existe na Storm e está PAGO/CANCELADO
        skip_record = False
        matched_status = None
        
        # Comparação exata de ADE 
        if proposta_clean in storm_data:
            matched_status = storm_data[proposta_clean]
            if matched_status in ["PAGO", "CANCELADO"]:
                skip_record = True
                removed_count += 1
                if matched_status == "PAGO":
                    pago_removido += 1
                else:
                    cancelado_removido += 1
                
                # Log apenas algumas para debug
                if removed_count <= 3:
                    logging.info(f"🚫 Removendo duplicata: ADE={proposta_clean} Status={matched_status}")
        
        # Se não foi removido como duplicata, incluir no resultado
        if not skip_record:
            filtered_data.append(row.to_dict())
    
    logging.info(f"📊 DUPLICATAS PROCESSADAS:")
    logging.info(f"   ✅ Registros mantidos: {len(filtered_data)}")
    logging.info(f"   🚫 Total removidos: {removed_count}")
    logging.info(f"      💰 PAGO removidos: {pago_removido}")
    logging.info(f"      ❌ CANCELADO removidos: {cancelado_removido}")
    
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
        "TELEFONE", "ENDERECO", "BAIRRO", "CEP", "UF",
        "TIPO DE CONTA", "TIPO DE PAGAMENTO", "AGENCIA CLIENTE", "CONTA CLIENTE",
        "FORMALIZACAO DIGITAL", "TAXA", "OBSERVACOES"
    ]
    
    # Reordenar colunas
    df_ordered = df.reindex(columns=required_columns, fill_value="")
    
    # 🧹 LIMPEZA ROBUSTA: Aplicar limpeza de caracteres especiais no relatório final
    logging.info(f"🧹 Aplicando limpeza de caracteres especiais no relatório final ({len(df_ordered)} linhas)")
    
    for col in df_ordered.columns:
        df_ordered[col] = df_ordered[col].astype(str).apply(clean_special_characters)
        df_ordered[col] = df_ordered[col].replace(['nan', 'None', 'null', 'NaN'], '')
    
    logging.info(f"✅ Limpeza de caracteres especiais concluída no relatório final")
    
    # 🔧 FIX: Corrigir formatação do CPF digitador (USUARIO BANCO) no relatório final
    if "USUARIO BANCO" in df_ordered.columns:
        def format_cpf_usuario_banco(cpf_str):
            """Manter formato original dos bancos que já vêm corretos
            QUERO MAIS, C6, PAULISTA, DIGIO, etc: Códigos como '12345678901_202902' MANTÉM com underscore
            Apenas formatar como CPF se for CPF puro sem código
            """
            if not cpf_str or cpf_str in ['', '0', '000.000.000-00']:
                return ''  # ✅ Retornar vazio em vez de CPF falso
            
            cpf_clean = str(cpf_str).strip()
            
            # 🎯 Se contém underscore, é formato banco correto - MANTER COMO ESTÁ
            if '_' in cpf_clean:
                # Ex: "12345678901_202902" → "12345678901_202902" (manter original)
                return cpf_clean
            
            # 🎯 Se tem mais de 14 dígitos, provavelmente é código longo - manter como está  
            cpf_digits = ''.join(filter(str.isdigit, cpf_clean))
            if len(cpf_digits) > 14:
                return cpf_clean  # Manter códigos longos originais
            
            # 🎯 CPF normal (sem código): formatar no padrão brasileiro
            if len(cpf_digits) == 11:
                return f"{cpf_digits[:3]}.{cpf_digits[3:6]}.{cpf_digits[6:9]}-{cpf_digits[9:11]}"
            else:
                # Menos de 11 dígitos ou formato especial, manter original
                return cpf_clean
        
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
                
                # DEBUG: Log adicional para PAULISTA
                if 'AF5EEBB7' in file.filename or 'paulista' in file.filename.lower():
                    logging.error(f"🔍 DEBUG PAULISTA: Arquivo={file.filename}, Banco detectado={bank_type}")
                    logging.error(f"🔍 DEBUG PAULISTA: Primeiras colunas: {list(df.columns)[:10]}")
                    if not df.empty:
                        first_row = df.iloc[0].to_dict()
                        logging.error(f"🔍 DEBUG PAULISTA: Primeira linha: {first_row}")
                
                # Mapear para formato final
                if bank_type == "PAULISTA":
                    logging.error(f"🏦 PAULISTA: Chamando map_to_final_format com {len(df)} linhas")
                
                mapped_df, mapped_count = map_to_final_format(df, bank_type)
                
                logging.info(f"🗺️ MAPEAMENTO RESULTADO: {bank_type} → {len(mapped_df)} linhas mapeadas de {len(df)} originais")
                
                if mapped_df.empty:
                    logging.error(f"❌ CRÍTICO: Nenhum dado mapeado para {file.filename} (banco: {bank_type})")
                    logging.error(f"   📊 DataFrame original tinha {len(df)} linhas")
                    logging.error(f"   🔍 Primeiras colunas do DF: {list(df.columns)[:10] if not df.empty else 'DF vazio'}")
                    continue
                
                # Remover duplicatas baseado na Storm
                original_count = len(mapped_df)
                filtered_df = remove_duplicates_enhanced(mapped_df, storm_data_global)
                duplicates_removed = original_count - len(filtered_df)
                
                logging.info(f"📊 DUPLICATAS: {duplicates_removed} removidas, {len(filtered_df)} restantes de {original_count}")
                
                if not filtered_df.empty:
                    all_final_data.append(filtered_df)
                    logging.info(f"✅ SUCESSO: DataFrame de {bank_type} adicionado ao resultado final ({len(filtered_df)} linhas)")
                else:
                    logging.error(f"❌ CRÍTICO: Todas as linhas de {bank_type} foram removidas como duplicatas!")
                    logging.error(f"   📊 Original: {original_count} → Duplicatas: {duplicates_removed} → Restou: 0")
                
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
        
        # 🧹 LIMPEZA FINAL: Garantir que não há caracteres especiais no relatório final
        logging.info(f"🧹 Aplicando limpeza final de caracteres especiais no relatório combinado ({len(final_df)} registros)")
        for col in final_df.columns:
            if final_df[col].dtype == 'object':
                final_df[col] = final_df[col].astype(str).apply(clean_special_characters)
        logging.info(f"✅ Limpeza final concluída - relatório pronto para Storm")
        
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

# Mount static files for frontend (comentado para Railway - frontend está no Azure)
# app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Configure CORS with a safe default.
# If CORS_ORIGINS is set to '*' or empty, we allow all origins but disable credentials
# because Starlette does not allow allow_credentials=True with '*' origin.
cors_origins_env = os.environ.get('CORS_ORIGINS', '').strip()
if not cors_origins_env or cors_origins_env == '*':
    # Allow all origins (no credentials)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Parse a comma-separated list of allowed origins and enable credentials
    origins_list = [o.strip() for o in cors_origins_env.split(',') if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=origins_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
