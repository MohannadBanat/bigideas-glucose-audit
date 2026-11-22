"""
Render manuscript.md as a Word file laid out like an MDPI Sensors article,
then (optionally) as PDF through LibreOffice.

Usage:
    python manuscript/build_mdpi.py OUT.docx [--pdf] [--csl mdpi.csl]

Needs pandoc (with --citeproc), python-docx, and LibreOffice for --pdf. The
body font is Palatino Linotype, as in the MDPI Word template; for the PDF,
map it to TeX Gyre Pagella (the font of MDPI's LaTeX output) with fontconfig.

Layout taken from a published Sensors article (Abu Owida et al. 2026, 26,
7340): A4; 1.27 cm side margins; body text indented 4.5 cm with figures and
tables at full width; 10 pt Palatino, justified, first-line indent; bold
level-1 and italic level-2 headings; 9 pt captions with bold labels;
three-line tables; running header "Sensors 2026, 26, x" with "n of N";
first page with the journal and publisher logos, title block with ORCID
icons, a left sidebar (editor, dates, licence) beside Highlights, Abstract
and Keywords, and a footer with the citation line and DOI; back matter in
the MDPI order (Author Contributions ... Conflicts of Interest,
Abbreviations, Appendices, References, Disclaimer); references at full
width.

The logos (manuscript/assets/sensors_logo.png, mdpi_logo.png) are MDPI's
and are not in the repository; without them the first-page header falls
back to text. E-mail addresses are never in the repository: pass
--emails FILE (a private JSON file with keys banat, abuowida, alsarhan,
alfraihat, algarni) to build the submission copy with them.

Highlights are read from a "## Highlights" section of manuscript.md (two "###"
questions, each followed by bullet points). Any [RESULT] placeholder still in
the text is kept and highlighted.
"""
import argparse
import json
import copy
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FONT = "Palatino Linotype"
INDENT = Cm(4.5)            # body indent from the left margin
SIDE = Cm(1.27)             # left and right page margins
TEXT_W = Cm(21.0) - 2 * SIDE
BLUE = RGBColor(0x0B, 0x57, 0xA4)
TEAL = RGBColor(0x1C, 0x7C, 0x86)
DATE = "22 Nov 2026"
PENDING = "PENDING REGISTERED ANALYSIS"
TAB = "QQTABQQ"              # pandoc turns tabs into spaces; restored as w:tab
ASSETS = HERE / "assets"
ORCID = {"banat": "0009-0007-1413-4746", "abuowida": "0000-0001-6943-6134", "alsarhan": "0000-0001-9075-2828",
         "alfraihat": "0000-0002-0993-8287", "algarni": "0000-0002-7556-958X"}
DISCLAIMER = ("**Disclaimer/Publisher's Note:** The statements, opinions and data contained in all publications are "
              "solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI "
              "and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any "
              "ideas, methods, instructions or products referred to in the content.")


