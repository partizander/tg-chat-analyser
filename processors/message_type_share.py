from typing import Any, Dict, List, Union
import pandas as pd
import matplotlib.pyplot as plt
from .base import BaseProcessor
from .registry import register


def _categorize_message(m: Dict[str, Any], include_service: bool) -> str:
    """
    Returns a normalized category for a Telegram export message.

    Categories:
      text, photo, video, gif, sticker, voice, audio, document,
      poll, location, contact, service, other
    """
    mtype = m.get("type")
    media = (m.get("media_type") or "").lower()

    # Service events (e.g., pin_message, join_group_by_link, etc.)
    if mtype != "message":
        return "service" if include_service else ""

    # Detect explicit media types from 'media_type'
    if media:
        if "photo" in media:
            return "photo"
        if media in ("video", "video_file", "video_message"):
            return "video"
        if media == "animation":
            return "gif"
        if media == "sticker":
            return "sticker"
        if media in ("voice_message", "voice"):
            return "voice"
        if media in ("audio_file", "audio"):
            return "audio"
        if media in ("document", "file"):
            return "document"
        if media == "poll":
            return "poll"
        if media == "location":
            return "location"
        if media == "contact":
            return "contact"

    # Polls can exist without 'media_type' but with 'poll' field
    if "poll" in m:
        return "poll"

    # Document/file detection without 'media_type'
    if "file" in m and m.get("file"):
        return "document"

    # Stickers can be detected by 'sticker_emoji' field
    if "sticker_emoji" in m:
        return "sticker"

    # Regular text (including emoji, links, etc.)
    text = m.get("text")
    if (isinstance(text, str) and text.strip()) or (isinstance(text, list) and text):
        return "text"

    # If nothing matches
    return "other"


@register("message_type_share")
class MessageTypeShare(BaseProcessor):
    """
    Generates a pie chart of message type distribution.

    Kwargs:
      chat_name: str = "" — chat name for the title
      include_service: bool = False — include service events
      top_k: int = 9 — keep top-k categories, merge the rest into 'Other'
      output_name: str = "message_type_share.png" — output filename
    """

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        if not messages:
            return

        chat_name: str = kwargs.get("chat_name", "")
        include_service: bool = bool(kwargs.get("include_service", False))
        top_k: int = int(kwargs.get("top_k", 9))
        out_name: str = kwargs.get("output_name", "message_type_share.png")

        # Categorize each message
        cats: List[str] = []
        for m in messages:
            c = _categorize_message(m, include_service=include_service)
            if c:  # empty string means excluded service event
                cats.append(c)

        if not cats:
            return

        # Count frequency of each category
        s = pd.Series(cats).value_counts()

        # Merge small categories into "Other"
        if len(s) > top_k:
            major = s.iloc[:top_k]
            other = pd.Series({"Other": s.iloc[top_k:].sum()})
            s = pd.concat([major, other])

        # Prepare labels with percentage and absolute count
        total = int(s.sum())
        labels = [f"{name} — {cnt / total * 100:.1f}% ({cnt})" for name, cnt in s.items()]

        # Create pie chart
        fig, ax = plt.subplots(figsize=(10, 10), dpi=150)
        wedges, texts = ax.pie(s.values, startangle=90)

        # Place legend outside the chart
        ax.legend(wedges, labels, title="Types", loc="center left", bbox_to_anchor=(1, 0.5))

        ax.set_title(f"Message type share — {chat_name}")
        ax.axis("equal")  # Equal aspect ratio to make the pie circular

        fig.tight_layout()
        fig.savefig(self.output_dir / out_name, bbox_inches="tight")
        plt.close(fig)
