from typing import Any, Dict, List, Union
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _text_to_str(t: Union[str, List[Any], Dict[str, Any], None]) -> str:
    if t is None:
        return ""
    if isinstance(t, str):
        return t
    if isinstance(t, list):
        parts: List[str] = []
        for item in t:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                val = item.get("text")
                if isinstance(val, str):
                    parts.append(val)
                elif isinstance(val, list):
                    parts.append(_text_to_str(val))
        return "".join(parts)
    if isinstance(t, dict):
        return _text_to_str(t.get("text"))
    return ""


def _snippet(s: str, n: int) -> str:
    s = " ".join(s.split())
    if len(s) <= n:
        return s
    return s[: max(1, n - 1)] + "…"


def _render_table_image(df: pd.DataFrame, title: str, out_path, col_widths) -> None:
    # 3 rows -> делаем низкую картинку без пустот
    n_rows, n_cols = df.shape
    fig_h = 2.0  # низкая шапка
    fig_w = 10.0
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
    ax.axis("off")

    ax.set_title(title, fontsize=12, pad=4)

    tbl = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        colWidths=col_widths,   # фикс ширины долями от fig_w
        loc="upper center",
        cellLoc="left",
    )
    # Стиль
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(9)
    tbl.scale(1.0, 1.1)

    # Тонкие линии
    for (r, c), cell in tbl.get_celld().items():
        cell.set_linewidth(0.6)

    fig.subplots_adjust(top=0.82)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)


@register("longest_messages_table")
class LongestMessagesTable(BaseProcessor):
    """
    Renders a PNG table (and CSV) of the longest messages.
    Shows exactly 3 rows; text is hard‑truncated to fit.

    Kwargs:
      chat_name: str = ""
      top_n: int = 3                      # always 3 by default
      snippet_len: int = 80               # max chars in snippet (hard cut with ellipsis)
      png_name: str = "longest_messages.png"
      csv_name: str = "longest_messages.csv"
      include_author: bool = True
      include_date: bool = True
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        top_n: int = int(kwargs.get("top_n", 3))
        # форсим ровно 3 строки
        top_n = 3
        snippet_len: int = int(kwargs.get("snippet_len", 80))
        png_name: str = kwargs.get("png_name", "longest_messages.png")
        csv_name: str = kwargs.get("csv_name", "longest_messages.csv")
        include_author: bool = bool(kwargs.get("include_author", True))
        include_date: bool = bool(kwargs.get("include_date", True))

        rows: List[Dict[str, Any]] = []
        for m in messages:
            txt = _text_to_str(m.get("text"))
            if not txt:
                continue
            rows.append({
                "id": m.get("id"),
                "from": m.get("from"),
                "date": m.get("date"),
                "length": len(txt),
                "snippet": _snippet(txt, snippet_len),
            })
        if not rows:
            return

        df = pd.DataFrame(rows).sort_values("length", ascending=False).head(top_n)

        # Колонки для PNG
        cols = ["id", "length", "snippet"]
        if include_author:
            cols.insert(1, "from")
        if include_date:
            insert_pos = 2 if include_author else 1
            cols.insert(insert_pos, "date")
        table_df = df[cols].copy()

        # Приводим типы/формат
        table_df["id"] = table_df["id"].astype("Int64").astype(str)
        table_df["length"] = table_df["length"].astype(int)
        # snippet уже обрезан _snippet

        # Фикс ширины колонок (в долях). Под 3-строчную компактную табличку.
        if include_author and include_date:
            # id, from, date, length, snippet
            col_widths = [0.08, 0.18, 0.18, 0.10, 0.46]
        elif include_author and not include_date:
            # id, from, length, snippet
            col_widths = [0.08, 0.22, 0.10, 0.60]
        elif not include_author and include_date:
            # id, date, length, snippet
            col_widths = [0.08, 0.22, 0.10, 0.60]
        else:
            # id, length, snippet
            col_widths = [0.10, 0.12, 0.78]

        title = f"Longest messages — {chat_name}".strip(" —")
        _render_table_image(table_df, title, self.output_dir / png_name, col_widths)
