from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path


class MessagesPerHour:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def run(self, messages):
        # Группируем по часу (0–23)
        hours = [
            datetime.fromisoformat(m["date"]).hour
            for m in messages
            if m.get("type") == "message"
        ]
        counts = Counter(hours)
        # Гарантируем наличие всех часов
        items = [(h, counts.get(h, 0)) for h in range(24)]

        x_labels = [str(k) for k, _ in items]
        y = [v for _, v in items]

        fig, ax = plt.subplots(figsize=(14, 6))
        bars = ax.bar(range(len(x_labels)), y, color="#F5A623", edgecolor="black", linewidth=0.5)

        ax.set_title("Messages per hour", fontsize=18, pad=16)
        ax.set_xlabel("Hour of day", fontsize=12)
        ax.set_ylabel("Messages", fontsize=12)

        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, fontsize=9)

        ax.yaxis.grid(True, linestyle=":", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Подписываем пики — топ-5 часов
        top_n = min(5, len(y))
        top_idx = sorted(range(len(y)), key=lambda i: y[i], reverse=True)[:top_n]
        for i in top_idx:
            bar = bars[i]
            h = y[i]
            ax.annotate(f"{h}", xy=(bar.get_x() + bar.get_width() / 2, h),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9, fontweight="bold")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / "messages_per_hour.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        print(f"Saved chart to {out_path}")
