from docxcompose.composer import Composer
from docx import Document
import os
import re

def extrair_numero(nome_arquivo):
    """
    Extrai os dígitos antes do primeiro underscore no nome do arquivo.
    Se encontrado, retorna o número como inteiro; caso contrário, retorna infinito para posicioná-lo ao final.
    """
    match = re.match(r'(\d+)_', nome_arquivo)
    if match:
        return int(match.group(1))
    return float('inf')

def merge_docs_with_page_breaks(output_path, input_paths):
    """
    Mescla os documentos DOCX presentes em input_paths, inserindo uma quebra de página entre cada um,
    e salva o documento final em output_path.
    """
    if not input_paths:
        print("Nenhum arquivo encontrado para mesclar.")
        return

    base_doc = Document(input_paths[0])
    composer = Composer(base_doc)

    for file_path in input_paths[1:]:
        doc = Document(file_path)
        # Adiciona uma quebra de página antes de anexar cada documento
        base_doc.add_page_break()
        composer.append(doc)

    composer.save(output_path)
    print(f"Documents merged successfully into {output_path}")

if __name__ == "__main__":
    # Diretório com os arquivos DOCX
    new_docx_dir = "docx_insight_pages"
    
    # Lista os conteúdos do diretório
    folder_contents = os.listdir(new_docx_dir)
    
    # Filtra e ordena apenas os arquivos DOCX utilizando a função extrair_numero
    docx_files = sorted(
        [f for f in folder_contents if f.lower().endswith('.docx')],
        key=lambda x: extrair_numero(x)
    )
    
    print(f"Arquivos DOCX em ordem no diretório '{new_docx_dir}':")
    for item in docx_files:
        print(item)
    
    # Monta os caminhos completos para os arquivos, mantendo a ordem correta
    input_files = [os.path.join(new_docx_dir, f) for f in docx_files]

    output_file = "merged_document_insight.docx"
    merge_docs_with_page_breaks(output_file, input_files)