# ----------------------------------------------------------------- markdown
def prepare_markdown(md, osf_url):
    meta = re.match(r"---\n(.*?)\n---\n", md, re.S)
    title = re.search(r'^title:\s*"(.*)"', meta.group(1), re.M).group(1)
    body = md[meta.end():]
    body = re.sub(r"<!--.*?-->", "", body, flags=re.S)

    hl = re.search(r"## Highlights\n(.*?)\n(?=## )", body, re.S)
    highlights = []
    if hl:
        for block in re.split(r"^### ", hl.group(1), flags=re.M)[1:]:
            q, *rest = block.strip().split("\n")
            highlights.append((q.strip(), [b[2:].strip() for b in rest if b.startswith("- ")]))
    abstract = re.search(r"## Abstract\n(.*?)\n\*\*Keywords:\*\*(.*?)\n\n", body, re.S)
    abstract_text = " ".join(abstract.group(1).split())
    keywords = " ".join(abstract.group(2).split())
    body = body[body.index("## 1. Introduction"):]

    note = lambda what: (f'\n\n::: {{custom-style="MDPI Placeholder"}}\n**Placeholder:** {what} waits on the '
                         f"registered analysis. The registration ({osf_url}) was filed on {DATE} and awaits OSF "
                         "approval; no model has been run on real glucose.\n:::\n\n")
    for h in ["## 3. Results\n", "## 4. Discussion\n", "## 5. Conclusions\n"]:
        sec = body.split(h, 1)[1].split("\n## ", 1)[0] if h in body else ""
        if "[RESULT" in sec:
            body = body.replace(h, h + note("this section"), 1)
    body = body.replace("[OSF DOI: RESULT]", f"[{osf_url}]")
    body = re.sub(r"\[RESULT\]", f"[**{PENDING}**]", body)
    body = re.sub(r"\[RESULT:", f"[**{PENDING}:**", body)
    abstract_text = re.sub(r"\[RESULT:", f"[**{PENDING}:**", abstract_text)
    abstract_text = abstract_text.replace("[RESULT]", f"[**{PENDING}**]")

    # Figures: absolute paths, bold label, full width
    body = re.sub(r"!\[Figure (\d+)\. ", r"![**Figure \1.** ", body)
    body = re.sub(r"\]\(\.\./results/([^)]+)\)", lambda m: f"]({ROOT / 'results' / m.group(1)}){{width=100%}}", body)
    # Table captions written as "**Table N.** ..." paragraphs
    body = re.sub(r"^(\*\*Table [A-Z]?\d+\.\*\*[^\n]*(?:\n[^\n|][^\n]*)*)", r'::: {custom-style="MDPI Table Caption"}\n\1\n:::', body, flags=re.M)
    # let bare URLs break after "/" so justified lines do not stretch
    body = re.sub(r"(?<![(<\]])(https?://)(\S+)", lambda m: m.group(1) + m.group(2).replace("/", "/\u200b"), body)
    # Abbreviation/notes line right after a table ("CV, cross-validation; ...")
    body = re.sub(r"\n\n((?:CV, cross-validation;|Notes?:|Abbreviations:)[^\n]*)\n",
                  r'\n\n::: {custom-style="MDPI Table Note"}\n\1\n:::\n', body)

    # Back matter: no heading, 9 pt run-in paragraphs
    bm_start = body.index("## 6. Back Matter")
    bm_end = body.index("## Abbreviations") if "## Abbreviations" in body else body.index("## Appendix A")
    back = body[bm_start:bm_end].replace("## 6. Back Matter\n", "")
    back = "\n".join(f'::: {{custom-style="MDPI Back"}}\n{p.strip()}\n:::\n' for p in back.split("\n\n") if p.strip())
    body = body[:bm_start] + back + "\n" + body[bm_end:]

    body = body.replace("\t", TAB)
    body += ("\n\n## References\n\n::: {#refs}\n:::\n\n"
             f'::: {{custom-style="MDPI Disclaimer"}}\n{DISCLAIMER}\n:::\n')
    return title, abstract_text, keywords, body, highlights


