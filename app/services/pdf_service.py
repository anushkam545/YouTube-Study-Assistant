"""
PDF Generation Service
Converts markdown/text study notes to downloadable PDF using ReportLab
"""

import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_LEFT, TA_CENTER


# Directory to save generated PDFs
PDF_OUTPUT_DIR = "./generated_pdfs"
os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


def _build_styles():
    """Build custom paragraph styles for the PDF."""
    base = getSampleStyleSheet()

    styles = {
        "h1": ParagraphStyle(
            "H1",
            parent=base["Title"],
            fontSize=22,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=14,
            spaceBefore=6,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#16213e"),
            spaceAfter=8,
            spaceBefore=14,
            borderPad=2,
        ),
        "h3": ParagraphStyle(
            "H3",
            parent=base["Heading3"],
            fontSize=13,
            textColor=colors.HexColor("#0f3460"),
            spaceAfter=6,
            spaceBefore=10,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=11,
            leading=16,
            textColor=colors.HexColor("#333333"),
            spaceAfter=4,
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=11,
            leading=16,
            leftIndent=20,
            firstLineIndent=0,
            textColor=colors.HexColor("#333333"),
            spaceAfter=3,
            bulletIndent=8,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontSize=9,
            leading=13,
            leftIndent=20,
            textColor=colors.HexColor("#555555"),
            backColor=colors.HexColor("#f5f5f5"),
            spaceAfter=6,
            spaceBefore=4,
        ),
    }
    return styles


def _escape_xml(text: str) -> str:
    """Escape special XML chars for ReportLab Paragraph."""
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _apply_inline_markdown(text: str) -> str:
    """Convert **bold** and *italic* to ReportLab XML tags."""
    # Bold
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)
    # Italic
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    text = re.sub(r"_(.+?)_", r"<i>\1</i>", text)
    # Inline code
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


def markdown_to_story(markdown_text: str, styles: dict) -> list:
    """
    Parse markdown text and return a ReportLab story (list of flowables).

    Supports:
    - # H1, ## H2, ### H3 headings
    - Bullet points (- or *)
    - **bold**, *italic*, `code` inline
    - Horizontal rules (---)
    - Plain paragraphs
    """
    story = []
    lines = markdown_text.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip empty lines (add small space)
        if not line.strip():
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$|^\*{3,}$|^_{3,}$", line.strip()):
            story.append(Spacer(1, 4))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
            story.append(Spacer(1, 4))
            i += 1
            continue

        # H1
        if line.startswith("# "):
            text = _apply_inline_markdown(_escape_xml(line[2:].strip()))
            story.append(Paragraph(text, styles["h1"]))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
            story.append(Spacer(1, 6))
            i += 1
            continue

        # H2
        if line.startswith("## "):
            text = _apply_inline_markdown(_escape_xml(line[3:].strip()))
            story.append(Paragraph(text, styles["h2"]))
            i += 1
            continue

        # H3
        if line.startswith("### "):
            text = _apply_inline_markdown(_escape_xml(line[4:].strip()))
            story.append(Paragraph(text, styles["h3"]))
            i += 1
            continue

        # Bullet point (- or *)
        if re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", line)
            text = _apply_inline_markdown(_escape_xml(text))
            story.append(Paragraph(f"&#8226; {text}", styles["bullet"]))
            i += 1
            continue

        # Numbered list
        if re.match(r"^\d+\.\s+", line):
            match = re.match(r"^(\d+)\.\s+(.*)", line)
            num, text = match.group(1), match.group(2)
            text = _apply_inline_markdown(_escape_xml(text))
            story.append(Paragraph(f"{num}. {text}", styles["bullet"]))
            i += 1
            continue

        # Regular paragraph
        text = _apply_inline_markdown(_escape_xml(line))
        story.append(Paragraph(text, styles["body"]))
        i += 1

    return story


def generate_pdf(notes: str, video_id: str, video_title: str = "Study Notes") -> str:
    """
    Generate a PDF from markdown notes and save locally.

    Args:
        notes: Markdown-formatted study notes
        video_id: YouTube video ID (used for filename)
        video_title: Title shown in PDF header

    Returns:
        Absolute path to the saved PDF file
    """
    filename = f"notes_{video_id}.pdf"
    filepath = os.path.join(PDF_OUTPUT_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.75 * inch,
        title=video_title,
        author="YouTube Study Assistant",
    )

    styles = _build_styles()
    story = markdown_to_story(notes, styles)

    doc.build(story)

    return os.path.abspath(filepath)


def get_pdf_path(video_id: str) -> str | None:
    """
    Return path to existing PDF for a video, or None if not found.

    Args:
        video_id: YouTube video ID

    Returns:
        Absolute path or None
    """
    filename = f"notes_{video_id}.pdf"
    filepath = os.path.join(PDF_OUTPUT_DIR, filename)
    return os.path.abspath(filepath) if os.path.exists(filepath) else None
