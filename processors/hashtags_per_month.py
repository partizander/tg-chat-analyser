from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


def _count_hashtags(entities: Any) -> int:
    """Count hashtag entities in Telegram's text_entities list."""
    if not isinstance(entities, list):
        return 0
    count = 0
    for e in entities:
        if isinstance(e, dict) and e.get("type") == "hashtag":
            count += 1
    return count


@register("hashtags_per_month")
class HashtagsPerMonth(BaseProcessor):
    """Line chart: number of hashtags per month."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "hashtags_per_month.png")

        rows: List[Dict[str, Any]] = []
        for m in messages:
            date_str = m.get("date")
            if not isinstance(date_str, str):
                continue
            cnt = _count_hashtags(m.get("text_entities"))
            if cnt > 0:
                rows.append({"date": date_str, "n": cnt})

        if not rows:
            return

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        if df.empty:
            return

        df["month"] = df["date"].dt.to_period("M")
        monthly = df.groupby("month")["n"].sum().sort_index()
        if monthly.empty:
            return

        x = monthly.index.to_timestamp()

        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.plot(x, monthly.values, marker="o")

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Hashtags per month — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Hashtags")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
