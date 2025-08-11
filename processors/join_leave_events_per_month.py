from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from .base import BaseProcessor
from .registry import register

JOIN_ACTIONS = {"invite", "join_group_by_link", "migrate_to_supergroup"}
LEAVE_ACTIONS = {"remove_member", "leave", "kick_user", "kick"}


@register("join_leave_events_per_month")
class JoinLeaveEventsPerMonth(BaseProcessor):
    """Two-line chart: joins vs leaves per month."""

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "join_leave_events_per_month.png")

        join_dates: List[str] = []
        leave_dates: List[str] = []

        for m in messages:
            if m.get("type") != "service":
                continue
            action = str(m.get("action") or "")
            date_str = m.get("date")
            if not isinstance(date_str, str):
                continue

            if action in JOIN_ACTIONS:
                join_dates.append(date_str)
            if action in LEAVE_ACTIONS:
                leave_dates.append(date_str)

        if not join_dates and not leave_dates:
            return

        # Parse to datetime
        jd = pd.to_datetime(join_dates, errors="coerce")
        ld = pd.to_datetime(leave_dates, errors="coerce")

        # Convert to monthly PeriodIndex
        pj = jd.dropna().to_period("M")
        pl = ld.dropna().to_period("M")

        if len(pj) == 0 and len(pl) == 0:
            return

        # Build continuous monthly index from min to max period
        start = min([p for p in [pj.min() if len(pj) else None,
                                 pl.min() if len(pl) else None] if p is not None], default=None)
        end = max([p for p in [pj.max() if len(pj) else None,
                               pl.max() if len(pl) else None] if p is not None], default=None)
        if start is None or end is None:
            return

        all_idx = pd.period_range(start=start, end=end, freq="M")

        # Monthly counts reindexed to full range
        s_j = pj.value_counts().reindex(all_idx, fill_value=0).sort_index()
        s_l = pl.value_counts().reindex(all_idx, fill_value=0).sort_index()

        # X-axis as timestamps
        x = all_idx.to_timestamp()

        # Plot
        fig, ax = plt.subplots(figsize=(12, 5), dpi=150)
        ax.plot(x, s_j.values, marker="o", label="Joins")
        ax.plot(x, s_l.values, marker="o", label="Leaves")

        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
        fig.autofmt_xdate()

        ax.set_title(f"Join/leave events per month — {chat_name}")
        ax.set_xlabel("Month")
        ax.set_ylabel("Events")
        ax.grid(False)
        ax.legend()

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
