from typing import Any, Dict, List, Optional
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _normalize_bot_name(v: Any, keep_at: bool = False) -> Optional[str]:
    """
    Normalize 'via_bot' value from Telegram export.
    Examples of possible shapes:
      - "QuizBot"
      - "@QuizBot"
      - {"username": "QuizBot"}   # rare, but be robust
    Returns a cleaned, case-sensitive name or None if not usable.
    """
    name: Optional[str] = None
    if isinstance(v, str):
        name = v.strip()
    elif isinstance(v, dict):
        u = v.get("username")
        if isinstance(u, str):
            name = u.strip()

    if not name:
        return None
    name = name if keep_at else name.lstrip("@")
    # empty after stripping -> ignore
    return name or None


@register("top_bots_by_messages")
class TopBotsByMessages(BaseProcessor):
    """
    Builds a bar chart of the most active bots (by count of messages sent via bots).

    Counts messages where 'via_bot' is present and non-empty.

    Kwargs:
      chat_name: str = ""                         # title suffix
      top_n: int = 20                             # number of bots to show
      keep_at: bool = False                       # keep leading '@' in labels
      output_name: str = "top_bots_by_messages.png"
      csv_name: str | None = None                 # e.g. "top_bots_by_messages.csv"
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 20))
        keep_at: bool = bool(kwargs.get("keep_at", False))
        out_name: str = kwargs.get("output_name", "top_bots_by_messages.png")
        csv_name = kwargs.get("csv_name", None)

        # Collect bot names from 'via_bot'
        rows = []
        for m in messages:
            bot_raw = m.get("via_bot")
            bot = _normalize_bot_name(bot_raw, keep_at=keep_at)
            if not bot:
                continue
            rows.append({"bot": bot, "count": 1})

        if not rows:
            return

        df = pd.DataFrame(rows)
        agg = df.groupby("bot", as_index=False)["count"].sum()
        agg = agg.sort_values("count", ascending=False).head(top_n)

        if agg.empty:
            return

        # Optional CSV export
        if csv_name:
            agg.to_csv(self.output_dir / csv_name, index=False)

        # Horizontal bar chart
        fig_h = max(6, 0.45 * len(agg))
        fig, ax = plt.subplots(figsize=(14, fig_h), dpi=150)
        ax.barh(agg["bot"], agg["count"])
        ax.invert_yaxis()  # most active on top

        ax.set_title(f"Most active bots — {chat_name}")
        ax.set_xlabel("Messages via bot")
        ax.set_ylabel("Bot")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
