"""Functional tests for the keyless multimodal defaults ("local, free").

The routing tests in test_sources.py check which parser is *selected*; these
check that the selected local parsers actually extract text from real files:
PDF through Docling (and the pypdf fallback), DOCX through Unstructured, and
a rendered "scan" through PaddleOCR. Each test is skipped, not failed, when
its optional stack is not installed — mirroring the runtime defaults, which
degrade the same way.

First runs download parser models (Docling layout models, PaddleOCR det/rec
weights) — these tests are ``slow`` and want network on a cold cache.
"""

from __future__ import annotations

import importlib.util

import pytest

pytestmark = pytest.mark.slow


def _has(module: str) -> bool:
    return importlib.util.find_spec(module) is not None


@pytest.fixture()
def registry():
    from serviette.indexer.graph import ParserRegistry

    return ParserRegistry()


@pytest.fixture()
def pdf_bytes() -> bytes:
    fpdf = pytest.importorskip("fpdf")
    doc = fpdf.FPDF()
    doc.add_page()
    doc.set_font("Helvetica", size=14)
    doc.cell(text="The serviette benchmark corpus fits twenty-six million pages.")
    return bytes(doc.output())


def test_pdf_parses_locally(registry, pdf_bytes):
    """PDF text extraction with the best available keyless parser."""
    kind, _ = registry._route(".pdf", "report.pdf")
    assert kind == ("docling" if _has("docling") else "pypdf")
    text = registry.parse(pdf_bytes, ".pdf", "report.pdf")
    assert "twenty-six million pages" in text


@pytest.mark.skipif(not _has("docling"), reason="docling not installed")
def test_pdf_pypdf_fallback_also_works(registry, pdf_bytes):
    """The fallback path must extract the same content (weaker layout)."""
    parser = registry._get("pypdf", {})
    result = parser.__wrapped__(pdf_bytes)
    import inspect as _inspect

    if _inspect.isawaitable(result):
        import asyncio

        result = asyncio.run(result)
    assert any("twenty-six million pages" in text for text, _ in result)


def test_docx_parses_via_unstructured(registry):
    docx = pytest.importorskip("docx")
    import io

    buffer = io.BytesIO()
    document = docx.Document()
    document.add_paragraph("Deletion semantics propagate to the vector store.")
    document.save(buffer)

    text = registry.parse(buffer.getvalue(), ".docx", "notes.docx")
    assert "Deletion semantics" in text


@pytest.mark.skipif(not _has("paddleocr"), reason="paddleocr not installed")
def test_scanned_image_ocr(registry):
    """A rendered 'scan' (text drawn onto a PNG) is read back by PaddleOCR."""
    import io

    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (900, 220), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf", 48
        )
    except OSError:
        font = ImageFont.load_default()
    draw.text((40, 80), "SERVIETTE INDEXES SCANS", fill="black", font=font)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")

    kind, _ = registry._route(".png", "scan.png")
    assert kind == "paddle_ocr"
    text = registry.parse(buffer.getvalue(), ".png", "scan.png")
    assert "SERVIETTE" in text.upper()
    assert "SCANS" in text.upper()
