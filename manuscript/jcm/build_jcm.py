"""
Build the Journal of Clinical Medicine (MDPI) version of the manuscript on the
official JCM Word template.

Usage:
    python manuscript/jcm/build_jcm.py TEMPLATE.docx OUT.docx

The template (JCM_Template.docx, from the MDPI JCM "Instructions for Authors"
page) is not in the repository. The script keeps the template's first page
(article type, title, authors, affiliations, the left-hand box with editor,
dates and licence, abstract, keywords), its styles, running header and footer,
line numbering and closing Disclaimer, fills them from manuscript_jcm.md, and
replaces the template's instructional body with the manuscript rendered by
pandoc (citeproc + mdpi.csl). Every paragraph, table and figure is given the
template's own MDPI_* style.

E-mail addresses are never written: the affiliation lines carry the tokens
QQEMAIL_<key>QQ (non-corresponding authors) and the correspondence line QQCORRQQ
(the two corresponding authors), as in Sensors 2026, 26, 7340. The public copy replaces
them with nothing / author initials (done here); the submission copy is made
from the tokenised file (--keep-tokens) outside the repository.

Text marked [[CONFIRM: ...]] in the markdown is kept and highlighted yellow.
"""
import argparse
import copy
import io
import re
import subprocess
import tempfile
import zipfile
from pathlib import Path

from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

HERE = Path(__file__).resolve().parent
MS = HERE.parent
ROOT = MS.parent
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TEXT_W = 7857        # body text width (twips), indented 2608 from the margin
FULL_W = 10465       # full width between margins
FIG_CM = 17.0        # figures at full width
MAX_FIG_H_CM = 11.5  # ... but no taller than this

AUTHORS = [("Mohannad Banat", "1"), ("Hamza Abu Owida", "1,*"), ("Ayoub Alsarhan", "2"),
           ("Dimah Al-Fraihat", "3"), ("Abdulmohsen Algarni", "4,*")]
AFFIL = [
    ("1", "Department of Medical Engineering, Faculty of Engineering, Al-Ahliyya Amman University, Amman 19328, Jordan",
     ["banat"]),
    ("2", "Department of Information Technology, Faculty of Prince Al-Hussein Bin Abdallah II for Information Technology, The Hashemite University, Zarqa 13133, Jordan", ["alsarhan"]),
    ("3", "Department of Software Engineering, Faculty of Information Technology, Isra University, Amman 11622, Jordan",
     ["alfraihat"]),
    ("4", "Department of Computer Science, King Khalid University, Abha 61421, Saudi Arabia", []),
]
CORR_PUBLIC = "H.A.O. and A.A. (Abdulmohsen Algarni)"


# ---------------------------------------------------------------- markdown
def split_markdown(md):
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    m = re.match(r"---\n(.*?)\n---\n", md, re.S)
    title = re.search(r'^title:\s*"(.*)"', m.group(1), re.M).group(1)
    md = md[m.end():]
    abstract = md[md.index("## Abstract") + len("## Abstract"):md.index("**Keywords:**")].strip()
    kw = md[md.index("**Keywords:**") + len("**Keywords:**"):md.index("## 1. Introduction")].strip()
    body = md[md.index("## 1. Introduction"):md.index("## 6. Back Matter")]
    back = md[md.index("## 6. Back Matter") + len("## 6. Back Matter"):md.index("## Abbreviations")].strip()
    abbr = md[md.index("## Abbreviations"):md.index("## Appendix A")]
    appx = md[md.index("## Appendix A"):]
    abbrevs = [tuple(l.rstrip("\\").split("\t", 1)) for l in abbr.splitlines() if "\t" in l]
    return title, abstract, " ".join(kw.split()), body, back, abbrevs, appx


def placeholders(md):
    return re.sub(r"\[\[(CONFIRM:.*?)\]\]", lambda m: "[\\[" + m.group(1) + "\\]]{custom-style=\"PLACEHOLDER\"}",
                  md, flags=re.S)


