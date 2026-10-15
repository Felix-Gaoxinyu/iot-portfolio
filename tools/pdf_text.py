"""PDF text extractor for Chrome-generated (subset-font, Identity-H) PDFs.

Groups glyphs into words via BT..ET blocks, then into lines via the text
matrix Y value, and decodes through each font's ToUnicode CMap.
"""
import re
import sys
import zlib

OBJ_RE = re.compile(rb"(\d+)\s+(\d+)\s+obj(.*?)endobj", re.S)


def decompress(head, raw):
    if b"FlateDecode" in head:
        for trim in (0, 1, 2):
            src = raw[trim:] if trim else raw
            try:
                return zlib.decompress(src)
            except Exception:
                pass
        try:
            return zlib.decompressobj().decompress(raw)
        except Exception:
            return None
    return raw


def parse_objects(data):
    objs = {}
    for m in OBJ_RE.finditer(data):
        num = int(m.group(1))
        body = m.group(3)
        sm = re.search(rb"stream\r?\n", body)
        stream = None
        if sm:
            raw = body[sm.end():]
            ei = raw.rfind(b"endstream")
            if ei != -1:
                raw = raw[:ei]
            stream = decompress(body[: sm.start()], raw)
        objs[num] = (body, stream)
    return objs


def deref(objs, token):
    m = re.match(rb"\s*(\d+)\s+\d+\s+R", token)
    if m:
        return int(m.group(1))
    return None


def balanced_dict(buf, start):
    """Return the <<...>> dict text starting at buf[start] == '<'."""
    assert buf[start:start + 2] == b"<<"
    depth = 0
    i = start
    while i < len(buf):
        if buf[i:i + 2] == b"<<":
            depth += 1
            i += 2
            continue
        if buf[i:i + 2] == b">>":
            depth -= 1
            i += 2
            if depth == 0:
                return buf[start:i]
            continue
        if buf[i:i + 1] == b"(":  # skip literal string
            j = i + 1
            d = 1
            while j < len(buf) and d:
                if buf[j:j + 1] == b"\\":
                    j += 2
                    continue
                if buf[j:j + 1] == b"(":
                    d += 1
                elif buf[j:j + 1] == b")":
                    d -= 1
                j += 1
            i = j
            continue
        i += 1
    return buf[start:]


def find_key_dict(buf, key):
    """Find `/key <<...>>` or `/key N 0 R` inside buf; return raw value."""
    m = re.search(rb"/" + key + rb"\s*", buf)
    if not m:
        return None
    i = m.end()
    if buf[i:i + 2] == b"<<":
        return balanced_dict(buf, i)
    m2 = re.match(rb"(\d+)\s+\d+\s+R", buf[i:])
    if m2:
        return m2.group(0)
    return None


def parse_tounicode(cmap_bytes, two_byte):
    table = {}
    for bm in re.finditer(rb"beginbfchar(.*?)endbfchar", cmap_bytes, re.S):
        for pair in re.finditer(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]*)>", bm.group(1)):
            src = int(pair.group(1), 16)
            dst = pair.group(2).decode()
            if len(dst) % 2:
                dst = "0" + dst
            try:
                table[src] = bytes.fromhex(dst).decode("utf-16-be", "replace")
            except Exception:
                pass
    for bm in re.finditer(rb"beginbfrange(.*?)endbfrange", cmap_bytes, re.S):
        body = bm.group(1)
        for r in re.finditer(
            rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*(<([0-9A-Fa-f]+)>|\[(.*?)\])",
            body,
            re.S,
        ):
            lo = int(r.group(1), 16)
            hi = int(r.group(2), 16)
            if r.group(4):
                dst = r.group(4).decode()
                if len(dst) % 2:
                    dst = "0" + dst
                base = int(dst, 16)
                for k in range(lo, min(hi, lo + 4096) + 1):
                    table[k] = chr(base + (k - lo))
            else:
                items = re.findall(rb"<([0-9A-Fa-f]+)>", r.group(5))
                for idx, it in enumerate(items):
                    d = it.decode()
                    if len(d) % 2:
                        d = "0" + d
                    try:
                        table[lo + idx] = bytes.fromhex(d).decode("utf-16-be", "replace")
                    except Exception:
                        pass
    return table


