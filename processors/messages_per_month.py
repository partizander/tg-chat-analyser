from collections import Counter
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path


class MessagesPerMonth:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def run(self, messages):
        # Группируем по месяцу (YYYY-MM)
        months = [
            datetime.fromisoformat(m["date"]).date().strftime("%Y-%m")
            for m in messages
            if m.get("type") == "message"
        ]
        counts = Counter(months)
        items = sorted(counts.items())
        x_labels = [k for k, _ in items]
        y = [v for _, v in items]

        fig, ax = plt.subplots(figsize=(18, 6))
        bars = ax.bar(range(len(x_labels)), y, color="#4A90E2", edgecolor="black", linewidth=0.5)

        ax.set_title("Messages per month", fontsize=18, pad=16)
        ax.set_xlabel("Month", fontsize=12)
        ax.set_ylabel("Messages", fontsize=12)

        # Подписи на оси X
        step = max(1, len(x_labels) // 18)
        ax.set_xticks(range(0, len(x_labels), step))
        ax.set_xticklabels(
            [x_labels[i] for i in range(0, len(x_labels), step)],
            rotation=45, ha="right", fontsize=9
        )

        # Сетка и стиль
        ax.yaxis.grid(True, linestyle=":", alpha=0.4)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        # Подписываем бары — если мало месяцев, подписываем все
        if len(x_labels) <= 36:
            for bar in bars:
                h = bar.get_height()
                if h:
                    ax.annotate(f"{h}", xy=(bar.get_x() + bar.get_width() / 2, h),
                                xytext=(0, 3), textcoords="offset points",
                                ha="center", va="bottom", fontsize=8)
        else:
            # Иначе только топ-10 месяцев
            top_n = min(10, len(y))
            top_idx = sorted(range(len(y)), key=lambda i: y[i], reverse=True)[:top_n]
            for i in top_idx:
                bar = bars[i]
                h = y[i]
                ax.annotate(f"{h}", xy=(bar.get_x() + bar.get_width() / 2, h),
                            xytext=(0, 3), textcoords="offset points",
                            ha="center", va="bottom", fontsize=9, fontweight="bold")

        # Сохраняем
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / "messages_per_month.png"
        plt.tight_layout()
        plt.savefig(out_path, dpi=150)
        plt.close()
        print(f"Saved chart to {out_path}")