def front_markdown(title, abstract_text, keywords, osf_url, highlights=None, emails=None):
    icon = ASSETS / "orcid.png"
    oid = lambda k: f"[![]({icon}){{height=9pt}}](https://orcid.org/{ORCID[k]})" if icon.exists() else ""
    authors = (f"Mohannad Banat ^1,\\*^{oid('banat')}, Hamza Abu Owida ^1^{oid('abuowida')}, "
               f"Ayoub Alsarhan ^2^{oid('alsarhan')}, Dimah Al-Fraihat ^3^{oid('alfraihat')} "
               f"and Abdulmohsen Algarni ^4,\\*^{oid('algarni')}")
    e = (lambda k: f"; {emails[k]}") if emails else (lambda k: "")
    corr = (f"{emails['banat']} (M.B.); {emails['algarni']} (A.A.)" if emails else
            "Mohannad Banat (M.B.) and Abdulmohsen Algarni (A.A.); e-mail addresses are given in the submission copy")
    affils = [
        f"^1^{TAB}Department of Medical Engineering, Faculty of Engineering, Al-Ahliyya Amman University, Amman 19328, Jordan{e('abuowida')}",
        f"^2^{TAB}Department of Information Technology, Faculty of Prince Al-Hussien bin Abdullah, The Hashemite University, Zarqa 13133, Jordan{e('alsarhan')}",
        f"^3^{TAB}Department of Software Engineering, Faculty of Information Technology, Isra University, Amman 11622, Jordan{e('alfraihat')}",
        f"^4^{TAB}Department of Computer Science, King Khalid University, Abha 61421, Saudi Arabia",
        f"\\*{TAB}Correspondence: {corr}",
    ]
    side = [
        "Academic Editor: [assigned by MDPI]",
        "Received: [date]\\\nRevised: [date]\\\nAccepted: [date]\\\nPublished: [date]",
        "**Copyright:** © 2026 by the authors. Submitted for possible open access publication under the terms "
        "and conditions of the Creative Commons Attribution (CC BY) license (https://creativecommons.org/licenses/by/4.0/).",
    ]
    zw = lambda t: t.replace("/", "/\u200b")   # let long URLs wrap in the narrow sidebar
    side = [zw(x) for x in side]
    div = lambda style, text: f'::: {{custom-style="{style}"}}\n{text}\n:::\n'
    out = [div("MDPI Article Type", "*Article*"), div("MDPI Title", title), div("MDPI Authors", authors)]
    out += [div("MDPI Affiliation", a) for a in affils]
    out += [div("MDPI Sidebar", s) for s in side]
    out += [div("MDPI Abstract Head", "Highlights"),
            *[d for q, bullets in (highlights or [("What are the main findings?", [f"[**{PENDING}**]"] * 2),
                                               ("What are the implications of the main findings?", [f"[**{PENDING}**]"] * 2)])
              for d in [div("MDPI Highlights Q", q)] + [div("MDPI Bullet", f"•{TAB}{b}") for b in bullets]],
            div("MDPI Abstract Head", "Abstract"),
            div("MDPI Abstract", abstract_text),
            div("MDPI Keywords", f"**Keywords:** {keywords}"),
            div("MDPI Rule", "\u00a0")]
    return "\n".join(out)


# ----------------------------------------------------------------- styles
def set_font(style_or_run, size=None, bold=None, italic=None, color=None):
    f = style_or_run.font
    f.name = FONT
    rpr = style_or_run.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts"); rpr.append(rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(a), FONT)
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        if rfonts.get(qn(a)) is not None:
            del rfonts.attrib[qn(a)]
    if size: f.size = Pt(size)
    if bold is not None: f.bold = bold
    if italic is not None: f.italic = italic
    f.color.rgb = color if color is not None else RGBColor(0, 0, 0)


def para_fmt(style, left=INDENT, first=None, hanging=None, before=0, after=0, line=None,
             align=WD_ALIGN_PARAGRAPH.JUSTIFY, keep=False):
    pf = style.paragraph_format
    pf.left_indent = left
    pf.right_indent = Cm(0)
    pf.first_line_indent = -hanging if hanging is not None else first
    pf.space_before = Pt(before); pf.space_after = Pt(after)
    if line:
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY; pf.line_spacing = Pt(line)
    else:
        pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.alignment = align
    pf.keep_with_next = keep
    pf.widow_control = True


def get_style(doc, name, base="Normal"):
    try:
        return doc.styles[name]
    except KeyError:
        s = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
        s.base_style = doc.styles[base]
        return s


