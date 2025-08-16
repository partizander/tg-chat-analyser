from pathlib import Path
from typing import List
from .templates import CSS, JS

IMG_EXTS = {".png", ".jpg", ".jpeg", ".svg", ".webp"}


def build_index_html(root_dir: Path, chat_dirs: List[Path]) -> None:
    """Builds index.html with inline image gallery and lightbox support."""
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'/>",
        "<title>Chat Analytics</title>",
        f"<style>{CSS}</style>",
        "</head><body>",
        "<h1>Chat Analytics</h1>",
    ]

    for chat_dir in chat_dirs:
        parts.append(f"<div class='chat'><h2>{chat_dir.name}</h2>")

        if not chat_dir.exists():
            parts.append("<div class='empty'>no output</div></div>")
            continue

        files = sorted(p for p in chat_dir.iterdir() if p.is_file())

        imgs = [p for p in files if p.suffix.lower() in IMG_EXTS]
        other = [p for p in files if p.suffix.lower() not in IMG_EXTS]

        # Inline image gallery
        if imgs:
            parts.append("<div class='grid'>")
            for img in imgs:
                rel = f"{chat_dir.name}/{img.name}"
                parts.append(
                    "<figure>"
                    f"<img src='{rel}' alt='{img.name}' loading='lazy'/>"
                    "</figure>"
                )
            parts.append("</div>")
        else:
            parts.append("<div class='empty'>no images</div>")

        # Non-image files as links
        if other:
            parts.append("<ul class='files'>")
            for f in other:
                rel = f"{chat_dir.name}/{f.name}"
                parts.append(f"<li><a href='{rel}' target='_blank'>{f.name}</a></li>")
            parts.append("</ul>")

        parts.append("</div>")  # .chat

    # Lightbox container
    parts.append("""
    <div id="lightbox">
      <img src="" alt="Preview"/>
    </div>
    """)
    parts.append(f"<script>{JS}</script>")
    parts.append("</body></html>")

    (root_dir / "index.html").write_text("\n".join(parts), encoding="utf-8")
