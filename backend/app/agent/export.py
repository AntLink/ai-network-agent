"""Document export for the AI Network Agent.

Generates downloadable files (CSV, JSON, TXT, Markdown, XLSX, PDF) from
structured device data using only the Python standard library. The document
model is a list of sections: (title, columns, rows).
"""
from __future__ import annotations

import io
import json
import zipfile
from typing import Any

Section = tuple[str, list[str], list[list[Any]]]

FORMATTERS = ("csv", "json", "txt", "md", "xlsx", "pdf")


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


# ---------------------------------------------------------------------------
# Text-based formats
# ---------------------------------------------------------------------------

def to_csv(title: str, sections: list[Section]) -> bytes:
    buf = io.StringIO()
    buf.write(f"# {title}\n\n")
    for section_title, columns, rows in sections:
        if section_title:
            buf.write(f"# {section_title}\n")
        if columns:
            buf.write(",".join(_quote_csv(c) for c in columns) + "\n")
        for row in rows:
            buf.write(",".join(_quote_csv(_cell(v)) for v in row) + "\n")
        buf.write("\n")
    return buf.getvalue().encode("utf-8-sig")


def _quote_csv(value: str) -> str:
    if any(ch in value for ch in (",", '"', "\n")):
        return '"' + value.replace('"', '""') + '"'
    return value


def to_json(title: str, sections: list[Section]) -> bytes:
    payload = {
        "title": title,
        "sections": [
            {
                "name": section_title,
                "columns": columns,
                "rows": [[_cell(v) for v in row] for row in rows],
            }
            for section_title, columns, rows in sections
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")


def to_txt(title: str, sections: list[Section]) -> bytes:
    lines = [title, "=" * len(title), ""]
    for section_title, columns, rows in sections:
        if section_title:
            lines.append(f"## {section_title}")
        if columns:
            lines.append("\t".join(columns))
        for row in rows:
            lines.append("\t".join(_cell(v) for v in row))
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def to_markdown(title: str, sections: list[Section]) -> bytes:
    lines = [f"# {title}", ""]
    for section_title, columns, rows in sections:
        if section_title:
            lines.append(f"## {section_title}")
            lines.append("")
        if columns:
            lines.append("| " + " | ".join(_md_escape(c) for c in columns) + " |")
            lines.append("| " + " | ".join("---" for _ in columns) + " |")
        for row in rows:
            lines.append("| " + " | ".join(_md_escape(_cell(v)) for v in row) + " |")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def _md_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------------------
# XLSX (minimal inline-string workbook via zipfile)
# ---------------------------------------------------------------------------

_XLSX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    '</Types>'
)

_XLSX_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    '</Relationships>'
)

_XLSX_WORKBOOK = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<sheets><sheet name="Report" sheetId="1" r:id="rId1"/></sheets>'
    '</workbook>'
)

_XLSX_WORKBOOK_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '</Relationships>'
)

_XLSX_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="3">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="12"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font>'
    '</fonts>'
    '<fills count="4">'
    '<fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FFF2F2F2"/><bgColor indexed="64"/></patternFill></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FF305496"/><bgColor indexed="64"/></patternFill></fill>'
    '</fills>'
    '<borders count="2">'
    '<border><left/><right/><top/><bottom/><diagonal/></border>'
    '<border><left style="thin"><color rgb="FFBFBFBF"/></left><right style="thin"><color rgb="FFBFBFBF"/></right><top style="thin"><color rgb="FFBFBFBF"/></top><bottom style="thin"><color rgb="FFBFBFBF"/></bottom><diagonal/></border>'
    '</borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="4">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1"/>'
    '<xf numFmtId="0" fontId="2" fillId="3" borderId="0" xfId="0" applyFont="1" applyFill="1"/>'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1"/>'
    '</cellXfs>'
    '</styleSheet>'
)


def _xlsx_escape(value: str) -> str:
    return (
        value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;").replace("'", "&apos;")
    )


def _col_letter(index: int) -> str:
    result = ""
    index += 1
    while index:
        index, rem = divmod(index - 1, 26)
        result = chr(65 + rem) + result
    return result


def to_xlsx(title: str, sections: list[Section]) -> bytes:
    # Build styled rows: (style_index, [cells]).
    # style: 2 = title/section (blue fill), 1 = header (bold + gray),
    #        3 = data (borders), 0 = plain (config lines).
    rows: list[tuple[int, list[str]]] = [(2, [title])]
    for section_title, columns, data_rows in sections:
        if section_title:
            rows.append((2, [section_title]))
        if columns:
            rows.append((1, list(columns)))
        for data_row in data_rows:
            rows.append((3 if columns else 0, [_cell(v) for v in data_row]))
        rows.append((0, [""]))

    max_cols = max((len(cells) for _, cells in rows), default=1)
    widths = [0] * max_cols
    for _, cells in rows:
        for col_index, cell in enumerate(cells):
            widths[col_index] = max(widths[col_index], min(len(cell), 60))

    cols_xml = "".join(
        f'<col min="{i + 1}" max="{i + 1}" width="{max(8, min(w, 60) + 2)}" customWidth="1"/>'
        for i, w in enumerate(widths)
    )

    sheet_rows: list[str] = []
    for row_index, (style, cells) in enumerate(rows, start=1):
        cell_xml = "".join(
            f'<c r="{_col_letter(ci)}{row_index}" s="{style}" t="inlineStr"><is><t>{_xlsx_escape(cell)}</t></is></c>'
            for ci, cell in enumerate(cells)
        )
        sheet_rows.append(f'<row r="{row_index}">{cell_xml}</row>')

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<cols>{cols_xml}</cols>'
        '<sheetData>'
        + "".join(sheet_rows)
        + "</sheetData></worksheet>"
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _XLSX_CONTENT_TYPES)
        zf.writestr("_rels/.rels", _XLSX_RELS)
        zf.writestr("xl/workbook.xml", _XLSX_WORKBOOK)
        zf.writestr("xl/_rels/workbook.xml.rels", _XLSX_WORKBOOK_RELS)
        zf.writestr("xl/styles.xml", _XLSX_STYLES)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# PDF (minimal text PDF using Helvetica)
