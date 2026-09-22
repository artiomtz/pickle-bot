from unittest.mock import patch

from backend.config import settings
from backend.services.scheduler_service import spontaneous_post_job


@patch("backend.services.scheduler_service.memory_service")
@patch("backend.services.scheduler_service.generate_spontaneous_message")
def test_spontaneous_job_no_active_chats(mock_gen, mock_mem):
    settings.spontaneous_enabled = True

    mock_mem.get_active_chat_ids.return_value = []
    spontaneous_post_job()

    mock_gen.assert_not_called()


@patch("backend.services.scheduler_service.memory_service")
@patch("backend.services.scheduler_service.generate_spontaneous_message")
def test_spontaneous_job_generates(mock_gen, mock_mem):
    settings.spontaneous_enabled = True

    mock_mem.get_active_chat_ids.return_value = ["chat1"]
    mock_mem.get_messages_since.return_value = []

    def fake_gen(chat_id):
        mock_mem.add_message(chat_id, "rick", "rick", "burp")
        return "burp"

    mock_gen.side_effect = fake_gen

    spontaneous_post_job()

    mock_gen.assert_called_once()
    assert mock_mem.add_message.call_count == 2