def build_reference(path):
    ref = subprocess.run(["pandoc", "-o", str(path), "--print-default-data-file", "reference.docx"], check=True)
    doc = Document(str(path))
    st = doc.styles
    # body
    for name in ["Normal", "Body Text", "First Paragraph"]:
        s = get_style(doc, name); set_font(s, 10)
        lang = OxmlElement("w:lang"); lang.set(qn("w:val"), "en-US"); s.element.get_or_add_rPr().append(lang)
        para_fmt(s, first=Cm(0.75), line=13.6)
    para_fmt(st["Normal"], left=Cm(0), first=None, line=None)
    s = get_style(doc, "Compact"); set_font(s, 10); para_fmt(s, first=Cm(0), line=13.6)
    for name, size, b, i, before, after in [("Heading 1", 12, True, False, 12, 6), ("Heading 2", 10, False, True, 8, 3),
                                            ("Heading 3", 10, False, False, 6, 3)]:
        s = get_style(doc, name); set_font(s, size, bold=b, italic=i)
        para_fmt(s, first=Cm(0), before=before, after=after, align=WD_ALIGN_PARAGRAPH.LEFT, keep=True)
    for name in ["Image Caption", "Table Caption", "MDPI Table Caption"]:
        s = get_style(doc, name); set_font(s, 9, italic=False)
        para_fmt(s, first=Cm(0), before=6, after=6, line=11.5, keep=name != "Image Caption")
    s = get_style(doc, "MDPI Table Note"); set_font(s, 8); para_fmt(s, first=Cm(0), before=2, after=8, line=10.5)
    for name in ["Captioned Figure", "Figure"]:
        s = get_style(doc, name); para_fmt(s, left=Cm(0), first=Cm(0), before=6, align=WD_ALIGN_PARAGRAPH.CENTER, keep=True)
    s = get_style(doc, "Bibliography"); set_font(s, 8.5); para_fmt(s, left=Cm(0.75), hanging=Cm(0.75), after=1, line=10.5)
    s = get_style(doc, "MDPI Disclaimer"); set_font(s, 8.5); para_fmt(s, left=Cm(0), first=Cm(0), before=24, line=10.5)
    s = get_style(doc, "MDPI Abbrev"); set_font(s, 9); para_fmt(s, first=Cm(0), before=6, after=6, line=11.5, align=WD_ALIGN_PARAGRAPH.LEFT)
    s.paragraph_format.tab_stops.add_tab_stop(INDENT + Cm(1.8))
    s.paragraph_format.keep_together = True
    s = get_style(doc, "MDPI Back"); set_font(s, 9); para_fmt(s, first=Cm(0), after=3, line=11.5)
    s = get_style(doc, "MDPI Placeholder"); set_font(s, 9); para_fmt(s, first=Cm(0), before=4, after=6, line=11.5)
    # front matter
    s = get_style(doc, "MDPI Article Type"); set_font(s, 10, italic=True); para_fmt(s, left=Cm(0), first=Cm(0), before=10, after=2, align=WD_ALIGN_PARAGRAPH.LEFT)
    s = get_style(doc, "MDPI Title"); set_font(s, 17, bold=True); para_fmt(s, left=Cm(0), first=Cm(0), after=10, line=21, align=WD_ALIGN_PARAGRAPH.LEFT)
    s = get_style(doc, "MDPI Authors"); set_font(s, 10, bold=True); para_fmt(s, left=Cm(0), first=Cm(0), after=12, line=13, align=WD_ALIGN_PARAGRAPH.LEFT)
    s = get_style(doc, "MDPI Affiliation"); set_font(s, 8.5); para_fmt(s, left=INDENT + Cm(0.5), hanging=Cm(0.5), line=10.5, align=WD_ALIGN_PARAGRAPH.LEFT)
    s.paragraph_format.tab_stops.add_tab_stop(INDENT + Cm(0.5))
    s = get_style(doc, "MDPI Sidebar"); set_font(s, 7.5); para_fmt(s, left=Cm(0), first=Cm(0), after=6, line=9.5, align=WD_ALIGN_PARAGRAPH.LEFT)
    s = get_style(doc, "MDPI Abstract Head"); set_font(s, 10, bold=True); para_fmt(s, left=Cm(0), first=Cm(0), before=10, after=8, align=WD_ALIGN_PARAGRAPH.LEFT, keep=True)
    s = get_style(doc, "MDPI Highlights Q"); set_font(s, 10, bold=True); para_fmt(s, left=Cm(0), first=Cm(0), before=4, after=2, align=WD_ALIGN_PARAGRAPH.LEFT, keep=True)
    s = get_style(doc, "MDPI Bullet"); set_font(s, 10); para_fmt(s, left=Cm(0.75), hanging=Cm(0.75), line=13.6)
    s.paragraph_format.tab_stops.add_tab_stop(Cm(0.75))
    s = get_style(doc, "MDPI Abstract"); set_font(s, 10); para_fmt(s, left=Cm(0), first=Cm(0), line=13.6)
    s = get_style(doc, "MDPI Keywords"); set_font(s, 10); para_fmt(s, left=Cm(0), first=Cm(0), before=10, line=13.6)
    s = get_style(doc, "MDPI Rule"); set_font(s, 4); para_fmt(s, first=Cm(0), after=10, line=6)
    border(s.element.get_or_add_pPr(), "bottom", 6)
    for name in ["MDPI Title", "MDPI Authors", "MDPI Affiliation", "MDPI Sidebar", "MDPI Abbrev", "Heading 1", "Heading 2",
                 "Heading 3", "MDPI Highlights Q", "MDPI Abstract Head"]:
        st[name].element.get_or_add_pPr().append(OxmlElement("w:suppressAutoHyphens"))
    # links in blue (citations, URLs)
    try:
        h = st["Hyperlink"]; h.font.color.rgb = BLUE; h.font.underline = False
    except KeyError:
        pass
    doc.save(str(path))


