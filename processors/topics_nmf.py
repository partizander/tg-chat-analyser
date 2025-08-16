# processors/topics_nmf.py
from typing import Any, Dict, List, Iterable, Optional, Set
import re
from textwrap import fill

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import numpy as np
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import TfidfVectorizer

from .base import BaseProcessor
from .registry import register

# ------------------------- tokenization & stopwords -------------------------

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]+(?:-[A-Za-zА-Яа-яЁё]+)?", re.U)

RU_STOP: Set[str] = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она", "так", "его", "но", "да",
    "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет",
    "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", "был",
    "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может",
    "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без",
    "будто", "чего", "раз", "тоже", "себе", "под", "кто", "этот", "того", "потому", "этого", "какой", "совсем",
    "ним", "здесь", "этом", "один", "почти", "мой", "тем", "чтобы", "нее", "кажется", "него", "были", "куда",
    "зачем", "сказать", "всегда", "тогда", "который", "сколько", "свою", "эта", "тот", "про", "будет", "такой",
    "эти", "каждый", "можно", "при", "ну", "разве", "впрочем",
}
EN_STOP: Set[str] = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "were", "be", "been",
    "it", "that", "this", "as", "at", "by", "from", "but", "if", "not", "no", "yes", "you", "we", "they", "he", "she",
    "i", "me", "my", "our", "your", "their", "them", "his", "her", "its", "do", "does", "did", "so", "than", "then",
    "there", "here", "about", "into", "over", "under", "out", "up", "down", "just", "very", "can", "could", "should",
}
TECH_STOP: Set[str] = {"http", "https", "www", "com", "org", "ru"}
STOPWORDS: Set[str] = RU_STOP | EN_STOP | TECH_STOP


def _norm(w: str) -> str:
    return w.lower().replace("ё", "е")


def iter_plain_text(messages: Iterable[Dict[str, Any]]) -> Iterable[str]:
    """Extract visible text from Telegram export messages."""
    for m in messages:
        if m.get("type") != "message":
            continue
        t = m.get("text")
        if isinstance(t, str):
            yield t
        elif isinstance(t, list):
            parts: List[str] = []
            for p in t:
                if isinstance(p, dict):
                    txt = p.get("text")
                    if isinstance(txt, str):
                        parts.append(txt)
                elif isinstance(p, str):
                    parts.append(p)
            if parts:
                yield " ".join(parts)


def simple_tokenize(s: str) -> List[str]:
    """Split text into lowercase tokens using WORD_RE."""
    return [_norm(w) for w in WORD_RE.findall(s)]


# Optional lemmatization (auto-enabled if pymorphy2 is available).
try:
    import pymorphy2  # type: ignore

    _MORPH = pymorphy2.MorphAnalyzer()


    def lemmatize(tokens: List[str]) -> List[str]:
        out: List[str] = []
        for w in tokens:
            if w.isdigit():
                continue
            p = _MORPH.parse(w)
            out.append(p[0].normal_form if p else w)
        return out
except Exception:
    _MORPH = None


    def lemmatize(tokens: List[str]) -> List[str]:
        return tokens


def preprocess(texts: List[str], use_lemma: bool, min_len: int, extra_stop: Set[str]) -> List[str]:
    """Tokenize, optionally lemmatize, filter by length/stopwords/digits, then join."""
    sw = {_norm(s) for s in (STOPWORDS | extra_stop)}
    out: List[str] = []
    for t in texts:
        toks = simple_tokenize(t)
        if use_lemma:
            toks = lemmatize(toks)
        toks = [w for w in toks if len(w) >= min_len and w not in sw and not w.isdigit()]
        out.append(" ".join(toks))
    return out


def _clip_word(w: str, max_len: int) -> str:
    """Prevent ultra-long tokens from breaking layout."""
    if len(w) <= max_len:
        return w
    base = w.split("-")[0][:max_len]
    return base + "…"


