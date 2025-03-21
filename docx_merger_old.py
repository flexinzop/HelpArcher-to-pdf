import os
import re
import json
import pypandoc
from urllib.parse import urlparse

# --- Parte 1: Construir o mapeamento de URLs para âncoras ---
with open("urls_solutions.json", "r", encoding="utf-8") as f:
    urls_data = json.load(f)

flattened_urls = []
for category, pages in urls_data.items():
    for title, url in pages.items():
        flattened_urls.append(url)

url_to_anchor = {}
for idx, url in enumerate(flattened_urls, start=1):
    url_to_anchor[url] = f"section_{idx}"

# --- Parte 2: Converter cada DOCX em HTML, inserir âncoras e concatenar ---
docx_dir = "new_docx"  # Diretório onde estão os DOCX individuais
docx_files = sorted([f for f in os.listdir(docx_dir) if f.lower().endswith('.docx')])

# Cria (ou usa) o diretório onde as imagens extraídas serão armazenadas
media_dir = "merged_media"
if not os.path.exists(media_dir):
    os.makedirs(media_dir)

merged_html = "<html><head><meta charset='utf-8'><title>Merged Document</title></head><body>"

for idx, filename in enumerate(docx_files, start=1):
    filepath = os.path.join(docx_dir, filename)
    # Converte o DOCX para HTML com extração das imagens para o diretório "merged_media"
    html_content = pypandoc.convert_file(
        filepath, 
        'html', 
        extra_args=["--extract-media=merged_media"]
    )
    # Insere uma âncora logo após a tag <body>
    anchor = f"section_{idx}"
    html_content = re.sub(r'(<body[^>]*>)', r'\1<a id="' + anchor + r'"></a>', html_content, count=1, flags=re.IGNORECASE)
    merged_html += html_content

merged_html += "</body></html>"

# --- Parte 3: Converter hyperlinks externos para links internos ---
def replace_link(match):
    href = match.group(1)
    for orig_url, anchor in url_to_anchor.items():
        if href.startswith(orig_url):
            return f'<a href="#{anchor}"'
    return match.group(0)

merged_html = re.sub(r'<a\s+href="([^"]+)"', replace_link, merged_html)

# Salva o HTML final para conferência (opcional)
with open("merged.html", "w", encoding="utf-8") as f:
    f.write(merged_html)

# --- Parte 4: Converter o HTML final para DOCX ---
output_docx = "archer_saas_documentation_solutions_v1.docx"
pypandoc.convert_file("merged.html", 'docx', outputfile=output_docx)
print("Merged DOCX generated:", output_docx)

# MERGE .DOCX
# Step: 4