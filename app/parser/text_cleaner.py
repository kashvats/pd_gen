"""Prepares dialogue text for natural speech synthesis while preserving prosodic punctuation."""

import re


def clean_text_for_speech(text: str) -> str:
    """Cleans markdown formatting while preserving punctuation crucial for prosody."""
    if not text:
        return ""

    cleaned = text

    # Strip markdown links [text](url) -> text
    cleaned = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', cleaned)

    # Strip markdown bold/italic: ***text*** -> text, **text** -> text, *text* -> text, _text_ -> text
    cleaned = re.sub(r'\*\*\*([^*]+)\*\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)
    cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)
    cleaned = re.sub(r'___([^_]+)___', r'\1', cleaned)
    cleaned = re.sub(r'__([^_]+)__', r'\1', cleaned)
    cleaned = re.sub(r'_([^_]+)_', r'\1', cleaned)

    # Strip inline code `code` -> code
    cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)

    # Strip strikethrough ~~text~~ -> text
    cleaned = re.sub(r'~~([^~]+)~~', r'\1', cleaned)

    # Strip bracketed metadata/directive tags: [emotion: ...], [preset: ...], [whisper], [sigh], [PAUSE: ...], etc.
    cleaned = re.sub(r'\[(?:emotion|preset|style|tone|whisper|sigh|laugh|applause|music|pause|sfx|sound|vibe|direction|speed|rate|pitch)[^\]]*\]', '', cleaned, flags=re.IGNORECASE)
    # Strip any standalone bracketed directives at the start or end of text: e.g. [passionate], [robotic]
    # Literal bracketed words are content; only documented directives are removed.

    # Convert em-dashes and en-dashes to standard dash with natural breathing spaces
    cleaned = cleaned.replace("—", " — ").replace("–", " – ")

    # Normalize multiple whitespace, tabs, and newlines into single spaces for fluid speech
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    return cleaned

