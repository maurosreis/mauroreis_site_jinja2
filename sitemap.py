import os
from datetime import datetime

# Configurações
base_url = "https://mauroreis.app"
public_dir = "public_html"
sitemap_path = os.path.join(public_dir, "sitemap.xml")

# Função para formatar URLs
def format_url(filepath):
    relative_path = filepath.replace("\\", "/").replace(public_dir + "/", "")
    if relative_path.endswith("index.html"):
        url = base_url + "/" + relative_path.replace("index.html", "")
    else:
        url = base_url + "/" + relative_path
    return url.rstrip("/")

# Buscar arquivos .html
entries = []
for root, dirs, files in os.walk(public_dir):
    for file in files:
        if file.endswith(".html"):
            full_path = os.path.join(root, file)
            url = format_url(full_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d")
            entries.append(f"""  <url>
    <loc>{url}</loc>
    <lastmod>{mod_time}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>""")

# Montar XML
sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(entries)}
</urlset>
"""

# Salvar
with open(sitemap_path, "w", encoding="utf-8") as f:
    f.write(sitemap_content)

print(f"Sitemap gerado com sucesso: {sitemap_path}")
