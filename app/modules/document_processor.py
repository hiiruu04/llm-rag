from pathlib import Path
from typing import List

import pypdf
import pytesseract
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file import DocxReader, PDFReader
from loguru import logger
from pdf2image import convert_from_path

from app.core.config import settings


def extract_text_with_ocr(file_path: Path) -> str:
    logger.info("Using OCR to extract text from scanned PDF")
    text = ""

    try:
        images = convert_from_path(file_path, dpi=200)
        logger.info(f"Converted {len(images)} pages to images")

        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            if page_text.strip():
                text += page_text + "\n"
                logger.debug(f"OCR extracted {len(page_text)} characters from page {i}")
            else:
                logger.warning(f"Page {i}: No text extracted via OCR")

    except Exception as e:
        logger.error(f"Error during OCR: {e}")
        raise

    return text


def extract_text_mixed(file_path: Path) -> str:
    logger.info("Processing mixed PDF (text + images) with page-by-page extraction")
    text = ""

    try:
        with open(file_path, "rb") as f:
            pdf_reader = pypdf.PdfReader(f)
            logger.info(f"PDF has {len(pdf_reader.pages)} pages")

        images = convert_from_path(file_path, dpi=200)
        logger.info(f"Converted {len(images)} pages to images for OCR fallback")

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text() or ""

            if page_text.strip() and len(page_text.strip()) > 50:
                logger.debug(f"Page {page_num}: Using text extraction ({len(page_text)} chars)")
                text += page_text + "\n"
            else:
                logger.info(
                    f"Page {page_num}: Low/no text extracted, using OCR ({len(page_text)} chars)"
                )
                ocr_text = pytesseract.image_to_string(images[page_num])
                if ocr_text.strip():
                    text += ocr_text + "\n"
                    logger.debug(f"OCR extracted {len(ocr_text)} characters from page {page_num}")
                else:
                    logger.warning(f"Page {page_num}: No text extracted via OCR either")

    except Exception as e:
        logger.error(f"Error during mixed extraction: {e}")
        raise

    return text


class DocumentProcessor:
    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def extract_text_from_file(self, file_path: str | Path) -> str:
        file_path = Path(file_path)
        logger.info(f"Extracting text from file: {file_path.name}")

        extension = file_path.suffix.lower()

        if extension == ".pdf":
            try:
                logger.info("Attempting PDF extraction")
                text = extract_text_mixed(file_path)

                if not text.strip():
                    logger.warning("Mixed extraction failed, trying pure OCR")
                    text = extract_text_with_ocr(file_path)

                if not text.strip():
                    logger.warning("OCR failed, trying LlamaIndex PDFReader")
                    reader = PDFReader()
                    documents = reader.load_data(file_path)
                    text = "\n".join([doc.text for doc in documents])

                if not text.strip():
                    raise ValueError("PDF appears to be corrupted or has no extractable text.")

            except Exception as e:
                logger.error(f"Error extracting PDF: {e}")
                raise ValueError(f"Failed to extract text from PDF: {e}")
        elif extension in [".txt", ".md"]:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        elif extension == ".docx":
            reader = DocxReader()
            documents = reader.load_data(file_path)
            text = "\n".join([doc.text for doc in documents])
        else:
            raise ValueError(f"Unsupported file format: {extension}")

        logger.info(f"Extracted {len(text)} characters from {file_path.name}")
        return text

    def chunk_text(self, text: str, metadata: dict | None = None) -> List[dict]:
        estimated_tokens = len(text) // 4

        if estimated_tokens < 300:
            chunk_size = 128
        elif estimated_tokens < 1000:
            chunk_size = 256
        else:
            chunk_size = self.chunk_size

        chunk_overlap = chunk_size // 10

        logger.info(
            f"Splitting text into chunks (size={chunk_size}, overlap={chunk_overlap}, "
            f"estimated_tokens={estimated_tokens})"
        )

        splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        doc = Document(text=text, metadata=metadata or {})
        nodes = splitter.get_nodes_from_documents([doc])

        chunks = []
        for i, node in enumerate(nodes):
            chunk_metadata = node.metadata.copy()
            chunk_metadata.update({"chunk_index": i})
            chunks.append({"text": node.text, "metadata": chunk_metadata})

        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def process_file(self, file_path: str | Path, metadata: dict | None = None) -> List[dict]:
        text = self.extract_text_from_file(file_path)
        chunks = self.chunk_text(text, metadata)
        return chunks

    def validate_file_size(self, file_size_bytes: int) -> bool:
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            raise ValueError(
                f"File size exceeds maximum allowed size of {settings.max_file_size_mb}MB"
            )
        return True
