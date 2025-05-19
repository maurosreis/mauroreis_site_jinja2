from jinja2 import Environment, FileSystemLoader
import os

env = Environment(loader=FileSystemLoader('templates'))
output_folder = 'public_html'

pages_data = [
    {
        'template': 'home_content.html',
        'output_path': 'index.html',
        'vars': {
            # title, description, keywords, path são agora definidos nos templates HTML
            'current_page': 'home',
            'is_home': True,
            'css_path': 'style.css',
            'nav_prefix': '',
            'assets_prefix': 'assets/'
        }
    },
    {
        'template': 'eletronica_potencia_content.html',
        'output_path': 'eletronica-potencia.html',
        'vars': {
            'current_page': 'eletronica_potencia',
            'is_home': False,
            'css_path': 'style.css',
            'nav_prefix': '',
            'assets_prefix': 'assets/'
        }
    },
    {
        'template': 'ensino_content.html',
        'output_path': 'ensino/index.html',
        'vars': {
            'current_page': 'ensino',
            'is_home': False,
            'css_path': '../style.css',
            'nav_prefix': '../',
            'assets_prefix': '../assets/'
        }
    },
    {
        'template': 'pesquisa_content.html',
        'output_path': 'pesquisa/index.html',
        'vars': {
            'current_page': 'pesquisa',
            'is_home': False,
            'css_path': '../style.css',
            'nav_prefix': '../',
            'assets_prefix': '../assets/'
        }
    },
    {
        'template': 'extensao_content.html',
        'output_path': 'extensao/index.html',
        'vars': {
            'current_page': 'extensao',
            'is_home': False,
            'css_path': '../style.css',
            'nav_prefix': '../',
            'assets_prefix': '../assets/'
        }
    }
]

for page_config in pages_data:
    template = env.get_template(page_config['template'])
    # As variáveis de 'vars' (css_path, etc.) são passadas
    # Os metadados (title, etc.) serão resolvidos pela herança de blocos do Jinja
    html_content = template.render(page_config['vars'])
    full_output_path = os.path.join(output_folder, page_config['output_path'])
    os.makedirs(os.path.dirname(full_output_path), exist_ok=True)
    with open(full_output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Página gerada: {full_output_path}")