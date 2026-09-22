import random

from backend.config import settings
from backend.services.model.model_service import get_model
from backend.utils.logger_utils import logger
from backend.utils.reply_utils import EXPLANATION_WORDS, SPECULATION_WORDS, ANALYSIS_WORDS, GUIDE_WORDS


def generate_model_output(prompt: str, message: str) -> str:
    model, tokenizer = get_model()
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    logger.info("Output: generating response...")
    max_tokens = get_reply_length(message)
    output = model.generate(
        **inputs,
        top_p=settings.model_top_p,
        do_sample=True,
        max_time=settings.model_max_time,
        temperature=settings.model_temperature,
        max_new_tokens=max_tokens,
        eos_token_id=tokenizer.eos_token_id,
        repetition_penalty=settings.model_repetition_penalty,
    )

    model_output = tokenizer.decode(output[0], skip_special_tokens=True)
    logger.debug("Output: %s\n", model_output)

    return model_output


def should_reply(message: str) -> bool:
    msg = message.lower().strip()

    direct_triggers = ["rick", "sanchez"]
    if any(t in msg for t in direct_triggers):
        logger.info("Reply decision: direct trigger detected")
        return True

    classifier_prompt = "\n".join(
        [
            "Decide if Rick Sanchez should reply to the following message.",
            "Reply only 'yes' or 'no'.",
            "",
            "Rules:",
            "- Reply 'yes' if the message is directed at Rick.",
            "- Reply 'yes' if the message asks Rick a question.",
            "- Reply 'yes' if the message mentions Rick by name.",
            "- Reply 'no' if the message is between other users.",
            "- Reply 'no' if the message is casual small talk between humans.",
            "",
            f'Message: "{message}"',
            "",
            "Answer:",
        ]
    )

    logger.info("Reply decision: getting decision model...")
    model, tokenizer = get_model()
    inputs = tokenizer(classifier_prompt, return_tensors="pt").to(model.device)

    logger.info("Reply decision: generating decision...")
    output = model.generate(
        **inputs,
        max_new_tokens=1,
        do_sample=False,
        eos_token_id=tokenizer.encode("\n")[0],
    )

    generated = output[0][inputs["input_ids"].shape[1] :]
    answer = tokenizer.decode(generated, skip_special_tokens=True)
    answer = answer.lower().strip()

    if answer not in ("yes", "no"):
        logger.info("Reply decision: model returned unexpected output: %s", answer)
        return False

    if answer == "yes":
        logger.info("Reply decision: model returned yes")
        return True

    if random.random() < settings.random_reply_chance:
        logger.info("Reply decision: spontaneous reply triggered")
        return True

    logger.info("Reply decision: no")
    return False


def get_reply_length(message: str) -> int:
    message = message.lower()

    if len(message) < 10:
        reply_length = settings.model_min_tokens

    elif len(message) < 20:
        reply_length = jitter(2 * settings.model_min_tokens)

    elif any(word in message for word in EXPLANATION_WORDS + SPECULATION_WORDS + ANALYSIS_WORDS + GUIDE_WORDS):
        reply_length = jitter(settings.model_max_tokens)

    elif "?" in message or "!" in message:
        reply_length = jitter(int(1.5 * settings.model_default_tokens))

    else:
        reply_length = settings.model_default_tokens

    logger.info("Reply decision reply length: %s tokens", reply_length)
    return reply_length


def jitter(length: int) -> int:
    return max(settings.model_min_tokens, length + random.randint(-settings.model_jitter_level, settings.model_jitter_level))
