# find_internal_link_opportunities.py
"""
===================================================================================
Analisador de Oportunidades de Linkagem Interna (find_internal_link_opportunities.py)
===================================================================================

Objetivo:
---------
Este script analisa todos os arquivos HTML de um site estático gerado para
sugerir oportunidades de linkagem interna. Para cada página do site, ele
procura outras páginas cujo conteúdo mencione termos relevantes (do título
ou palavras-chave da página alvo) e que ainda não possuam um link para ela.

Como Usar:
-----------
Execute após o site ter sido completamente gerado. Forneça o diretório
raiz do site gerado (normalmente 'public_html') como argumento.

Sintaxe:
  python find_internal_link_opportunities.py <DIRETORIO_RAIZ_DO_SITE_GERADO>

Exemplo de Uso:
  python find_internal_link_opportunities.py public_html

Dependências:
-------------
- beautifulsoup4: Para parsear o conteúdo HTML.
  (Certifique-se de que está listado em seu requirements.txt)

Importante:
-----------
- As sugestões são baseadas em correspondência de palavras-chave e devem ser
  avaliadas manualmente quanto à relevância e contexto.
- A qualidade das sugestões depende do quão bem os títulos e palavras-chave
  definem o tópico de cada página e da riqueza do conteúdo textual.
- Palavras comuns (stopwords) são filtradas para melhorar a relevância dos termos.
"""
import os
import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import argparse
import re

# --- Lista de Stopwords em Português (Pode ser expandida) ---
PORTUGUESE_STOPWORDS = set([
    "de", "a", "o", "que", "e", "do", "da", "em", "um", "para", "é", "com", "não", "uma", "os", "no", "na",
    "por", "mais", "as", "dos", "como", "mas", "foi", "ao", "ele", "das", "tem", "à", "seu", "sua", "ou",
    "ser", "quando", "muito", "há", "nos", "já", "está", "eu", "também", "só", "pelo", "pela", "até", "isso",
    "ela", "entre", "era", "depois", "sem", "mesmo", "aos", "ter", "seus", "quem", "nas", "me", "esse",
    "eles", "estão", "você", "tinha", "foram", "essa", "num", "nem", "suas", "meu", "às", "minha", "têm",
    "numa", "pelos", "elas", "havia", "seja", "qual", "será", "nós", "tenho", "lhe", "deles", "essas",
    "esses", "pelas", "este", "fosse", "dele", "tu", "te", "vocês", "vos", "lhes", "meus", "minhas",
    "teu", "tua", "teus", "tuas", "nosso", "nossa", "nossos", "nossas", "dela", "delas", "esta", "estes",
    "estas", "aquele", "aquela", "aqueles", "aquelas", "isto", "aquilo", "estou", "está", "estamos",
    "estão", "estive", "esteve", "estivemos", "estiveram", "estava", "estávamos", "estavam", "estivera",
    "estivéramos", "esteja", "estejamos", "estejam", "estivesse", "estivéssemos", "estivessem", "estiver",
    "estivermos", "estiverem", "hei", "há", "havemos", "hão", "houve", "houvemos", "houveram", "houvera",
    "houvéramos", "haja", "hajamos", "hajam", "houvesse", "houvéssemos", "houvessem", "houver", "houvermos",
    "houverem", "houverei", "houverá", "houveremos", "houverão", "houveria", "houveríamos", "houveriam",
    "sou", "somos", "são", "era", "éramos", "eram", "fui", "foi", "fomos", "foram", "fora", "fôramos",
    "seja", "sejamos", "sejam", "fosse", "fôssemos", "fossem", "for", "formos", "forem", "serei", "será",
    "seremos", "serão", "seria", "seríamos", "seriam", "tenho", "tem", "temos", "tém", "tinha", "tínhamos",
    "tinham", "tive", "teve", "tivemos", "tiveram", "tivera", "tivéramos", "tenha", "tenhamos", "tenham",
    "tivesse", "tivéssemos", "tivessem", "tiver", "tivermos", "tiverem", "terei", "terá", "teremos", "terão",
    "teria", "teríamos", "teriam", "sobre", "qualquer", "todo", "todos", "toda", "todas", "outro", "outra",
    "outros", "outras", "tal", "tais", "mesma", "mesmos", "mesmas", "grande", "pequeno", "pouco", "muita",
    "algum", "alguma", "alguns", "algumas", "assim", "então", "logo", "porque", "pois", "onde", "quando",
    "enquanto", "sempre", "nunca", "agora", "hoje", "ontem", "amanhã", "cedo", "tarde", "aqui", "ali",
    "lá", "dentro", "fora", "acima", "abaixo", "frente", "atrás", "cada", "coisa", "caso", "cujo", "etc",
    "mim", "si", "consigo", "tipo", "ainda", "poder", "pode", "deve", "devem", "fazer", "dizer",
    "quer", "quê", "quem", "serão", "àquele", "àquela", "naquele", "naquela", "neste", "nesta", "nisto",
    "nisso", "daqui", "dali", "desta", "deste", "daquele", "daquela"
])


