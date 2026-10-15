import asyncio
from datetime import datetime, timezone
from typing import Dict

import discord
from discord.ext import tasks

from .client import BackendClient
from .config import DiscordConfig
from .logging import logger, setup_logging


class RickDiscordBot(discord.Client):
    def __init__(self, config: DiscordConfig, backend_client: BackendClient) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(intents=intents)

        self._config = config
        self._backend = backend_client
        self._last_ts: Dict[str, datetime] = {}
        self._poll_task = self._create_polling_task()

    def _create_polling_task(self):
        @tasks.loop(seconds=self._config.polling_interval_seconds)
        async def poll():
            await self._poll_backend()

        return poll

    async def setup_hook(self):
        self._poll_task.start()
        logger.info("Started polling task")

    async def on_ready(self):
        logger.info("Discord bot logged in as %s", self.user)

    async def on_message(self, message: discord.Message):
        if message.author.id == self.user.id:
            return

        chat_id = str(message.channel.id)
        user_id = str(message.author.id)
        content = message.content

        logger.info("Calling backend. chat %s user %s posted: %s", chat_id, user_id, content)
        reply = await self._backend.send_user_message(
            chat_id=chat_id,
            user_id=user_id,
            content=content,
        )

        if reply is None:
            logger.warning("Backend returned no reply")
            return

        if not reply.reply:
            logger.warning("Backend returned empty reply")
            return
        logger.info("Posting to chat %s: %s", chat_id, reply.reply)
        await message.channel.send(reply.reply)
        self._last_ts[chat_id] = datetime.now(timezone.utc)

    async def _poll_backend(self):
        for chat_id, last_ts in list(self._last_ts.items()):
            logger.info("Polling: calling backend for latest posts for chat %s", chat_id)
            messages = await self._backend.fetch_new_messages(chat_id, last_ts)

            for msg in messages:
                channel = self.get_channel(int(chat_id))
                if channel is None:
                    continue

                logger.info("Polling: posting to chat %s: %s", chat_id, msg.content)
                await channel.send(msg.content)
                self._last_ts[chat_id] = msg.created_at


async def main():
    setup_logging()

    logger.info("Fetching config...")
    config = DiscordConfig.from_env()

    logger.info("Initiating client...")
    backend = BackendClient(config)

    logger.info("Fetching config...")
    bot = RickDiscordBot(config, backend)

    try:
        logger.info("Starting frontend...")
        await bot.start(config.discord_token)
    finally:
        logger.info("Stopping frontend...")
        await backend.close()


if __name__ == "__main__":
    asyncio.run(main())
