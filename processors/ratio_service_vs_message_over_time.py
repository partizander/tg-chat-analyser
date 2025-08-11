from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


@register("ratio_service_vs_message_over_time")
class RatioServiceVsMessageOverTime(BaseProcessor):
    """100% stacked area: monthly share of service vs message."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "ratio_service_vs_message_over_time.png")

        rows: List[Dict[str, str]] = []
        for m in messages:
            date_str = m.get("date")
            typ = m.get("type")
            if isinstance(date_str, str) and isinstance(typ, str):
                rows.append({"date": date_str, "type": typ})

        if not rows:
            return

        df = pd.DataFrame(rows)
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        if df.empty:
            return

        df["month"] = df["date"].dt.to_period("M")

        # Счётчики по месяцам/типам
        counts = (
            df.pivot_table(index="month", columns="type", values="date", aggfunc="size", fill_value=0)
            .sort_index()
        )

        # Полный месячный диапазон + фиксируем порядок колонок
        all_idx = pd.period_range(start=counts.index.min(), end=counts.index.max(), freq="M")
        counts = (
            counts.reindex(all_idx, fill_value=0)
            .reindex(columns=["message", "service"], fill_value=0)
        )

        if counts.empty:
            return

        totals = counts.sum(axis=1).replace(0, 1)
        share = counts.divide(totals, axis=0)

        x = share.index.to_timestamp()

        # Рисуем 100% stacked area
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.stackplot(x, share["message"].values, share["service"].values, labels=["Message", "Service"])

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_ylim(0, 1)
        ax.set_title(f"Service vs message share over time — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Share")
        ax.legend(loc="upper right")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
