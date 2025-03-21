from docxcompose.composer import Composer
from docx import Document
import os

def merge_docs_with_page_breaks(output_path, input_paths):
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
    new_docx_dir = "new_docx"
    # Lista todos os arquivos .docx do diretório e ordena-os
    input_files = sorted([os.path.join(new_docx_dir, f) for f in os.listdir(new_docx_dir) if f.lower().endswith('.docx')])
    output_file = "archer_saas_documentation_solutions_v1.docx"
    merge_docs_with_page_breaks(output_file, input_files)
