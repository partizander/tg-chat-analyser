from typing import Any, Dict, List
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from .base import BaseProcessor
from .registry import register


@register("new_members_activity")
class NewMembersActivity(BaseProcessor):
    """
    Shows activity of new members joining the chat.
    Sources:
      - service messages with action == 'invite'
      - messages with 'inviter' field
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        out_name: str = kwargs.get("output_name", "new_members_activity.png")

        join_dates = []

        for m in messages:
            # Only service messages or invites
            if m.get("type") == "service" and m.get("action") == "invite":
                join_dates.append(m.get("date"))
            elif "inviter" in m and m.get("inviter"):
                join_dates.append(m.get("date"))

        if not join_dates:
            return

        # Convert to datetime and group
        df = pd.DataFrame({"date": join_dates})
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])

        # Group by month
        df["month"] = df["date"].dt.to_period("M")
        monthly_counts = df.groupby("month").size().reset_index(name="count")

        # Plot
        fig, ax = plt.subplots(figsize=(10, 6), dpi=150)
        ax.plot(monthly_counts["month"].astype(str), monthly_counts["count"], marker="o")

        ax.set_xlabel("Month")
        ax.set_ylabel("New members")
        ax.set_title(f"New members activity over time — {chat_name}")
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.xticks(rotation=45)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
