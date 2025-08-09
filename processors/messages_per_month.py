from pathlib import Path
from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base import BaseProcessor
from .registry import register


@register("messages_per_month")
class MessagesPerMonth(BaseProcessor):
    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        # Convert message dates to pandas datetime
        dates = pd.to_datetime(
            [m.get("date") for m in messages if isinstance(m.get("date"), str)],
            errors="coerce",
        ).dropna()
        if dates.empty:
            return

        # Group by month in chronological order
        s = (
            pd.Series(1, index=dates)
            .groupby(dates.to_period("M"))
            .sum()
            .sort_index()
        )

        # Convert PeriodIndex to Timestamp for plotting
        idx = s.index.to_timestamp()
        vals = s.values

        # Create bar chart
        fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
        ax.bar(idx, vals, width=25)  # width ~25 days to avoid overlap

        # Show labels every 6 months
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

        # Rotate labels for better readability
        fig.autofmt_xdate()

        # Titles and labels
        ax.set_title(f"Messages per Month — {kwargs.get('chat_name', '')}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Messages")

        # No grid for a cleaner look
        ax.grid(False)

        # Save to file
        fig.tight_layout()
        fig.savefig(self.output_dir / "messages_per_month.png")
        plt.close(fig)
