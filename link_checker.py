# link_checker.py (Versão original antes do tratamento específico do HTTP 999)
import os
import glob
import requests # Para verificar links externos
from bs4 import BeautifulSoup # Para parsear HTML
from urllib.parse import urlparse # Para manipular URLs
import argparse # Para argumentos da linha de comando

# Cache para URLs externas já verificadas na sessão atual para evitar re-checagens
_checked_external_urls_cache = {}

def _resolve_internal_link_path(link_href, source_file_abs_path, site_root_abs_path):
    """Resolve um href de link interno para um caminho absoluto no sistema de arquivos e fragmento."""
    parsed_link = urlparse(link_href)
    path_part = parsed_link.path
    fragment = parsed_link.fragment

    if not path_part: # Apenas fragmento, ex: #section. Aponta para o mesmo arquivo.
        return os.path.normpath(source_file_abs_path), fragment

    if path_part.startswith('/'):
        # Caminho absoluto a partir da raiz do site
        target_file_abs_path = os.path.normpath(os.path.join(site_root_abs_path, path_part.lstrip('/')))
    else:
        # Caminho relativo à página atual
        source_dir = os.path.dirname(source_file_abs_path)
        target_file_abs_path = os.path.normpath(os.path.join(source_dir, path_part))
    return target_file_abs_path, fragment

