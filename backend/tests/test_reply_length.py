from backend.config import settings
from backend.services.model.reply_service import get_reply_length


def test_reply_length_short():
    assert get_reply_length("hi") == settings.model_min_tokens


def test_reply_length_medium():
    length = get_reply_length("hello world")
    assert settings.model_min_tokens <= length <= settings.model_min_tokens * 2 + settings.model_jitter_level


def test_reply_length_question():
    length = get_reply_length("what is going on here?")
    assert (
        int(1.5 * settings.model_default_tokens) - settings.model_jitter_level
        <= length
        <= int(1.5 * settings.model_default_tokens) + settings.model_jitter_level
    )


def test_reply_length_explanation():
    msg = "please explain the meaning of life"
    length = get_reply_length(msg)
    assert settings.model_max_tokens - settings.model_jitter_level <= length <= settings.model_max_tokens + settings.model_jitter_level
