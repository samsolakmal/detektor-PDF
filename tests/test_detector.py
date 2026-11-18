import io
import unittest

from docx import Document
from pypdf import PdfWriter

from detector import analyze_text, extract_document


class UploadedFile:
    def __init__(self, name, content):
        self.name = name
        self._content = content

    def getvalue(self):
        return self._content


class DetectorTests(unittest.TestCase):
    def test_scores_all_indicators_and_stays_within_bounds(self):
        text = (
            "Selain itu, penting untuk dicatat. Selain itu, kita perlu menilai hasil.\n"
            "1. Judul Poin: Penjelasan ini memuat beberapa kata.\n"
            "\u2014 \u2013 \u200b\u200c"
        )
        result = analyze_text(text)

        self.assertEqual(result["special_score"], 20)
        self.assertEqual(result["phrase_score"], 15)
        self.assertEqual(result["list_score"], 5)
        self.assertLessEqual(result["total_score"], 100)

    def test_extract_docx_paragraphs_tables_and_author(self):
        document = Document()
        document.core_properties.author = "Test Author"
        document.add_paragraph(
            "Dokumen ini berisi teks contoh yang cukup panjang untuk melewati "
            "ambang validasi lima puluh karakter."
        )
        document.add_table(rows=1, cols=1).cell(0, 0).text = "Teks dari tabel"
        content = io.BytesIO()
        document.save(content)

        text, page_count, metadata = extract_document(
            UploadedFile("sample.docx", content.getvalue())
        )

        self.assertIn("Dokumen ini berisi", text)
        self.assertIn("Teks dari tabel", text)
        self.assertIsNone(page_count)
        self.assertEqual(metadata["Creator"], "Test Author")

    def test_short_pdf_is_rejected(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        content = io.BytesIO()
        writer.write(content)

        with self.assertRaisesRegex(ValueError, "kurang dari 50 karakter"):
            extract_document(UploadedFile("sample.pdf", content.getvalue()))

    def test_legacy_doc_is_rejected(self):
        with self.assertRaisesRegex(ValueError, r"\.docx"):
            extract_document(UploadedFile("sample.doc", b"legacy word"))


if __name__ == "__main__":
    unittest.main()
