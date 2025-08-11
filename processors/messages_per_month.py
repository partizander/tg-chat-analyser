from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


@register("messages_per_month")
class MessagesPerMonthV2(BaseProcessor):
    """Bar chart of messages per month (chronological)."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "messages_per_month.png")

        # Parse dates
        dates = pd.to_datetime(
            [m.get("date") for m in messages if isinstance(m.get("date"), str)],
            errors="coerce"
        ).dropna()

        if dates.empty:
            return

        # Count per month
        s = (
            pd.Series(1, index=dates, dtype="int64")
            .groupby(dates.to_period("M"))
            .sum()
            .sort_index()
        )

        # Ensure continuous monthly range (show zeros for gaps)
        all_idx = pd.period_range(start=s.index.min(), end=s.index.max(), freq="M")
        s = s.reindex(all_idx, fill_value=0)

        x = s.index.to_timestamp()

        # Plot
        fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
        # width in days (matplotlib date units are days)
        ax.bar(x, s.values, width=25)

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Messages per month — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Messages")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