def border(ppr, side, size, space=1):
    pbdr = ppr.find(qn("w:pBdr"))
    if pbdr is None:
        pbdr = OxmlElement("w:pBdr"); ppr.append(pbdr)
    b = OxmlElement(f"w:{side}")
    b.set(qn("w:val"), "single"); b.set(qn("w:sz"), str(size)); b.set(qn("w:space"), str(space)); b.set(qn("w:color"), "000000")
    pbdr.append(b)


# ----------------------------------------------------------------- post-processing
def field(p, instr, size=8):
    """PAGE/NUMPAGES field split over runs that all carry the size, so the number is not rendered larger."""
    for kind, text in [("begin", None), (None, instr), ("separate", None), ("1", None), ("end", None)]:
        r = styled_run(p, "", size)
        if kind == "1":
            t = OxmlElement("w:t"); t.text = "1"; r._r.append(t)
        elif kind:
            el = OxmlElement("w:fldChar"); el.set(qn("w:fldCharType"), kind); r._r.append(el)
        else:
            el = OxmlElement("w:instrText"); el.set(qn("xml:space"), "preserve"); el.text = f" {instr} "; r._r.append(el)


def styled_run(p, text, size=8, bold=False, italic=False, color=None):
    r = p.add_run(text); set_font(r, size, bold=bold, italic=italic, color=color)
    return r


def header_footer(doc):
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
    sec.left_margin = sec.right_margin = SIDE
    sec.top_margin, sec.bottom_margin = Cm(2.2), Cm(2.0)
    sec.header_distance, sec.footer_distance = Cm(1.0), Cm(1.0)
    sec.different_first_page_header_footer = True

    def clear(part):
        for p in part.paragraphs[1:]:
            p._p.getparent().remove(p._p)
        p = part.paragraphs[0]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        p.paragraph_format.left_indent = Cm(0); p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.tab_stops.add_tab_stop(TEXT_W, WD_TAB_ALIGNMENT.RIGHT)
        return p

    def cite_line(p, size=8):
        styled_run(p, "Sensors", size, italic=True); styled_run(p, " 2026", size, bold=True)
        styled_run(p, ", ", size); styled_run(p, "26", size, italic=True); styled_run(p, ", x", size)

    # first page: journal and publisher logos, thin rule
    p = clear(sec.first_page_header)
    logo, mdpi = ASSETS / "sensors_logo.png", ASSETS / "mdpi_logo.png"
    if logo.exists() and mdpi.exists():
        p.add_run().add_picture(str(logo), height=Cm(1.25))
        styled_run(p, "\t")
        p.add_run().add_picture(str(mdpi), height=Cm(0.95))
    else:
        styled_run(p, "sensors", 17, bold=True, italic=True, color=TEAL)
        styled_run(p, "\t")
        styled_run(p, "MDPI", 13, bold=True)
    border(p._p.get_or_add_pPr(), "bottom", 4, space=16)
    # other pages: running head with page n of N
    p = clear(sec.header)
    cite_line(p)
    styled_run(p, "\t", 8)
    field(p, "PAGE"); styled_run(p, " of ", 8); field(p, "NUMPAGES")
    border(p._p.get_or_add_pPr(), "bottom", 4, space=3)
    # first page footer: rule, citation line and DOI; other pages: DOI only
    p = clear(sec.first_page_footer)
    border(p._p.get_or_add_pPr(), "top", 4, space=4)
    cite_line(p)
    styled_run(p, "\t", 8); styled_run(p, "https://doi.org/10.3390/xxxxx", 8, color=BLUE)
    p = clear(sec.footer)
    styled_run(p, "\t", 8); styled_run(p, "https://doi.org/10.3390/xxxxx", 8, color=BLUE)


