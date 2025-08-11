from typing import Any, Dict, List

import pandas as pd
import matplotlib.pyplot as plt

from .base import BaseProcessor
from .registry import register


def _trim_label(s: str, max_len: int = 40) -> str:
    s = (s or "").replace("\n", " ").strip()
    return (s[: max_len - 1] + "…") if len(s) > max_len else s


@register("top_users_by_messages_from_id")
class TopUsersByMessagesFromId(BaseProcessor):
    """
    Leaderboard by message count grouped on from_id.
    Label uses the most frequent 'from' per id (fallback to empty).
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 20))
        out_name: str = kwargs.get("output_name", "top_users_by_messages_from_id.png")

        rows: List[Dict[str, str]] = []
        for m in messages:
            if m.get("type") != "message":
                continue
            fid = m.get("from_id")
            if fid is None:
                continue
            rows.append({
                "from_id": str(fid),
                "from": (m.get("from") or "").strip(),
            })

        if not rows:
            return

        df = pd.DataFrame(rows)

        # Кол-во сообщений на from_id
        cnt = df["from_id"].value_counts().rename_axis("from_id").rename("cnt").to_frame()

        # Самое частое имя на from_id (mode; устойчиво при тай-брейке)
        def most_frequent_name(s: pd.Series) -> str:
            mode = s.mode(dropna=True)
            return str(mode.iloc[0]) if len(mode) else ""

        names = (
            df.groupby("from_id")["from"]
            .apply(most_frequent_name)
            .rename("display_name")
            .to_frame()
        )

        agg = (
            cnt.join(names, how="left")
            .fillna({"display_name": ""})
            .reset_index()
            .sort_values(["cnt", "display_name"], ascending=[False, True])
            .head(top_n)
        )

        labels = [f"{_trim_label(row.display_name) or 'Unknown'} ({row.from_id})"
                  for _, row in agg.iterrows()]

        fig_h = max(6.0, 0.5 * len(agg))
        fig, ax = plt.subplots(figsize=(14, fig_h), dpi=150)
        bars = ax.barh(labels, agg["cnt"].values)
        ax.invert_yaxis()

        # Подписи чисел справа от полос
        ax.bar_label(bars, labels=[str(v) for v in agg["cnt"].values], padding=4, label_type="edge")

        ax.set_title(f"Top users by messages (from_id) — {chat_name}")
        ax.set_xlabel("Messages")
        ax.set_ylabel("User")
        ax.grid(False)

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name)
        plt.close(fig)