def _check_internal_link_target(target_file_abs_path, fragment, site_root_abs_path):
    """Verifica se o arquivo de destino e o fragmento (âncora) de um link interno existem."""
    if not target_file_abs_path.startswith(site_root_abs_path):
        relative_target = target_file_abs_path.replace(site_root_abs_path, '').lstrip(os.sep)
        return False, f"Link interno aponta para fora do diretório do site: {relative_target}"

    actual_file_to_check = target_file_abs_path
    if os.path.isdir(target_file_abs_path):
        index_in_dir_path = os.path.join(target_file_abs_path, "index.html")
        if os.path.isfile(index_in_dir_path):
            actual_file_to_check = index_in_dir_path
        else:
            relative_dir_link = target_file_abs_path.replace(site_root_abs_path, '').lstrip(os.sep)
            return False, f"Link de diretório '{relative_dir_link}/' não possui um arquivo 'index.html' correspondente."
    
    if not os.path.isfile(actual_file_to_check):
        relative_file_path = actual_file_to_check.replace(site_root_abs_path, '').lstrip(os.sep)
        return False, f"Arquivo de destino não encontrado: '{relative_file_path}'"

    if fragment:
        try:
            with open(actual_file_to_check, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            if not soup.find(id=fragment) and not soup.find('a', attrs={'name': fragment}):
                relative_file_path = actual_file_to_check.replace(site_root_abs_path, '').lstrip(os.sep)
                return False, f"Âncora '#{fragment}' não encontrada em '{relative_file_path}'"
        except Exception as e:
            relative_file_path = actual_file_to_check.replace(site_root_abs_path, '').lstrip(os.sep)
            return False, f"Erro ao verificar âncora '#{fragment}' em '{relative_file_path}': {e}"
    return True, "OK"

def _fetch_external_link(link_href, cache, user_site_url="http://example.com"):
    """Verifica um link externo usando requests e atualiza o cache."""
    status_ok, message = False, "Erro desconhecido ao verificar link externo"
    final_status_to_evaluate = None
    method_trail_message = ""

    try:
        headers = {'User-Agent': f'Mozilla/5.0 (compatible; SiteLinkCheckerBot/1.0; +{user_site_url})'}
        
        # Tenta HEAD primeiro
        head_response = requests.head(link_href, timeout=10, allow_redirects=True, headers=headers)
        final_status_to_evaluate = head_response.status_code
        method_trail_message = f"(HEAD {head_response.status_code})"

        # Se HEAD deu erro (>=400), tenta GET
        if head_response.status_code >= 400:
            get_response = requests.get(link_href, timeout=15, allow_redirects=True, headers=headers, stream=True)
            get_response.close() 
            
            final_status_to_evaluate = get_response.status_code # Usa o status do GET como final
            method_trail_message = f"(GET {get_response.status_code} após HEAD {head_response.status_code})"

        # Avaliação final
        if final_status_to_evaluate < 400:
            status_ok, message = True, f"OK {method_trail_message}"
        else:
            # Aqui, se final_status_to_evaluate for 999, será reportado como "Erro HTTP 999" genérico
            status_ok, message = False, f"Erro HTTP {final_status_to_evaluate} {method_trail_message}"

    except requests.exceptions.Timeout:
        status_ok, message = False, "Timeout (excedeu tempo limite)"
    except requests.exceptions.TooManyRedirects:
        status_ok, message = False, "Muitos redirecionamentos"
    except requests.exceptions.RequestException as e: 
        status_ok, message = False, f"Erro de requisição: {type(e).__name__}"
    except Exception as e: 
        status_ok, message = False, f"Erro inesperado ao verificar: {e}"
    
    cache[link_href] = (status_ok, message)
    return status_ok, message

def _check_one_link(link_href, source_file_abs_path, site_root_abs_path, enable_external_checking, ext_cache, user_site_url):
    """Verifica um único link, seja interno ou externo, usando o cache para links externos."""
    if not link_href or link_href.startswith('mailto:') or \
       link_href.startswith('tel:') or link_href.startswith('data:') or \
       link_href.startswith('javascript:'):
        return True, "Skipped (tipo de link não verificável ou local)"

    parsed_url = urlparse(link_href)

    if parsed_url.scheme and parsed_url.netloc: # Provavelmente um link externo
        if not enable_external_checking:
            return True, "Skipped (verificação de link externo desabilitada)"
        if link_href in ext_cache: # Verifica se já está no cache
            return ext_cache[link_href]
        return _fetch_external_link(link_href, ext_cache, user_site_url)
    else: # Link interno
        if link_href.startswith('#'):
             target_file_abs_path = source_file_abs_path
             fragment = link_href[1:]
        else:
            target_file_abs_path, fragment = _resolve_internal_link_path(link_href, source_file_abs_path, site_root_abs_path)
        return _check_internal_link_target(target_file_abs_path, fragment, site_root_abs_path)

def _extract_and_check_links_from_file(html_file_abs_path, site_root_abs_path, enable_external_checking, ext_cache, user_site_url):
    """Extrai e verifica todos os links relevantes de um único arquivo HTML."""
    broken_links = []
    try:
        with open(html_file_abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        soup = BeautifulSoup(content, 'html.parser')
        source_page_relative_path = html_file_abs_path.replace(site_root_abs_path, '').lstrip(os.sep)
        link_tags_attributes = {
            'a': 'href', 'link': 'href', 'img': 'src', 'script': 'src'
        }
        for tag_name, attr_name in link_tags_attributes.items():
            for tag in soup.find_all(tag_name, **{attr_name: True}):
                link_href = tag[attr_name]
                if tag_name == 'link':
                    rel_values = tag.get('rel', [])
                    if not any(val in rel_values for val in ['stylesheet', 'icon', 'shortcut icon', 'apple-touch-icon', 'manifest']):
                        continue
                is_ok, message = _check_one_link(link_href, html_file_abs_path, site_root_abs_path, enable_external_checking, ext_cache, user_site_url)
                if not is_ok:
                    broken_links.append({
                        'source': source_page_relative_path,
                        'tag': str(tag),
                        'href': link_href,
                        'status': message
                    })
        return broken_links
    except Exception as e:
        return [{
            'source': html_file_abs_path.replace(site_root_abs_path, '').lstrip(os.sep),
            'tag': 'N/A (Erro ao processar arquivo fonte)',
            'href': 'N/A',
            'status': f'Erro crítico de leitura/parse: {e}'
        }]

def check_website_links(output_dir, check_external=True, site_url_for_user_agent="http://example.com"):
    """
    Verifica todos os links em arquivos HTML de um diretório de saída.
    Retorna uma lista de dicionários, cada um representando um link quebrado.
    """
    global _checked_external_urls_cache
    _checked_external_urls_cache.clear() 

    site_root_abs = os.path.abspath(output_dir)
    all_found_broken_links = []
    html_files_in_output = glob.glob(os.path.join(site_root_abs, '**', '*.html'), recursive=True)

    if not html_files_in_output:
        print("LinkChecker: Nenhum arquivo HTML encontrado na pasta de saída para verificar links.")
        return []

    total_html_files = len(html_files_in_output)
    print(f"\n🔗 LinkChecker: Iniciando verificação de links em {total_html_files} arquivo(s) HTML em '{output_dir}'...")
    if not check_external:
        print("LinkChecker: AVISO: Verificação de links externos está DESABILITADA.")
    
    for i, html_file_path in enumerate(html_files_in_output):
        progress_percent = ((i + 1) / total_html_files) * 100
        relative_file_path = html_file_path.replace(site_root_abs, '').lstrip(os.sep)
        print(f"  LinkChecker: [{i+1}/{total_html_files} | {progress_percent:.1f}%] Processando: {relative_file_path:<70}", end='\r')
        
        try:
            broken_links_in_current_file = _extract_and_check_links_from_file(
                html_file_path, 
                site_root_abs, 
                check_external,
                _checked_external_urls_cache, 
                site_url_for_user_agent
            )
            all_found_broken_links.extend(broken_links_in_current_file)
        except Exception as e:
            print(f"\nLinkChecker: Erro crítico ao chamar _extract_and_check_links_from_file para {relative_file_path}: {e}")
            all_found_broken_links.append({
                'source': relative_file_path, 
                'tag': 'N/A (Erro no processamento do arquivo)',
                'href': 'N/A', 
                'status': f'Falha geral no processamento: {e}'
            })

    print("\nLinkChecker: Verificação de links concluída." + " " * 80) 
    return all_found_broken_links

def print_link_report(broken_links_list):
    """Imprime o relatório de links quebrados de forma legível."""
    if broken_links_list:
        print("\n‼️ --- LINKS QUEBRADOS ENCONTRADOS --- ‼️")
        for broken in broken_links_list:
            print(f"  Página Fonte: {broken['source']}")
            print(f"  Tag HTML:     {broken['tag']}")
            print(f"  URL Quebrada: {broken['href']}")
            print(f"  Status/Erro:  {broken['status']}")
            print("  ------------------------------------")
        print(f"Total de links quebrados: {len(broken_links_list)}")
    else:
        print("\n✅ LinkChecker: Nenhum link quebrado encontrado.")
    print("-------------------------------------------\n")

# --- Bloco para Execução via Linha de Comando ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Verificador de links para sites HTML estáticos. Analisa arquivos HTML em um diretório em busca de links quebrados (internos e externos).",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        "directory",
        help="O diretório raiz do site contendo os arquivos HTML gerados a serem verificados (ex: public_html)."
    )
    
    parser.add_argument(
        "--skip-external",
        action="store_true", 
        help="Pula a verificação de links externos. A execução será mais rápida e não dependerá de conexão com a internet."
    )
    
    parser.add_argument(
        "--site-url",
        default="http://example.com/link-checker-script", 
        help="URL base do seu site para ser incluída no User-Agent das requisições HTTP a links externos (ex: https://meusite.com)."
    )

    args = parser.parse_args()

    check_external_links_enabled = not args.skip_external

    if not os.path.isdir(args.directory):
        print(f"Erro: O diretório especificado '{args.directory}' não existe ou não é um diretório.")
        exit(1)

    print(f"Iniciando verificação de links para o diretório: {os.path.abspath(args.directory)}")
    if not check_external_links_enabled:
        print("AVISO: A verificação de links externos foi DESABILITADA via linha de comando (--skip-external).")

    list_of_broken_links = check_website_links(
        output_dir=args.directory,
        check_external=check_external_links_enabled,
        site_url_for_user_agent=args.site_url
    )

    print_link_report(list_of_broken_links)