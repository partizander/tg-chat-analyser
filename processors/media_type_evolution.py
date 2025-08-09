from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base import BaseProcessor
from .registry import register


@register("media_type_evolution")
class MediaTypeEvolution(BaseProcessor):
    """
    Plots a stacked area chart showing the evolution of different media types over time.

    Kwargs:
      chat_name: str = "" — chat name for the title
      top_k: int = 7 — keep top-k media types, merge the rest into "Other"
      output_name: str = "media_type_evolution.png" — output filename
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        top_k: int = int(kwargs.get("top_k", 7))
        out_name: str = kwargs.get("output_name", "media_type_evolution.png")

        # Prepare DataFrame with date and media_type
        rows = []
        for m in messages:
            date_str = m.get("date")
            media_type = m.get("media_type")
            if not date_str or not isinstance(date_str, str):
                continue
            if not media_type:
                continue  # skip non-media messages
            rows.append({
                "date": pd.to_datetime(date_str, errors="coerce"),
                "media_type": str(media_type).lower()
            })

        if not rows:
            return

        df = pd.DataFrame(rows).dropna(subset=["date"])
        if df.empty:
            return

        # Group by month and media_type
        df["month"] = df["date"].dt.to_period("M")
        grouped = df.groupby(["month", "media_type"]).size().reset_index(name="count")

        # Pivot table: index = month, columns = media_type, values = count
        pivot = grouped.pivot(index="month", columns="media_type", values="count").fillna(0)

        # Keep top_k media types and merge others into "Other"
        total_counts = pivot.sum(axis=0).sort_values(ascending=False)
        top_media = total_counts.head(top_k).index
        pivot["Other"] = pivot.loc[:, ~pivot.columns.isin(top_media)].sum(axis=1)
        pivot = pivot.loc[:, list(top_media) + ["Other"]]

        # Convert PeriodIndex to Timestamp for plotting
        pivot.index = pivot.index.to_timestamp()

        # Plot stacked area chart
        fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
        ax.stackplot(
            pivot.index,
            [pivot[col] for col in pivot.columns],
            labels=pivot.columns
        )

        # Format x-axis as months
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Media type evolution over time — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Messages count")

        ax.legend(loc="upper left")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
