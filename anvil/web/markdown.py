"""The Markdown the players' README uses, as HTML, for the site's home page (make_site.py): headings (with GitHub's
ids, so its own links to them work), paragraphs, lists, block quotes, code blocks, tables, rules, and inline code,
bold, italics, links, images and <br>. Small on purpose: the README is ours, and the site needs nothing else."""
import html
import re

INLINE = re.compile(r"`([^`]+)`|\*\*(.+?)\*\*|\*(.+?)\*|!\[([^\]]*)\]\(([^)]+)\)|\[([^\]]+)\]\(([^)]+)\)|(<br>)")


def inline(text: str, link) -> str:
    """A line's inline Markdown; link(url) gives where a link or image points on the site."""
    out, pos = [], 0
    for m in INLINE.finditer(text):
        out.append(html.escape(text[pos:m.start()], quote=False))
        code, bold, italic, alt, src, label, href, br = m.groups()
        if code is not None:
            out.append(f"<code>{html.escape(code, quote=False)}</code>")
        elif bold is not None:
            out.append(f"<strong>{inline(bold, link)}</strong>")
        elif italic is not None:
            out.append(f"<em>{inline(italic, link)}</em>")
        elif src is not None:
            out.append(f'<img src="{html.escape(link(src))}" alt="{html.escape(alt)}">')
        elif href is not None:
            out.append(f'<a href="{html.escape(link(href))}">{inline(label, link)}</a>')
        else:
            out.append("<br>")
        pos = m.end()
    out.append(html.escape(text[pos:], quote=False))
    return "".join(out)


def slug(title: str) -> str:
    """GitHub's id for a heading: lower case, without punctuation, spaces as hyphens."""
    return re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")


def to_html(text: str, link=lambda url: url) -> str:
    lines = text.splitlines()
    out, i = [], 0

    def para_end(j):
        return j >= len(lines) or not lines[j].strip() or re.match(r"(#{1,6} |[-*] |\d+\. |> |```|\||---\s*$)",
                                                                    lines[j])

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
        elif m := re.match(r"(#{1,6}) (.*)", line):
            level, title = len(m[1]), m[2].strip()
            out.append(f'<h{level} id="{slug(title)}">{inline(title, link)}</h{level}>')
            i += 1
        elif re.match(r"---\s*$", line):
            out.append("<hr>")
            i += 1
        elif line.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:j]), quote=False) + "</code></pre>")
            i = j + 1
        elif line.startswith(">"):
            j = i
            while j < len(lines) and lines[j].startswith(">"):
                j += 1
            quote = "\n".join(l[1:].removeprefix(" ") for l in lines[i:j])
            out.append(f"<blockquote>{to_html(quote, link)}</blockquote>")
            i = j
        elif line.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines[i:j]]
            head, body = rows[0], rows[2:]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c, link)}</th>" for c in head) + "</tr></thead>"
                       + "<tbody>" + "".join("<tr>" + "".join(f"<td>{inline(c, link)}</td>" for c in row) + "</tr>"
                                             for row in body) + "</tbody></table>")
            i = j
        elif m := re.match(r"([-*]|\d+\.) ", line):
            ordered = m[1][0].isdigit()
            items, j = [], i
            while j < len(lines) and (m := re.match(r"([-*]|\d+\.) (.*)", lines[j])) and m[1][0].isdigit() == ordered:
                item = [m[2]]
                j += 1
                # Its lines go on while they're indented
                while j < len(lines) and lines[j].startswith(" ") and lines[j].strip():
                    item.append(lines[j].strip())
                    j += 1
                items.append(" ".join(item))
            tag = "ol" if ordered else "ul"
            out.append(f"<{tag}>" + "".join(f"<li>{inline(item, link)}</li>" for item in items) + f"</{tag}>")
            i = j
        elif line.lstrip().startswith("<"):
            # HTML, as it is, to the next blank line
            j = i
            while j < len(lines) and lines[j].strip():
                j += 1
            out.append("\n".join(lines[i:j]))
            i = j
        else:
            j = i + 1
            while not para_end(j):
                j += 1
            out.append("<p>" + inline(" ".join(l.strip() for l in lines[i:j]), link) + "</p>")
            i = j
    return "\n".join(out)
