from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt

from .base import BaseProcessor
from .registry import register


@register("messages_per_hour")
class MessagesPerHour(BaseProcessor):
    """Bar chart: messages by hour of day (0–23)."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "messages_per_hour.png")

        # Даты сообщений
        dates = pd.to_datetime(
            [m["date"] for m in messages if isinstance(m.get("date"), str)],
            errors="coerce"
        ).dropna()

        if dates.empty:
            return

        # Количество сообщений по часам
        counts = (
            pd.Series(1, index=dates, dtype="int64")
            .groupby(dates.hour)
            .sum()
            .reindex(range(24), fill_value=0)
        )

        # Рисуем
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.bar(counts.index, counts.values)
        ax.set_title(f"Messages per hour — {chat_name}")
        ax.set_xlabel("Hour (0–23)")
        ax.set_ylabel("Messages")
        ax.set_xticks(range(0, 24, 2))
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
