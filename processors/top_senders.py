# chatviz/processors/top_senders.py
from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register

TOP_N = 20  # number of senders to display

@register("top_senders")
class TopSenders(BaseProcessor):
    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        # Collect names from "from" (ignore service messages without it)
        senders = [m.get("from") for m in messages if isinstance(m.get("from"), str)]
        if not senders:
            return

        # Count and keep top N
        s = pd.Series(senders, name="sender").value_counts().head(TOP_N)

        # Sort ascending so largest bar ends up at the top in barh
        counts = s.sort_values(ascending=True)
        labels = [str(x) for x in counts.index.tolist()]
        values = counts.values

        fig, ax = plt.subplots(figsize=(16, 9), dpi=200)
        ax.barh(range(len(values)), values)

        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels)

        ax.set_title(f"Top {TOP_N} Senders — {kwargs.get('chat_name', '')}")
        ax.set_xlabel("Messages")
        ax.set_ylabel("Sender")

        for i, v in enumerate(values):
            ax.text(v, i, f" {int(v)}", va="center", ha="left", fontsize=9)

        fig.tight_layout()
        fig.savefig(self.output_dir / "top_senders.png", bbox_inches="tight")
        plt.close(fig)
