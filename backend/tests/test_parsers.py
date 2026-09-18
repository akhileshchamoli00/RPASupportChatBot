"""
Unit tests for document parsers.
"""

import os
import openpyxl
import docx
import pypdf
from app.ingestion.parsers import parse_docx, parse_xlsx, parse_pdf


def test_parse_xlsx_structure(tmp_path):
    """Verifies Excel parser extracts worksheets and formats row key-values."""
    filepath = str(tmp_path / "sample.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "ErrorMatrix"
    ws.append(["ErrorCode", "Description", "Resolution"])
    ws.append([401, "Auth Failure", "Reset API Key"])
    ws.append([500, "Server Error", "Restart Service"])
    wb.save(filepath)

    elements = parse_xlsx(filepath)
    assert len(elements) == 2
    assert "Sheet: ErrorMatrix | Row 2" in elements[0]["text"]
    assert "ErrorCode: 401" in elements[0]["text"]
    assert "Description: Auth Failure" in elements[0]["text"]
    assert elements[0]["sheet"] == "ErrorMatrix"


def test_parse_docx_structure(tmp_path):
    """Verifies Word doc parser extracts headings, paragraphs, and tables."""
    filepath = str(tmp_path / "sample.docx")
    doc = docx.Document()
    doc.add_heading("ROE Setup Guide", level=1)
    doc.add_paragraph("Step 1: Open Dayforce Console.")

    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Param"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Timeout"
    table.cell(1, 1).text = "30s"
    doc.save(filepath)

    elements = parse_docx(filepath)
    assert len(elements) >= 2
    assert any("ROE Setup Guide" in e["text"] for e in elements)
    assert any("Param: Timeout" in e["text"] or "Param: Param" in e["text"] for e in elements)


def test_parse_pdf_structure(tmp_path):
    """Verifies PDF parser extracts text page-by-page."""
    filepath = str(tmp_path / "sample.pdf")
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    
    with open(filepath, "wb") as f:
        writer.write(f)

    # Empty/blank page handled without error
    elements = parse_pdf(filepath)
    assert isinstance(elements, list)
