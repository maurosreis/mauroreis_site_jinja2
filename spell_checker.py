# spell_checker.py
"""
===================================================================
Verificador Ortográfico para Arquivos de Conteúdo HTML
===================================================================

Objetivo:
---------
Este script analisa o texto dentro de arquivos HTML de conteúdo
(especificamente os arquivos *_content.html do seu projeto) para
identificar possíveis erros ortográficos e sugerir correções.
Utiliza a biblioteca 'pyspellchecker' para verificação em Português.

Como Usar:
-----------
O script pode ser executado a partir do terminal, passando o caminho
para um arquivo de template de conteúdo específico ou um diretório
contendo múltiplos arquivos de template.

Sintaxe:
  python spell_checker.py <CAMINHO_PARA_ARQUIVO_OU_DIRETORIO_TEMPLATES>

Exemplos de Uso:
  
  # Para verificar um arquivo específico
  python spell_checker.py templates/home_content.html

  # Para verificar todos os arquivos *_content.html na pasta 'templates'
  python spell_checker.py templates

Dependências:
-------------
- beautifulsoup4: Para extrair texto do HTML.
- pyspellchecker: Para a verificação ortográfica.

O que o script faz:
-------------------
1.  Recebe um caminho (arquivo ou diretório) como argumento.
2.  Se for um diretório, encontra todos os arquivos '*_content.html' dentro dele.
3.  Para cada arquivo:
    a. Lê o conteúdo HTML.
    b. Extrai o texto puro usando BeautifulSoup.
    c. Tokeniza o texto em palavras.
    d. Verifica cada palavra contra um dicionário de Português.
    e. Lista palavras não encontradas (potenciais erros) e suas sugestões.

Importante:
-----------
- A verificação ortográfica não é perfeita e pode sinalizar palavras
  corretas que não estão no dicionário (ex: gírias, termos técnicos, nomes próprios).
- As sugestões podem não ser sempre a correção desejada.
- **Este script NÃO corrige automaticamente os erros.** Ele apenas os identifica
  e sugere correções para revisão manual. A correção automática é arriscada.
"""
import os
import glob
import re
import argparse
from bs4 import BeautifulSoup
from spellchecker import SpellChecker # Da biblioteca pyspellchecker

def extract_text_from_html(html_content):
    """Extrai texto puro de um conteúdo HTML."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove tags de script e style
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    
    # Obtém o texto, separando por espaços e removendo espaços extras
    text = soup.get_text(separator=' ', strip=True)
    return text

def check_spelling_in_file(filepath):
    """Verifica a ortografia de um arquivo HTML e retorna os erros encontrados."""
    print(f"\n🔎 Verificando ortografia em: {filepath}")
    found_issues = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        print(f"  ❌ Erro ao ler o arquivo: {e}")
        return [{'file': filepath, 'error': f"Erro ao ler o arquivo: {e}"}]

    text_content = extract_text_from_html(html_content)
    
    # Configura o verificador para Português
    # Se o dicionário pt-BR não estiver disponível, pode ser necessário instalar pacotes de idioma
    # ou verificar a documentação da pyspellchecker para adicionar dicionários.
    # Para o pyspellchecker, geralmente ele tenta encontrar o dicionário pt ou pt_BR.
    try:
        spell = SpellChecker(language='pt')
    except Exception as e:
        print(f"  ❌ Erro ao carregar o dicionário de Português: {e}")
        print("  Verifique se os dicionários de idioma para 'pyspellchecker' estão instalados.")
        return [{'file': filepath, 'error': f"Erro ao carregar dicionário: {e}"}]

    # Tokeniza o texto em palavras.
    # Remove pontuação e números, considera apenas sequências de letras.
    # Converte para minúsculas para evitar problemas com capitalização.
    words = re.findall(r'\b[a-záéíóúâêôãõçüA-ZÁÉÍÓÚÂÊÔÃÕÇÜ-]+\b', text_content.lower())
    
    # Encontra palavras que não estão no dicionário
    misspelled = spell.unknown(words)
    
    if misspelled:
        print(f"  ⚠️  Possíveis erros ortográficos encontrados:")
        for word in misspelled:
            suggestions = list(spell.candidates(word)) # Pega as sugestões
            # A primeira sugestão é geralmente a mais provável
            best_suggestion = spell.correction(word) 
            
            issue_detail = {
                'file': filepath,
                'palavra_errada': word,
                'sugestao_principal': best_suggestion,
                'outras_sugestoes': suggestions[:5] # Lista as top 5 sugestões
            }
            found_issues.append(issue_detail)
            print(f"    - Palavra: '{word}'")
            print(f"      Melhor sugestão: '{best_suggestion}'")
            if suggestions:
                print(f"      Outras sugestões: {', '.join(f'{s}' for s in suggestions[:5])}")
    else:
        print(f"  ✅ Nenhum erro ortográfico aparente encontrado.")
        
    return found_issues

def main():
    parser = argparse.ArgumentParser(
        description="Verificador ortográfico para arquivos HTML de conteúdo (*_content.html).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "path",
        help="Caminho para um arquivo *_content.html específico ou para a pasta 'templates' para verificar todos."
    )
    args = parser.parse_args()

    target_path = args.path
    files_to_check = []

    if os.path.isfile(target_path):
        if target_path.endswith("_content.html"):
            files_to_check.append(target_path)
        else:
            print(f"❌ O arquivo '{target_path}' não parece ser um arquivo de conteúdo válido (não termina com '_content.html').")
            return
    elif os.path.isdir(target_path):
        # Procura por todos os arquivos *_content.html recursivamente se for um diretório
        search_pattern = os.path.join(target_path, '**', '*_content.html')
        files_to_check.extend(glob.glob(search_pattern, recursive=True))
    else:
        print(f"❌ O caminho especificado '{target_path}' não é um arquivo ou diretório válido.")
        return

    if not files_to_check:
        print(f"Nenhum arquivo de conteúdo para verificar em '{target_path}'.")
        return

    all_issues_found = []
    for f_path in files_to_check:
        issues_in_file = check_spelling_in_file(f_path)
        if issues_in_file:
            # Verifica se o primeiro item é um erro de leitura de arquivo para não adicionar à lista principal de palavras
            if not (len(issues_in_file) == 1 and 'error' in issues_in_file[0]):
                 all_issues_found.extend(issues_in_file)


    if not all_issues_found:
        print("\n🎉 Nenhum problema ortográfico significativo encontrado em todos os arquivos verificados.")
    else:
        print("\n--- Resumo dos Problemas Ortográficos Encontrados ---")
        # Você pode adicionar um resumo mais elaborado aqui se desejar,
        # por exemplo, agrupando por arquivo.
        # Por enquanto, a função check_spelling_in_file já imprime os detalhes.
        print(f"Total de palavras com grafia potencialmente incorreta (considerando todas as sugestões): {len(all_issues_found)}")

if __name__ == "__main__":
    main()