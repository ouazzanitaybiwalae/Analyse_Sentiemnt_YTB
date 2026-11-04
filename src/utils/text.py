"""Text cleaning shared by training AND inference (must stay identical)."""
import re

URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"[@#]\w+")
NON_TEXT_RE = re.compile(r"[^a-z0-9\s']")   # drops emojis & special chars, keeps apostrophes (don't, it's)
SPACES_RE = re.compile(r"\s+")


def clean_text(text) -> str:
    """Lowercase, remove URLs / mentions / hashtags / special chars / emojis."""
    if text is None:
        return ""
    text = str(text).lower()
    text = URL_RE.sub(" ", text)
    text = MENTION_RE.sub(" ", text)
    text = NON_TEXT_RE.sub(" ", text)
    return SPACES_RE.sub(" ", text).strip()
