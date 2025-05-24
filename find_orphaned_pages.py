# find_orphaned_pages.py
"""
===================================================================
Localizador de Páginas Órfãs (find_orphaned_pages.py)
===================================================================

Objetivo:
---------
Este script analisa um site estático gerado (conjunto de arquivos HTML)
para identificar "páginas órfãs". Uma página órfã é uma página HTML
que existe no site, mas não possui nenhum link interno apontando para ela
a partir de outras páginas do mesmo site.

Identificar páginas órfãs é importante para SEO e para a experiência
do usuário, pois essas páginas podem ser difíceis de serem descobertas
por motores de busca e visitantes.

Como Usar:
-----------
O script deve ser executado a partir do terminal após o site ter sido
completamente gerado (ex: após rodar o build.py). Você precisa
passar o caminho para o diretório raiz do site gerado (normalmente
'public_html') como um argumento.

Sintaxe:
  python find_orphaned_pages.py <DIRETORIO_RAIZ_DO_SITE_GERADO>

Exemplo de Uso:
  python find_orphaned_pages.py public_html

Dependências:
-------------
- beautifulsoup4: Para parsear o conteúdo HTML e extrair links.
  (Certifique-se de que está listado em seu requirements.txt)

O que o script faz:
-------------------
1.  Varre o diretório fornecido para encontrar todos os arquivos .html.
2.  Para cada arquivo .html encontrado, extrai todos os links <a>.
3.  Filtra e normaliza os links internos, resolvendo-os para caminhos
    relativos à raiz do site.
4.  Compara a lista de todos os arquivos HTML existentes com a lista de
    todos os arquivos HTML que são alvos de links internos.
5.  Reporta os arquivos HTML que existem mas não são linkados.

Nota: A página inicial (index.html na raiz) pode aparecer como órfã
se não houver links explícitos para ela, mas geralmente é o ponto de
entrada do site e não é considerada uma órfã no sentido problemático.
"""
import os
import glob
from bs4 import BeautifulSoup
from urllib.parse import urlparse, unquote
import argparse

def normalize_path(path_str):
    """Normaliza um caminho, decodifica e remove barras extras."""
    return os.path.normpath(unquote(path_str)).replace(os.sep, '/')

def resolve_internal_link_target(href_value, source_file_relative_path, site_root_abs_path):
    """
    Resolve um valor href para um caminho de arquivo normalizado relativo à raiz do site.
    Retorna None para links externos, âncoras na mesma página ou links não resolvidos.
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

    # Se o link resolvido aponta para um diretório, assume que ele deveria apontar para o index.html dentro dele
    if os.path.isdir(normalized_abs_path):
        normalized_abs_path_with_index = normalize_path(os.path.join(normalized_abs_path, 'index.html'))
        # Verifica se o index.html realmente existe nesse diretório
        if os.path.isfile(normalized_abs_path_with_index):
             normalized_abs_path = normalized_abs_path_with_index
        # Se não há index.html, mas o diretório existe, o link pode ser para o diretório em si.
        # No entanto, para comparar com arquivos, precisamos de um arquivo.
        # Se você não quiser essa lógica de index.html automático, remova este bloco.
        # else:
            # return None # Ou considera o link para diretório como não apontando para um arquivo HTML específico

    # Garante que o caminho resolvido ainda está dentro do diretório do site
    if not normalized_abs_path.startswith(normalize_path(site_root_abs_path)):
        return None # Link aponta para fora do site

    # Retorna o caminho relativo à raiz do site
    relative_target_path = os.path.relpath(normalized_abs_path, site_root_abs_path)
    return normalize_path(relative_target_path)


def find_orphaned_pages_in_site(output_dir_path):
    """
    Encontra e retorna uma lista de páginas HTML órfãs em um diretório de site.
    """
    site_root_abs = os.path.abspath(output_dir_path)
    all_site_html_files = set() # Armazena caminhos relativos à raiz, ex: 'ensino/index.html'
    internally_linked_html_files = set()

    # 1. Descobre todos os arquivos HTML no site
    for html_filepath_abs in glob.glob(os.path.join(site_root_abs, '**', '*.html'), recursive=True):
        relative_path = os.path.relpath(html_filepath_abs, site_root_abs)
        all_site_html_files.add(normalize_path(relative_path))

    if not all_site_html_files:
        print(f"Nenhum arquivo HTML encontrado em '{output_dir_path}'.")
        return []

    # 2. Processa cada arquivo HTML para encontrar para onde ele linka
    for html_filepath_abs in glob.glob(os.path.join(site_root_abs, '**', '*.html'), recursive=True):
        current_file_relative = normalize_path(os.path.relpath(html_filepath_abs, site_root_abs))
        
        try:
            with open(html_filepath_abs, 'r', encoding='utf-8') as f:
                content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                resolved_target = resolve_internal_link_target(href, current_file_relative, site_root_abs)
                
                if resolved_target and resolved_target in all_site_html_files:
                    internally_linked_html_files.add(resolved_target)
        except Exception as e:
            print(f"⚠️  Erro ao processar o arquivo '{current_file_relative}' para links: {e}")

    # 3. Identifica as páginas órfãs
    # Uma página é órfã se ela existe (está em all_site_html_files)
    # mas não é o destino de nenhum link interno (não está em internally_linked_html_files).
    orphaned_pages = all_site_html_files - internally_linked_html_files
    
    # A página inicial (index.html) geralmente não é considerada órfã,
    # mesmo que não haja links para ela de outras páginas, pois é o ponto de entrada.
    # Você pode optar por removê-la da lista de órfãs se ela aparecer.
    homepage_normalized = normalize_path('index.html')
    if homepage_normalized in orphaned_pages:
        # print(f"Nota: '{homepage_normalized}' está listada como órfã, mas é a página inicial.")
        # Opcionalmente, remova-a se não quiser que seja reportada:
        # orphaned_pages.remove(homepage_normalized)
        pass


    return sorted(list(orphaned_pages))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Encontra páginas HTML órfãs (não linkadas por outros links internos) em um site estático gerado.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "directory",
        help="O diretório raiz do site gerado (ex: public_html) para verificar por páginas órfãs."
    )
    args = parser.parse_args()

    if not os.path.isdir(args.directory):
        print(f"❌ Erro: O diretório especificado '{args.directory}' não existe ou não é um diretório válido.")
        exit(1)

    print(f"🔎 Verificando páginas órfãs em: {os.path.abspath(args.directory)}")
    orphans = find_orphaned_pages_in_site(args.directory)

    if orphans:
        print("\n‼️ --- PÁGINAS ÓRFÃS ENCONTRADAS --- ‼️")
        print("As seguintes páginas HTML existem no site, mas nenhum link interno aponta para elas:")
        for page_path in orphans:
            print(f"  - {page_path}")
        print(f"\nTotal de páginas órfãs encontradas: {len(orphans)}")
        print("Considere adicionar links para estas páginas a partir de conteúdo relevante,")
        print("ou removê-las se não forem mais necessárias ou se forem conteúdo de rascunho.")
    else:
        print("\n✅ Nenhuma página órfã encontrada no site.")
    print("-" * 40 + "\n")