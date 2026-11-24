"""Small, deterministic TTS text cleaner; no LLM calls and no stored speech.

The dictionary is user-owned configuration, never generated from web content.
"""
import json
import re
import unicodedata


def dictionary(raw):
    if not raw:
        return {}
    if len(raw) > 4096:
        raise ValueError("pronunciation dictionary exceeds 4096 bytes")
    result = json.loads(raw)
    if not isinstance(result, dict) or len(result) > 32:
        raise ValueError("pronunciation dictionary must contain at most 32 entries")
    for key, value in result.items():
        if (not isinstance(key, str) or not isinstance(value, str)
                or not 1 <= len(key) <= 40 or not 1 <= len(value) <= 100
                or any(ord(c) < 32 for c in key + value)):
            raise ValueError("invalid pronunciation dictionary entry")
    return result


def prepare_text(text, mapping=None):
    if not isinstance(text, str):
        raise ValueError("invalid text")
    prepared = unicodedata.normalize("NFC", text)
    # Only turn human-readable Markdown links into their visible titles.
    prepared = re.sub(r"\[([^\]\n]{1,120})\]\(https?://[^\s)]{1,500}\)", r"\1", prepared)
    prepared = re.sub(r"(?<!\w)(?:\*\*|__|\x60)(?=\w)|(?<=\w)(?:\*\*|__|\x60)(?!\w)", "", prepared)
    prepared = re.sub(r"[\r\n\t]+", " ", prepared)
    prepared = re.sub(r" {2,}", " ", prepared).strip()
    for term, spoken in sorted((mapping or {}).items(), key=lambda kv: -len(kv[0])):
        # Match complete abbreviations/words, without replacing substrings.
        pattern = r"(?<!\w)" + re.escape(term) + r"(?!\w)"
        prepared = re.sub(pattern, lambda _match: spoken, prepared)
    if not 0 < len(prepared) <= 900:
        raise ValueError("processed speech length outside bounds")
    return prepared


def split_sentences(text, max_chars=180):
    """Break a long reply at sentence/word boundaries; never split inside words."""
    if max_chars < 40:
        raise ValueError("max_chars must be at least 40")
    words = text.split()
    parts, current = [], ""
    for word in words:
        if len(word) > max_chars:
            raise ValueError("a word exceeds the segment limit")
        proposal = current + (" " if current else "") + word
        if len(proposal) > max_chars:
            if current:
                parts.append(current)
            current = word
        else:
            current = proposal
        if current.endswith((".", "!", "?", ";")) and len(current) >= 45:
            parts.append(current)
            current = ""
    if current:
        parts.append(current)
    return parts