def pandoc_body(body, back, appx, out):
    back_paras = [p.strip() for p in back.split("\n\n") if p.strip()]
    back_md = "\n\n".join("::: {custom-style=\"BACKMATTER\"}\n" + p + "\n:::" for p in back_paras)
    md = (body + "\n\n" + back_md + "\n\n## Abbreviations\n\nQQABBREVQQ\n\n" + appx +
          "\n\n## References\n\n::: {#refs}\n:::\n")
    md = re.sub(r"`([^`]+)`", r"\1", md)          # no code font in a clinical journal
    md = placeholders(md)
    src = Path(out).with_suffix(".md")
    src.write_text("---\nbibliography: " + str(ROOT / "references" / "references.bib") + "\n---\n\n" + md)
    subprocess.run(["pandoc", str(src), "--citeproc", "--csl", str(MS / "mdpi.csl"),
                    "--resource-path", str(MS), "--shift-heading-level-by=-1", "-o", str(out)], check=True)


# ---------------------------------------------------------------- docx helpers
def el(tag, **attrs):
    e = OxmlElement(tag)
    for k, v in attrs.items():
        e.set(qn(k), str(v))
    return e


def run(text, bold=False, italic=False, sup=False, size=None, highlight=False):
    r = el("w:r")
    rpr = el("w:rPr")
    if bold:
        rpr.append(el("w:b"))
    if italic:
        rpr.append(el("w:i"))
    if highlight:
        rpr.append(el("w:highlight", **{"w:val": "yellow"}))
    if size:
        rpr.append(el("w:sz", **{"w:val": size}))
        rpr.append(el("w:szCs", **{"w:val": size}))
    if sup:
        rpr.append(el("w:vertAlign", **{"w:val": "superscript"}))
    if len(rpr):
        r.append(rpr)
    parts = text.split("\t")
    for i, part in enumerate(parts):
        if i:
            r.append(el("w:tab"))
        if part:
            t = el("w:t")
            t.text = part
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
            r.append(t)
    return r


def clear_runs(p):
    for c in list(p):
        if c.tag != qn("w:pPr"):
            p.remove(c)


def set_style(p, sid):
    ppr = p.find(qn("w:pPr"))
    if ppr is None:
        ppr = el("w:pPr")
        p.insert(0, ppr)
    ps = ppr.find(qn("w:pStyle"))
    if ps is None:
        ps = el("w:pStyle")
        ppr.insert(0, ps)
    ps.set(qn("w:val"), sid)
    return ppr


def md_inline_runs(text, size=None):
    """**bold** and *italic* and ^sup^ in short front-matter strings."""
    out = []
    for tok in re.split(r"(\*\*[^*]+\*\*|\*[^*]+\*|\^[^^]+\^)", text):
        if not tok:
            continue
        if tok.startswith("**"):
            out.append(run(tok[2:-2], bold=True, size=size))
        elif tok.startswith("*"):
            out.append(run(tok[1:-1], italic=True, size=size))
        elif tok.startswith("^"):
            out.append(run(tok[1:-1], sup=True, size=size))
        else:
            out.append(run(tok, size=size))
    return out


