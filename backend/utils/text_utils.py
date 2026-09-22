import re
import uuid
import unicodedata


def sanitize_user_message(message: str) -> str:
    if not message:
        return ""

    message = remove_html_tags(message)
    message = normalize_unicode(message)
    message = remove_control_chars(message)
    message = remove_zero_width(message)
    message = remove_sql(message)
    message = collapse_repeated_chars(message)
    message = normalize_spaces(message)

    return message.strip()


def extract_reply(full_text: str) -> str:
    if re.search(r"user:", full_text, flags=re.IGNORECASE):
        full_text = re.split(r"user:", full_text, flags=re.IGNORECASE)[-1]

    if re.search(r"rick:", full_text, flags=re.IGNORECASE):
        reply = re.split(r"rick:", full_text, flags=re.IGNORECASE)[-1].strip()
    else:
        reply = full_text.strip()

    reply = normalize_unicode(reply)
    if is_structured_output(reply):
        return reply

    reply = remove_html_tags(reply)
    reply = remove_stage_directions(reply)
    reply = normalize_spaces(reply)
    reply = normalize_quotes(reply)
    reply = trim_to_last_sentence(reply)
    reply = clean_artifacts(reply)
    reply = trim_fake_speaker_turns(reply)

    return reply or "Whatever."


def trim_fake_speaker_turns(reply: str) -> str:
    pattern = r"(?:^|\s)([A-Za-z0-9_\-]{2,20})\s*:"

    match = re.search(pattern, reply)
    if not match:
        return reply

    cutoff_index = match.start()
    cleaned = reply[:cutoff_index].strip()

    return cleaned


def is_structured_output(text: str) -> bool:
    if "```" in text:
        return True
    if "\n" in text:
        return True
    if re.search(r"[{}();=<>]", text):
        return True
    if re.search(r'"\w+":', text):
        return True

    return False


def trim_to_last_sentence(text: str) -> str:
    match = re.search(r"[.!?](?!.*[.!?])", text)
    if match:
        return text[: match.end()].strip()

    return text.strip()


def normalize_spaces(text: str) -> str:
    text = text.replace("\n", " ")
    text = re.sub(r"([a-z])([A-Z][a-z])", r"\1 \2", text)
    text = re.sub(r"\s{2,}", " ", text)

    return text.strip()


def normalize_quotes(text: str) -> str:
    text = text.replace('\\"', '"')
    text = text.replace("\\'", "'")
    if '"' in text[1:-1]:
        text = text.replace('"', "'")

    return text


def clean_artifacts(text: str) -> str:
    text = re.sub(r"\*[^*]+\*", "", text)
    text = re.sub(r"\[[^\]]+\]", "", text)
    text = re.sub(r"\{[^}]+\}", "", text)

    text = re.sub(r"\.{3,}", ".", text)
    text = re.sub(r'("{2,})', '"', text)
    text = re.sub(r"('{2,})", "'", text)

    text = re.sub(r"^[\.\,\;\:]+", "", text).strip()
    text = re.sub(r"\s{2,}", " ", text).strip()

    return text


def remove_stage_directions(text: str) -> str:
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)

    text = re.sub(r"\([^)]*$", "", text)
    text = re.sub(r"\[[^\]]*$", "", text)

    text = re.sub(r"^[^\(]*\)", "", text)
    text = re.sub(r"^[^\[]*\]", "", text)

    return text


def normalize_unicode(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("—", "-").replace("–", "-")
    text = text.replace("\x00", "")

    return text


def remove_sql(text: str) -> str:
    text = re.sub(r"--+", "-", text)
    text = re.sub(r";{2,}", ".", text)
    return text


def remove_control_chars(text: str) -> str:
    return re.sub(r"[\x00-\x08\x0B-\x1F\x7F]", "", text)


def remove_zero_width(text: str) -> str:
    return re.sub(r"[\u200B-\u200F\uFEFF]", "", text)


def remove_html_tags(text: str) -> str:
    return re.sub(r"</?[a-zA-Z][^>]*>", "", text)


def collapse_repeated_chars(text: str) -> str:
    return re.sub(r"(.)\1{20,}", r"\1\1\1", text)


def generate_id() -> str:
    return uuid.uuid4().hex[:8]
