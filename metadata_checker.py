# metadata_checker.py
import os
import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse

# --- Configurações e Constantes Esperadas ---
# Estas devem ser ajustadas conforme a configuração do seu site em base.html e templates
EXPECTED_SITE_DOMAIN = "https://mauroreis.app"
EXPECTED_AUTHOR = "Mauro Sandro dos Reis"
EXPECTED_OG_TYPE = "website"
EXPECTED_TWITTER_CARD = "summary_large_image"
DEFAULT_PROFILE_IMAGE_PATH = "/assets/img/foto-perfil-mauroreis.webp" # Relativo ao domínio

# Valores mínimos para "corretamente preenchido" (ajuste conforme necessário)
MIN_TITLE_LENGTH = 5
MIN_DESCRIPTION_LENGTH = 20 # Um pouco mais que "muito curto"
MIN_KEYWORDS_COUNT = 1 # Pelo menos uma keyword

# Descrição padrão do base.html para verificar se foi sobrescrita
DEFAULT_BASE_DESCRIPTION = "Site pessoal de Mauro Sandro dos Reis, pesquisador em eletrônica de potência, energias renováveis e controle."


def _validate_url(url_string, context_msg="URL", base_domain_required=None, path_must_exist_locally_root=None):
    """Valida uma string de URL. Verifica se é absoluta e, opcionalmente, se pertence a um domínio ou existe localmente."""
    issues = []
    if not url_string:
        issues.append(f"{context_msg}: URL está vazia.")
        return issues
    
    try:
        parsed = urlparse(url_string)
        if not parsed.scheme or not parsed.netloc:
            issues.append(f"{context_msg}: URL '{url_string}' não é absoluta (falta scheme ou netloc).")
        
        if base_domain_required and not url_string.startswith(base_domain_required):
            # Permitir CDNs para imagens se base_domain_required não for estritamente para o domínio principal
            if context_msg not in ["Open Graph Image URL", "Twitter Image URL"] or parsed.netloc == urlparse(base_domain_required).netloc:
                 issues.append(f"{context_msg}: URL '{url_string}' não pertence ao domínio esperado '{base_domain_required}'.")

        if path_must_exist_locally_root and parsed.scheme and parsed.netloc:
            # Constrói o caminho local a partir da raiz do site (ex: public_html)
            local_path = os.path.join(path_must_exist_locally_root, parsed.path.lstrip('/'))
            if not os.path.exists(local_path):
                issues.append(f"{context_msg}: Arquivo local para URL '{url_string}' (caminho '{parsed.path}') não encontrado em '{local_path}'.")

    except ValueError:
        issues.append(f"{context_msg}: URL '{url_string}' tem formato inválido.")
    return issues

def _check_meta_tag(soup, issues_list, name_attr=None, property_attr=None, 
                    expected_content_value=None, check_non_empty=True, 
                    min_length=1, is_url=False, url_context="URL", 
                    url_base_domain_required=None, local_file_root_for_url=None):
    """Função auxiliar para verificar uma tag <meta>."""
    tag_type = "name" if name_attr else "property"
    attr_value = name_attr if name_attr else property_attr
    tag_description = f"<meta {tag_type}='{attr_value}'>"
    
    tag = soup.find('meta', attrs={tag_type: attr_value})
    
    if not tag:
        issues_list.append(f"{tag_description} ausente.")
        return None

    content = tag.get('content')
    if content is None: # Atributo 'content' ausente na tag meta
        issues_list.append(f"{tag_description} não possui o atributo 'content'.")
        return None

    if check_non_empty:
        stripped_content = content.strip()
        if not stripped_content or len(stripped_content) < min_length:
            issues_list.append(f"Conteúdo de {tag_description} está vazio ou muito curto (mínimo: {min_length}, encontrado: '{content}').")
    
    if expected_content_value and content != expected_content_value:
        issues_list.append(f"Conteúdo de {tag_description}: esperado '{expected_content_value}', encontrado '{content}'.")

    if is_url:
        issues_list.extend(_validate_url(content, url_context, url_base_domain_required, local_file_root_for_url))
    
    return content # Retorna o conteúdo para possíveis verificações de consistência

