import os
import re
import json
import time
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from weasyprint import HTML

# ============================
# Parte 1: Converter pages.txt para JSON
# ============================

def parse_pages_txt(filename):
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    data = {}
    current_category = None
    stack = []         # Guarda os títulos dos níveis atuais
    indent_stack = []  # Guarda o nível de indentação de cada item no stack

    for line in lines:
        line = line.rstrip("\n")
        if not line.strip():
            continue

        # Calcular o número de espaços à esquerda (indent)
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.lstrip(" ")

        # Se a linha começar com "-" e NÃO contiver "[" assume-se que é um cabeçalho de categoria
        if stripped.startswith("-") and "[" not in stripped:
            cat = stripped[1:].strip()
            current_category = cat
            data[current_category] = {}
            stack = []
            indent_stack = []
            continue

        # Caso contrário, a linha deve conter um link no formato: - [Título](URL)
        m = re.search(r'-\s*\[([^\]]+)\]\(([^)]+)\)', stripped)
        if m:
            title = m.group(1).strip()
            url = m.group(2).strip()
            level = indent // 4  # assumindo 4 espaços por nível

            # Ajusta o stack para que seu comprimento seja igual ao nível atual
            while indent_stack and indent_stack[-1] >= indent:
                stack.pop()
                indent_stack.pop()
            stack.append(title)
            indent_stack.append(indent)
            flat_title = " - ".join(stack)
            if current_category is not None:
                data[current_category][flat_title] = url
        else:
            continue

    return data

# Converte o arquivo "pages.txt" para JSON (estrutura de dicionário)
pages_data = parse_pages_txt("pages.txt")

# Salva o JSON em "urls.json" (opcional)
with open("urls.json", "w", encoding="utf-8") as f:
    json.dump(pages_data, f, ensure_ascii=False, indent=4)

print("JSON gerado:")
print(json.dumps(pages_data, ensure_ascii=False, indent=4))

# ============================
# Parte 2: Webscraping e geração de PDFs
# ============================

# Configura o Selenium (Chrome em modo headless)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=chrome_options)

# Cria o diretório para salvar os PDFs, se não existir
output_dir = "pdf_pages"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

def get_main_content(html):
    """Extrai e retorna o conteúdo da div com a classe 'content'. Se não encontrada, retorna uma string vazia."""
    soup = BeautifulSoup(html, "html.parser")
    content_div = soup.find("div", class_="content")
    if content_div:
        # Remove tags <link> e <style> que possam interferir
        for tag in content_div.find_all(["link", "style"]):
            tag.decompose()
        return content_div.decode_contents()
    else:
        return ""

# CSS customizado para formatação do PDF
custom_css = """
@page { margin: 1in !important; }
body { margin: 0 !important; font-family: sans-serif !important; }
table { border-collapse: collapse !important; width: 100% !important; margin-bottom: 1em !important; }
table, th, td { border: 1px solid #000 !important; }
th, td { padding: 8px !important; text-align: left !important; word-wrap: break-word !important; }
"""

pdf_index = 1

# Itera sobre o levantamento e gera um PDF para cada URL
for category, pages in pages_data.items():
    for title, url in pages.items():
        try:
            print(f"Processando: {title} - {url}")
            driver.get(url)
            time.sleep(2)  # Aguarda o carregamento completo da página
            page_source = driver.page_source
            content = get_main_content(page_source)
            if not content:
                print(f"Nenhum conteúdo encontrado em: {url}")
                continue

            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>{custom_css}</style>
</head>
<body>
    {content}
</body>
</html>
"""
            # Cria um nome de arquivo seguro para o PDF (remove caracteres inválidos)
            safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)
            pdf_filename = os.path.join(output_dir, f"{pdf_index:02d}_{safe_title}.pdf")
            HTML(string=html_content, base_url=url).write_pdf(pdf_filename)
            print(f"PDF gerado: {pdf_filename}")
            pdf_index += 1
        except Exception as e:
            print(f"Erro ao processar {url}: {e}")

driver.quit()