def make_decoder(table, two_byte):
    def dec(raw):
        out = []
        if two_byte:
            i = 0
            while i < len(raw):
                if i + 1 < len(raw):
                    code = (raw[i] << 8) | raw[i + 1]
                    if code in table:
                        out.append(table[code])
                        i += 2
                        continue
                code = raw[i]
                out.append(table.get(code, chr(code)))
                i += 1
        else:
            for b in raw:
                out.append(table.get(b, chr(b)))
        return "".join(out)
    return dec


TOKEN_RE = re.compile(
    rb"(?P<str><[0-9A-Fa-f\s]*>|\((?:\\.|[^\\()])*\))"
    rb"\s*(?P<op>Tj|TJ|'|\")"
    rb"|(?P<num>-?\d*\.?\d+)\s+(?P<num2>-?\d*\.?\d+)\s+(?P<tdop>Td|TD)"
    rb"|(?P<tm>[-\d.\s]+?)\s+Tm"
    rb"|(?P<font>/[A-Za-z0-9_.+-]+)\s+(?P<size>[\d.]+)\s+Tf"
    rb"|(?P<bt>BT)|(?P<et>ET)",
    re.S,
)


def unescape(s):
    out = bytearray()
    i = 0
    while i < len(s):
        c = s[i]
        if c == 0x5C and i + 1 < len(s):
            n = s[i + 1]
            mp = {0x6E: 10, 0x72: 13, 0x74: 9, 0x62: 8, 0x66: 12}
            if n in mp:
                out.append(mp[n]); i += 2; continue
            if 0x30 <= n <= 0x37:
                j = i + 1; digs = b""
                while j < len(s) and len(digs) < 3 and 0x30 <= s[j] <= 0x37:
                    digs += bytes([s[j]]); j += 1
                out.append(int(digs, 8) & 0xFF); i = j; continue
            out.append(n); i += 2; continue
        out.append(c); i += 1
    return bytes(out)


def hexbytes(tok):
    h = re.sub(rb"\s", b"", tok[1:-1])
    if len(h) % 2:
        h += b"0"
    try:
        return bytes.fromhex(h.decode())
    except Exception:
        return b""


def extract_words(content, decoders, default_dec):
    """Yield (y, x, text) words using BT..ET blocks."""
    words = []
    cur_font = None
    in_bt = False
    x = 0.0
    y = 0.0
    pending = []

    def flush():
        if pending:
            txt = "".join(pending)
            if txt.strip():
                words.append((round(y, 1), round(x0, 2), txt))
        pending.clear()

    x0 = 0.0
    for m in TOKEN_RE.finditer(content):
        if m.group("bt"):
            in_bt = True
            pending.clear()
            x = 0.0
            continue
        if m.group("et"):
            flush()
            in_bt = False
            continue
        if not in_bt:
            continue
        if m.group("font"):
            name = m.group("font")[1:].decode()
            cur_font = name
            continue
        if m.group("tm"):
            parts = m.group("tm").split()
            # a b c d e f Tm -> y = f (with b/d sign handling ignored)
            try:
                y = float(parts[-1])
                x = float(parts[-2])
            except Exception:
                pass
            continue
        if m.group("tdop"):
            dx = float(m.group("num"))
            x += dx
            continue
        if m.group("op"):
            tok = m.group("str")
            dec = decoders.get(cur_font, default_dec)
            if m.group("op") in (b"Tj", b"'", b'"'):
                raw = hexbytes(tok) if tok.startswith(b"<") else unescape(tok[1:-1])
                if not pending:
                    x0 = x
                pending.append(dec(raw))
            else:  # TJ array
                if tok.startswith(b"["):
                    for e in re.finditer(
                        rb"<[0-9A-Fa-f\s]*>|\((?:\\.|[^\\()])*\)|-?\d*\.?\d+",
                        tok,
                        re.S,
                    ):
                        t = e.group(0)
                        if t.startswith(b"<"):
                            if not pending:
                                x0 = x
                            pending.append(dec(hexbytes(t)))
                        elif t.startswith(b"("):
                            if not pending:
                                x0 = x
                            pending.append(dec(unescape(t[1:-1])))
                        else:
                            try:
                                if float(t) < -140 and pending:
                                    flush()
                            except Exception:
                                pass
            continue
    flush()
    return words


