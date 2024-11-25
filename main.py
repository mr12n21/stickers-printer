import fitz

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text")
    return text

def create_code_from_text(text, num_chars=8):
    lines = text.splitlines()
    code = ""
    
    for line in lines:
        code += line[:num_chars]
    
    return code[:num_chars]

pdf_path = "path_to_pdf.pdf"
text = extract_text_from_pdf(pdf_path)
code = create_code_from_text(text)
print(f"stitek: {code}")
