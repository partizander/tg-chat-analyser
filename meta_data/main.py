#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, gzip, sys, math
from pathlib import Path
from typing import Any, Dict, List

TRIM = 140  # how many characters to show in examples


def load_json(p: Path) -> Any:
    if p.suffix == ".gz":
        with gzip.open(p, "rt", encoding="utf-8") as f:
            return json.load(f)
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def example_str(v: Any) -> str:
    if isinstance(v, (dict, list)):
        return ""
    s = repr(v)
    if len(s) > TRIM:
        s = s[:TRIM] + "…"
    return s


def type_name(v: Any) -> str:
    if v is None: return "null"
    if isinstance(v, bool): return "bool"
    if isinstance(v, int): return "int"
    if isinstance(v, float): return "float"
    if isinstance(v, str): return "str"
    if isinstance(v, list): return "list"
    if isinstance(v, dict): return "dict"
    return type(v).__name__


class Node:
    __slots__ = ("kind", "example", "children", "elem_kinds")

    def __init__(self, kind="unknown", example=None):
        self.kind = kind  # node type (dict/list/str/int/…)
        self.example = example  # example (for primitives)
        self.children: Dict[str, "Node"] = {}  # for dict: key -> Node
        self.elem_kinds: List[str] = []  # for list: element types encountered


def merge(dst: Node, src: Node):
    # тип
    if dst.kind == "unknown":
        dst.kind = src.kind
    # пример
    if dst.example is None and src.example is not None:
        dst.example = src.example
    # дети
    for k, ch in src.children.items():
        if k not in dst.children:
            dst.children[k] = Node()
        merge(dst.children[k], ch)
    # типы элементов списка
    for k in src.elem_kinds:
        if k not in dst.elem_kinds:
            dst.elem_kinds.append(k)


def build_schema(x: Any) -> Node:
    n = Node(kind=type_name(x), example=example_str(x))
    if isinstance(x, dict):
        for k, v in x.items():
            n.children.setdefault(k, Node())
            merge(n.children[k], build_schema(v))
    elif isinstance(x, list):
        # we reduce the diagram of elements to a subnode by the key "[*]"
        elem_schema = Node(kind="unknown")
        kinds = []
        for v in x:
            kinds.append(type_name(v))
            merge(elem_schema, build_schema(v))
        n.elem_kinds = sorted(set(kinds))
        n.children["[*]"] = elem_schema
    return n


def print_tree(n: Node, name: str = "(root)", indent: int = 0):
    pad = "  " * indent
    extra = ""
    if n.kind == "list":
        extra = f"  elem_types={n.elem_kinds}"
    ex = f"  example={n.example}" if n.example not in (None, "") else ""
    print(f"{pad}{name} : {n.kind}{extra}{ex}")
    for k in sorted(n.children.keys()):
        print_tree(n.children[k], k, indent + 1)


def iter_messages(data: Any):
    if isinstance(data, dict) and "messages" in data and isinstance(data["messages"], list):
        yield from data["messages"]
    elif isinstance(data, list):
        for x in data:
            if isinstance(x, dict):
                yield x
    else:
        raise SystemExit("Format not recognized: dict with 'messages' or list of messages needed.")


def main():
    s = "../data/sns_msk"

    p = Path(s)
    data = load_json(p)

    root = Node(kind="dict")
    for msg in iter_messages(data):
        merge(root, build_schema(msg))

    # print only the FIRST level keys as nodes, but with their nesting
    for top_key in sorted(root.children.keys()):
        print_tree(root.children[top_key], top_key, 0)


if __name__ == "__main__":
    main()
