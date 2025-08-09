from pathlib import Path
from typing import Any, Dict, List, Union
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _text_to_str(t: Union[str, List[Any], Dict[str, Any], None]) -> str:
    """Converts the 'text' field from a Telegram export into a plain string."""
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


@register("top_authors_by_text_length")
class TopAuthorsByTextLength(BaseProcessor):
    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        top_n: int = int(kwargs.get("top_n", 20))
        chat_name: str = kwargs.get("chat_name", "")

        if not messages:
            return

        # Calculate total text length per author
        rows = []
        for m in messages:
            author = m.get("from")
            if not isinstance(author, str) or not author.strip():
                continue
            txt = _text_to_str(m.get("text"))
            if not txt:
                continue
            rows.append({"from": author, "len": len(txt)})

        if not rows:
            return

        df = pd.DataFrame(rows)
        agg = df.groupby("from", as_index=False)["len"].sum()
        agg = agg.sort_values("len", ascending=False).head(top_n)

        if agg.empty:
            return

        # Horizontal bar chart
        fig, ax = plt.subplots(figsize=(14, 8), dpi=150)
        ax.barh(agg["from"], agg["len"])
        ax.invert_yaxis()  # top authors first

        ax.set_title(f"Top users by total message length — {chat_name}")
        ax.set_xlabel("Total text length (characters)")
        ax.set_ylabel("Author")
        ax.grid(False)

        fig.tight_layout()
        out_name = kwargs.get("output_name", "top_authors_by_text_length.png")
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
