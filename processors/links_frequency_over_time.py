from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from .base import BaseProcessor
from .registry import register


def _count_links_in_entities(entities: Any) -> int:
    """Return how many items in text_entities have type == 'link'."""
    if not isinstance(entities, list):
        return 0
    cnt = 0
    for e in entities:
        if isinstance(e, dict) and e.get("type") == "link":
            cnt += 1
    return cnt


@register("links_frequency_over_time")
class LinksFrequencyOverTime(BaseProcessor):
    """
    Plots link mention frequency by month as a line chart.

    Data source: text_entities[*].type == "link"

    Kwargs:
      chat_name: str = ""                         # title suffix
      count_mode: str = "links"                   # "links" -> count all links;
                                                  # "messages" -> count messages that have >=1 link
      output_name: str = "links_frequency.png"
      show_points: bool = True                    # draw markers on the line
      ma_window: int | None = None                # moving average window in months (e.g., 3)
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        count_mode: str = str(kwargs.get("count_mode", "links")).lower()
        out_name: str = kwargs.get("output_name", "links_frequency.png")
        show_points: bool = bool(kwargs.get("show_points", True))
        ma_window = kwargs.get("ma_window", None)
        if isinstance(ma_window, str) and ma_window.isdigit():
            ma_window = int(ma_window)
        elif not isinstance(ma_window, int):
            ma_window = None

        # Collect (date -> value) rows
        rows: List[Dict[str, Any]] = []
        for m in messages:
            date_str = m.get("date")
            if not isinstance(date_str, str):
                continue
            date = pd.to_datetime(date_str, errors="coerce")
            if pd.isna(date):
                continue

            entities = m.get("text_entities")
            links_cnt = _count_links_in_entities(entities)

            if count_mode == "messages":
                val = 1 if links_cnt > 0 else 0
            else:  # "links"
                val = links_cnt

            if val > 0:
                rows.append({"date": date, "value": val})

        if not rows:
            return

        df = pd.DataFrame(rows)
        df["month"] = df["date"].dt.to_period("M")

        # Aggregate by month
        s = df.groupby("month")["value"].sum().sort_index()
        if s.empty:
            return

        # Optional moving average (on the monthly series)
        if ma_window and ma_window > 1:
            ma = s.rolling(ma_window, min_periods=1).mean()
        else:
            ma = None

        # Convert PeriodIndex to Timestamp for plotting
        idx = s.index.to_timestamp()

        # Plot
        fig, ax = plt.subplots(figsize=(14, 6), dpi=150)
        ax.plot(idx, s.values, marker="o" if show_points else None)

        # Add moving average series if requested
        if ma is not None:
            ax.plot(idx, ma.values)  # same color policy (no explicit colors)

        # X axis formatting: months
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        title_suffix = "links" if count_mode == "links" else "messages with links"
        ax.set_title(f"Link mention frequency over time — {chat_name} ({title_suffix})")
        ax.set_xlabel("Month")
        ax.set_ylabel("Count")

        ax.grid(False)
        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
