"""
Debug específico para VCTEX - identificar qual entrada está sendo selecionada
"""

import sys
import os

# Adicionar o diretório backend ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from server import load_organ_mapping, TABELA_MAPPING

# Carregar mapeamentos
print("🔄 Carregando mapeamento de órgãos...")
ORGAN_MAPPING, DETAILED_MAPPING, TABELA_MAPPING, BANK_ORGAN_MAPPING = load_organ_mapping()
print(f"✅ Mapeamento carregado: {len(TABELA_MAPPING)} entradas no TABELA_MAPPING\n")

print("=" * 80)
print("DEBUG VCTEX - Analisando entradas específicas")
print("=" * 80)

# Procurar todas as entradas VCTEX relacionadas a EXP e Exponencial
vctex_exp_entries = []
for key, details in TABELA_MAPPING.items():
    if "BANCO VCTEX" in key and ("EXP" in key.upper() or "EXPONENCIAL" in key.upper()):
        vctex_exp_entries.append((key, details))

print(f"\n🔍 Encontradas {len(vctex_exp_entries)} entradas VCTEX relacionadas a EXP/Exponencial:")
for i, (key, details) in enumerate(vctex_exp_entries, 1):
    parts = key.split('|')
    tabela_banco = parts[3] if len(parts) > 3 else "N/A"
    codigo_storm = details.get('codigo_tabela', 'N/A')
    print(f"   {i}. Chave: '{key}'")
    print(f"      Tabela Banco: '{tabela_banco}'")
    print(f"      Código Storm: '{codigo_storm}'")
    print(f"      Taxa: {details.get('taxa_storm', 'N/A')}")
    print()

# Testar busca específica
print("=" * 80)
print("TESTE DE BUSCA ESPECÍFICA - SIMULANDO apply_mapping")
print("=" * 80)

test_cases = [
    "Tabela EXP",
    "Tabela Exponencial"
]

for test_tabela in test_cases:
    print(f"\n🎯 Buscando por: '{test_tabela}'")
    
    # Simular a normalização exata do apply_mapping
    tabela_normalized = ' '.join(test_tabela.strip().upper().split())
    print(f"   📝 Normalizada para: '{tabela_normalized}'")
    
    # Construir chave esperada
    expected_key = f"BANCO VCTEX|FGTS|MARGEM LIVRE (NOVO)|{tabela_normalized}"
    print(f"   🔑 Chave esperada: '{expected_key}'")
    
    # Buscar exatamente essa chave
    if expected_key in TABELA_MAPPING:
        details = TABELA_MAPPING[expected_key]
        codigo = details.get('codigo_tabela', 'N/A')
        print(f"   ✅ ENCONTRADA! Código: '{codigo}'")
    else:
        print(f"   ❌ NÃO ENCONTRADA")
        
        # Listar chaves similares para debug
        similar_keys = [k for k in TABELA_MAPPING.keys() if "BANCO VCTEX" in k and tabela_normalized in k]
        if similar_keys:
            print(f"   🔍 Chaves similares encontradas:")
            for sk in similar_keys:
                print(f"      - '{sk}'")
        else:
            print(f"   🔍 Nenhuma chave similar encontrada")

print("\n" + "=" * 80)
print("FIM DO DEBUG")
print("=" * 80)