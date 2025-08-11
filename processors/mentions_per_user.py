from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt

from .base import BaseProcessor
from .registry import register


def _extract_mentions(entities: Any) -> List[str]:
    """Извлекает @упоминания из text_entities."""
    out: List[str] = []
    if isinstance(entities, list):
        for e in entities:
            if isinstance(e, dict) and e.get("type") in ("mention", "mention_name"):
                t = e.get("text")
                if isinstance(t, str) and t.strip():
                    out.append(t.strip())
    return out


@register("mentions_per_user")
class MentionsPerUser(BaseProcessor):
    """Horizontal bar: most mentioned handles (@user)."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 20))
        out_name: str = kwargs.get("output_name", "mentions_per_user.png")

        rows: List[Dict[str, Any]] = []
        for m in messages:
            for handle in _extract_mentions(m.get("text_entities")):
                rows.append({"handle": handle, "cnt": 1})

        if not rows:
            return

        df = pd.DataFrame(rows)
        agg = (
            df.groupby("handle", as_index=False)["cnt"]
            .sum()
            .sort_values("cnt", ascending=False)
            .head(top_n)
        )

        if agg.empty:
            return

        fig_height = max(6, 0.45 * len(agg))
        fig, ax = plt.subplots(figsize=(14, fig_height), dpi=150)
        ax.barh(agg["handle"], agg["cnt"])
        ax.invert_yaxis()

        ax.set_title(f"Mentions per user — {chat_name}")
        ax.set_xlabel("Mentions")
        ax.set_ylabel("Handle")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