def front_table(doc):
    """Move sidebar paragraphs and Highlights..Keywords into a borderless 2-column table."""
    body = doc.element.body
    paras = doc.paragraphs
    side = [p for p in paras if p.style.name == "MDPI Sidebar"]
    right_names = {"MDPI Abstract Head", "MDPI Highlights Q", "MDPI Bullet", "MDPI Abstract", "MDPI Keywords"}
    right = [p for p in paras if p.style.name in right_names]
    anchor = side[0]._p
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl.autofit = False
    widths = [INDENT, TEXT_W - INDENT]
    for ci, (cell, w) in enumerate(zip(tbl.rows[0].cells, widths)):
        cell.width = w
        tcpr = cell._tc.get_or_add_tcPr()
        mar = OxmlElement("w:tcMar")
        for sd, v in [("left", 0), ("right", 280 if ci == 0 else 0)]:
            e = OxmlElement(f"w:{sd}"); e.set(qn("w:w"), str(v)); e.set(qn("w:type"), "dxa"); mar.append(e)
        tcpr.append(mar)
    grid = tbl._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(int(w.twips if hasattr(w, "twips") else w / 635)))
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(int(TEXT_W / 635))); tw.set(qn("w:type"), "dxa")
    for el in tbl._tbl.tblPr.findall(qn("w:tblW")):
        tbl._tbl.tblPr.remove(el)
    tbl._tbl.tblPr.append(tw)
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tbl._tbl.tblPr.append(lay)
    tbl.rows[0].cells[0].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
    tblpr = tbl._tbl.tblPr
    for el in tblpr.findall(qn("w:tblBorders")):
        tblpr.remove(el)
    bd = OxmlElement("w:tblBorders")
    for sd in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        e = OxmlElement(f"w:{sd}"); e.set(qn("w:val"), "nil"); bd.append(e)
    tblpr.append(bd)
    anchor.addprevious(tbl._tbl)
    for cell, ps in zip(tbl.rows[0].cells, [side, right]):
        cell._tc.remove(cell.paragraphs[0]._p)
        for p in ps:
            cell._tc.append(p._p)


def three_line_tables(doc):
    for t in doc.tables[1:]:
        tblpr = t._tbl.tblPr
        for el in tblpr.findall(qn("w:tblBorders")) + tblpr.findall(qn("w:tblW")) + tblpr.findall(qn("w:tblInd")):
            tblpr.remove(el)
        w = OxmlElement("w:tblW"); w.set(qn("w:w"), "5000"); w.set(qn("w:type"), "pct"); tblpr.append(w)
        bd = OxmlElement("w:tblBorders")
        for sd, val in [("top", "single"), ("bottom", "single"), ("left", "nil"), ("right", "nil"),
                        ("insideH", "nil"), ("insideV", "nil")]:
            e = OxmlElement(f"w:{sd}"); e.set(qn("w:val"), val)
            if val == "single":
                e.set(qn("w:sz"), "8"); e.set(qn("w:color"), "000000")
            bd.append(e)
        tblpr.append(bd)
        for ri, row in enumerate(t.rows):
            for ci, cell in enumerate(row.cells):
                if ri == 0:
                    tcpr = cell._tc.get_or_add_tcPr()
                    tb = OxmlElement("w:tcBorders"); e = OxmlElement("w:bottom")
                    e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); e.set(qn("w:color"), "000000")
                    tb.append(e); tcpr.append(tb)
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(1.5); p.paragraph_format.space_after = Pt(1.5)
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT if ci == 0 else WD_ALIGN_PARAGRAPH.CENTER
                    p.paragraph_format.left_indent = Cm(0); p.paragraph_format.first_line_indent = Cm(0)
                    for r in p.runs:
                        r.font.size = Pt(9)
                        r.font.name = FONT
                        if ri == 0:
                            r.font.bold = True


