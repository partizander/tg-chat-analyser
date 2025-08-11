from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register


@register("first_time_posters_over_time")
class FirstTimePostersOverTime(BaseProcessor):
    """Bar chart: count of users whose first message falls in each month."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "first_time_posters_over_time.png")

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

        # Первая дата сообщения для каждого пользователя
        firsts = df.groupby("from_id")["date"].min()

        # Счётчик "новых авторов" по месяцам
        monthly_new = firsts.groupby(firsts.dt.to_period("M")).size().sort_index()
        if monthly_new.empty:
            return

        x = monthly_new.index.to_timestamp()

        # Рисуем
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        # width в днях (matplotlib date units — дни)
        ax.bar(x, monthly_new.values, width=25)

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"First-time posters over time — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("New posters")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
