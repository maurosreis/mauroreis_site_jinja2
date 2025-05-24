# suggest_orphan_links.py
"""
===================================================================
Sugeridor de Links para Páginas Órfãs (suggest_orphan_links.py)
===================================================================

Objetivo:
---------
Este script tenta sugerir páginas existentes onde uma página órfã
poderia ser linkada. Ele faz isso analisando o título e as palavras-chave
da página órfã e procurando por ocorrências dessas palavras em outras
páginas do site.

Como Usar:
-----------
Execute após gerar o site. Forneça o diretório raiz do site gerado.

Sintaxe:
  python suggest_orphan_links.py <DIRETORIO_RAIZ_DO_SITE_GERADO>

Exemplo de Uso:
  python suggest_orphan_links.py public_html

Dependências:
-------------
- beautifulsoup4: Para parsear HTML.

Importante:
-----------
- As sugestões são baseadas em correspondência de palavras-chave e
  precisam de avaliação manual.
- A qualidade das sugestões depende da relevância das palavras-chave
  e do conteúdo das páginas.
"""
import os
import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import argparse
import re

# Funções reutilizadas ou adaptadas de find_orphaned_pages.py
def normalize_path(path_str):
    return os.path.normpath(unquote(path_str)).replace(os.sep, '/')

def resolve_internal_link_target(href_value, source_file_relative_path, site_root_abs_path):
    parsed_href = urlparse(href_value)
    if parsed_href.scheme or parsed_href.netloc or \
       href_value.startswith(('mailto:', 'tel:', 'javascript:', '#')) or \
       not href_value.strip():
        return None
    path_part = parsed_href.path
    if path_part.startswith('/'):
        target_abs_path = os.path.join(site_root_abs_path, path_part.lstrip('/'))
    else:
        source_dir_abs = os.path.dirname(os.path.join(site_root_abs_path, source_file_relative_path))
        target_abs_path = os.path.join(source_dir_abs, path_part)
    normalized_abs_path = normalize_path(target_abs_path)
    if os.path.isdir(normalized_abs_path):
        normalized_abs_path_with_index = normalize_path(os.path.join(normalized_abs_path, 'index.html'))
        if os.path.isfile(normalized_abs_path_with_index):
             normalized_abs_path = normalized_abs_path_with_index
    if not normalized_abs_path.startswith(normalize_path(site_root_abs_path)):
        return None
    relative_target_path = os.path.relpath(normalized_abs_path, site_root_abs_path)
    return normalize_path(relative_target_path)

