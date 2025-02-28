import re
import json
import pypandoc
from urllib.parse import urlparse
import zipfile
import shutil
import os
from lxml import etree

# --- Parte 1: Construir o mapeamento de URLs para âncoras ---

# Carrega o levantamento de URLs (assumindo que foi salvo em "urls.json")
with open("urls.json", "r", encoding="utf-8") as f:
    urls_data = json.load(f)

# "Achata" o JSON preservando a ordem (Python 3.7+ mantém a ordem de inserção)
flattened_urls = []
for category, pages in urls_data.items():
    for title, url in pages.items():
        flattened_urls.append(url)

# Cria um mapeamento: URL -> âncora (ex.: section_1, section_2, ...)
url_to_anchor = {}
for idx, url in enumerate(flattened_urls, start=1):
    url_to_anchor[url] = f"section_{idx}"

# --- Parte 2: Converter cada DOCX em HTML, inserir âncoras e concatenar ---
docx_dir = "docx_pages_solutions/"  # Diretório onde estão os DOCX individuais
# Ordena os arquivos DOCX; pressupõe-se que a ordem corresponda à do JSON achatado
docx_files = sorted([f for f in os.listdir(docx_dir) if f.lower().endswith('.docx')])

merged_html = "<html><head><meta charset='utf-8'><title>Merged Document</title></head><body>"

for idx, filename in enumerate(docx_files, start=1):
    filepath = os.path.join(docx_dir, filename)
    # Converte o DOCX para HTML usando pypandoc
    html_content = pypandoc.convert_file(filepath, 'html')
    # Insere uma âncora logo após a tag <body>
    anchor = f"section_{idx}"
    html_content = re.sub(r'(<body[^>]*>)', r'\1<a id="' + anchor + r'"></a>', html_content, count=1, flags=re.IGNORECASE)
    merged_html += html_content

merged_html += "</body></html>"

# --- Parte 3: Converter hyperlinks externos para links internos ---
# Substitui links que comecem com uma das URLs do mapeamento por links internos apontando para a âncora correspondente.
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
output_docx = "archer_saas_documentation_athena_v4_sorted.docx"
pypandoc.convert_file("merged.html", 'docx', outputfile=output_docx)
print("Merged DOCX generated:", output_docx)

def remove_external_hyperlinks(docx_path, output_path):
    # Cria um diretório temporário para extrair o DOCX
    temp_dir = "temp_docx"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Extrai o conteúdo do DOCX (é um arquivo ZIP)
    with zipfile.ZipFile(docx_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    # Caminhos para os arquivos XML principais
    document_xml = os.path.join(temp_dir, "word", "document.xml")
    rels_xml = os.path.join(temp_dir, "word", "_rels", "document.xml.rels")
    
    # Parseia o arquivo de relações
    parser = etree.XMLParser(remove_blank_text=True)
    rels_tree = etree.parse(rels_xml, parser)
    nsmap_rels = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}
    
    # Cria um dicionário com os r:id e seus targets externos (aqueles que começam com "http")
    external_rels = {}
    for rel in rels_tree.xpath("//r:Relationship", namespaces=nsmap_rels):
        rId = rel.get("Id")
        target = rel.get("Target")
        if target and target.startswith("http"):
            external_rels[rId] = target
    
    # Parseia o documento principal
    doc_tree = etree.parse(document_xml, parser)
    ns = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    }
    
    # Para cada hyperlink com um r:id que esteja em external_rels,
    # substituímos o elemento pelo seu conteúdo interno (mantendo o texto e formatação)
    hyperlinks = doc_tree.xpath("//w:hyperlink[@r:id]", namespaces=ns)
    for hyperlink in hyperlinks:
        rId = hyperlink.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        if rId in external_rels:
            parent = hyperlink.getparent()
            index = parent.index(hyperlink)
            for child in list(hyperlink):
                parent.insert(index, child)
                index += 1
            parent.remove(hyperlink)
    
    # Opcional: Remover os relacionamentos externos do arquivo rels
    for rel in rels_tree.xpath("//r:Relationship", namespaces=nsmap_rels):
        rId = rel.get("Id")
        if rId in external_rels:
            rel.getparent().remove(rel)
    
    # Salva as modificações nos arquivos XML
    doc_tree.write(document_xml, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    rels_tree.write(rels_xml, pretty_print=True, xml_declaration=True, encoding="UTF-8")
    
    # Recria o DOCX com o conteúdo modificado
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as docx_zip:
        for foldername, subfolders, filenames in os.walk(temp_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, temp_dir)
                docx_zip.write(file_path, arcname)
    
    # Remove o diretório temporário
    shutil.rmtree(temp_dir)
    print(f"Novo DOCX gerado: {output_path}")