from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


@register("top_reactions")
class TopReactions(BaseProcessor):
    """
    Builds a bar chart of the most popular reaction emojis.

    Expects Telegram export messages where each message may contain:
      reactions: [
        {"emoji": "👍", "count": 3},
        {"emoji": "❤️", "count": 1},
        ...
      ]

    Kwargs:
      chat_name: str = ""        # title suffix
      top_n: int = 20            # take top-N emojis
      output_name: str = "top_reactions.png"
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 20))
        out_name: str = kwargs.get("output_name", "top_reactions.png")

        # Collect (emoji -> total count). If 'count' missing, treat as 1.
        rows = []
        for m in messages:
            reactions = m.get("reactions")
            if not reactions or not isinstance(reactions, list):
                continue
            for r in reactions:
                if not isinstance(r, dict):
                    continue
                emoji = r.get("emoji")
                if not emoji:
                    continue
                cnt = r.get("count")
                try:
                    cnt_val = int(cnt) if cnt is not None else 1
                except Exception:
                    cnt_val = 1
                if cnt_val <= 0:
                    continue
                rows.append({"emoji": str(emoji), "count": cnt_val})

        if not rows:
            return

        df = pd.DataFrame(rows)
        agg = df.groupby("emoji", as_index=False)["count"].sum()
        agg = agg.sort_values("count", ascending=False).head(top_n)

        if agg.empty:
            return

        # Build a vertical bar chart (emojis as X labels)
        fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
        ax.bar(agg["emoji"], agg["count"])

        ax.set_title(f"Most popular reaction emojis — {chat_name}")
        ax.set_xlabel("Emoji")
        ax.set_ylabel("Reactions (count)")

        # Improve label readability in case of many emojis
        plt.setp(ax.get_xticklabels(), rotation=0, ha="center")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
