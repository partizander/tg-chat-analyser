from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt

from .base import BaseProcessor
from .registry import register


@register("messages_by_weekday")
class MessagesByWeekday(BaseProcessor):
    """Bar chart of messages by weekday (Mon–Sun)."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "messages_by_weekday.png")

        # Parse dates
        dates = pd.to_datetime(
            [m.get("date") for m in messages if isinstance(m.get("date"), str)],
            errors="coerce",
        ).dropna()

        if len(dates) == 0:
            return

        dates = pd.DatetimeIndex(dates)

        # Count messages per weekday (0=Mon ... 6=Sun)
        s = pd.Series(1, index=dates)
        by_wd = s.groupby(s.index.dayofweek).sum()
        by_wd = by_wd.reindex(range(7), fill_value=0)

        # Plot
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
        ax.bar(labels, by_wd.values)

        ax.set_title(f"Messages by weekday — {chat_name}")
        ax.set_xlabel("Weekday")
        ax.set_ylabel("Messages")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
