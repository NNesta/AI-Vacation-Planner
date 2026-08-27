import os
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "source_text")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "pdfs")

os.makedirs(OUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()
title_style = ParagraphStyle(
    "DocTitle", parent=styles["Title"], alignment=TA_LEFT, spaceAfter=18
)
heading_style = ParagraphStyle(
    "Heading", parent=styles["Heading2"], spaceBefore=14, spaceAfter=8
)
body_style = ParagraphStyle(
    "Body", parent=styles["BodyText"], leading=15, spaceAfter=10
)


def text_to_pdf(txt_path: str, pdf_path: str) -> None:
    with open(txt_path, "r", encoding="utf-8") as f:
        raw = f.read()

    blocks = [b.strip() for b in raw.split("\n\n") if b.strip()]

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=LETTER,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )

    story = []
    first = True
    for block in blocks:
        lines = block.split("\n")
        heading, rest = lines[0], "\n".join(lines[1:]).strip()

        # Treat the very first block's first line as the document title,
        # short lines without trailing punctuation as sub-headings.
        if first:
            story.append(Paragraph(heading, title_style))
            first = False
        elif len(heading) < 90 and not heading.endswith("."):
            story.append(Paragraph(heading, heading_style))
        else:
            story.append(Paragraph(heading, body_style))

        if rest:
            story.append(Paragraph(rest.replace("\n", " "), body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    for fname in sorted(os.listdir(SRC_DIR)):
        if not fname.endswith(".txt"):
            continue
        txt_path = os.path.join(SRC_DIR, fname)
        pdf_path = os.path.join(OUT_DIR, fname.replace(".txt", ".pdf"))
        text_to_pdf(txt_path, pdf_path)
