from pathlib import Path
from typing import List

def build_index_html(root_dir: Path, chat_dirs: List[Path]) -> None:
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'><title>Chat Analytics</title>",
        "<style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;margin:24px}"
        "h1{margin:0 0 16px}h2{margin:24px 0 8px}ul{margin:8px 0 24px}"
        "li{margin:4px 0}a{color:#0366d6;text-decoration:none}a:hover{text-decoration:underline}</style>",
        "</head><body><h1>Chat Analytics</h1>",
    ]
    for chat_dir in chat_dirs:
        rel = chat_dir.name
        parts.append(f"<h2>{rel}</h2><ul>")
        if chat_dir.exists():
            files = sorted(p for p in chat_dir.iterdir() if p.is_file())
            if files:
                for f in files:
                    parts.append(f"<li><a href='{rel}/{f.name}' target='_blank'>{f.name}</a></li>")
            else:
                parts.append("<li><em>no files</em></li>")
        else:
            parts.append("<li><em>no output</em></li>")
        parts.append("</ul>")
    parts.append("</body></html>")
    (root_dir / "index.html").write_text("\n".join(parts), encoding="utf-8")
