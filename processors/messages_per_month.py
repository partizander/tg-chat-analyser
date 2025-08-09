from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register

def _ym(ts: str) -> str:
    # 'YYYY-MM'
    try:
        return ts[:7]
    except Exception:
        return "unknown"

@register("messages_per_month")
class MessagesPerMonth(BaseProcessor):
    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        vals = []
        for m in messages:
            ts = m.get("date")
            if isinstance(ts, str) and len(ts) >= 7:
                vals.append(ts[:7])  # 'YYYY-MM'

        if not vals:
            return

        # индекс уже = 'YYYY-MM', просто сортируем по индексу
        s = pd.Series(vals, name="ym").value_counts().sort_index()

        out_csv = self.output_dir / "messages_per_month.csv"
        s.to_csv(out_csv, header=["count"])

        plt.figure()
        s.plot(kind="bar")
        plt.title(f"Messages per Month — {kwargs.get('chat_name', '')}")
        plt.xlabel("Month")
        plt.ylabel("Messages")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(self.output_dir / "messages_per_month.png", dpi=150)
        plt.close()
