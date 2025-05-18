from jinja2 import Environment, FileSystemLoader
import os

env = Environment(loader=FileSystemLoader('templates'))
output_folder = 'public_html'

pages_data = [
    {'template': 'home_content.html', 'output_path': 'index.html', 'vars': {
        'page_title': 'Página Inicial', 'is_home': True, 'current_page': 'home',
        'css_path': 'style.css', 'nav_prefix': '', 'assets_prefix': 'assets/'
    }},
    {'template': 'eletronica_potencia_content.html', 'output_path': 'eletronica-potencia.html', 'vars': {
        'page_title': 'Eletrônica de Potência', 'is_home': False, 'current_page': 'eletronica_potencia',
        'page_header_title': 'Eletrônica de Potência', 'css_path': 'style.css', 'nav_prefix': '', 'assets_prefix': 'assets/'
    }},
    {'template': 'ensino_content.html', 'output_path': 'ensino/index.html', 'vars': {
        'page_title': 'Ensino', 'is_home': False, 'current_page': 'ensino',
        'page_header_title': 'Ensino', 'css_path': '../style.css', 'nav_prefix': '../', 'assets_prefix': '../assets/'
    }},
    {'template': 'pesquisa_content.html', 'output_path': 'pesquisa/index.html', 'vars': {
        'page_title': 'Pesquisa', 'is_home': False, 'current_page': 'pesquisa',
        'page_header_title': 'Pesquisa', 'css_path': '../style.css', 'nav_prefix': '../', 'assets_prefix': '../assets/'
    }},
    {'template': 'extensao_content.html', 'output_path': 'extensao/index.html', 'vars': {
        'page_title': 'Extensão', 'is_home': False, 'current_page': 'extensao',
        'page_header_title': 'Extensão', 'css_path': '../style.css', 'nav_prefix': '../', 'assets_prefix': '../assets/'
    }}
]

for page in pages_data:
    template = env.get_template(page['template'])
    html = template.render(page['vars'])
    full_path = os.path.join(output_folder, page['output_path'])
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Página gerada: {full_path}")