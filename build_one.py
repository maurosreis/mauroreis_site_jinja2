# build_one.py
"""
Script de build genérico para gerar uma única página HTML a partir de um
template de conteúdo específico.

Objetivo:
---------
Permitir a rápida regeneração de uma página individual sem executar o
processo de build completo. Ele tenta replicar a lógica de saída do
script build.py principal para páginas individuais.

Como Usar:
-----------
O script deve ser executado a partir do terminal, passando o nome do
arquivo de template de conteúdo que você deseja gerar como argumento.
Você também pode especificar um caminho de saída relativo opcional.

Sintaxe:
  python build_one.py <NOME_DO_TEMPLATE_DE_CONTEÚDO> [CAMINHO_DE_SAÍDA_OPCIONAL]

Exemplos de Uso:
  
  # Gerar 'sobre-o-projeto.html' na raiz (saída padrão)
  python build_one.py sobre_projeto_content.html

  # Gerar a página de ensino em seu subdiretório específico
  python build_one.py ensino_content.html ensino/index.html

  # Gerar a página inicial
  python build_one.py home_content.html index.html
  
"""
import os
import sys
from jinja2 import Environment, FileSystemLoader

# --- Início da Lógica do Script ---

# 1. Validar Argumentos da Linha de Comando
if len(sys.argv) < 2:
    print("❌ Erro: Faltando argumento. Você precisa especificar o nome do arquivo de template a ser gerado.")
    print("Uso: python build_one.py <nome_do_arquivo_content.html> [caminho_de_saida_opcional.html]")
    sys.exit(1)

template_to_build = sys.argv[1]
# O caminho de saída é opcional
output_path_arg = sys.argv[2] if len(sys.argv) > 2 else None

# 2. Configuração do Ambiente Jinja2 e Pastas
templates_dir = 'templates'
output_folder = 'public_html'

env = Environment(loader=FileSystemLoader(templates_dir))

# Verifica se o template solicitado existe
try:
    template = env.get_template(template_to_build)
except Exception as e:
    print(f"❌ Erro: Não foi possível encontrar ou carregar o template '{template_to_build}' na pasta '{templates_dir}'.")
    print(f"Detalhe: {e}")
    sys.exit(1)

print(f"⚙️  Iniciando build para o template: {template_to_build}...")

# 3. Gerar Configuração da Página
def get_page_config(template_filename, custom_output_path=None):
    """
    Gera a configuração para uma página, usando um caminho de saída personalizado se fornecido,
    ou gerando um padrão caso contrário.
    """
    base_name = template_filename.removesuffix('_content.html')
    output_path = custom_output_path

    # Se nenhum caminho de saída foi fornecido, gera um padrão
    if output_path is None:
        if base_name == 'home':
            output_path = 'index.html'
        else:
            output_path = base_name.replace('_', '-') + '.html'
    
    # Determina a profundidade do diretório para ajustar os caminhos relativos
    depth = output_path.count('/')
    nav_prefix_value = '../' * depth
    
    # Regra para as variáveis (vars)
    page_vars = {
        'current_page': base_name,
        'is_home': (base_name == 'home'),
        'css_path': nav_prefix_value + 'style.css',
        'nav_prefix': nav_prefix_value,
        'assets_prefix': nav_prefix_value + 'assets/'
    }
    
    return {
        'template': template_filename,
        'output_path': output_path,
        'vars': page_vars
    }

page_config = get_page_config(template_to_build, output_path_arg)

# 4. Processo de Renderização e Geração
try:
    # Renderiza o template com as variáveis geradas
    html_content = template.render(page_config['vars'])
    
    # Define o caminho completo de saída
    full_output_path = os.path.join(output_folder, page_config['output_path'])
    
    # Cria o diretório de saída se ele não existir
    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
    
    # Escreve o conteúdo HTML no arquivo
    with open(full_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ Página gerada com sucesso: {full_output_path}")
    print(f"   -> Variáveis usadas: css_path='{page_config['vars']['css_path']}', nav_prefix='{page_config['vars']['nav_prefix']}'")

except Exception as e:
    print(f"❌ Erro ao gerar a página: {e}")
    sys.exit(1)