from __future__ import annotations
from typing import Any, List
import re

def adf_to_text(adf: Any) -> str:
    if not adf:
        return ""
    chunks: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            t = node.get("type")
            if t == "text":
                chunks.append(node.get("text", ""))
            for v in node.values():
                walk(v)
            if t in {"paragraph", "heading"}:
                chunks.append("\n")
        elif isinstance(node, list):
            for it in node:
                walk(it)

    walk(adf)
    text = "".join(chunks)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text
