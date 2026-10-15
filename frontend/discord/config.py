import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class DiscordConfig:
    timezone: str
    auth_key: str | None
    discord_token: str
    backend_base_url: str
    polling_interval_seconds: int

    @classmethod
    def from_env(cls) -> "DiscordConfig":
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise RuntimeError("DISCORD_TOKEN is required in .env")

        timezone = os.getenv("TIMEZONE", "America/Toronto")
        auth_key = os.getenv("AUTH_KEY")
        backend_base_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
        polling_interval_seconds = int(os.getenv("FRONTEND_POLLING_INTERVAL_SECONDS", "300"))

        return cls(
            timezone=timezone,
            auth_key=auth_key,
            discord_token=token,
            backend_base_url=backend_base_url,
            polling_interval_seconds=polling_interval_seconds,
        )


load_dotenv()
