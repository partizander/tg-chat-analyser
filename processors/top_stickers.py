from typing import Any, Dict, List, Optional
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from .base import BaseProcessor
from .registry import register


def _pick_emoji_font() -> str:
    """
    Try to pick a system font that supports emoji glyphs.
    Returns a family name (usable in Matplotlib) or empty string.
    """
    candidates = [
        "Apple Color Emoji",   # macOS
        "Segoe UI Emoji",      # Windows
        "Noto Color Emoji",    # Linux
        "Twemoji Mozilla",
        "EmojiOne Color",
    ]
    installed = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in installed:
            return name
    # Slow scan fallback
    for fpath in font_manager.findSystemFonts(fontext="ttf"):
        try:
            name = font_manager.FontProperties(fname=fpath).get_name()
        except Exception:
            continue
        if name in candidates:
            return name
    return ""


def _is_sticker_file(name: Optional[str]) -> bool:
    """True if file name looks like a Telegram sticker file (.webp or .tgs)."""
    if not name or not isinstance(name, str):
        return False
    ext = os.path.splitext(name)[1].lower()
    return ext in (".webp", ".tgs")


def _label_for_sticker(m: Dict[str, Any], keep_ext: bool = False, max_name: int = 24) -> Optional[str]:
    """
    Build a human-friendly label for a sticker:
      1) Prefer sticker_emoji if present (e.g., 👍).
      2) Else fall back to file_name (basename, optionally trimmed).
    Returns None if we cannot derive a label.
    """
    emo = m.get("sticker_emoji")
    if isinstance(emo, str) and emo.strip():
        return emo.strip()

    fname = m.get("file_name") or m.get("file")  # some exports store path in "file"
    if isinstance(fname, str) and _is_sticker_file(fname):
        base = os.path.basename(fname)
        if not keep_ext:
            base = os.path.splitext(base)[0]
        if len(base) > max_name:
            base = base[: max_name - 1] + "…"
        return base

    # Some exports mark media_type == "sticker" without emoji/filename
    if m.get("media_type") == "sticker":
        # As a last resort, try 'file' path even if name check failed
        f = m.get("file")
        if isinstance(f, str):
            base = os.path.basename(f)
            if len(base) > max_name:
                base = base[: max_name - 1] + "…"
            return base or "sticker"

    return None


@register("top_stickers")
class TopStickers(BaseProcessor):
    """
    Leaderboard of most frequent stickers.

    Detection rules (any of):
      - media_type == "sticker"
      - 'sticker_emoji' present
      - 'file_name' (or 'file') with .webp / .tgs extension

    Kwargs:
      chat_name: str = ""                        # title suffix
      top_n: int = 20                            # number of stickers to show
      keep_file_ext: bool = False                # keep extension in file-based labels
      casefold_names: bool = False               # lowercase file-based labels before grouping
      output_name: str = "top_stickers.png"
      csv_name: str | None = None                # e.g., "top_stickers.csv"
      label_fontsize: int = 18                   # emoji/file label font on axis
      axis_fontsize: int = 12
      title_fontsize: int = 14
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 20))
        keep_file_ext: bool = bool(kwargs.get("keep_file_ext", False))
        casefold_names: bool = bool(kwargs.get("casefold_names", False))
        out_name: str = kwargs.get("output_name", "top_stickers.png")
        csv_name = kwargs.get("csv_name", None)
        label_fontsize: int = int(kwargs.get("label_fontsize", 18))
        axis_fontsize: int = int(kwargs.get("axis_fontsize", 12))
        title_fontsize: int = int(kwargs.get("title_fontsize", 14))

        rows = []
        for m in messages:
            # Quick negative checks to skip non-stickers
            mt = m.get("media_type")
            fname = m.get("file_name") or m.get("file")
            has_emj = isinstance(m.get("sticker_emoji"), str) and bool(m.get("sticker_emoji").strip())
            is_stickerish = (mt == "sticker") or has_emj or _is_sticker_file(fname if isinstance(fname, str) else None)
            if not is_stickerish:
                continue

            label = _label_for_sticker(m, keep_ext=keep_file_ext)
            if not label:
                continue
            if casefold_names and label and not any(ch for ch in label if ch.strip() == ""):
                # Only apply lowercasing to non-emoji labels (heuristic)
                if not any("\U0001F000" <= ch <= "\U0001FFFF" for ch in label):
                    label = label.casefold()

            rows.append({"sticker": label, "count": 1})

        if not rows:
            return

        df = pd.DataFrame(rows)
        agg = df.groupby("sticker", as_index=False)["count"].sum()
        agg = agg.sort_values("count", ascending=False).head(top_n)
        if agg.empty:
            return

        # Optional CSV export
        if csv_name:
            agg.to_csv(self.output_dir / csv_name, index=False)

        # Plot horizontal leaderboard
        fig_h = max(6, 0.45 * len(agg))
        fig, ax = plt.subplots(figsize=(14, fig_h), dpi=150)
        ax.barh(agg["sticker"], agg["count"])
        ax.invert_yaxis()

        ax.set_title(f"Top stickers by frequency — {chat_name}", fontsize=title_fontsize)
        ax.set_xlabel("Count", fontsize=axis_fontsize)
        ax.set_ylabel("Sticker", fontsize=axis_fontsize)
        ax.grid(False)

        # Improve emoji rendering on y-ticks
        emoji_font = _pick_emoji_font()
        yticks = ax.get_yticklabels()
        if emoji_font:
            for t in yticks:
                t.set_fontname(emoji_font)
                t.set_fontsize(label_fontsize)
        else:
            for t in yticks:
                t.set_fontsize(label_fontsize)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
