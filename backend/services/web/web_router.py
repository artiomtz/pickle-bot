import re

from backend.services.model.model_service import get_model
from backend.utils.logger_utils import logger
from backend.utils.reply_utils import FLUFF_PATTERNS, TIME_PATTERNS


def should_use_web(message: str) -> bool:
    classifier_prompt = "\n".join(
        [
            "Decide if the following user message requires fresh web search.",
            "Reply only 'yes' or 'no'.",
            "",
            "Rules:",
            "- Reply 'yes' if the user asks for current, recent, or latest information.",
            "- Reply 'yes' if the user asks for facts that may change over time.",
            "- Reply 'yes' if the user asks about news, events, sports results, prices, or updates.",
            "- Reply 'no' if the answer can be derived from general knowledge.",
            "- Reply 'no' if the question is about Rick, the conversation, or fictional content.",
            "",
            f'Message: "{message}"',
            "",
            "Answer:",
        ]
    )

    logger.info("Web decision: getting decision model...")
    model, tokenizer = get_model()
    inputs = tokenizer(classifier_prompt, return_tensors="pt").to(model.device)

    logger.info("Web decision: generating decision...")
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
        logger.info("Web decision: model returned unexpected output: %s", answer)
        return False

    if answer == "yes":
        logger.info("Web decision: model returned yes")
        return True

    logger.info("Web decision: no")
    return False


def build_web_query(message: str) -> str:
    logger.info("Web query: %s", message)
    msg = message.lower().strip()

    msg = re.sub(r"\bricks?\b", "", msg)
    msg = re.sub(r"\bsanchez\b", "", msg)

    for pat in FLUFF_PATTERNS:
        msg = re.sub(rf"\b{re.escape(pat)}\b", "", msg)

    parts = re.split(r"[.?!]", msg)
    parts = [p.strip() for p in parts if p.strip()]
    if parts:
        msg = parts[-1]

    if not any(k in msg for k in TIME_PATTERNS):
        msg = msg + " latest"

    msg = re.sub(r"[^a-z0-9\s\-]", "", msg)
    msg = re.sub(r"\s{2,}", " ", msg).strip()

    if not msg:
        logger.info("Web query: default value")
        return "latest news"

    logger.info("Web query (clean): %s", msg)
    return msg


def summarize_web_results(results: list, search_query: str, max_chars: int = 1200) -> str:
    logger.debug("Web summary: %s", results)
    if not results:
        logger.info("Web summary: no results")
        return "No reliable web results were found."

    filtered = filter_relevant_results(results, search_query)
    if not filtered:
        logger.info("Web summary: no relevant results")
        return "No relevant web results were found."

    lines = []
    for r in filtered:
        title = r.get("title") or ""
        snippet = r.get("content") or r.get("snippet") or ""
        snippet = snippet.replace("\n", " ").strip()
        source = r.get("source") or r.get("url") or ""
        line = f"- {title} — {snippet} (source: {source})"
        lines.append(line)

    summary = "\n".join(lines)
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "..."

    return summary


def score_result(result: dict, topic: str) -> float:
    title = (result.get("title") or "").lower()
    snippet = (result.get("content") or result.get("snippet") or "").lower()
    topic = topic.lower()

    score = 0
    for word in topic.split():
        if word in title:
            score += 3
        if word in snippet:
            score += 2

    return score


def filter_relevant_results(results: list, topic: str, limit: int = 3) -> list:
    scored = [(score_result(r, topic), r) for r in results]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for score, r in scored[:limit] if score > 0]
