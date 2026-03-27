import pdfplumber
import os

# Extract all PDFs
pdfs = {
    'TP0': r'TP0\TP0_Mise_en_Place_ShopFlow.pdf',
    'TP1': r'TP1\TP1_Tests_Unitaires_ShopFlow.pdf',
    'TP2': r'TP2\TP2_Tests_Integration_ShopFlow.pdf',
    'TP3': r'TP3\TP3_Pipeline_Jenkins_ShopFlow.pdf'
}

for name, pdf_path in pdfs.items():
    if os.path.exists(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            txt_path = pdf_path.replace('.pdf', '.txt')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"✓ {name} extracted")
    else:
        print(f"✗ {name} not found")