# ---------------------------------------------------------------- front page
def fill_front(doc, title, abstract, kw):
    body = doc.element.body
    paras = {}
    for p in body.iter(qn("w:p")):
        ps = p.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        if ps is not None:
            paras.setdefault(ps.get(qn("w:val")), []).append(p)
    p = paras["MDPI11articletype"][0]; clear_runs(p); p.append(run("Article"))
    p = paras["MDPI12title"][0]; clear_runs(p); p.append(run(title))
    p = paras["MDPI13authornames"][0]; clear_runs(p)
    for i, (name, sup) in enumerate(AUTHORS):
        sep = "" if i == 0 else (" and " if i == len(AUTHORS) - 1 else ", ")
        p.append(run(sep + name + " "))
        p.append(run(sup, sup=True))
    aff = paras["MDPI16affiliation"]
    proto = aff[0]
    for a in aff[:-1]:
        body.remove(a)
    corr = aff[-1]
    for num, text, keys in AFFIL:
        q = copy.deepcopy(proto); clear_runs(q)
        q.append(run(num, sup=False)); q.append(run("\t" + text))
        for k in keys:
            q.append(run("; QQEMAIL_" + k + "QQ"))
        corr.addprevious(q)
    clear_runs(corr)
    corr.append(run("*", bold=True)); corr.append(run("\tCorrespondence: QQCORRQQ"))
    # abstract: second MDPI_1.7 paragraph holds the text
    p = paras["MDPI17abstract"][1]; clear_runs(p)
    for r_ in md_inline_runs(" ".join(abstract.split())):
        p.append(r_)
    p = paras["MDPI18keywords"][0]; clear_runs(p)
    p.append(run("Keywords: ", bold=True)); p.append(run(kw))
    # licence year in the left-hand box
    for t in body.iter(qn("w:t")):
        if t.text and "2025 by the authors" in t.text:
            t.text = t.text.replace("2025", "2026")
    return paras["MDPI19line"][0]


# ---------------------------------------------------------------- body
def build_body(doc, src, anchor, abbrevs):
    sdoc = Document(src)
    sid2name = {s.style_id: s.name for s in sdoc.styles}
    # list kinds from pandoc numbering
    kinds = {}
    numbering = sdoc.part.numbering_part.element
    absfmt = {}
    for an in numbering.findall(qn("w:abstractNum")):
        lvl = an.find(qn("w:lvl"))
        fmt = lvl.find(qn("w:numFmt")).get(qn("w:val"))
        absfmt[an.get(qn("w:abstractNumId"))] = fmt
    for n in numbering.findall(qn("w:num")):
        kinds[n.get(qn("w:numId"))] = absfmt.get(n.find(qn("w:abstractNumId")).get(qn("w:val")))

    tpl_styles = {s.style_id for s in doc.styles}
    elems = [e for e in sdoc.element.body if e.tag in (qn("w:p"), qn("w:tbl"))]
    out = []
    for i, e in enumerate(elems):
        e = copy.deepcopy(e)
        fix_rels(e, sdoc, doc)
        if e.tag == qn("w:tbl"):
            out.append(fix_table(e))
            continue
        ps = e.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        name = sid2name.get(ps.get(qn("w:val")), "") if ps is not None else ""
        text = "".join(t.text or "" for t in e.iter(qn("w:t")))
        nxt = elems[i + 1] if i + 1 < len(elems) else None
        prv = elems[i - 1] if i else None
        if text.strip() == "QQABBREVQQ":
            q = el("w:p"); set_style(q, "MDPI32textnoindent")
            q.append(run("The following abbreviations are used in this manuscript:", size=18))
            out.append(q); out.append(abbrev_table(abbrevs))
            continue
        numpr = e.find(qn("w:pPr") + "/" + qn("w:numPr"))
        if numpr is not None:
            nid = numpr.find(qn("w:numId")).get(qn("w:val"))
            numpr.getparent().remove(numpr)
            set_style(e, "MDPI38bullet" if kinds.get(nid) == "bullet" else "MDPI37itemize")
        elif name.startswith("Heading 1") or name == "heading 1":
            set_style(e, "MDPI21heading1")
        elif name.lower() == "heading 2":
            set_style(e, "MDPI22heading2")
        elif name.lower() == "heading 3":
            set_style(e, "MDPI23heading3")
        elif name == "Captioned Figure" or e.find(".//" + qn("w:drawing")) is not None:
            set_style(e, "MDPI52figure")
        elif name == "Image Caption":
            set_style(e, "MDPI511onefigurecaption")
            bold_label(e, r"^(Figure \w+\.)")
        elif name == "BACKMATTER":
            set_style(e, "MDPI62backmatter")
        elif name == "Bibliography":
            set_style(e, "MDPI81references")
            strip_number(e)
        elif nxt is not None and nxt.tag == qn("w:tbl") and re.match(r"^Table [A-Z]?\d+\.", text):
            wide = len(nxt.findall(qn("w:tblGrid") + "/" + qn("w:gridCol"))) >= 5
            set_style(e, "MDPI411onetablecaption" if wide else "MDPI41tablecaption")
        elif prv is not None and prv.tag == qn("w:tbl") and text.startswith("CV, cross-validation"):
            set_style(e, "MDPI43tablefooter")
        elif nxt is not None and nxt.find(qn("w:pPr") + "/" + qn("w:numPr")) is not None:
            set_style(e, "MDPI35textbeforelist")
        else:
            set_style(e, "MDPI31text")
        clean_runs(e, tpl_styles)
        out.append(e)
    for e in reversed(out):
        anchor.addnext(e)


