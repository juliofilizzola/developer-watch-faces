"""Minimal XML tree + serializer tuned for Watch Face Format documents.

Why a custom serializer: WFF templates are written as CDATA (they contain `%s`
and arbitrary symbols) and attribute order is kept stable so generated files
diff cleanly in Git.
"""
from __future__ import annotations

from typing import Iterable


class Cdata(str):
    """Text node serialized as <![CDATA[...]]>."""


class Node:
    __slots__ = ("tag", "attrs", "children")

    def __init__(self, tag: str, attrs: dict | None = None, children: Iterable | None = None):
        self.tag = tag
        self.attrs = {k: v for k, v in (attrs or {}).items() if v is not None}
        self.children: list = []
        if children:
            self.extend(children)

    def add(self, child):
        if child is None:
            return self
        if isinstance(child, (list, tuple)):
            return self.extend(child)
        self.children.append(child)
        return self

    def extend(self, children: Iterable):
        for c in children:
            self.add(c)
        return self


def E(tag: str, children: Iterable | None = None, **attrs) -> Node:
    return Node(tag, attrs, children)


def _fmt_value(v) -> str:
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        s = f"{v:.2f}".rstrip("0").rstrip(".")
        return s if s not in ("-0", "") else "0"
    return str(v)


def _esc_attr(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;").replace("\n", "&#10;"))


def _esc_text(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def serialize(node: Node, indent: int = 0, step: str = "  ") -> str:
    pad = step * indent
    attrs = "".join(f' {k}="{_esc_attr(_fmt_value(v))}"' for k, v in node.attrs.items())
    if not node.children:
        return f"{pad}<{node.tag}{attrs}/>\n"
    # Inline form when the node only holds text (keeps Template/Expression compact).
    if all(isinstance(c, str) for c in node.children):
        body = "".join(
            f"<![CDATA[{c}]]>" if isinstance(c, Cdata) else _esc_text(c) for c in node.children
        )
        return f"{pad}<{node.tag}{attrs}>{body}</{node.tag}>\n"
    out = [f"{pad}<{node.tag}{attrs}>"]
    first_text = True
    for c in node.children:
        if isinstance(c, Node):
            if first_text:
                out.append("\n")
                first_text = False
            out.append(serialize(c, indent + 1, step))
        else:
            # Template: CDATA text must precede the <Parameter> nodes on the same line.
            out.append(f"<![CDATA[{c}]]>" if isinstance(c, Cdata) else _esc_text(c))
    out.append(f"{pad}</{node.tag}>\n")
    return "".join(out)


def document(root: Node, header_comment: str | None = None) -> str:
    head = '<?xml version="1.0" encoding="utf-8"?>\n'
    if header_comment:
        head += f"<!--\n{header_comment}\n-->\n"
    return head + serialize(root)
