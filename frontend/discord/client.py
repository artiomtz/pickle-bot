from datetime import datetime
from typing import List, Optional

import httpx

from .config import DiscordConfig
from .logging import logger
from .models import BackendReply, BackendMessage, MessageBatch


class BackendClient:
    def __init__(self, config: DiscordConfig) -> None:
        self._config = config

        headers = {}
        if self._config.auth_key:
            headers["X-API-Key"] = self._config.auth_key

        self._client = httpx.AsyncClient(base_url=self._config.backend_base_url, timeout=httpx.Timeout(10.0, connect=5.0), headers=headers)

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, url: str, **kwargs) -> Optional[httpx.Response]:
        try:
            resp = await self._client.request(method, url, **kwargs)

            if resp.status_code == 401:
                logger.error("Backend rejected request: missing X-API-Key")
                return None

            if resp.status_code == 403:
                logger.error("Backend rejected request: invalid X-API-Key")
                return None

            resp.raise_for_status()
            return resp

        except httpx.HTTPError as exc:
            logger.error("Backend request error (%s %s): %s", method, url, exc)
            return None

    async def send_user_message(self, chat_id: Optional[str], user_id: Optional[str], content: str) -> Optional[BackendReply]:
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
            "message": content,
        }

        resp = await self._request("POST", "/chat", json=payload)
        if resp is None:
            return None

        try:
            return BackendReply.model_validate(resp.json())
        except Exception as exc:
            logger.error("Malformed backend reply payload: %s", exc)
            return None

    async def fetch_new_messages(self, chat_id: str, since: datetime) -> List[BackendMessage]:
        params = {
            "chat_id": chat_id,
            "since": since.isoformat(),
        }

        resp = await self._request("GET", "/messages/since", params=params)
        if resp is None:
            return []

        try:
            batch = MessageBatch.model_validate(resp.json())
        except Exception as exc:
            logger.error("Malformed messages payload: %s", exc)
            return []

        return batch.messages
