from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    is_dev: bool = False
    version: str = "0.1.0"
    timezone: str = "America/Toronto"
    model_config = ConfigDict(env_file=".env")
    lora_adapter_path: str = "bot/model/picklebot-lora-v1"
    base_model_name: str = "mistralai/Mistral-7B-Instruct-v0.2"

    auth_key: str | None = None
    hf_token: str | None = None
    web_token: str | None = None
    web_enabled: bool = True
    web_max_chars: int = 1200
    allowed_origins: str | None = ""

    model_top_p: float = 0.9
    model_max_time: int = 10
    model_temperature: float = 0.7
    model_repetition_penalty: float = 1.1

    model_min_tokens: int = 20
    model_max_tokens: int = 180
    model_default_tokens: int = 60
    model_jitter_level: int = 15

    no_posts_days: int = 5
    active_chat_days: int = 60
    max_message_age_days: int = 100
    max_messages_per_chat: int = 300
    max_message_length: int = 2000
    random_reply_chance: float = 0.2
    context_memory_num_messages: int = 20

    spontaneous_enabled: bool = True
    spontaneous_max_chats: int = 5
    spontaneous_max_tokens: int = 160
    spontaneous_min_interval_hours: int = 72
    spontaneous_max_interval_hours: int = 120

    rate_limit_max_tokens: int = 20
    rate_limit_refill_interval_seconds: int = 5


settings = Settings()
