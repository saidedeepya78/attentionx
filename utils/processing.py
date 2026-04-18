"""
AttentionX — Processing utilities
Handles: input validation, text cleaning, result formatting
"""

import re


# ── Input Validation ────────────────────────────────────────────────────────

MIN_CONTENT_LENGTH = 200   # characters
MAX_CONTENT_LENGTH = 50_000  # characters (~10,000 words)


def validate_content(text: str) -> tuple[bool, str]:
    """
    Validate that content is suitable for analysis.
    Returns (is_valid: bool, error_message: str)
    """
    text = text.strip()

    if not text:
        return False, "Content cannot be empty."

    if len(text) < MIN_CONTENT_LENGTH:
        return False, (
            f"Content is too short ({len(text)} characters). "
            f"Please provide at least {MIN_CONTENT_LENGTH} characters for meaningful analysis."
        )

    if len(text) > MAX_CONTENT_LENGTH:
        return False, (
            f"Content is too long ({len(text):,} characters). "
            f"Please trim to under {MAX_CONTENT_LENGTH:,} characters."
        )

    return True, ""


# ── Text Cleaning ───────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Light cleaning: normalize whitespace, remove null bytes.
    Preserves punctuation and structure.
    """
    # Remove null bytes
    text = text.replace("\x00", "")

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse 3+ consecutive blank lines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Collapse multiple spaces into one (but preserve newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    return text.strip()


def truncate_for_display(text: str, max_chars: int = 300) -> str:
    """Truncate text for card preview, ending at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return truncated + "…"


# ── Result Formatting ───────────────────────────────────────────────────────

HOOK_TYPE_LABELS = {
    "bold_claim": "Bold Claim",
    "curiosity_gap": "Curiosity Gap",
    "shocking_stat": "Shocking Stat",
    "question": "Question Hook",
    "contrarian": "Contrarian Take",
    "unknown": "Hook",
}

EMOTION_COLORS = {
    "Surprise":      {"bg": "#FFF3CD", "border": "#F0A500", "text": "#7D5A00"},
    "Inspiration":   {"bg": "#D4EDDA", "border": "#28A745", "text": "#155724"},
    "Curiosity":     {"bg": "#CCE5FF", "border": "#0D6EFD", "text": "#003D80"},
    "Relatability":  {"bg": "#E2CFEE", "border": "#8B34AC", "text": "#4B0070"},
    "Urgency":       {"bg": "#F8D7DA", "border": "#DC3545", "text": "#721C24"},
    "Humor":         {"bg": "#FFF0CC", "border": "#FFC107", "text": "#7B5B00"},
    "Empathy":       {"bg": "#D1ECF1", "border": "#17A2B8", "text": "#0C5460"},
}

DEFAULT_EMOTION_STYLE = {"bg": "#F0F0F0", "border": "#999999", "text": "#333333"}


def get_emotion_style(emotion_tag: str) -> dict:
    """Return color scheme for an emotion tag."""
    for key, style in EMOTION_COLORS.items():
        if key.lower() in emotion_tag.lower():
            return style
    return DEFAULT_EMOTION_STYLE


def get_hook_type_label(hook_type: str) -> str:
    return HOOK_TYPE_LABELS.get(hook_type, "Hook")


def get_virality_bar(score: int) -> str:
    """Return a Unicode progress bar for virality score."""
    filled = round(score / 10 * 10)
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar}  {score}/10"


def format_word_count(text: str) -> str:
    count = len(text.split())
    return f"{count:,} words"