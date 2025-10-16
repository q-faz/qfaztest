#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Correção de caracteres especiais no relat_orgaos.csv
"""

import pandas as pd
import os

def fix_relat_orgaos_encoding():
    """Corrigir encoding do arquivo relat_orgaos.csv"""
    
    file_path = "./backend/relat_orgaos.csv"
    backup_path = "./backend/relat_orgaos_backup.csv"
    
    print("🔧 CORRIGINDO ENCODING DO relat_orgaos.csv")
    print("=" * 50)
    
    # Fazer backup
    if os.path.exists(file_path):
        import shutil
        shutil.copy2(file_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
    
    # Tentar ler com diferentes encodings
    df = None
    original_encoding = None
    
    for encoding in ['latin1', 'cp1252', 'utf-8']:
        try:
            df = pd.read_csv(file_path, encoding=encoding, sep=';')
            original_encoding = encoding
            print(f"✅ Arquivo lido com encoding: {encoding}")
            break
        except Exception as e:
            print(f"❌ Falhou com {encoding}: {e}")
            continue
    
    if df is None:
        print("❌ Não foi possível ler o arquivo")
        return
    
    print(f"📊 Arquivo original: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Mostrar caracteres problemáticos antes
    print("\n🔍 CARACTERES PROBLEMÁTICOS ENCONTRADOS:")
    problematic_chars = {}
    
    for col in df.columns:
        if any(char in str(col) for char in ['�', '�', '�']):
            print(f"   Coluna: '{col}'")
    
    for idx, row in df.head(10).iterrows():
        for col in df.columns:
            value = str(row[col])
            if any(char in value for char in ['�', '�', '�']):
                print(f"   Linha {idx}, Coluna '{col}': '{value}'")
    
    # Mapeamento de correções
    char_fixes = {
        # Caracteres acentuados
        'ORG�O': 'ÓRGÃO',
        'OPERA��O': 'OPERAÇÃO', 
        'CR�DITO': 'CRÉDITO',
        'CART�O': 'CARTÃO',
        'BENEF�CIO': 'BENEFÍCIO',
        'COMPLEM�NTAR': 'COMPLEMENTAR',
        'EXCLUS�VE': 'EXCLUSIVE',
        'PRIV�': 'PRIVÉ',
        'F�CIL': 'FÁCIL',
        'M�XIM': 'MÁXIM',
        'PR�MIUM': 'PRÉMIUM',
        'CONVEN��O': 'CONVENÇÃO',
        'CONTRIBUI��O': 'CONTRIBUIÇÃO',
        'SITUA��O': 'SITUAÇÃO',
        'INFORM���ES': 'INFORMAÇÕES',
        
        # Caracteres especiais comuns
        '�': 'Ã',
        '�': 'Á', 
        '�': 'À',
        '�': 'Â',
        '�': 'É',
        '�': 'Ê',
        '�': 'Í',
        '�': 'Ó',
        '�': 'Ô',
        '�': 'Õ',
        '�': 'Ú',
        '�': 'Ç',
    }
    
    # Aplicar correções
    print(f"\n🔧 APLICANDO CORREÇÕES...")
    corrections_made = 0
    
    # Corrigir nomes das colunas
    new_columns = []
    for col in df.columns:
        new_col = col
        for bad_char, good_char in char_fixes.items():
            if bad_char in new_col:
                new_col = new_col.replace(bad_char, good_char)
                corrections_made += 1
        new_columns.append(new_col)
    
    df.columns = new_columns
    
    # Corrigir dados das células
    for col in df.columns:
        if df[col].dtype == 'object':  # Apenas colunas de texto
            for bad_char, good_char in char_fixes.items():
                mask = df[col].str.contains(bad_char, na=False)
                if mask.any():
                    df.loc[mask, col] = df.loc[mask, col].str.replace(bad_char, good_char)
                    corrections_made += mask.sum()
    
    print(f"✅ Correções aplicadas: {corrections_made}")
    
    # Salvar arquivo corrigido
    df.to_csv(file_path, sep=';', index=False, encoding='utf-8')
    print(f"💾 Arquivo salvo com encoding UTF-8: {file_path}")
    
    # Mostrar resultado
    print(f"\n📊 RESULTADO:")
    print(f"   ✅ Colunas corrigidas: {list(df.columns)}")
    
    return df

if __name__ == "__main__":
    fix_relat_orgaos_encoding()