def list_indents(doc):
    for p in doc.paragraphs:
        ppr = p._p.pPr
        if ppr is not None and ppr.find(qn("w:numPr")) is not None:
            p.paragraph_format.left_indent = INDENT + Cm(0.75)
            p.paragraph_format.first_line_indent = -Cm(0.75)


def bold_figure_labels(doc):
    for p in doc.paragraphs:
        if p.style.name in ("Image Caption",):
            p.paragraph_format.left_indent = INDENT


def restore_tabs(doc):
    """Turn the TAB marker back into real tab characters (body, table cells, front table)."""
    for t in doc.element.body.iter(qn("w:t")):
        if t.text and TAB in t.text:
            parts = t.text.split(TAB)
            r = t.getparent()
            t.text = parts[0]; t.set(qn("xml:space"), "preserve")
            prev = t
            for part in parts[1:]:
                tab = OxmlElement("w:tab"); prev.addnext(tab)
                nt = OxmlElement("w:t"); nt.text = part; nt.set(qn("xml:space"), "preserve"); tab.addnext(nt)
                prev = nt


def tight_inline_images(doc):
    """LibreOffice pads inline images that carry no wrap distances; set them to zero (ORCID icons)."""
    WP = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}inline"
    for el in doc.element.body.iter(WP):
        for k in ("distT", "distB", "distL", "distR"):
            el.set(k, "0")


def keep_rows_whole(doc):
    for t in doc.tables[1:]:
        for ri, row in enumerate(t.rows):
            trpr = row._tr.get_or_add_trPr()
            trpr.append(OxmlElement("w:cantSplit"))
            if ri == 0 and trpr.find(qn("w:tblHeader")) is None:
                trpr.append(OxmlElement("w:tblHeader"))


def hyphenate(doc):
    st = doc.settings.element
    for tag in ("w:autoHyphenation", "w:doNotHyphenateCaps"):
        if st.find(qn(tag)) is None:
            el = OxmlElement(tag); st.append(el)


def references_full_width(doc):
    for p in doc.paragraphs:
        if p.style.name.startswith("Heading") and p.text.strip() == "References":
            p.paragraph_format.left_indent = Cm(0)
            p.paragraph_format.page_break_before = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--csl", default=str(HERE / "mdpi.csl"))
    ap.add_argument("--osf", default="https://doi.org/10.17605/OSF.IO/CVFA3")
    ap.add_argument("--emails", help="private JSON file with author e-mails (submission copy only; never commit it)")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    md = (HERE / "manuscript.md").read_text()
    title, abstract_text, keywords, body, highlights = prepare_markdown(md, a.osf)
    emails = json.loads(Path(a.emails).read_text()) if a.emails else None
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ref = td / "reference.docx"; build_reference(ref)
        src = td / "ms.md"
        src.write_text("---\nbibliography: " + str(ROOT / "references" / "references.bib") +
                       "\nlink-citations: true\n---\n\n" + front_markdown(title, abstract_text, keywords, a.osf, highlights, emails) +
                       "\n\n" + body)
        subprocess.run(["pandoc", str(src), "--citeproc", "--csl", a.csl, "--reference-doc", str(ref), "--shift-heading-level-by=-1",
                        "-o", str(out)], check=True)
    doc = Document(str(out))
    header_footer(doc)
    front_table(doc)
    three_line_tables(doc)
    list_indents(doc)
    bold_figure_labels(doc)
    restore_tabs(doc)
    tight_inline_images(doc)
    first_back = next((p for p in doc.paragraphs if p.style.name == "MDPI Back"), None)
    if first_back is not None:
        first_back.paragraph_format.space_before = Pt(14)
    keep_rows_whole(doc)
    hyphenate(doc)
    references_full_width(doc)
    doc.save(str(out))
    print("wrote", out)
    if a.pdf:
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", str(out), "--outdir", str(out.parent)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("wrote", out.with_suffix(".pdf"))


if __name__ == "__main__":
    main()