def bold_label(p, pattern):
    """Make the 'Figure 1.' label of a caption bold (it may be split over runs)."""
    runs = p.findall(qn("w:r"))
    if not runs:
        return
    first = runs[0]
    t = first.find(qn("w:t"))
    if t is None:
        return
    m = re.match(pattern, t.text or "")
    if not m:
        return
    rest = t.text[m.end():]
    t.text = m.group(1)
    rpr = first.find(qn("w:rPr"))
    if rpr is None:
        rpr = el("w:rPr"); first.insert(0, rpr)
    rpr.insert(0, el("w:b"))
    r2 = copy.deepcopy(first)
    r2.find(qn("w:rPr")).remove(r2.find(qn("w:rPr")).find(qn("w:b")))
    r2.find(qn("w:t")).text = rest
    r2.find(qn("w:t")).set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    first.addnext(r2)


def strip_number(p):
    """Drop citeproc's '1.' label and the spacing after it; the style numbers the list."""
    started = False
    for r_ in list(p.findall(qn("w:r"))):
        t = r_.find(qn("w:t"))
        txt = t.text if t is not None and t.text else ""
        if not started:
            txt2 = re.sub(r"^\s*\d+\.\s*", "", txt).lstrip()
            if txt2:
                t.text = txt2
                started = True
            else:
                p.remove(r_)


def clean_runs(p, tpl_styles):
    for b in list(p.iter(qn("w:bookmarkStart"))) + list(p.iter(qn("w:bookmarkEnd"))):
        b.getparent().remove(b)
    for r_ in p.iter(qn("w:r")):
        rpr = r_.find(qn("w:rPr"))
        if rpr is None:
            continue
        rs = rpr.find(qn("w:rStyle"))
        if rs is None:
            continue
        val = rs.get(qn("w:val"))
        if val == "PLACEHOLDER":
            rpr.remove(rs); rpr.append(el("w:highlight", **{"w:val": "yellow"}))
        elif val not in tpl_styles:
            rpr.remove(rs)


def fix_rels(e, sdoc, doc):
    for blip in e.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
        key = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
        part = sdoc.part.related_parts[blip.get(key)]
        rid, _ = doc.part.get_or_add_image(io.BytesIO(part.blob))
        blip.set(key, rid)
    for ext in e.iter("{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent"):
        cx, cy = int(ext.get("cx")), int(ext.get("cy"))
        nx = int(FIG_CM * 360000); ny = int(cy * nx / cx)
        if ny > int(MAX_FIG_H_CM * 360000):                 # keep tall figures on the page
            ny = int(MAX_FIG_H_CM * 360000); nx = int(cx * ny / cy)
        ext.set("cx", str(nx)); ext.set("cy", str(ny))
        for a in e.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}ext"):
            if a.get("cx"):
                a.set("cx", str(nx)); a.set("cy", str(ny))
    for h in e.iter(qn("w:hyperlink")):
        rid = h.get(qn("r:id"))
        if rid:
            url = sdoc.part.rels[rid].target_ref
            h.set(qn("r:id"), doc.part.relate_to(url, RT.HYPERLINK, is_external=True))


