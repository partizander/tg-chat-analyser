import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_input_file(base: Path, stem: str) -> Optional[Path]:
    p = base / f"{stem}"
    if p.exists():
        return p

    return None


def load_messages(path: Path) -> List[Dict[str, Any]]:
    msgs: List[Dict[str, Any]] = []

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("messages"), list):
            return data["messages"]
        if isinstance(data, list):
            return data
        return []

    # jsonl/ndjson
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                msgs.append(json.loads(line))
            except Exception:
                pass

    return msgs
