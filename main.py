#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from typing import List, Dict, Any
import shutil

from analyser.config import load_app_cfg
from analyser.io_loader import find_input_file, load_messages
from processors.registry import REGISTRY
from analyser.webindex import build_index_html


def run_processor(name: str, messages, out_dir: Path, context: Dict[str, Any]) -> None:
    """Instantiate and run a processor by its registry id."""
    cls = REGISTRY.get(name)
    if not cls:
        print(f"[warn] unknown processor: {name} (skip)")
        return
    try:
        inst = cls(output_dir=out_dir, **context)
    except TypeError:
        inst = cls(output_dir=out_dir)
    try:
        inst.run(messages, **context)
    except TypeError:
        inst.run(messages)


def clear_dir_contents(p: Path) -> None:
    """Delete directory completely and recreate it."""
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m analyser.main <config.yaml>")
        sys.exit(1)

    cfg_path = Path(sys.argv[1])
    cfg = load_app_cfg(cfg_path)

    if not cfg.input_dir.exists():
        raise SystemExit(f"input_dir does not exist: {cfg.input_dir}")

    # Clear root output dir once
    clear_dir_contents(cfg.output_dir)

    chat_dirs: List[Path] = []
    graphics_list = (
        ", ".join(f"{g.id}{'[anon]' if getattr(g, 'anon', False) else ''}" for g in (cfg.graphics or []))
        if getattr(cfg, "graphics", None) else "(none)"
    )

    print(f"[info] input_dir:  {cfg.input_dir}")
    print(f"[info] output_dir: {cfg.output_dir}")
    print(f"[info] graphics:   {graphics_list}")
    print(f"[info] chats:      {len(cfg.chats)}")

    for chat in cfg.chats:
        in_file = find_input_file(cfg.input_dir, chat.file)
        if not in_file:
            print(f"[warn] not found: {cfg.input_dir}/{chat.file}.json")
            continue

        out_dir = cfg.output_dir / chat.file
        out_dir.mkdir(parents=True, exist_ok=True)
        chat_dirs.append(out_dir)

        print(f"[info] processing: {chat.name} ({chat.channel_type}) <- {in_file.name}")
        messages = load_messages(in_file)

        ctx: Dict[str, Any] = {
            "chat_file": chat.file,
            "chat_name": chat.name,
            "channel_type": chat.channel_type,
        }

        is_anon = (chat.channel_type == "anonymous")

        for g in cfg.graphics:
            if is_anon and not getattr(g, "anon", False):
                print(f"[skip anonymous] {g.id}")
                continue
            run_processor(g.id, messages, out_dir, ctx)

    if getattr(cfg, "need_make_web_page", False):
        build_index_html(cfg.output_dir, chat_dirs)
        print(f"[info] built: {cfg.output_dir / 'index.html'}")

    print("[done]")


if __name__ == "__main__":
    main()