def border(tag, sz):
    return el(tag, **{"w:val": "single", "w:sz": sz, "w:space": "0", "w:color": "auto"})


def fix_table(t):
    grid = t.find(qn("w:tblGrid"))
    cols = grid.findall(qn("w:gridCol"))
    n = len(cols)
    wide = n >= 5
    total = FULL_W if wide else TEXT_W
    raw = [int(c.get(qn("w:w")) or 1) for c in cols]
    s = sum(raw) or n
    widths = [max(500, int(total * r / s)) for r in raw]
    for c, w in zip(cols, widths):
        c.set(qn("w:w"), str(w))
    old = t.find(qn("w:tblPr")); t.remove(old)
    tp = el("w:tblPr")
    tp.append(el("w:tblW", **{"w:w": total, "w:type": "dxa"}))
    if wide:
        tp.append(el("w:jc", **{"w:val": "center"}))
    else:
        tp.append(el("w:tblInd", **{"w:w": 2608, "w:type": "dxa"}))
    b = el("w:tblBorders"); b.append(border("w:top", 8)); b.append(border("w:bottom", 8)); tp.append(b)
    tp.append(el("w:tblLayout", **{"w:type": "fixed"}))
    m = el("w:tblCellMar")
    m.append(el("w:left", **{"w:w": 40, "w:type": "dxa"})); m.append(el("w:right", **{"w:w": 40, "w:type": "dxa"}))
    tp.append(m)
    t.insert(0, tp)
    size = 16 if n >= 7 else 18
    for ri, tr in enumerate(t.findall(qn("w:tr"))):
        trpr = tr.find(qn("w:trPr"))
        if trpr is None:
            trpr = el("w:trPr"); tr.insert(0, trpr)
        for x in list(trpr):
            trpr.remove(x)
        trpr.append(el("w:cantSplit"))
        if ri == 0:
            trpr.append(el("w:tblHeader"))
        for ci, tc in enumerate(tr.findall(qn("w:tc"))):
            tcpr = tc.find(qn("w:tcPr"))
            if tcpr is None:
                tcpr = el("w:tcPr"); tc.insert(0, tcpr)
            for x in list(tcpr):
                tcpr.remove(x)
            tcpr.append(el("w:tcW", **{"w:w": widths[min(ci, n - 1)], "w:type": "dxa"}))
            if ri == 0:
                bb = el("w:tcBorders"); bb.append(border("w:bottom", 4)); tcpr.append(bb)
            tcpr.append(el("w:vAlign", **{"w:val": "center"}))
            for p in tc.findall(qn("w:p")):
                ppr = set_style(p, "MDPI42tablebody")
                if ci == 0 or n == 2:
                    ppr.append(el("w:jc", **{"w:val": "left"}))
                for r_ in p.iter(qn("w:r")):
                    rpr = r_.find(qn("w:rPr"))
                    if rpr is None:
                        rpr = el("w:rPr"); r_.insert(0, rpr)
                    rs = rpr.find(qn("w:rStyle"))
                    if rs is not None:
                        rpr.remove(rs)
                    if ri == 0 and rpr.find(qn("w:b")) is None:
                        rpr.insert(0, el("w:b"))
                    rpr.append(el("w:sz", **{"w:val": size})); rpr.append(el("w:szCs", **{"w:val": size}))
    return t