@register("topics_nmf")
class TopicsNMF(BaseProcessor):
    """
    Render ONE PNG with a simple single-column table:
    - one row per topic;
    - soft wrap inside each row;
    - horizontal separators of equal width;
    - adaptive figure size (no overflow).
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        # ---- parameters ----
        n_topics: int = int(kwargs.get("n_topics", 8))
        max_features: int = int(kwargs.get("max_features", 30000))
        min_df = kwargs.get("min_df", 3)
        max_df: float = float(kwargs.get("max_df", 0.9))
        use_lemma: bool = bool(kwargs.get("use_lemmatization", False))
        min_len: int = int(kwargs.get("min_len", 3))
        extra_stop: Set[str] = {str(s).lower() for s in kwargs.get("stopwords", [])}

        topk_table: int = int(kwargs.get("topk_table", 5))  # how many strongest topics
        table_words: int = max(1, int(kwargs.get("table_words", 8)))
        max_word_len: int = max(6, int(kwargs.get("max_word_len", 18)))
        wrap_chars: int = max(30, int(kwargs.get("wrap_chars", 48)))  # target row width (chars)
        font_size: int = int(kwargs.get("font_size", 13))
        title: Optional[str] = kwargs.get("title")
        out_name: str = kwargs.get("out_name", "topics_nmf.png")

        # ---- data ----
        texts = list(iter_plain_text(messages))
        if not texts:
            print("[topics_nmf] No texts; nothing to process")
            return
        cleaned = preprocess(texts, use_lemma, min_len, extra_stop)

        vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df,
            tokenizer=str.split,
            lowercase=False,
            norm="l2",
        )
        X = vectorizer.fit_transform(cleaned)
        if X.shape[0] == 0 or X.shape[1] == 0:
            print("[topics_nmf] Empty matrix after vectorization")
            return

        nmf = NMF(n_components=n_topics, init="nndsvd", random_state=42, max_iter=500)
        W = nmf.fit_transform(X)  # docs x topics
        H = nmf.components_  # topics x terms
        vocab = np.array(vectorizer.get_feature_names_out())

        # strongest topics
        topic_strength = W.sum(axis=0)
        k = max(1, min(topk_table, n_topics))
        top_idx = np.argsort(topic_strength)[::-1][:k]

        # lines (one per topic), pre-wrapped
        lines: List[str] = []
        for rank, ti in enumerate(top_idx, start=1):
            idx = np.argsort(H[ti])[::-1][:table_words]
            words = [_clip_word(w, max_word_len) for w in vocab[idx]]
            raw = f"{rank}. " + ", ".join(words)
            wrapped = fill(raw, width=wrap_chars, break_long_words=False, break_on_hyphens=False)
            lines.append(wrapped)

        # ---- sizing (inches) ----
        # Empirical char/line sizing for DejaVu Sans
        char_w_in = 0.11 * (font_size / 12.0)
        line_h_in = 0.26 * (font_size / 12.0)

        content_w_in = wrap_chars * char_w_in
        row_vert_pad_in = 0.22  # vertical padding inside each row
        row_heights = [(s.count("\n") + 1) * line_h_in + row_vert_pad_in for s in lines]

        left_right_margin = 0.9
        top_margin = 1.0 if title else 0.7
        bottom_margin = 0.7

        fig_w = left_right_margin * 2 + content_w_in
        fig_h = top_margin + bottom_margin + sum(row_heights)

        # ---- draw ----
        fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=150)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        if title:
            ax.set_title(title, loc="left", fontsize=font_size + 1, pad=10)

        # Convert to axis units
        inner_w_in = content_w_in
        inner_h_in = sum(row_heights)
        x0_ax = left_right_margin / fig_w
        y0_ax = bottom_margin / fig_h
        w_ax = inner_w_in / fig_w

        # cumulative y for each row (top-to-bottom)
        y_cursor_in = top_margin + inner_h_in
        for i, (txt, row_h_in) in enumerate(zip(lines, row_heights)):
            # row frame (full width)
            y_cursor_in -= row_h_in
            x_ax = x0_ax
            y_ax = y0_ax + (y_cursor_in - top_margin) / fig_h
            h_ax = row_h_in / fig_h

            # top line for the first row and bottom line for each row -> clean separators
            # draw rect with no fill to get top and bottom edges
            ax.add_patch(Rectangle((x_ax, y_ax), width=w_ax, height=h_ax, fill=False, linewidth=1.2))

            # text padding
            pad_x_ax = 0.015  # relative to axis (small left indent)
            pad_y_ax = 0.03  # relative to row height
            ax.text(
                x_ax + pad_x_ax,
                y_ax + h_ax - pad_y_ax,
                txt,
                ha="left",
                va="top",
                fontsize=font_size,
                family="DejaVu Sans",
            )

        fig.tight_layout(pad=0.2)
        out_path = self.output_dir / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(out_path, bbox_inches="tight")
        plt.close(fig)
        print(f"[topics_nmf] Saved topics list PNG to {out_path}")
