from dataclasses import dataclass
from pathlib import Path
from typing import List
from yaml import safe_load

ALLOWED_CHANNEL_TYPES = {"anonymous", "public", "unknown"}


@dataclass
class ChatCfg:
    file: str
    name: str
    channel_type: str


@dataclass
class AppCfg:
    input_dir: Path
    output_dir: Path
    graphics: List[str]
    chats: List[ChatCfg]
    need_make_web_page: bool


def load_app_cfg(cfg_path: Path) -> AppCfg:
    if not cfg_path.exists():
        raise SystemExit(f"Config file not found: {cfg_path}")
    raw = safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    out_dir = raw.get("output_dir", "./results")
    if out_dir.strip("./") == "resuls":
        out_dir = "./results"

    input_dir = Path(raw.get("input_dir", "./data"))
    output_dir = Path(out_dir)

    graphics = [x for x in (raw.get("graphics", []) or [])]

    chats_raw = raw.get("chats", [])
    if not isinstance(chats_raw, list) or not chats_raw:
        raise SystemExit("config.chats must be a non-empty list")

    chats: List[ChatCfg] = []
    for i, c in enumerate(chats_raw, 1):
        file = str(c.get("file", "")).strip()
        name = str(c.get("name", file)).strip()
        channel_type = str(c.get("channel_type", "unknown")).strip()
        if not file:
            raise SystemExit(f"Chat #{i}: 'file' is empty")
        if channel_type not in ALLOWED_CHANNEL_TYPES:
            channel_type = "unknown"
        chats.append(ChatCfg(file=file, name=name, channel_type=channel_type))

    need_web = bool(raw.get("need_make_web_page", False))
    return AppCfg(input_dir=input_dir, output_dir=output_dir,
                  graphics=graphics, chats=chats, need_make_web_page=need_web)
