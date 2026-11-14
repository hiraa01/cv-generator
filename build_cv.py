#!/usr/bin/env python3
"""
CV generator: builds a Word (.docx) CV from a JSON data file and optionally
converts it to PDF with LibreOffice (or Microsoft Word on Windows).

Usage:
    python build_cv.py cv_tr.json              # -> cv_tr.docx
    python build_cv.py cv_en.json --pdf        # -> cv_en.docx + cv_en.pdf
    python build_cv.py cv_tr.json cv_en.json --pdf --out output

Requirements: Python 3.9+, python-docx (pip install -r requirements.txt)
PDF: LibreOffice ("soffice") on PATH, or Microsoft Word on Windows (docx2pdf).
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt


def new_document():
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)  # A4
    sec.left_margin = sec.right_margin = Cm(2.0)
    sec.top_margin = sec.bottom_margin = Cm(1.8)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(2)
    normal.paragraph_format.line_spacing = 1.08
    lb = doc.styles["List Bullet"]
    lb.font.name = "Calibri"
    lb.font.size = Pt(10.5)
    lb.paragraph_format.space_after = Pt(2)
    return doc


def add_link(doc, paragraph, text, url, bold=False):
    """Append a clickable hyperlink run to a paragraph (works in Word and LibreOffice)."""
    rid = doc.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hl = OxmlElement("w:hyperlink")
    hl.set(qn("r:id"), rid)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    if bold:
        rpr.append(OxmlElement("w:b"))
    color = OxmlElement("w:color"); color.set(qn("w:val"), "0563C1"); rpr.append(color)
    underline = OxmlElement("w:u"); underline.set(qn("w:val"), "single"); rpr.append(underline)
    run.append(rpr)
    t = OxmlElement("w:t"); t.set(qn("xml:space"), "preserve"); t.text = text
    run.append(t)
    hl.append(run)
    paragraph._p.append(hl)


def bottom_border(paragraph):
    ppr = paragraph._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    b = OxmlElement("w:bottom")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), "6")
    b.set(qn("w:space"), "1"); b.set(qn("w:color"), "444444")
    pbdr.append(b)
    ppr.append(pbdr)


def heading(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text.upper())
    r.bold = True
    r.font.size = Pt(11.5)
    bottom_border(p)


def render_item(doc, item):
    kind = item["type"]
    if kind == "para":
        p = doc.add_paragraph(item["text"])
        p.paragraph_format.space_after = Pt(2)
    elif kind == "labeled":
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        p.add_run(item["label"] + ": ").bold = True
        p.add_run(item["text"])
    elif kind == "entry":
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.keep_with_next = True
        p.add_run(item["title"]).bold = True
        p.add_run(f" | {item['org']}")
        q = doc.add_paragraph()
        q.paragraph_format.space_after = Pt(2)
        q.paragraph_format.keep_with_next = True
        q.add_run(item["dates"]).italic = True
    elif kind == "bullet":
        p = doc.add_paragraph(style="List Bullet")
        if item.get("url"):
            add_link(doc, p, item["text"], item["url"])
        else:
            p.add_run(item["text"])
    else:
        raise ValueError(f"Unknown item type: {kind}")


def build_docx(data, out_path):
    doc = new_document()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.space_after = Pt(2)
    r = p.add_run(data["name"]); r.bold = True; r.font.size = Pt(18)

    para = doc.add_paragraph(data["title"])
    para.paragraph_format.space_after = Pt(2)

    contact = doc.add_paragraph()
    contact.paragraph_format.space_after = Pt(0)
    for seg in data["contact"]:
        if seg.get("url"):
            add_link(doc, contact, seg["text"], seg["url"])
        else:
            contact.add_run(seg["text"])

    for section in data["sections"]:
        heading(doc, section["heading"])
        for item in section["items"]:
            render_item(doc, item)

    doc.core_properties.title = f"{data['name']} - CV"
    doc.core_properties.author = data["name"].title()
    doc.save(out_path)


def to_pdf(docx_path):
    """Convert with LibreOffice if available, else Microsoft Word (Windows)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                        "--outdir", str(docx_path.parent), str(docx_path)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return docx_path.with_suffix(".pdf")
    try:
        from docx2pdf import convert  # uses Microsoft Word on Windows/macOS
        pdf_path = docx_path.with_suffix(".pdf")
        convert(str(docx_path), str(pdf_path))
        return pdf_path
    except ImportError:
        sys.exit("PDF için LibreOffice kurulu olmalı (soffice) ya da 'pip install docx2pdf' ile Word kullanılmalı.")


def main():
    ap = argparse.ArgumentParser(description="Generate CV .docx (and .pdf) from JSON data.")
    ap.add_argument("data", nargs="+", help="JSON data file(s), e.g. cv_tr.json cv_en.json")
    ap.add_argument("--pdf", action="store_true", help="also export PDF")
    ap.add_argument("--out", default=".", help="output folder (default: current folder)")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name in args.data:
        data = json.loads(Path(name).read_text(encoding="utf-8"))
        lang = Path(name).stem.split("_")[-1].upper()
        base = "_".join(data["name"].split())
        docx_path = out_dir / f"{base}_CV_{lang}.docx"
        build_docx(data, docx_path)
        print("DOCX:", docx_path)
        if args.pdf:
            print("PDF :", to_pdf(docx_path))


if __name__ == "__main__":
    main()