def get_all_html_files_and_links(output_dir_path):
    site_root_abs = os.path.abspath(output_dir_path)
    all_site_html_files = set()
    internally_linked_html_files = set()
    page_data = {} # Para armazenar título, keywords e texto de cada página

    for html_filepath_abs in glob.glob(os.path.join(site_root_abs, '**', '*.html'), recursive=True):
        relative_path = normalize_path(os.path.relpath(html_filepath_abs, site_root_abs))
        all_site_html_files.add(relative_path)
        
        try:
            with open(html_filepath_abs, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extrair dados da página para sugestões
            title_tag = soup.find('title')
            page_title = title_tag.string.strip() if title_tag and title_tag.string else ""
            
            meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            page_keywords = meta_keywords_tag['content'].strip().lower() if meta_keywords_tag and meta_keywords_tag.get('content') else ""
            
            # Extrair texto principal (simplificado)
            main_text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
            page_text_content = ' '.join(el.get_text(separator=' ', strip=True) for el in main_text_elements).lower()

            page_data[relative_path] = {
                'title': page_title,
                'keywords': set(k.strip() for k in page_keywords.split(',') if k.strip()),
                'text_content': page_text_content
            }
            
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                resolved_target = resolve_internal_link_target(href, relative_path, site_root_abs)
                if resolved_target and resolved_target in all_site_html_files: # Verifica se o link resolvido é um HTML existente
                     internally_linked_html_files.add(resolved_target)
        except Exception as e:
            print(f"⚠️  Erro ao processar o arquivo '{relative_path}': {e}")
            page_data[relative_path] = {'title': '', 'keywords': set(), 'text_content': ''}


    orphaned_pages = all_site_html_files - internally_linked_html_files
    homepage_normalized = normalize_path('index.html')
    if homepage_normalized in orphaned_pages:
        # orphaned_pages.remove(homepage_normalized) # Opcional
        pass
        
    return sorted(list(orphaned_pages)), page_data, all_site_html_files


def suggest_linking_opportunities(orphaned_pages, page_data, all_html_files):
    suggestions = {}
    non_orphan_pages = all_html_files - set(orphaned_pages)

    for orphan_path in orphaned_pages:
        if orphan_path not in page_data:
            continue
            
        orphan_info = page_data[orphan_path]
        orphan_title_words = set(re.findall(r'\b\w{3,}\b', orphan_info['title'].lower())) # Palavras com 3+ letras
        orphan_keywords = orphan_info['keywords']
        
        # Termos de busca da página órfã (título e keywords)
        search_terms = orphan_title_words.union(orphan_keywords)
        if not search_terms: # Se não há termos, difícil sugerir
            continue

        suggestions[orphan_path] = []

        for potential_source_path in non_orphan_pages:
            if potential_source_path not in page_data:
                continue

            source_info = page_data[potential_source_path]
            
            # Verifica se algum termo da página órfã está no texto da página fonte
            found_terms_count = 0
            for term in search_terms:
                if term and len(term) > 2: # Evita termos muito curtos/comuns demais
                    # Usando regex para encontrar a palavra inteira
                    if re.search(r'\b' + re.escape(term) + r'\b', source_info['text_content']):
                        found_terms_count += 1
            
            # Define um limiar para considerar uma sugestão válida (ex: pelo menos 1 ou 2 termos)
            if found_terms_count > 0: 
                suggestions[orphan_path].append({
                    'link_from_page': potential_source_path,
                    'matching_terms_count': found_terms_count,
                    'source_page_title': source_info['title']
                })
        
        # Ordena as sugestões pela contagem de termos correspondentes (mais relevantes primeiro)
        if suggestions[orphan_path]:
            suggestions[orphan_path].sort(key=lambda x: x['matching_terms_count'], reverse=True)

    return suggestions

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Sugere onde linkar páginas HTML órfãs em um site estático gerado.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        help="O diretório raiz do site gerado (ex: public_html)."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"❌ Erro: O diretório especificado '{args.directory}' não existe ou não é um diretório válido.")
        exit(1)

    print(f"🔎 Analisando páginas órfãs e buscando sugestões de links em: {os.path.abspath(args.directory)}")
    
    orphaned_pages_list, all_page_data, all_html_files_list = get_all_html_files_and_links(args.directory)

    if not orphaned_pages_list:
        print("\n✅ Nenhuma página órfã encontrada. Nada a sugerir.")
    else:
        print(f"\nIdentificadas {len(orphaned_pages_list)} página(s) órfã(s):")
        for orphan in orphaned_pages_list:
            print(f"  - {orphan} (Título: {all_page_data.get(orphan, {}).get('title', 'N/A')})")

        link_suggestions = suggest_linking_opportunities(orphaned_pages_list, all_page_data, all_html_files_list)
        
        print("\n💡 --- Sugestões de Links para Páginas Órfãs --- 💡")
        if not any(link_suggestions.values()):
            print("Nenhuma sugestão de linkagem automática pôde ser gerada com base nas palavras-chave.")
        else:
            for orphan_page, suggested_sources in link_suggestions.items():
                if suggested_sources:
                    print(f"\n  🔗 Para a página órfã: {orphan_page} (Título: \"{all_page_data.get(orphan_page, {}).get('title', 'N/A')}\")")
                    print("     Considere adicionar um link a partir de:")
                    for suggestion in suggested_sources[:5]: # Mostra as top 5 sugestões
                        print(f"       - {suggestion['link_from_page']} (Título: \"{suggestion['source_page_title']}\") - {suggestion['matching_terms_count']} termo(s) em comum.")
                else:
                    print(f"\n  🔗 Para a página órfã: {orphan_page} (Título: \"{all_page_data.get(orphan_page, {}).get('title', 'N/A')}\")")
                    print("     Nenhuma página fonte com palavras-chave correspondentes encontradas para sugestão automática.")
    
    print("-" * 40 + "\n")