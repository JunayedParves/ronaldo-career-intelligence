"""Minimal rowspan/colspan-aware MediaWiki table parser (stdlib only)."""
import re

def _mask(s):
    """Hide pipes inside templates and links so cell splitting is safe."""
    out, depth = [], 0
    i = 0
    while i < len(s):
        two = s[i:i+2]
        if two in ("{{", "[["):
            depth += 1; out.append(two); i += 2; continue
        if two in ("}}", "]]"):
            depth = max(0, depth-1); out.append(two); i += 2; continue
        c = s[i]
        out.append("\x00" if (c == "|" and depth) else c)
        i += 1
    return "".join(out)

def strip_refs(s):
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"<ref[\s\S]*?</ref>", "", s)
    return s

def plain(s):
    s = strip_refs(s).replace("\x00", "|")
    s = re.sub(r"\{\{Citation needed[^{}]*\}\}", "[cn]", s, flags=re.I)
    s = re.sub(r"\{\{(?:efn|refn|sfn)[^{}]*\}\}", "", s, flags=re.I)
    s = re.sub(r"\{\{#invoke:flag\|icon\|[^{}]*\}\}", "", s)
    s = re.sub(r"\{\{fb\|([^{}|]*)[^{}]*\}\}", r"\1", s)
    s = re.sub(r"\{\{(?:won|lost|draw|tie|Runner-up|runner-up|nom|sho|Nom|Sho|Unknown)(?:\|([^{}]*))?\}\}",
               lambda m: (m.group(1) or m.group(0).strip("{}")).split("|")[0], s)
    s = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", s)
    s = s.replace("'''", "").replace("''", "").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()

ATTR = re.compile(r'^\s*((?:[\w-]+\s*=\s*(?:"[^"]*"|[^\s|]+)\s*)+)(?:\|(.*))?$', re.S)

def tables(text):
    """Yield (caption, rows) for every top-level table; rows are lists of cell strings."""
    out = []
    pos = 0
    while True:
        i = text.find("{|", pos)
        if i < 0: break
        depth, k = 1, i+2
        while depth and k < len(text):
            a, b = text.find("{|", k), text.find("|}", k)
            if b < 0: k = len(text); break
            if 0 <= a < b: depth += 1; k = a+2
            else: depth -= 1; k = b+2
        out.append(_parse(text[i:k])); pos = k
    return out

def _parse(tbl):
    body = tbl[2:-2]
    caption = ""
    rows, spans = [], {}
    chunks = re.split(r"\n\|-[^\n]*", "\n"+body)
    head = chunks[0]
    m = re.search(r"\n\|\+(.*)", head)
    if m: caption = plain(m.group(1))
    for ch in chunks:
        m = re.search(r"\n\|\+(.*)", ch)
        if m: caption = caption or plain(m.group(1))
        cells = []
        for line in re.split(r"\n(?=[|!])", ch):
            if not line or line[0] not in "|!" or line.startswith("|+"): continue
            masked = _mask(line[1:].lstrip("|"))
            for c in re.split(r"\|\||!!", masked):
                cells.append(c)
        if not cells: continue
        row, col, idx = [], 0, 0
        def fill():
            nonlocal col
            while col in spans:
                val, left = spans[col]
                row.append(val)
                if left <= 1: del spans[col]
                else: spans[col] = (val, left-1)
                col += 1
        for c in cells:
            fill()
            rs = re.search(r'rowspan\s*=\s*"?(\d+)', c.split("{{")[0], re.I)
            cs = re.search(r'colspan\s*=\s*"?(\d+)', c.split("{{")[0], re.I)
            m = ATTR.match(c)
            if m and m.group(2) is not None: val = m.group(2)
            else:
                val = re.sub(r'^\s*(?:[\w-]+\s*=\s*(?:"[^"]*"|[^\s{|]+)\s*)+', "", c) if "=" in c.split("{{")[0][:40] else c
            val = plain(val)
            for n in range(int(cs.group(1)) if cs else 1):
                row.append(val)
                if rs and int(rs.group(1)) > 1: spans[col] = (val, int(rs.group(1))-1)
                col += 1
        fill()
        rows.append(row)
    return caption, rows
