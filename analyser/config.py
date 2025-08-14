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
class GraphicCfg:
    """Single graphic configuration."""
    id: str
    anon: bool  # whether this graphic should run for anonymous channels


@dataclass
class AppCfg:
    input_dir: Path
    output_dir: Path
    graphics: List[GraphicCfg]
    chats: List[ChatCfg]
    need_make_web_page: bool


def load_app_cfg(cfg_path: Path) -> AppCfg:
    """
    Load application config from YAML.

    Supports two graphic formats:
      - short form: "id"
      - object form: { id: "...", anon: true|false }
    Backward compatibility: per-graphic key "run_on_anonymous" is also accepted.
    Defaults can be provided as:
      defaults:
        run_on_anonymous: false
    """
    if not cfg_path.exists():
        raise SystemExit(f"Config file not found: {cfg_path}")

    raw = safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    # I/O dirs
    input_dir = Path(raw.get("input_dir", "./data"))
    output_dir = Path(raw.get("output_dir", "./results"))

    # Defaults
    defaults = raw.get("defaults") or {}
    default_anon = bool(defaults.get("run_on_anonymous", False))

    # Graphics
    graphics_raw = raw.get("graphics", [])
    if not isinstance(graphics_raw, list) or not graphics_raw:
        raise SystemExit("config.graphics must be a non-empty list")

    graphics: List[GraphicCfg] = []
    for i, g in enumerate(graphics_raw, 1):
        if isinstance(g, str):
            gid = g.strip()
            if not gid:
                raise SystemExit(f"graphics[{i}]: empty id")
            graphics.append(GraphicCfg(id=gid, anon=default_anon))
        elif isinstance(g, dict):
            gid = str(g.get("id", "")).strip()
            if not gid:
                raise SystemExit(f"graphics[{i}]: 'id' is required")
            # prefer 'anon', fallback to 'run_on_anonymous', then default
            if "anon" in g:
                anon = bool(g.get("anon"))
            elif "run_on_anonymous" in g:
                anon = bool(g.get("run_on_anonymous"))
            else:
                anon = default_anon
            graphics.append(GraphicCfg(id=gid, anon=anon))
        else:
            raise SystemExit(f"graphics[{i}]: invalid item type {type(g).__name__}")

    # Chats
    chats_raw = raw.get("chats", [])
    if not isinstance(chats_raw, list) or not chats_raw:
        raise SystemExit("config.chats must be a non-empty list")

    chats: List[ChatCfg] = []
    for i, c in enumerate(chats_raw, 1):
        if not isinstance(c, dict):
            raise SystemExit(f"chats[{i}]: must be an object")
        file = str(c.get("file", "")).strip()
        name = str(c.get("name", file)).strip()
        channel_type = str(c.get("channel_type", "unknown")).strip()
        if not file:
            raise SystemExit(f"chats[{i}]: 'file' is empty")
        if channel_type not in ALLOWED_CHANNEL_TYPES:
            channel_type = "unknown"
        chats.append(ChatCfg(file=file, name=name, channel_type=channel_type))

    need_web = bool(raw.get("need_make_web_page", False))

    return AppCfg(
        input_dir=input_dir,
        output_dir=output_dir,
        graphics=graphics,
        chats=chats,
        need_make_web_page=need_web,
    )
