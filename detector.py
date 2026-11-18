import re
import statistics
from io import BytesIO
from zipfile import BadZipFile

from docx import Document
from docx.opc.exceptions import PackageNotFoundError
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from pypdf import PdfReader
from pypdf.errors import PdfReadError


# Maintain the explicit phrase and symbol lists used by the rule-based detector.
TRANSITION_PHRASES = (
    "selain itu",
    "oleh karena itu",
    "penting untuk dicatat",
    "dalam era digital",
    "secara keseluruhan",
    "kesimpulannya",
    "di sisi lain",
    "dengan demikian",
    "hal ini menunjukkan bahwa",
    "moreover",
    "furthermore",
    "in conclusion",
    "it is important to note",
)
SPECIAL_CHARACTERS = {
    "Em dash (—)": "—",
    "En dash (–)": "–",
    "Zero-width space (U+200B)": "\u200b",
    "Zero-width non-joiner (U+200C)": "\u200c",
}
LIST_PATTERN = re.compile(
    r"^[ \t]*(?:\d+[.)]|[-*•])[ \t]+[^:\r\n]{1,100}:[ \t]+\S[^\r\n]*",
    re.MULTILINE,
)


def _extract_pdf(uploaded_file):
    """Read digital text and Creator/Producer metadata from a PDF upload."""
    try:
        reader = PdfReader(BytesIO(uploaded_file.getvalue()))
        if reader.is_encrypted:
            raise ValueError("PDF terenkripsi atau dilindungi kata sandi.")

        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except PdfReadError as error:
        raise ValueError(f"Struktur PDF tidak dapat dibaca: {error}") from error

    if len(text.strip()) < 50:
        raise ValueError(
            "Teks yang berhasil diekstrak kurang dari 50 karakter. "
            "PDF kemungkinan berupa hasil scan gambar atau tidak memiliki teks yang dapat dibaca."
        )

    metadata = reader.metadata
    return text, len(reader.pages), {
        "Creator": (
            str(metadata.get("/Creator") or "Tidak tersedia")
            if metadata
            else "Tidak tersedia"
        ),
        "Producer": (
            str(metadata.get("/Producer") or "Tidak tersedia")
            if metadata
            else "Tidak tersedia"
        ),
    }


def _extract_docx(uploaded_file):
    """Read paragraphs, tables, headers, footers, and author metadata from DOCX."""
    try:
        document = Document(BytesIO(uploaded_file.getvalue()))
    except (BadZipFile, PackageNotFoundError, KeyError) as error:
        raise ValueError("File Word tidak valid atau rusak. Unggah file .docx yang benar.") from error

    text_blocks = []
    for block in document.element.body.iterchildren():
        if isinstance(block, CT_P):
            paragraph = Paragraph(block, document)
            if paragraph.text.strip():
                text_blocks.append(paragraph.text)
        elif isinstance(block, CT_Tbl):
            table = Table(block, document)
            for row in table.rows:
                row_text = "\t".join(cell.text.strip() for cell in row.cells)
                if row_text.strip():
                    text_blocks.append(row_text)

    for section in document.sections:
        for paragraph in (*section.header.paragraphs, *section.footer.paragraphs):
            if paragraph.text.strip():
                text_blocks.append(paragraph.text)

    text = "\n".join(text_blocks)
    if len(text.strip()) < 50:
        raise ValueError(
            "Teks yang berhasil dibaca kurang dari 50 karakter. "
            "Pastikan dokumen Word berisi teks."
        )

    return text, None, {
        "Creator": document.core_properties.author or "Tidak tersedia",
        "Producer": "Tidak tersedia untuk DOCX",
    }


def extract_document(uploaded_file):
    """Extract text and metadata from a supported PDF or DOCX upload."""
    filename = getattr(uploaded_file, "name", "").lower()
    if filename.endswith(".pdf"):
        return _extract_pdf(uploaded_file)
    if filename.endswith(".docx"):
        return _extract_docx(uploaded_file)
    raise ValueError("Format file tidak didukung. Unggah PDF atau Word (.docx).")


def analyze_text(text):
    """Score four independent textual signals; no embedding/model is used here."""
    special_counts = {
        label: text.count(character)
        for label, character in SPECIAL_CHARACTERS.items()
    }
    special_total = sum(special_counts.values())
    special_score = min(25, special_total * 5)

    lowered_text = text.casefold()
    phrase_counts = {
        phrase: len(list(re.finditer(re.escape(phrase), lowered_text)))
        for phrase in TRANSITION_PHRASES
    }
    phrase_counts = {phrase: count for phrase, count in phrase_counts.items() if count}
    phrase_total = sum(phrase_counts.values())
    phrase_score = min(30, phrase_total * 5)

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text.strip())
        if sentence.strip()
    ]
    sentence_word_counts = [
        len(re.findall(r"\b[\w'-]+\b", sentence, flags=re.UNICODE))
        for sentence in sentences
    ]
    if len(sentence_word_counts) >= 2:
        sentence_stdev = statistics.stdev(sentence_word_counts)
        if sentence_stdev < 4.5:
            burstiness_score = 30
        elif sentence_stdev < 6.5:
            burstiness_score = 18
        else:
            burstiness_score = 5
    else:
        sentence_stdev = None
        burstiness_score = 0

    list_matches = LIST_PATTERN.findall(text)
    list_score = min(15, len(list_matches) * 5)
    total_score = min(
        100, special_score + phrase_score + burstiness_score + list_score
    )

    return {
        "special_counts": special_counts,
        "special_total": special_total,
        "special_score": special_score,
        "phrase_counts": phrase_counts,
        "phrase_score": phrase_score,
        "sentence_count": len(sentences),
        "sentence_stdev": sentence_stdev,
        "burstiness_score": burstiness_score,
        "list_matches": list_matches,
        "list_score": list_score,
        "word_count": len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)),
        "total_score": total_score,
    }
