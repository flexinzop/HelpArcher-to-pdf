import os
import re
import json
import time
import hashlib
import requests
import pypandoc
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def get_main_content(html):
    soup = BeautifulSoup(html, "html.parser")
    main_div = soup.find("div", class_="content")
    if not main_div:
        main_div = soup.find("div", class_="home-page-layout")
    if main_div:
        for tag in main_div.find_all(["link", "style"]):
            tag.decompose()
        return main_div.decode_contents()
    else:
        body = soup.body
        return body.decode_contents() if body else html

def process_images(html, base_url, images_dir):
    soup = BeautifulSoup(html, "html.parser")
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
    for img in soup.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        # Primeira tentativa: usar base_url
        abs_url = urljoin(base_url, src)
        # Se o resultado não parecer um URL válido, tenta com a raiz do domínio
        if not abs_url.startswith("http"):
            parsed = urlparse(base_url)
            root = f"{parsed.scheme}://{parsed.netloc}/"
            abs_url = urljoin(root, src)
        try:
            response = requests.get(abs_url, timeout=10)
            # Se o status code não for 200, tenta com a raiz do domínio
            if response.status_code != 200:
                parsed = urlparse(base_url)
                root = f"{parsed.scheme}://{parsed.netloc}/"
                abs_url = urljoin(root, src)
                response = requests.get(abs_url, timeout=10)
            if response.status_code == 200:
                ext = os.path.splitext(abs_url)[1]
                if not ext:
                    ext = ".jpg"
                filename = hashlib.md5(abs_url.encode("utf-8")).hexdigest() + ext
                local_path = os.path.join(images_dir, filename)
                with open(local_path, "wb") as f:
                    f.write(response.content)
                local_path_for_html = os.path.abspath(local_path).replace("\\", "/")
                img["src"] = local_path_for_html
            else:
                img["alt"] = "STB_XX"
                if "src" in img.attrs:
                    del img["src"]
        except Exception as e:
            img["alt"] = "STB_XX"
            if "src" in img.attrs:
                del img["src"]
    return str(soup)

# Carrega o levantamento de URLs (assumindo que foi salvo em "urls.json")
with open("urls_insight.json", "r", encoding="utf-8") as f:
    pages_data = json.load(f)

# Configura o Selenium (Chrome em modo headless)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)

# Diretório para salvar os DOCX individuais
docx_output_dir = "docx_insight_pages"
if not os.path.exists(docx_output_dir):
    os.makedirs(docx_output_dir)

# Diretório para armazenar imagens baixadas
images_dir = "images"
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

# CSS customizado simples (para o HTML que será convertido para DOCX)
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
        # Processa as imagens para baixar e atualizar os src
        content = process_images(content, url, images_dir)
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
        # Cria um nome de arquivo seguro para o DOCX
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
        docx_filename = os.path.join(docx_output_dir, f"{index:02d}_{safe_title}.docx")
        pypandoc.convert_text(html_content, "docx", format="html", outputfile=docx_filename)
        print(f"DOCX gerado: {docx_filename}")
    except Exception as e:
        print(f"Erro ao processar {url}: {e}")

docx_index = 1
for category, pages in pages_data.items():
    for title, url in pages.items():
        generate_docx(url, category, title, docx_index)
        docx_index += 1

driver.quit()
