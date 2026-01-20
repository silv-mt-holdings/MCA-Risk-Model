"""
PDF Extractor
=============
Extract text and tables from bank statement PDFs.

Uses pdfplumber for text extraction and table detection.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class ExtractedPage:
    """Represents extracted content from a PDF page"""
    page_number: int
    text: str
    tables: List[List[List[str]]]


class PDFExtractor:
    """
    Extract text and tables from PDF files.

    Usage:
        extractor = PDFExtractor('statement.pdf')
        pages = extractor.extract_all()
        tables = extractor.get_tables()
    """

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pages: List[ExtractedPage] = []

    def extract_all(self) -> List[ExtractedPage]:
        """
        Extract text and tables from all pages.

        Returns:
            List of ExtractedPage objects
        """
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber required: pip install pdfplumber")

        pages = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                extracted = ExtractedPage(
                    page_number=i + 1,
                    text=page.extract_text() or '',
                    tables=page.extract_tables() or [],
                )
                pages.append(extracted)

        self.pages = pages
        return pages

    def get_tables(self) -> List[List[List[str]]]:
        """Get all tables from all pages"""
        if not self.pages:
            self.extract_all()

        all_tables = []
        for page in self.pages:
            all_tables.extend(page.tables)
        return all_tables

    def get_text(self) -> str:
        """Get all text from all pages"""
        if not self.pages:
            self.extract_all()

        return '\n\n'.join(page.text for page in self.pages)


def extract_tables(pdf_path: str) -> List[List[List[str]]]:
    """Convenience function to extract tables from PDF"""
    extractor = PDFExtractor(pdf_path)
    return extractor.get_tables()


def extract_text(pdf_path: str) -> str:
    """Convenience function to extract text from PDF"""
    extractor = PDFExtractor(pdf_path)
    return extractor.get_text()