def page_resources(objs, body):
    res = find_key_dict(body, b"Resources")
    if res is None:
        return b""
    if res.strip().endswith(b"R"):
        n = deref(objs, res)
        if n in objs:
            return objs[n][0]
        return b""
    return res


def build_decoders(objs, res):
    fonts = find_key_dict(res, b"Font")
    if fonts is None:
        return {}
    if fonts.strip().endswith(b"R"):
        n = deref(objs, fonts)
        fonts = objs[n][0] if n in objs else b""
    out = {}
    for m in re.finditer(rb"/([A-Za-z0-9_.+-]+)\s+(\d+)\s+\d+\s+R", fonts):
        name = m.group(1).decode()
        fobj = int(m.group(2))
        if fobj not in objs:
            continue
        fbody = objs[fobj][0]
        two_byte = b"/Type0" in fbody or b"Identity-H" in fbody
        tu = find_key_dict(fbody, b"ToUnicode")
        table = {}
        if tu:
            n = deref(objs, tu)
            if n in objs and objs[n][1]:
                table = parse_tounicode(objs[n][1], two_byte)
        if not table and fobj in objs and objs[fobj][1]:
            table = parse_tounicode(objs[fobj][1], two_byte)
        out[name] = make_decoder(table, two_byte)
    return out


def fallback_decoder(objs):
    merged = {}
    for num, (body, stream) in objs.items():
        if stream and (b"beginbfchar" in stream or b"beginbfrange" in stream):
            merged.update(parse_tounicode(stream, False))
    return make_decoder(merged, False)


def main():
    path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    data = open(path, "rb").read()
    objs = parse_objects(data)

    # pages in document order: walk the page tree if possible, else numeric order
    page_nums = []
    for num, (body, _) in objs.items():
        if re.search(rb"/Type\s*/Page[^s]", body):
            page_nums.append(num)
    kids_order = []
    for num, (body, _) in objs.items():
        if re.search(rb"/Type\s*/Pages", body):
            k = find_key_dict(body, b"Kids")
            if k and k.startswith(b"<<"):
                inner = k
            else:
                m2 = re.search(rb"/Kids\s*\[(.*?)\]", body, re.S)
                inner = m2.group(1) if m2 else b""
            for m3 in re.finditer(rb"(\d+)\s+\d+\s+R", inner):
                if int(m3.group(1)) in page_nums:
                    kids_order.append(int(m3.group(1)))
    ordered = kids_order + [n for n in sorted(page_nums) if n not in kids_order]

    default_dec = fallback_decoder(objs)
    lines_out = []
    for pnum in ordered:
        body, _ = objs[pnum]
        res = page_resources(objs, body)
        decoders = build_decoders(objs, res)
        # content streams
        contents = []
        cm = re.search(rb"/Contents\s*(\d+)\s+\d+\s+R", body)
        if cm:
            contents.append(int(cm.group(1)))
        else:
            marr = re.search(rb"/Contents\s*\[(.*?)\]", body, re.S)
            if marr:
                for mm in re.finditer(rb"(\d+)\s+\d+\s+R", marr.group(1)):
                    contents.append(int(mm.group(1)))
        words = []
        for c in contents:
            if c in objs and objs[c][1]:
                words.extend(extract_words(objs[c][1], decoders, default_dec))
        if not words:
            continue
        # group into lines by y
        words.sort(key=lambda w: (w[0], w[1]))
        lines = []
        cur = [words[0]]
        for w in words[1:]:
            if abs(w[0] - cur[-1][0]) <= 2.0:
                cur.append(w)
            else:
                lines.append(cur)
                cur = [w]
        lines.append(cur)
        lines_out.append(f"\n===== PAGE (obj {pnum}) =====")
        for ln in lines:
            ln.sort(key=lambda w: w[1])
            txt = ""
            prev_end = None
            for _, wx, t in ln:
                if prev_end is not None and wx - prev_end > 1.2 and not txt.endswith(" "):
                    txt += " "
                txt += t
                prev_end = wx + len(t) * 0.0
                prev_end = wx
            lines_out.append(txt.rstrip())
    text = "\n".join(lines_out)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
