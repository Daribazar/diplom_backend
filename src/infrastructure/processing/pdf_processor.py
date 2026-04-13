"""PDF file processor."""

import pypdf
from io import BytesIO
from typing import List


class PDFProcessor:
    """Process PDF files and extract text."""

    async def extract_text(self, file_data: bytes) -> str:
        """
        Extract text from PDF file.

        Args:
            file_data: PDF file content as bytes

        Returns:
            Extracted text content

        Raises:
            ValueError: If PDF extraction fails
        """
        try:
            # Create PDF reader from bytes
            pdf_file = BytesIO(file_data)
            reader = pypdf.PdfReader(pdf_file)

            # Extract text from all pages
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            # Clean text
            text = self._clean_text(text)

            if not text or len(text) < 100:
                raise ValueError("Extracted text is too short or empty")

            return text

        except Exception as e:
            raise ValueError(f"PDF extraction failed: {str(e)}")

    async def extract_pages(self, file_data: bytes) -> List[str]:
        """
        Extract text from each page separately.

        Args:
            file_data: PDF file content as bytes

        Returns:
            List of text content per page
        """
        try:
            pdf_file = BytesIO(file_data)
            reader = pypdf.PdfReader(pdf_file)

            pages = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    pages.append(self._clean_text(page_text))

            return pages

        except Exception as e:
            raise ValueError(f"PDF extraction failed: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text.

        Args:
            text: Raw extracted text

        Returns:
            Cleaned text
        """
        # Remove excessive whitespace
        text = " ".join(text.split())

        # Remove page numbers (simple heuristic)
        lines = text.split("\n")
        cleaned_lines = [
            line
            for line in lines
            if not (line.strip().isdigit() and len(line.strip()) < 4)
        ]

        return "\n".join(cleaned_lines)
