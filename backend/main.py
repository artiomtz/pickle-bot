from typing import Optional

from fastapi import Security, Depends, Request, HTTPException

from backend.app_factory import create_app, api_key_header
from backend.config import settings
from backend.schemas import ChatRequest, ChatResponse
from backend.services.chat_service import generate_reply
from backend.services.memory_service import memory_service
from backend.services.rate_limiter_service import rate_limiter
from backend.utils.api_utils import rows_to_messages
from backend.utils.logger_utils import logger
from backend.utils.text_utils import generate_id
from backend.utils.validation_utils import validate_id, validate_days, validate_limit, validate_since

app = create_app()


def verify_auth(api_key: str = Security(api_key_header)):
    if settings.is_dev:
        logger.info("Authentication verification: dev mode")
        return

    if settings.auth_key is None:
        logger.warning("Authentication verification: no API key in environment")
        return

    if not api_key:
        logger.warning("Authentication verification: missing X-API-Key header")
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")

    if api_key != settings.auth_key:
        logger.warning("Authentication verification: invalid API key")
        raise HTTPException(status_code=403, detail="Invalid API key")


@app.get("/")
def root():
    logger.info("Pickle Bot API is running. Use /chat to talk to Rick.")
    return {
        "name": "Pickle Bot Backend",
        "version": settings.version,
        "is_dev": settings.is_dev,
        "message": "Pickle Bot API is running. Use /chat to talk to Rick.",
    }


@app.get("/health")
def health_check():
    logger.info("Status: ok. is_dev: %s", settings.is_dev)
    return {"status": "ok", "is_dev": settings.is_dev}


@app.get("/chats")
def get_all_chat_ids(_auth=Depends(verify_auth)):
    logger.info("Request for all chat ids")
    if not rate_limiter.allow():
        logger.warning("rate limit exceeded")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    chat_ids = memory_service.get_all_chat_ids()
    return {"chats": chat_ids}


@app.get("/chats/active")
def get_active_chats(days: int = settings.active_chat_days, _auth=Depends(verify_auth)):
    logger.info("Request for active chats (days=%s)", days)
    if not rate_limiter.allow():
        logger.warning("rate limit exceeded")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        validate_days(days)
    except ValueError as e:
        logger.info("invalid days value: %s", e)
        raise HTTPException(status_code=400, detail="Invalid days value")

    chat_ids = memory_service.get_active_chat_ids(days=days)
    return {"active_chats": chat_ids}


@app.get("/messages/since")
def get_messages_since(chat_id: str, since: str, _auth=Depends(verify_auth)):
    logger.info("Request for messages for chat id=%s (since %s)", chat_id, since)
    if not rate_limiter.allow():
        logger.warning("rate limit exceeded")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        validate_id(chat_id)
        since = validate_since(since)
    except ValueError as e:
        logger.info("invalid chat id or since values: %s", e)
        raise HTTPException(status_code=400, detail="Invalid chat id or since arguments")

    rows = memory_service.get_messages_since(chat_id, since)
    messages = rows_to_messages(rows)

    return {"messages": messages}


@app.get("/messages/{chat_id}")
def get_messages(chat_id: str, limit: Optional[int] = None, _auth=Depends(verify_auth)):
    logger.info("Request for messages for chat id=%s (limit=%s)", chat_id, limit)
    if not rate_limiter.allow():
        logger.warning("rate limit exceeded")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    try:
        validate_id(chat_id)
        if limit is not None:
            validate_limit(limit)
    except ValueError as e:
        logger.info("invalid chat id or limit arguments: %s", e)
        raise HTTPException(status_code=400, detail="Invalid request parameters")

    rows = memory_service.get_messages(chat_id, limit=limit)
    messages = rows_to_messages(rows)

    return {"messages": messages}


@app.post(
    "/chat",
    response_model=ChatResponse,
    responses={
        401: {"description": "Missing API key"},
        403: {"description": "Invalid API key"},
    },
)
def chat(request: ChatRequest, fastapi_request: Request = None, _auth=Depends(verify_auth)):
    origin = fastapi_request.headers.get("origin")
    client_ip = fastapi_request.client.host
    logger.info("Request from origin=%s, ip=%s", origin, client_ip)

    if not rate_limiter.allow():
        logger.warning("rate limit exceeded")
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    user_id = request.user_id or generate_id()
    chat_id = request.chat_id or generate_id()

    logger.info("Request chat_id=%s, user_id=%s, message=%s", request.chat_id or "<none>", request.user_id or "<none>", request.message)
    reply = generate_reply(request.message, user_id=user_id, chat_id=chat_id)

    return ChatResponse(
        chat_id=chat_id,
        user_id=user_id,
        reply=reply,
    )


@app.get("/{path:path}")
def catch_all(path: str, request: Request):
    logger.warning("Request for wrong path: %s", path)
    return {"error": "Unknown endpoint", "path": path, "method": request.method, "hint": "Use /chat to talk to Rick."}