def check_metadata_for_file(html_filepath, site_root_path_for_local_urls):
    """Verifica os metadados de um único arquivo HTML. Retorna uma lista de problemas."""
    issues = []
    try:
        with open(html_filepath, 'r', encoding='utf-8') as f:
            content_html = f.read()
        soup = BeautifulSoup(content_html, 'html.parser')

        # 1. Tag <title>
        title_tag = soup.find('title')
        page_title_text = None
        if not title_tag:
            issues.append("Tag <title> ausente.")
        else:
            page_title_text = title_tag.string.strip() if title_tag.string else ""
            if not page_title_text or len(page_title_text) < MIN_TITLE_LENGTH:
                issues.append(f"<title> está vazio ou muito curto (mínimo: {MIN_TITLE_LENGTH}, encontrado: '{page_title_text}').")
        
        # 2. Meta Description
        meta_description_content = _check_meta_tag(soup, issues, name_attr='description', 
                                                  check_non_empty=True, min_length=MIN_DESCRIPTION_LENGTH)
        # Checa se a descrição é a padrão em páginas não-home
        is_home_page = os.path.basename(html_filepath) == "index.html" and \
                       os.path.dirname(html_filepath) == site_root_path_for_local_urls # Raiz do site
        if meta_description_content and meta_description_content.strip() == DEFAULT_BASE_DESCRIPTION and not is_home_page:
            issues.append(f"Alerta: Meta description parece ser o valor padrão do 'base.html' e pode não ser específico para esta página ('{os.path.basename(html_filepath)}').")

        # 3. Meta Author
        _check_meta_tag(soup, issues, name_attr='author', expected_content_value=EXPECTED_AUTHOR)

        # 4. Meta Keywords
        keywords_content = _check_meta_tag(soup, issues, name_attr='keywords', check_non_empty=True)
        if keywords_content:
            keywords_list = [k.strip() for k in keywords_content.split(',') if k.strip()]
            if len(keywords_list) < MIN_KEYWORDS_COUNT:
                issues.append(f"Meta keywords: esperado pelo menos {MIN_KEYWORDS_COUNT} palavra(s)-chave, encontrado: {len(keywords_list)} ('{keywords_content}').")

        # 5. Link Canonical
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        canonical_href = None
        if not canonical_tag:
            issues.append("<link rel='canonical'> ausente.")
        else:
            canonical_href = canonical_tag.get('href')
            if not canonical_href:
                issues.append("<link rel='canonical'> não possui o atributo 'href'.")
            else:
                issues.extend(_validate_url(canonical_href, "Canonical URL", base_domain_required=EXPECTED_SITE_DOMAIN))
        
        # --- Open Graph Tags ---
        # A imagem OG principal é definida no base.html e deve existir localmente.
        expected_og_image_url = EXPECTED_SITE_DOMAIN + DEFAULT_PROFILE_IMAGE_PATH

        og_title = _check_meta_tag(soup, issues, property_attr='og:title', check_non_empty=True)
        og_description = _check_meta_tag(soup, issues, property_attr='og:description', check_non_empty=True, min_length=MIN_DESCRIPTION_LENGTH)
        og_url = _check_meta_tag(soup, issues, property_attr='og:url', check_non_empty=True, is_url=True, 
                                 url_context="Open Graph URL", url_base_domain_required=EXPECTED_SITE_DOMAIN)
        og_image = _check_meta_tag(soup, issues, property_attr='og:image', check_non_empty=True, is_url=True, 
                                   url_context="Open Graph Image URL", url_base_domain_required=EXPECTED_SITE_DOMAIN, 
                                   local_file_root_for_url=site_root_path_for_local_urls)
        _check_meta_tag(soup, issues, property_attr='og:type', expected_content_value=EXPECTED_OG_TYPE)

        # --- Twitter Card Tags ---
        _check_meta_tag(soup, issues, name_attr='twitter:card', expected_content_value=EXPECTED_TWITTER_CARD)
        twitter_title = _check_meta_tag(soup, issues, name_attr='twitter:title', check_non_empty=True)
        twitter_description = _check_meta_tag(soup, issues, name_attr='twitter:description', check_non_empty=True, min_length=MIN_DESCRIPTION_LENGTH)
        twitter_image = _check_meta_tag(soup, issues, name_attr='twitter:image', check_non_empty=True, is_url=True, 
                                        url_context="Twitter Image URL", url_base_domain_required=EXPECTED_SITE_DOMAIN,
                                        local_file_root_for_url=site_root_path_for_local_urls)

        # --- Verificações de Consistência (baseadas na estrutura dos seus templates) ---
        if page_title_text and og_title and page_title_text != og_title:
             issues.append(f"Inconsistência: <title> ('{page_title_text}') e og:title ('{og_title}') diferem.")
        if page_title_text and twitter_title and page_title_text != twitter_title:
             issues.append(f"Inconsistência: <title> ('{page_title_text}') e twitter:title ('{twitter_title}') diferem.")
        
        if meta_description_content and og_description and meta_description_content != og_description:
            issues.append(f"Inconsistência: meta description ('{meta_description_content[:30]}...') e og:description ('{og_description[:30]}...') diferem.")
        if meta_description_content and twitter_description and meta_description_content != twitter_description:
            issues.append(f"Inconsistência: meta description ('{meta_description_content[:30]}...') e twitter:description ('{twitter_description[:30]}...') diferem.")

        if og_image and twitter_image and og_image != twitter_image:
            issues.append(f"Inconsistência: og:image ('{og_image}') e twitter:image ('{twitter_image}') diferem.")
        # Se a imagem padrão é usada, ela deve ser a mesma para OG e Twitter
        if og_image == expected_og_image_url and twitter_image != expected_og_image_url :
             issues.append(f"Inconsistência de imagem padrão: og:image é '{expected_og_image_url}', mas twitter:image é '{twitter_image}'.")


        if canonical_href and og_url and canonical_href != og_url:
            issues.append(f"Inconsistência: Canonical URL ('{canonical_href}') e og:url ('{og_url}') diferem.")

    except FileNotFoundError:
        issues.append(f"Arquivo HTML não encontrado: {html_filepath}")
    except Exception as e:
        issues.append(f"Erro ao processar metadados do arquivo {os.path.basename(html_filepath)}: {e}")
    
    return issues

