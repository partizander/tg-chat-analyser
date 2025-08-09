from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from .base import BaseProcessor
from .registry import register


@register("poll_lifetime_vs_votes")
class PollLifetimeVsVotes(BaseProcessor):
    """
    Plots poll lifetime vs total voters.

    Fields:
      - poll.closed: ISO date string when poll closed
      - date: ISO date string when poll created
      - poll.total_voters: number of voters

    X-axis: lifetime (hours)
    Y-axis: total voters
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "poll_lifetime_vs_votes.png")

        rows = []
        for m in messages:
            poll = m.get("poll")
            if not isinstance(poll, dict):
                continue

            # Parse creation date
            date_str = m.get("date")
            closed_str = poll.get("closed")
            total_voters = poll.get("total_voters")

            if not date_str or not closed_str or total_voters is None:
                continue

            try:
                created_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                closed_dt = datetime.fromisoformat(closed_str.replace("Z", "+00:00"))
            except Exception:
                continue

            lifetime_hours = (closed_dt - created_dt).total_seconds() / 3600.0
            if lifetime_hours < 0:
                continue

            try:
                total_voters = int(total_voters)
            except Exception:
                continue

            rows.append({
                "lifetime_hours": lifetime_hours,
                "total_voters": total_voters
            })

        if not rows:
            return

        df = pd.DataFrame(rows)

        # Plot scatter
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        ax.scatter(df["lifetime_hours"], df["total_voters"], alpha=0.7)

        ax.set_xlabel("Poll lifetime (hours)")
        ax.set_ylabel("Total voters")
        ax.set_title(f"Poll lifetime vs total voters — {chat_name}")

        ax.grid(True, linestyle="--", alpha=0.5)
        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
