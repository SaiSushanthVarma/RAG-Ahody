import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF.
    Handles multi-page PDFs and cleans up whitespace.
    """
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    
    full_text = []
    for page in doc:
        text = page.get_text()
        if text.strip():
            full_text.append(text.strip())
    
    doc.close()
    return "\n\n".join(full_text)