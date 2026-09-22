from backend.config import settings

from backend.services.memory_service import memory_service
from backend.services.model.reply_service import should_reply, generate_model_output
from backend.services.web.web_client import web_client
from backend.services.web.web_router import build_web_query, should_use_web, summarize_web_results

from backend.types import Role, User
from backend.utils.logger_utils import logger
from backend.utils.prompt_utils import build_full_prompt
from backend.utils.text_utils import extract_reply


def generate_reply(message: str, user_id: str, chat_id: str) -> str:
    if settings.is_dev:
        logger.info("Dev mode response...")
        return f"Alright, listen up, {user_id}. You said: '{message}' - and I'm telling you, that's barely a C- idea."

    logger.info("Saving request message...")
    memory_service.add_message(chat_id=chat_id, user_id=user_id, role=Role.USER, content=message)

    logger.info("Deciding whether to reply...")
    if not should_reply(message):
        return ""

    web_summary = None
    logger.info("Deciding whether to use web...")

    if should_use_web(message):
        logger.info("Preparing web search query...")
        search_query = build_web_query(message)

        logger.info("Executing web search...")
        results = web_client.search(query=search_query)

        if results:
            web_summary = summarize_web_results(results, search_query, max_chars=settings.web_max_chars)
            logger.info("Web search summary length: %s", len(web_summary))
        else:
            logger.info("Web search returned no results; falling back to regular prompt.")

    logger.info("Building prompt...")
    prompt = build_full_prompt(chat_id=chat_id, message=message, web_summary=web_summary)

    logger.info("Generating response...")
    full_text = generate_model_output(prompt, message)

    reply = extract_reply(full_text)
    logger.info("Rick's reply: %s", reply)

    logger.info("Saving response message...")
    memory_service.add_message(chat_id=chat_id, user_id=User.RICK.value, role=Role.RICK, content=reply)

    return reply
