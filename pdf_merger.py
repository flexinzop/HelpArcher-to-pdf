import os
from PyPDF2 import PdfMerger

def merge_pdfs(pdf_dir, output_filename):
    merger = PdfMerger()
    # Lista os PDFs, ordenando pelo nome (para manter a ordem desejada, se necessário)
    pdf_files = sorted([os.path.join(pdf_dir, f) for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')])
    
    for pdf in pdf_files:
        merger.append(pdf)
        print(f"Adicionado: {pdf}")
    
    merger.write(output_filename)
    merger.close()
    print(f"PDF final gerado: {output_filename}")

# Exemplo de uso:
merge_pdfs("pdf_pages", "archer_saas_documentation_athena.pdf")
