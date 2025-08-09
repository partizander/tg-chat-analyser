from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _to_hour(ts: str) -> int:
    # ts: 'YYYY-MM-DDTHH:MM:SS'
    try:
        return int(ts[11:13])
    except Exception:
        return -1


@register("messages_per_hour")
class MessagesPerHour(BaseProcessor):
    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        hours = []
        for m in messages:
            ts = m.get("date")
            if isinstance(ts, str):
                h = _to_hour(ts)
                if 0 <= h <= 23:
                    hours.append(h)
        if not hours:
            return

        s = pd.Series(hours, name="hour").value_counts().sort_index()

        plt.figure()
        s.plot(kind="bar")
        plt.title(f"Messages per Hour — {kwargs.get('chat_name', '')}")
        plt.xlabel("Hour")
        plt.ylabel("Messages")
        plt.tight_layout()
        plt.savefig(self.output_dir / "messages_per_hour.png", dpi=150)
        plt.close()
