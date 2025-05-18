import os
from datetime import datetime

# Configuração
base_url = "https://mauroreis.app"
public_dir = "public_html"
output_path = os.path.join(public_dir, "sitemap.xml")

def format_url(filepath):
    # Converte caminho absoluto para relativo e constrói URL limpa
    relative = filepath.replace("\\", "/").replace(public_dir + "/", "")
    if relative.endswith("index.html"):
        url = base_url + "/" + relative.replace("index.html", "")
    else:
        url = base_url + "/" + relative
    return url.rstrip("/")

# Geração das entradas do sitemap
entries = []
for root, dirs, files in os.walk(public_dir):
    for file in files:
        if file.endswith(".html"):
            full_path = os.path.join(root, file)
            url = format_url(full_path)
            mod_time = datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d")
            priority = "1.0" if url == base_url else "0.8"
            entry = (
                "  <url>\n"
                f"    <loc>{url}</loc>\n"
                f"    <lastmod>{mod_time}</lastmod> <changefreq>monthly</changefreq> <priority>{priority}</priority> </url>"
            )
            entries.append(entry)

# Montagem do XML final
sitemap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "\n".join(entries) +
    "\n</urlset>"
)

# Escrita do arquivo
with open(output_path, "w", encoding="utf-8") as f:
    f.write(sitemap)

print(f"Sitemap gerado com sucesso: {output_path}")
