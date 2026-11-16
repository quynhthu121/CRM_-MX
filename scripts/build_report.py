"""
Chuyển báo cáo Markdown (docs/Bao_cao_A4.2.1_Nhom_DienMayXanh.md) sang Word (.docx) bằng python-docx,
chèn trực tiếp ảnh minh chứng trong docs/screenshots/.

    pip install python-docx pillow
    python scripts/build_report.py
"""
import os
import re
import sys
import tempfile

from docx import Document
from docx.enum.section import WD_ORIENT  # noqa: F401
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "Bao_cao_A4.2.1_Nhom_DienMayXanh.md")
OUT = os.path.join(ROOT, "docs", "Bao_cao_A4.2.1_Nhom_DienMayXanh.docx")
BLUE = RGBColor(0x00, 0x66, 0xB3)
FONT = "Times New Roman"
CONTENT_W_CM = 17.0
MAX_IMG_H_CM = 23.0
SEP = (154, 160, 166)  # màu dải phân cách giữa các phần ảnh ghép (take_screenshots.py)


def set_font(run, size=None, bold=None, color=None, italic=None):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_inline(par, text, size=13):
    """Hỗ trợ **đậm**, *nghiêng* và `code`."""
    for part in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)", text):
        if not part:
            continue
        if part.startswith("**"):
            r = par.add_run(part[2:-2])
            set_font(r, size, bold=True)
        elif part.startswith("*") and len(part) > 2:
            r = par.add_run(part[1:-1])
            set_font(r, size, italic=True)
        elif part.startswith("`"):
            r = par.add_run(part[1:-1])
            set_font(r, size - 1)
            r.font.name = "Consolas"
            r._element.rPr.rFonts.set(qn("w:eastAsia"), "Consolas")
            r.font.color.rgb = RGBColor(0x0B, 0x3D, 0x6B)
        else:
            r = par.add_run(part)
            set_font(r, size)


def shade(cell, hex_fill):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcPr.append(shd)


def add_table(doc, rows):
    header, body = rows[0], rows[1:]
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        add_inline(p, h, 11)
        for r in p.runs:
            r.bold = True
            r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        shade(c, "0066B3")
    for k, row in enumerate(body):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            add_inline(cells[i].paragraphs[0], v, 11)
            if k % 2:
                shade(cells[i], "EEF5FB")
    # độ rộng cột theo độ dài nội dung
    lens = [max(len(r[i]) if i < len(r) else 0 for r in rows) for i in range(len(header))]
    weights = [min(max(n, 6), 38) for n in lens]
    total = sum(weights)
    t.autofit = False
    for i, col in enumerate(t.columns):
        col.width = Cm(CONTENT_W_CM * weights[i] / total)
    for row in t.rows:
        for i, c in enumerate(row.cells):
            c.width = Cm(CONTENT_W_CM * weights[i] / total)
    # lặp lại hàng tiêu đề khi sang trang
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    doc.add_paragraph()


def split_image(path):
    """Tách ảnh ghép thành các phần theo dải phân cách màu xám."""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    px = im.load()
    sep_rows = [y for y in range(h) if all(px[x, y] == SEP for x in (5, w // 3, w // 2, w - 5))]
    parts, start, y_prev = [], 0, None
    for y in sep_rows + [h]:
        if y_prev is not None and y == y_prev + 1:
            y_prev = y
            continue
        if y > start + 20:
            parts.append(im.crop((0, start, w, y)))
        start = y
        y_prev = y
    # bỏ khoảng trống sau dải phân cách
    cleaned = []
    for p in parts:
        top = 0
        while top < p.height and all(p.getpixel((x, top)) == SEP for x in (5, w // 2)):
            top += 1
        cleaned.append(p.crop((0, top, w, p.height)))
    return cleaned or [im]


def add_image(doc, path, caption, tmpdir):
    for i, part in enumerate(split_image(path)):
        f = os.path.join(tmpdir, f"{os.path.basename(path)}_{i}.png")
        part.save(f)
        w_cm = CONTENT_W_CM
        h_cm = w_cm * part.height / part.width
        if h_cm > MAX_IMG_H_CM:
            w_cm = CONTENT_W_CM * MAX_IMG_H_CM / h_cm
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next = True
        p.add_run().add_picture(f, width=Cm(w_cm))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = cap.add_run(caption)
    set_font(r, 11, italic=True, color=RGBColor(0x37, 0x41, 0x51))


def setup_styles(doc):
    st = doc.styles["Normal"]
    st.font.name = FONT
    st.font.size = Pt(13)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    st.paragraph_format.space_after = Pt(6)
    st.paragraph_format.line_spacing = 1.2
    for name, size in (("Title", 20), ("Heading 1", 16), ("Heading 2", 14)):
        s = doc.styles[name]
        s.font.name = FONT
        s.font.size = Pt(size)
        s.font.bold = True
        s.font.color.rgb = BLUE
        rf = s.element.rPr.rFonts
        for att in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rf.get(qn(att)) is not None:
                del rf.attrib[qn(att)]
        for att in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            rf.set(qn(att), FONT)
        s.paragraph_format.space_before = Pt(14)
        s.paragraph_format.space_after = Pt(8)
        s.paragraph_format.keep_with_next = True
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(2)
    sec.top_margin = sec.bottom_margin = Cm(2)
    # số trang ở chân trang
    fp = sec.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = fp.add_run("Đồ án CRM – Điện Máy Xanh · Trang ")
    set_font(run, 10)
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        r = fp.add_run()
        set_font(r, 10)
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        r._element.append(el)


def build(src=SRC, out=OUT):
    doc = Document()
    setup_styles(doc)
    base = os.path.dirname(src)
    lines = open(src, encoding="utf-8").read().splitlines()
    tmpdir = tempfile.mkdtemp()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line:
            i += 1
            continue
        if line.startswith("# "):
            p = doc.add_paragraph(style="Title")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r = p.add_run(line[2:])
            set_font(r, 20, bold=True, color=BLUE)
        elif line.startswith("## "):
            doc.add_heading(line[3:], level=1)
        elif line.startswith("### "):
            doc.add_heading(line[4:], level=2)
        elif line.startswith("!["):
            m = re.match(r"!\[(.*?)\]\((.*?)\)", line)
            add_image(doc, os.path.join(base, m.group(2)), m.group(1), tmpdir)
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            add_table(doc, rows)
            continue
        elif line.startswith("- "):
            p = doc.add_paragraph(style="List Bullet")
            add_inline(p, line[2:])
        else:
            p = doc.add_paragraph()
            p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_inline(p, line)
        i += 1
    doc.core_properties.title = "Báo cáo A4.2.1 – Nhóm Điện Máy Xanh"
    doc.core_properties.author = "Nhóm Điện Máy Xanh – UIT"
    doc.save(out)
    print("Đã tạo", out)


if __name__ == "__main__":
    build(*sys.argv[1:])
