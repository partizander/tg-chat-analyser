from typing import Any, Dict, List, Union
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _text_to_str(t: Union[str, List[Any], Dict[str, Any], None]) -> str:
    """Convert Telegram export 'text' field (str | list | dict) to a plain string."""
    if t is None:
        return ""
    if isinstance(t, str):
        return t
    if isinstance(t, list):
        parts: List[str] = []
        for item in t:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                val = item.get("text")
                if isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, list):
                    parts.append(_text_to_str(val))
        return "".join(parts)
    if isinstance(t, dict):
        return _text_to_str(t.get("text"))
    return ""


def _build_label(m: Dict[str, Any], mode: str, snippet_len: int) -> str:
    """
    Build a label for the X-axis:
      - mode="id"     -> "#<id>"
      - mode="snippet"-> first N chars of text (fallback to #id)
      - mode="both"   -> "#<id> — snippet"
    """
    mid = m.get("id")
    snippet = _text_to_str(m.get("text")).strip()
    if snippet:
        # collapse whitespace/newlines and trim
        snippet = " ".join(snippet.split())
        if len(snippet) > snippet_len:
            snippet = snippet[: max(1, snippet_len - 1)] + "…"

    if mode == "id":
        return f"#{mid}" if mid is not None else (snippet or "(no text)")
    if mode == "snippet":
        return snippet or (f"#{mid}" if mid is not None else "(no text)")
    # both
    base = f"#{mid}" if mid is not None else ""
    return (base + (" — " if base and snippet else "") + (snippet or "")).strip() or "(no text)"


@register("top_messages_by_reactions")
class TopMessagesByReactions(BaseProcessor):
    """
    Plots top messages by total number of reactions.

    For each message we sum reactions[*].count (if 'count' is missing, treat as 1).
    Then we select top-N and draw a horizontal bar chart.

    Kwargs:
      chat_name: str = ""                      # title suffix
      top_n: int = 20                          # number of messages to show
      label_mode: str = "both"                 # "id" | "snippet" | "both"
      snippet_len: int = 60                    # max chars for snippet in labels
      annotate: bool = True                    # draw value labels on bars
      output_name: str = "top_messages_by_reactions.png"
      csv_name: str | None = "top_messages_by_reactions.csv"  # save details (id,text,count,date)
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 20))
        label_mode: str = str(kwargs.get("label_mode", "both")).lower()
        snippet_len: int = int(kwargs.get("snippet_len", 60))
        annotate: bool = bool(kwargs.get("annotate", True))
        out_name: str = kwargs.get("output_name", "top_messages_by_reactions.png")

        # Collect per-message reaction totals
        rows = []
        for m in messages:
            reactions = m.get("reactions")
            if not reactions or not isinstance(reactions, list):
                continue
            total = 0
            for r in reactions:
                if not isinstance(r, dict):
                    continue
                cnt = r.get("count")
                try:
                    total += int(cnt) if cnt is not None else 1
                except Exception:
                    total += 1
            if total <= 0:
                continue

            label = _build_label(m, label_mode, snippet_len)
            rows.append({
                "id": m.get("id"),
                "date": m.get("date"),
                "text": _text_to_str(m.get("text")),
                "label": label,
                "reactions": total,
            })

        if not rows:
            return

        df = pd.DataFrame(rows)
        df = df.sort_values("reactions", ascending=False).head(top_n)

        if df.empty:
            return

        # Horizontal bar chart (labels on Y-axis handle long text better)
        fig, ax = plt.subplots(figsize=(14, max(6, 0.6 * len(df))), dpi=150)
        ax.barh(df["label"], df["reactions"])
        ax.invert_yaxis()  # most reacted on top

        ax.set_title(f"Top messages by reactions — {chat_name}")
        ax.set_xlabel("Total reactions")
        ax.set_ylabel("Message")

        # Optional numeric labels at the end of bars
        if annotate:
            for i, (v) in enumerate(df["reactions"].values):
                ax.text(v, i, f" {v}", va="center")

        ax.grid(False)
        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
