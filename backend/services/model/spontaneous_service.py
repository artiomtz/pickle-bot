import random

from backend.config import settings
from backend.services.model.model_service import get_model
from backend.utils.logger_utils import logger
from backend.utils.text_utils import extract_reply

SPONTANEOUS_MOODS = [
    "drunk rant",
    "chaotic nonsense",
    "dark humor",
    "bored genius",
    "existential crisis",
    "pickle-powered madness",
    "sarcastic insult",
    "cosmic wisdom",
]


def generate_spontaneous_message(chat_id: str) -> str:
    mood = random.choice(SPONTANEOUS_MOODS)

    prompt = "\n".join(
        [
            "You are Rick Sanchez from Rick and Morty."
            "Generate a spontaneous message unrelated to the current conversation."
            f"Tone: {mood}."
            "Keep it short-medium, chaotic, sarcastic, dismissive, or drunk."
            "Do not reference the user directly."
            "Do not continue the conversation."
            "Just say something random."
            "",
            "Rick: ",
        ]
    )

    logger.info("Spontaneous message: getting model...")
    model, tokenizer = get_model()
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    logger.info("Spontaneous message: generating...")
    output = model.generate(
        **inputs,
        top_p=settings.model_top_p,
        do_sample=True,
        temperature=settings.model_temperature,
        max_new_tokens=settings.spontaneous_max_tokens,
        eos_token_id=tokenizer.eos_token_id,
        repetition_penalty=settings.model_repetition_penalty,
    )

    full_text = tokenizer.decode(output[0], skip_special_tokens=True)

    reply = extract_reply(full_text)
    logger.info("Spontaneous message: %s", reply)

    return reply
