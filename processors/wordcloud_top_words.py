from typing import Any, Dict, List, Iterable
from collections import Counter
import re

import matplotlib.pyplot as plt
from matplotlib import font_manager
from wordcloud import WordCloud

from .base import BaseProcessor
from .registry import register

WORD_RE = re.compile(r"[A-Za-zА-Яа-яЁё]+(?:-[A-Za-zА-Яа-яЁё]+)?", re.U)

BUILTIN_STOPWORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она", "так", "его", "но", "да",
    "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет",
    "о", "из", "ему", "теперь", "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", "был",
    "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может",
    "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без",
    "будто", "чего", "раз", "тоже", "себе", "под", "кто", "этот", "того", "потому", "этого", "какой", "совсем",
    "ним", "здесь", "этом", "один", "почти", "мой", "тем", "чтобы", "нее", "кажется", "него", "были", "куда",
    "зачем", "сказать", "всегда", "тогда", "который", "сколько", "свою", "эта", "тот", "про", "будет", "такой",
    "эти", "каждый", "можно", "при", "ну", "разве", "впрочем",
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "were", "be", "been",
    "it", "that", "this", "as", "at", "by", "from", "but", "if", "not", "no", "yes", "you", "we", "they", "he", "she",
    "i", "me", "my", "our", "your", "their", "them", "his", "her", "its", "do", "does", "did", "so", "than", "then",
    "there", "here", "about", "into", "over", "under", "out", "up", "down", "just", "very", "can", "could", "should",
    "это"
}


def _norm(w: str) -> str:
    return w.lower().replace("ё", "е")


def iter_plain_text(messages: Iterable[Dict[str, Any]]) -> Iterable[str]:
    for m in messages:
        t = m.get("text")
        if isinstance(t, str):
            yield t
        elif isinstance(t, list):
            chunks: List[str] = []
            for part in t:
                if isinstance(part, dict):
                    txt = part.get("text")
                    if isinstance(txt, str):
                        chunks.append(txt)
                elif isinstance(part, str):
                    chunks.append(part)
            if chunks:
                yield " ".join(chunks)


def tokenize(text: str) -> List[str]:
    return [_norm(w) for w in WORD_RE.findall(text)]


@register("wordcloud_top_words")
class WordsCloudTopWords(BaseProcessor):
    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        max_words: int = int(kwargs.get("max_words", 300))
        min_freq: int = int(kwargs.get("min_freq", 2))
        width: int = int(kwargs.get("width", 1600))
        height: int = int(kwargs.get("height", 900))
        background_color: str = kwargs.get("background_color", "white")
        font_path: str | None = kwargs.get("font_path")
        min_len: int = int(kwargs.get("min_len", 2))
        out_name: str = kwargs.get("out_name", "wordcloud_top_words.png")

        extra_stop = {_norm(s) for s in kwargs.get("stopwords", [])}
        stopwords = {_norm(s) for s in BUILTIN_STOPWORDS} | extra_stop

        cnt = Counter()
        for text in iter_plain_text(messages):
            for w in tokenize(text):
                if len(w) < min_len:
                    continue
                if w in stopwords:
                    continue
                if w.isdigit():
                    continue
                cnt[w] += 1

        if min_freq > 1:
            cnt = Counter({k: v for k, v in cnt.items() if v >= min_freq})

        if not cnt:
            print("[wordcloud_top_words] No words passed filters; nothing to plot")
            return

        if not font_path:
            try:
                font_path = font_manager.findfont("DejaVu Sans", fallback_to_default=True)
            except Exception:
                font_path = None

        wc = WordCloud(
            width=width,
            height=height,
            background_color=background_color,
            max_words=max_words,
            prefer_horizontal=0.9,
            collocations=False,
            font_path=font_path
        ).generate_from_frequencies(cnt)

        out_path = self.output_dir / out_name
        out_path.parent.mkdir(parents=True, exist_ok=True)
        plt.figure(figsize=(width / 100, height / 100), dpi=100)
        plt.imshow(wc, interpolation="bilinear")
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(out_path, bbox_inches="tight", pad_inches=0)
        plt.close()

        print(f"[wordcloud_top_words] Saved wordcloud to {out_path}")