def audit_all_metadata(output_directory):
    """Audita os metadados de todos os arquivos HTML em um diretório e retorna os problemas."""
    site_root_abs_path = os.path.abspath(output_directory)
    all_issues_by_file = {}
    
    html_files_to_check = glob.glob(os.path.join(site_root_abs_path, '**', '*.html'), recursive=True)

    if not html_files_to_check:
        print("MetadataChecker: Nenhum arquivo HTML encontrado para verificar metadados.")
        return {}

    total_files = len(html_files_to_check)
    print(f"\n🔎 MetadataChecker: Iniciando auditoria de metadados em {total_files} arquivo(s) HTML em '{output_directory}'...")

    for i, html_file_path in enumerate(html_files_to_check):
        progress_percent = ((i + 1) / total_files) * 100
        relative_file_path = html_file_path.replace(site_root_abs_path, '').lstrip(os.sep)
        print(f"  MetadataChecker: [{i+1}/{total_files} | {progress_percent:.1f}%] Processando: {relative_file_path:<70}", end='\r')
        
        file_issues = check_metadata_for_file(html_file_path, site_root_abs_path)
        if file_issues:
            all_issues_by_file[relative_file_path] = file_issues
            
    print("\nMetadataChecker: Auditoria de metadados concluída." + " " * 80) 
    return all_issues_by_file

def print_metadata_report(all_issues_by_file):
    """Imprime o relatório de problemas de metadados de forma legível."""
    if not all_issues_by_file:
        print("\n✅ MetadataChecker: Nenhum problema de metadados encontrado.")
    else:
        print("\n‼️ --- PROBLEMAS DE METADADOS ENCONTRADOS --- ‼️")
        for filepath, issues in sorted(all_issues_by_file.items()): # Ordena por nome do arquivo
            print(f"\n  📄 Arquivo: {filepath}")
            for issue in issues:
                print(f"    - {issue}")
        print(f"\nTotal de arquivos com problemas de metadados: {len(all_issues_by_file)}")
    print("------------------------------------------------\n")

# --- Bloco para Execução via Linha de Comando ---
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Verificador de metadados (SEO, Open Graph, Twitter Cards) para sites HTML estáticos.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        help="O diretório raiz do site contendo os arquivos HTML gerados a serem verificados (ex: public_html)."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"Erro: O diretório especificado '{args.directory}' não existe ou não é um diretório.")
        exit(1)
        
    issues_found = audit_all_metadata(args.directory)
    print_metadata_report(issues_found)