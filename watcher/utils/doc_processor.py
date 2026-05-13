import pypdf
import docx
from typing import List, Any

def extract_text_from_pdf(file_bytes) -> str:
    """Extract text from a PDF file."""
    reader = pypdf.PdfReader(file_bytes)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()

def extract_text_from_docx(file_bytes) -> str:
    """Extract text from a DOCX file."""
    doc = docx.Document(file_bytes)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text.strip()

def process_uploaded_file(uploaded_file):
    """Detect file type and extract text."""
    name = uploaded_file.name
    if name.lower().endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)
    elif name.lower().endswith(".docx"):
        return extract_text_from_docx(uploaded_file)
    elif name.lower().endswith(".txt"):
        return uploaded_file.read().decode("utf-8")
    else:
        raise ValueError("Unsupported file type. Please upload PDF, DOCX, or TXT.")
