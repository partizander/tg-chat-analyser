from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


@register("pinned_messages_per_month")
class PinnedMessagesPerMonth(BaseProcessor):
    """Bar chart: action='pin_message' per month."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "pinned_messages_per_month.png")

        # Собираем даты пинов
        dates_raw: List[str] = []
        for m in messages:
            if m.get("type") == "service" and m.get("action") == "pin_message":
                d = m.get("date")
                if isinstance(d, str):
                    dates_raw.append(d)

        if not dates_raw:
            return

        dates = pd.to_datetime(dates_raw, errors="coerce").dropna()
        if dates.empty:
            return

        # Счётчик пинов по месяцам
        s = (
            pd.Series(1, index=dates, dtype="int64")
            .groupby(dates.to_period("M"))
            .sum()
            .sort_index()
        )

        # Непрерывный месячный диапазон (заполним нулями)
        all_idx = pd.period_range(start=s.index.min(), end=s.index.max(), freq="M")
        s = s.reindex(all_idx, fill_value=0)

        x = s.index.to_timestamp()

        # Рисуем
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.bar(x, s.values, width=25)  # width в днях

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Pinned messages per month — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Pins")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