def normalize_path(path_str):
    """Normaliza um caminho, decodifica e remove barras extras, usando / como separador."""
    return os.path.normpath(unquote(path_str)).replace(os.sep, '/')


def resolve_internal_link_target(href_value, source_file_relative_path, site_root_abs_path):
    """
    Resolve um valor href para um caminho de arquivo normalizado relativo à raiz do site.
    Retorna None para links externos, âncoras na mesma página, ou links não resolvidos para um arquivo HTML interno.
    """
    parsed_href = urlparse(href_value)

    # Ignora links externos, mailto, tel, javascript, vazios ou âncoras na mesma página
    if parsed_href.scheme or parsed_href.netloc or \
       href_value.startswith(('mailto:', 'tel:', 'javascript:', '#')) or \
       not href_value.strip():
        return None

    path_part = parsed_href.path

    # Constrói o caminho absoluto do link alvo
    if path_part.startswith('/'):
        # Link absoluto a partir da raiz do site
        target_abs_path = os.path.join(site_root_abs_path, path_part.lstrip('/'))
    else:
        # Link relativo à página fonte
        source_dir_abs = os.path.dirname(os.path.join(site_root_abs_path, source_file_relative_path))
        target_abs_path = os.path.join(source_dir_abs, path_part)
    
    normalized_abs_path = normalize_path(target_abs_path)

    # Se o link resolvido aponta para um diretório, tenta encontrar o index.html dentro dele
    if os.path.isdir(normalized_abs_path):
        index_in_dir_path = normalize_path(os.path.join(normalized_abs_path, 'index.html'))
        if os.path.isfile(index_in_dir_path):
             normalized_abs_path = index_in_dir_path
        else: # Se não há index.html, o link para diretório não aponta para um arquivo HTML específico
            return None
    
    # Verifica se o caminho resolvido é um arquivo HTML existente
    if not os.path.isfile(normalized_abs_path) or not normalized_abs_path.endswith('.html'):
        return None # Não é um arquivo HTML ou não existe

    # Garante que o caminho resolvido ainda está dentro do diretório do site
    if not normalized_abs_path.startswith(normalize_path(site_root_abs_path)):
        return None

    relative_target_path = os.path.relpath(normalized_abs_path, site_root_abs_path)
    return normalize_path(relative_target_path)