def abbrev_table(abbrevs):
    t = el("w:tbl")
    tp = el("w:tblPr")
    tp.append(el("w:tblW", **{"w:w": TEXT_W, "w:type": "dxa"}))
    tp.append(el("w:tblInd", **{"w:w": 2608, "w:type": "dxa"}))
    tp.append(el("w:tblLayout", **{"w:type": "fixed"}))
    t.append(tp)
    g = el("w:tblGrid")
    for w in (1300, TEXT_W - 1300):
        g.append(el("w:gridCol", **{"w:w": w}))
    t.append(g)
    for a, b in abbrevs:
        tr = el("w:tr")
        for w, txt in ((1300, a), (TEXT_W - 1300, b)):
            tc = el("w:tc"); tcpr = el("w:tcPr"); tcpr.append(el("w:tcW", **{"w:w": w, "w:type": "dxa"})); tc.append(tcpr)
            p = el("w:p"); ppr = set_style(p, "MDPI42tablebody"); ppr.append(el("w:jc", **{"w:val": "left"}))
            p.append(run(txt, size=18)); tc.append(p); tr.append(tc)
        t.append(tr)
    return t


def strip_template_body(doc, line_p):
    body = doc.element.body
    kids = list(body)
    start = kids.index(line_p)
    disclaimer = None
    for e in kids[start + 1:]:
        if e.tag == qn("w:sectPr"):
            continue
        ps = e.find(qn("w:pPr") + "/" + qn("w:pStyle"))
        if ps is not None and ps.get(qn("w:val")) == "MDPI63notes":
            disclaimer = e
            continue
        body.remove(e)
    return disclaimer


def finish_zip(path, public):
    tmp = Path(path).with_suffix(".tmp")
    with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.match(r"word/(header|footer)\d+\.xml", item.filename):
                x = data.decode("utf8").replace(">2025<", ">2026<").replace("> 14<", "> 15<")
                data = x.encode("utf8")
            if item.filename == "word/document.xml":
                x = data.decode("utf8")
                # Anchor the left-hand box (editor, dates, licence) to the text rather than to a fixed
                # page position: same place on the first page, and LibreOffice no longer loops on it.
                x = x.replace('w:vertAnchor="page" w:horzAnchor="margin" w:tblpY="11407"',
                              'w:vertAnchor="text" w:horzAnchor="margin" w:tblpY="1600"')
                # The template's section is flagged right-to-left (<w:bidi/>), which reverses the column
                # order of tables in some renderers; the article is left-to-right.
                x = re.sub(r"(<w:sectPr\b(?:(?!</w:sectPr>).)*?)<w:bidi/>", r"\1", x, flags=re.S)
                data = x.encode("utf8")
            if public and item.filename == "word/document.xml":
                x = data.decode("utf8")
                x = re.sub(r"; QQEMAIL_\w+QQ", "", x).replace("QQCORRQQ", CORR_PUBLIC)
                data = x.encode("utf8")
            zout.writestr(item, data)
    tmp.replace(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("template"); ap.add_argument("out")
    ap.add_argument("--md", default=str(HERE / "manuscript_jcm.md"))
    ap.add_argument("--keep-tokens", action="store_true", help="leave e-mail tokens for the private submission copy")
    a = ap.parse_args()
    title, abstract, kw, body, back, abbrevs, appx = split_markdown(Path(a.md).read_text())
    doc = Document(a.template)
    line_p = fill_front(doc, title, abstract, kw)
    disclaimer = strip_template_body(doc, line_p)
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "body.docx"
        pandoc_body(body, back, appx, src)
        build_body(doc, src, line_p, abbrevs)
    if disclaimer is not None:          # keep the template's Disclaimer last
        body_el = doc.element.body
        body_el.remove(disclaimer)
        body_el.find(qn("w:sectPr")).addprevious(disclaimer)
    doc.core_properties.title = title
    doc.core_properties.author = "Mohannad Banat"
    doc.save(a.out)
    finish_zip(a.out, public=not a.keep_tokens)
    print("wrote", a.out)


if __name__ == "__main__":
    main()
