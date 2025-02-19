import os
import json
import time
import pypandoc
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Função para extrair o conteúdo principal: tenta a div "content"; se não encontrar, retorna o conteúdo do <body>
def get_main_content(html):
    soup = BeautifulSoup(html, "html.parser")
    main_div = soup.find("div", class_="content")
    if not main_div:
        main_div = soup.find("div", class_="home-page-layout")
    if main_div:
        # Remove tags <link> e <style> para evitar conflitos
        for tag in main_div.find_all(["link", "style"]):
            tag.decompose()
        return main_div.decode_contents()
    else:
        body = soup.body
        return body.decode_contents() if body else html

# Carrega o levantamento de URLs do arquivo JSON (gerado anteriormente, por exemplo, a partir do pages.txt)
with open("urls.json", "r", encoding="utf-8") as f:
    pages_data = json.load(f)

# Configura o Selenium (Chrome em modo headless)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)

# Cria o diretório para salvar os DOCX, se não existir
docx_output_dir = "docx_pages"
if not os.path.exists(docx_output_dir):
    os.makedirs(docx_output_dir)

# CSS simples (opcional) para formatação do DOCX – será incorporado no HTML convertido
custom_css = """
<style>
body { font-family: sans-serif; }
h1 { font-size: 24pt; }
p { font-size: 12pt; }
</style>
"""

def generate_docx(url, category, title, index):
    try:
        print(f"Processando: {title} - {url}")
        driver.get(url)
        time.sleep(2)  # Aguarda o carregamento completo da página
        page_source = driver.page_source
        content = get_main_content(page_source)
        if not content.strip():
            print(f"Nenhum conteúdo encontrado em: {url}")
            return
        # Monta o HTML a ser convertido para DOCX
        html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{custom_css}
</head>
<body>
<h1>{title}</h1>
<p><strong>Categoria:</strong> {category}</p>
<p><strong>URL:</strong> <a href="{url}">{url}</a></p>
{content}
</body>
</html>
"""
        # Cria um nome de arquivo seguro (removendo caracteres inválidos)
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        docx_filename = os.path.join(docx_output_dir, f"{index:02d}_{safe_title}.docx")
        # Converte o HTML para DOCX usando pypandoc
        pypandoc.convert_text(html_content, 'docx', format='html', outputfile=docx_filename)
        print(f"DOCX gerado: {docx_filename}")
    except Exception as e:
        print(f"Erro ao processar {url}: {e}")

# Gera um DOCX para cada URL no levantamento
docx_index = 1
for category, pages in pages_data.items():
    for title, url in pages.items():
        generate_docx(url, category, title, docx_index)
        docx_index += 1

driver.quit()
