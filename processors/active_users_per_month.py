from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


@register("active_users_per_month")
class ActiveUsersPerMonth(BaseProcessor):
    """Line chart: unique from_id per month."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "active_users_per_month.png")

        rows: List[Dict[str, str]] = []
        for m in messages:
            date_str = m.get("date")
            from_id = m.get("from_id")
            if isinstance(date_str, str) and from_id is not None:
                rows.append({"date": date_str, "from_id": str(from_id)})

        if not rows:
            return

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Month buckets
        df["month"] = df["date"].dt.to_period("M")

        # Unique authors per month
        monthly_unique = (
            df.groupby("month")["from_id"].nunique().sort_index()
        )

        if monthly_unique.empty:
            return

        x = monthly_unique.index.to_timestamp()

        # Plot
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.plot(x, monthly_unique.values, marker="o")

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Active users per month — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Unique users")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
