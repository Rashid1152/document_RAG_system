from typing import List
import os
from PyPDF2 import PdfReader
import docx
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter


def chunk_text(text: str, min_tokens: int = 400, max_tokens: int = 500) -> List[str]:
    encoding = tiktoken.get_encoding("cl100k_base")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_tokens,
        chunk_overlap=50,
        separators=["\n\n", ".", "\n", " "]
    )

    raw_chunks = splitter.split_text(text)

    # Filter out chunks that are too small
    final_chunks = []
    buffer = ""

    for chunk in raw_chunks:
        buffer += chunk + " "
        token_len = len(encoding.encode(buffer))

        if token_len >= min_tokens:
            final_chunks.append(buffer.strip())
            buffer = ""

    # Add remaining buffer if it's large enough
    if buffer and len(encoding.encode(buffer)) >= min_tokens:
        final_chunks.append(buffer.strip())

    return final_chunks


def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path: str) -> str:
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError('Unsupported file type') 