# ---------------------------------------------------------------------------

_PDF_PAGE_H = 842.0
_PDF_PAGE_W = 595.0
_PDF_MARGIN = 48.0
_PDF_LEADING = 13.0
_PDF_LINES_PER_PAGE = int((_PDF_PAGE_H - 2 * _PDF_MARGIN) // _PDF_LEADING)


def _pdf_text(value: str) -> str:
    encoded = value.encode("cp1252", "replace").decode("cp1252")
    return encoded.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def _pdf_content_stream(lines: list[str]) -> bytes:
    commands = ["BT", "/F1 9 Tf"]
    y = _PDF_PAGE_H - _PDF_MARGIN
    for line in lines:
        commands.append(f"1 0 0 1 {_PDF_MARGIN} {y:.1f} Tm")
        commands.append(f"({_pdf_text(line)}) Tj")
        y -= _PDF_LEADING
    commands.append("ET")
    return "\n".join(commands).encode("cp1252")


def _pdf_text_lines(title: str, sections: list[Section]) -> list[str]:
    text_lines: list[str] = [title, ""]
    for section_title, columns, rows in sections:
        if section_title:
            text_lines.append(section_title)
        if columns:
            text_lines.append("  |  ".join(columns))
        for row in rows:
            text_lines.append("  |  ".join(_cell(v) for v in row))
        text_lines.append("")
    return text_lines


def to_pdf(title: str, sections: list[Section]) -> bytes:
    text_lines = _pdf_text_lines(title, sections)
    page_chunks = [
        text_lines[i : i + _PDF_LINES_PER_PAGE]
        for i in range(0, len(text_lines), _PDF_LINES_PER_PAGE)
    ]
    page_contents = [_pdf_content_stream(chunk) for chunk in page_chunks]

    # Build a flat list of (object_number, content).
    objects: list[tuple[int, bytes]] = []

    def add(content: bytes) -> int:
        number = len(objects) + 1
        objects.append((number, content))
        return number

    catalog_num = add(b"<< /Type /Catalog /Pages 2 0 R >>")
    pages_num = add(b"")  # placeholder, fixed below
    page_obj_nums: list[int] = []
    for _ in page_contents:
        page_obj_nums.append(len(objects) + 1)  # each page = Page obj + Content obj
    font_num = len(objects) + 2 * len(page_contents) + 1

    for content in page_contents:
        page_num = len(objects) + 1
        content_num = page_num + 1
        page_obj = (
            f"<< /Type /Page /Parent {pages_num} 0 R /MediaBox [0 0 {_PDF_PAGE_W:.0f} {_PDF_PAGE_H:.0f}] "
            f"/Resources << /Font << /F1 {font_num} 0 R >> >> /Contents {content_num} 0 R >>"
        ).encode("latin-1")
        add(page_obj)
        add(b"<< /Length " + str(len(content)).encode("latin-1") + b" >>\nstream\n" + content + b"\nendstream")

    kids = " ".join(f"{n} 0 R" for n in page_obj_nums)
    objects[pages_num - 1] = (pages_num, f"<< /Type /Pages /Kids [{kids}] /Count {len(page_contents)} >>".encode("latin-1"))

    add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")

    out: list[bytes] = [b"%PDF-1.4\n"]
    offsets: dict[int, int] = {}
    for number, content in objects:
        offsets[number] = len(b"".join(out))
        out.append(f"{number} 0 obj\n".encode("latin-1"))
        out.append(content)
        out.append(b"\nendobj\n")

    xref_pos = len(b"".join(out))
    count = len(objects) + 1
    out.append(f"xref\n0 {count}\n".encode("latin-1"))
    out.append(b"0000000000 65535 f \n")
    for number in range(1, count):
        out.append(f"{offsets.get(number, 0):010d} 00000 n \n".encode("latin-1"))
    out.append(
        f"trailer\n<< /Size {count} /Root {catalog_num} 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("latin-1")
    )
    return b"".join(out)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def render_document(title: str, sections: list[Section], fmt: str) -> bytes:
    fmt = (fmt or "csv").lower()
    if fmt == "csv":
        return to_csv(title, sections)
    if fmt == "json":
        return to_json(title, sections)
    if fmt == "txt":
        return to_txt(title, sections)
    if fmt in {"md", "markdown"}:
        return to_markdown(title, sections)
    if fmt == "xlsx":
        return to_xlsx(title, sections)
    if fmt == "pdf":
        return to_pdf(title, sections)
    return to_csv(title, sections)