def get_site_data_and_link_map(output_dir_path):
    """
    Coleta dados (título, keywords, texto) e o mapa de links de saída para todas as páginas HTML.
    """
    site_root_abs = os.path.abspath(output_dir_path)
    all_html_files = set()
    page_data = {}  # Formato: rel_path -> {title, keywords_set, text_content_for_matching, raw_text_content_for_snippet}
    outgoing_link_map = {} # Formato: source_rel_path -> set of target_rel_paths

    html_file_paths_abs = glob.glob(os.path.join(site_root_abs, '**', '*.html'), recursive=True)

    # Primeira passada: Coleta informações básicas das páginas
    for html_filepath_abs in html_file_paths_abs:
        relative_path = normalize_path(os.path.relpath(html_filepath_abs, site_root_abs))
        all_html_files.add(relative_path)
        try:
            with open(html_filepath_abs, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            title_tag = soup.find('title')
            page_title = title_tag.string.strip() if title_tag and title_tag.string else os.path.basename(relative_path)
            
            meta_keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
            raw_keywords_str = meta_keywords_tag['content'].strip() if meta_keywords_tag and meta_keywords_tag.get('content') else ""
            
            page_keywords_set = set(
                k.strip().lower() for k in raw_keywords_str.split(',') 
                if k.strip() and len(k.strip()) > 2 and k.strip().lower() not in PORTUGUESE_STOPWORDS
            )
            
            main_text_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'span', 'article', 'section', 'td', 'th'])
            page_text_content_full = ' '.join(el.get_text(separator=' ', strip=True) for el in main_text_elements).lower()
            
            words_in_text = re.findall(r'\b[a-záéíóúâêôãõçüA-ZÁÉÍÓÚÂÊÔÃÕÇÜ-]{3,}\b', page_text_content_full)
            filtered_text_words = [word for word in words_in_text if word not in PORTUGUESE_STOPWORDS]
            page_text_for_matching = ' '.join(filtered_text_words)

            page_data[relative_path] = {
                'title': page_title,
                'keywords_set': page_keywords_set,
                'text_content_for_matching': page_text_for_matching,
                'raw_text_content_for_snippet': page_text_content_full
            }
            outgoing_link_map[relative_path] = set() # Inicializa
        except Exception as e:
            print(f"⚠️  Erro ao coletar dados de '{relative_path}': {e}")
            page_data[relative_path] = {'title': os.path.basename(relative_path), 
                                        'keywords_set': set(), 
                                        'text_content_for_matching': '',
                                        'raw_text_content_for_snippet': ''}
            outgoing_link_map[relative_path] = set()

    # Segunda passada: Constrói o mapa de links de saída
    for html_filepath_abs in html_file_paths_abs:
        current_file_relative = normalize_path(os.path.relpath(html_filepath_abs, site_root_abs))
        if current_file_relative not in page_data: continue

        try:
            with open(html_filepath_abs, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                resolved_target = resolve_internal_link_target(href, current_file_relative, site_root_abs)
                
                if resolved_target and resolved_target in all_html_files:
                    outgoing_link_map[current_file_relative].add(resolved_target)
        except Exception as e:
            print(f"⚠️  Erro ao extrair links de '{current_file_relative}': {e}")
            
    return sorted(list(all_html_files)), page_data, outgoing_link_map


def suggest_internal_linking_opportunities(all_html_files, page_data, outgoing_link_map):
    """
    Analisa todas as páginas e sugere oportunidades de linkagem interna.
    Retorna um dicionário: target_page -> [lista de {source_page, source_title, matched_terms, context_snippet}]
    """
    all_opportunities = {} 

    for target_page_rel_path in all_html_files:
        if target_page_rel_path not in page_data: continue
        
        target_info = page_data[target_page_rel_path]
        
        target_title_words_raw = re.findall(r'\b[a-záéíóúâêôãõçüA-ZÁÉÍÓÚÂÊÔÃÕÇÜ-]{3,}\b', target_info['title'].lower())
        target_title_words = set(word for word in target_title_words_raw if word not in PORTUGUESE_STOPWORDS)
        
        target_keywords = target_info['keywords_set'] # Já filtrado
        
        target_topic_terms = target_title_words.union(target_keywords)
        if not target_topic_terms: continue 

        all_opportunities[target_page_rel_path] = []

        for source_page_rel_path in all_html_files:
            if source_page_rel_path == target_page_rel_path: continue 
            if source_page_rel_path not in page_data: continue

            if target_page_rel_path in outgoing_link_map.get(source_page_rel_path, set()):
                continue 

            source_info = page_data[source_page_rel_path]
            source_text_for_matching = source_info['text_content_for_matching']
            source_text_for_snippet = source_info['raw_text_content_for_snippet']
            
            found_matching_terms = set()
            for term in target_topic_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', source_text_for_matching):
                    found_matching_terms.add(term)
            
            if found_matching_terms:
                context_snippet = ""
                if found_matching_terms:
                    first_found_term_for_snippet_search = list(found_matching_terms)[0]
                    try:
                        match_obj = re.search(r'\b' + re.escape(first_found_term_for_snippet_search) + r'\b', source_text_for_snippet)
                        if match_obj:
                            match_pos = match_obj.start()
                            start = max(0, match_pos - 60)
                            end = min(len(source_text_for_snippet), match_pos + len(first_found_term_for_snippet_search) + 60)
                            snippet_raw = source_text_for_snippet[start:end]
                            context_snippet = "..." + ' '.join(snippet_raw.split()) + "..."
                    except Exception:
                        context_snippet = "[Não foi possível gerar snippet de contexto]"

                all_opportunities[target_page_rel_path].append({
                    'source_page': source_page_rel_path,
                    'source_page_title': source_info['title'],
                    'matching_terms_count': len(found_matching_terms),
                    'matched_terms_list': sorted(list(found_matching_terms)),
                    'context_snippet': context_snippet
                })

        if all_opportunities[target_page_rel_path]:
            all_opportunities[target_page_rel_path].sort(key=lambda x: x['matching_terms_count'], reverse=True)
            
    return all_opportunities


def print_detailed_link_opportunities_report(opportunities, page_content_data_map):
    """Imprime um relatório mais didático e detalhado das oportunidades de linkagem interna."""
    
    if not any(opportunities.values()):
        print("\n✅ Nenhuma oportunidade clara de nova linkagem interna foi identificada com os critérios atuais.")
        print("-" * 70 + "\n")
        return

    print("\n💡 --- RELATÓRIO DETALHADO: OPORTUNIDADES DE LINKAGEM INTERNA --- 💡")
    print("Este relatório sugere onde você pode adicionar links internos para melhorar a conexão entre suas páginas.")
    print("Analise cada sugestão para verificar se o link é contextualmente relevante.\n")

    suggested_links_count = 0

    for target_page, suggestions_list in sorted(opportunities.items()):
        if suggestions_list: # Só imprime se houver sugestões para esta página alvo
            target_page_info = page_content_data_map.get(target_page, {})
            target_title = target_page_info.get('title', target_page)
            # As keywords já são um set, então convertemos para string para display
            target_keywords_str = ", ".join(sorted(list(target_page_info.get('keywords_set', [])))) if target_page_info.get('keywords_set') else "Nenhuma"


            print("=====================================================================================")
            print(f"🎯 PÁGINA ALVO (Para onde linkar): {target_page}")
            print(f"   Título da Página Alvo: \"{target_title}\"")
            print(f"   Palavras-chave da Alvo (filtradas): [{target_keywords_str}]")
            print("-------------------------------------------------------------------------------------")
            print("   Sugestões de PÁGINAS FONTE (De onde linkar):")
            
            for i, sug in enumerate(suggestions_list[:5], 1): # Limita a 5 sugestões por alvo
                suggested_links_count +=1
                print(f"\n     Sugestão #{i}:")
                print(f"       ➡️  Link da Página Fonte: {sug['source_page']}")
                print(f"          Título da Fonte: \"{sug['source_page_title']}\"")
                print(f"          Termos Relevantes Encontrados ({sug['matching_terms_count']}): {', '.join(sug['matched_terms_list'])}")
                if sug['context_snippet']:
                    highlighted_snippet = sug['context_snippet']
                    for term in sug['matched_terms_list']:
                        try:
                            # Usa (?i) para case-insensitive no padrão regex, \b para palavra inteira
                            highlighted_snippet = re.sub(r'(?i)(\b' + re.escape(term) + r'\b)', 
                                                         r'**\1**', 
                                                         highlighted_snippet)
                        except re.error: 
                            pass 
                    print(f"          Contexto Sugerido (na página fonte): {highlighted_snippet}")
                else:
                    print(f"          Contexto Sugerido: [Não foi possível gerar snippet de contexto]")
                print(f"          Ação: Considere adicionar um link de '{sug['source_page']}' para '{target_page}'.")
                print("          ----")
            if not suggestions_list: # Esta linha nunca será alcançada devido ao if externo
                print("     Nenhuma página fonte encontrada com correspondência significativa de termos.")
            print("=====================================================================================\n")

    if suggested_links_count == 0 and any(opportunities.values()): # Se houve processamento mas nenhuma sugestão específica
         print("\nNenhuma sugestão de linkagem específica pôde ser gerada com base nas palavras-chave e conteúdo atuais, apesar de algumas páginas alvo terem sido analisadas.")
    elif suggested_links_count > 0 :
        print(f"Total de sugestões de linkagem específicas apresentadas: {suggested_links_count}")
    # Se `any(opportunities.values())` for falso, a primeira mensagem no topo da função já foi impressa.
    print("-" * 70 + "\n")


# --- Main CLI Execution ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analisa todas as páginas de um site e sugere oportunidades de linkagem interna.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        help="O diretório raiz do site gerado (ex: public_html) para análise."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"❌ Erro: O diretório especificado '{args.directory}' não existe ou não é um diretório válido.")
        exit(1)

    print(f"🔎 Analisando oportunidades de linkagem interna em: {os.path.abspath(args.directory)}")
    
    all_html_files_list, page_content_data, current_outgoing_links = get_site_data_and_link_map(args.directory)
    
    if not all_html_files_list:
        print("Nenhum arquivo HTML para analisar.")
    else:
        link_opportunities = suggest_internal_linking_opportunities(
            all_html_files_list, 
            page_content_data, 
            current_outgoing_links
        )
        print_detailed_link_opportunities_report(link_opportunities, page_content_data)