import requests
from bs4 import BeautifulSoup
import json

# URL inicial
base_url = "https://help.archerirm.cloud/platform_2025_02/pt-br/content/platform/gettingstarted/platform_welcome.htm"

# Função para capturar os links
def get_links(url):
    response = requests.get(url)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Pegando todos os links da página
    main_menu = soup.find_all("a")

    sections = {}
    for link in main_menu:
        if link.has_attr("href"):
            href = link["href"]
            if not href.startswith("http"):  # Construir URL completa se for relativa
                full_url = "/".join(url.split("/")[:-1]) + "/" + href
            else:
                full_url = href
            
            text = link.get_text(strip=True)
            if text:
                sections[text] = full_url

    return sections

# Captura os links do primeiro nível
first_level_links = get_links(base_url)

# Estrutura do JSON
data_structure = {"root": first_level_links}

# Para cada seção do primeiro nível, capturar os links do segundo nível
for section, section_url in first_level_links.items():
    sub_links = get_links(section_url)
    if sub_links:
        data_structure[section] = sub_links

# Salvar o JSON
with open("archer_doc_structure.json", "w", encoding="utf-8") as json_file:
    json.dump(data_structure, json_file, ensure_ascii=False, indent=4)

print("JSON gerado com sucesso!")
