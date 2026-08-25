import random
import re
import unicodedata

MORTY_REPLACEMENTS = [
    "ace",
    "buddy",
    "champ",
    "chief",
    "junior",
    "kiddo",
    "pal",
    "skipper",
    "sport",
    "tiger",
]


def clean_line(text: str) -> str:
    text = normalize_unicode(text)
    text = normalize_new_lines(text)
    text = extract_quoted_scene(text)
    text = normalize_quotes(text)
    text = remove_stage_directions(text)
    text = replace_morty(text)
    text = normalize_spaces(text)
    text = trim_after_last_sentence(text)
    return text.strip()


def normalize_new_lines(text: str) -> str:
    """Replace all newline characters with spaces."""
    return text.replace("\n", " ").replace("\r", " ")


def normalize_unicode(text: str) -> str:
    """Normalize unicode punctuation and quotes."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("—", "-").replace("–", "-")

    return text


def normalize_spaces(text: str) -> str:
    """Normalize multiple spaces and new lines."""
    text = text.replace("\n", " ")
    text = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


def normalize_quotes(text: str) -> str:
    """Remove escaped quotes and convert internal double quotes to single quotes."""
    text = text.replace('\\"', '"')
    text = text.replace("\\'", "'")
    if '"' in text[1:-1]:
        text = text.replace('"', "'")

    return text


def extract_quoted_scene(text: str) -> str:
    """If text contains a quoted segment, extract it."""
    parts = text.split('"')
    if len(parts) >= 3:
        candidate = parts[1].strip()
        if len(candidate) > 100:
            return candidate
    return text


def trim_after_last_sentence(text: str) -> str:
    """Trim everything after the last sentence-ending punctuation."""
    match = re.search(r"[.!?](?!.*[.!?])", text)
    if match:
        return text[: match.end()]
    return text


def replace_morty(text: str) -> str:
    """Replace Morty with a random Rick-style nickname."""
    replacement = random.choice(MORTY_REPLACEMENTS)
    return re.sub(r"\bMorty\b", replacement, text, flags=re.IGNORECASE)


def remove_stage_directions(text: str) -> str:
    """Remove stage directions like ( ... ), [ ... ]."""
    # Remove complete bracketed segments
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)

    # Remove dangling opening brackets at end of line
    text = re.sub(r"\([^)]*$", "", text)
    text = re.sub(r"\[[^\]]*$", "", text)

    # Remove dangling closing brackets at start of line
    text = re.sub(r"^[^\(]*\)", "", text)
    text = re.sub(r"^[^\[]*\]", "", text)

    return text
