"""
Generate CV PDF from Master CV Markdown
"""
from fpdf import FPDF
import re, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MD_FILE = os.path.join(ROOT, "3_Live_Reports", "Tebello_Lelosa_Master_CV_2026.md")
PDF_FILE = os.path.join(ROOT, "3_Live_Reports", "Tebello_Lelosa_CV_2026.pdf")

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)

with open(MD_FILE, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Strip HTML comments
clean = []
skip = False
for line in lines:
    if "<!--" in line and "-->" in line:
        continue
    if line.strip().startswith("<!--"):
        skip = True
    if "-->" in line:
        skip = False
        continue
    if not skip:
        clean.append(line.rstrip())

def clean_text(text):
    """Strip Markdown formatting and fix Unicode issues."""
    # Fix problematic characters for Helvetica
    text = text.replace('\u2014', '--')   # em dash
    text = text.replace('\u2013', '-')    # en dash
    text = text.replace('\u2018', "'")    # left single quote
    text = text.replace('\u2019', "'")    # right single quote
    text = text.replace('\u201c', '"')    # left double quote
    text = text.replace('\u201d', '"')    # right double quote
    text = text.replace('\u2022', '-')    # bullet
    text = text.replace('\u2026', '...')  # ellipsis
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    return text[:140]

pdf.add_page()

for line in clean:
    stripped = line.strip()
    if not stripped:
        pdf.ln(2)
        continue

    if stripped.startswith("# "):
        # Name
        pdf.set_font('Helvetica', 'B', 22)
        pdf.set_text_color(26, 26, 26)
        pdf.cell(0, 12, clean_text(stripped[2:]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(37, 99, 235)
        pdf.set_line_width(0.8)
        y = pdf.get_y()
        pdf.line(10, y, 200, y)
        pdf.ln(4)

    elif stripped.startswith("## "):
        # Section header
        pdf.ln(3)
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(37, 99, 235)
        pdf.cell(0, 8, clean_text(stripped[3:]), new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(220, 225, 235)
        pdf.set_line_width(0.4)
        y = pdf.get_y()
        pdf.line(10, y, 200, y)
        pdf.ln(1)

    elif stripped.startswith("### "):
        # Subsection - Role title
        pdf.ln(1)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(31, 41, 55)
        pdf.cell(0, 6, clean_text(stripped[4:]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0)

    elif stripped.startswith("- ") or stripped.startswith("* "):
        # Bullet point
        text = clean_text(stripped[2:])
        pdf.cell(6)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(4, 4, '-')
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 51, 51)
        pdf.multi_cell(0, 4.5, text, border=0)
        pdf.ln(0.5)

    elif "|" in stripped and "---" not in stripped:
        # Table row
        cells = [c.strip() for c in stripped.split("|") if c.strip()]
        if len(cells) >= 2:
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(51, 51, 51)
            text = clean_text(f"{cells[0]}  |  {cells[1]}")
            if len(cells) > 2:
                text = clean_text(f"{cells[0]}  |  {cells[1]}  |  {cells[2]}")
            pdf.multi_cell(0, 4.5, text, border=0)

    else:
        # Contact line / regular text
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(51, 51, 51)
        text = clean_text(stripped)
        if text.strip():
            pdf.cell(0, 5, text, new_x="LMARGIN", new_y="NEXT")

pdf.output(PDF_FILE)
size = os.path.getsize(PDF_FILE)
print(f"PDF created: {PDF_FILE}")
print(f"File size: {size:,} bytes ({size/1024:.1f} KB)")
