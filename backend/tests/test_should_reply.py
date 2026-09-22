from unittest.mock import patch

from backend.config import settings
from backend.services.chat_service import should_reply


def test_should_reply_direct_trigger():
    assert should_reply("hey rick") is True
    assert should_reply("SANCHEZ!") is True


@patch("backend.services.model.reply_service.get_model")
def test_should_reply_model_yes(mock_get_model):

    class FakeTensor(list):
        @property
        def shape(self):
            return (1, 3)

    class FakeInputs(dict):
        def to(self, device):
            return self

    class FakeTokenizer:
        def __init__(self):
            self.eos_token_id = 0

        def __call__(self, prompt, return_tensors):
            return FakeInputs({"input_ids": FakeTensor([1, 2, 3])})

        def decode(self, ids, skip_special_tokens=True):
            return "yes"

        def encode(self, x):
            return [0]

    class FakeModel:
        device = "cpu"

        def generate(self, **kwargs):
            return [FakeTensor([1, 2, 3, 999])]

    mock_get_model.return_value = (FakeModel(), FakeTokenizer())

    assert should_reply("hello") is True


@patch("backend.services.model.reply_service.get_model")
def test_should_reply_model_no(mock_get_model):

    class FakeTensor(list):
        @property
        def shape(self):
            return (1, 3)

    class FakeInputs(dict):
        def to(self, device):
            return self

    class FakeTokenizer:
        def __init__(self):
            self.eos_token_id = 0

        def __call__(self, prompt, return_tensors):
            return FakeInputs({"input_ids": FakeTensor([1, 2, 3])})

        def decode(self, ids, skip_special_tokens=True):
            return "no"

        def encode(self, x):
            return [0]

    class FakeModel:
        device = "cpu"

        def generate(self, **kwargs):
            return [FakeTensor([1, 2, 3, 4])]

    mock_get_model.return_value = (FakeModel(), FakeTokenizer())

    settings.random_reply_chance = 0
    assert should_reply("hello") is False
