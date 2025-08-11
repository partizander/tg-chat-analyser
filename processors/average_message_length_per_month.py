from typing import Any, Dict, List, Union

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


def _text_to_str(t: Union[str, List[Any], Dict[str, Any], None]) -> str:
    """Extract plain text from Telegram export's 'text' field of mixed types."""
    if t is None:
        return ""
    if isinstance(t, str):
        return t
    if isinstance(t, list):
        parts: List[str] = []
        for it in t:
            if isinstance(it, str):
                parts.append(it)
            elif isinstance(it, dict):
                parts.append(_text_to_str(it.get("text")))
        return "".join(parts)
    if isinstance(t, dict):
        return _text_to_str(t.get("text"))
    return ""


@register("average_message_length_per_month")
class AvgMessageLengthPerMonth(BaseProcessor):
    """Line chart: average text length per month (characters)."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "average_message_length_per_month.png")

        rows: List[Dict[str, Union[str, int]]] = []
        for m in messages:
            date_str = m.get("date")
            txt = _text_to_str(m.get("text"))
            if isinstance(date_str, str) and txt:
                rows.append({"date": date_str, "len": len(txt)})

        if not rows:
            return

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Bucket by month
        df["month"] = df["date"].dt.to_period("M")

        # Average length per month
        monthly_avg = df.groupby("month")["len"].mean().sort_index()
        if monthly_avg.empty:
            return

        x = monthly_avg.index.to_timestamp()

        # Plot
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.plot(x, monthly_avg.values, marker="o")

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Average message length per month — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Avg length (chars)")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
