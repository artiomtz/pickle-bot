from unittest.mock import MagicMock

from backend.services.web.web_client import WebSearchClient, MAX_INPUT_LENGTH
from backend.services.web.web_router import should_use_web, build_web_query, summarize_web_results, score_result, filter_relevant_results


def test_trim_query_short():
    client = WebSearchClient(api_key="dummy")
    assert client._trim_query("short query") == "short query"


def test_trim_query_long():
    client = WebSearchClient(api_key="dummy")
    long_query = "word " * MAX_INPUT_LENGTH
    trimmed = client._trim_query(long_query)
    assert len(trimmed) <= MAX_INPUT_LENGTH
    assert trimmed.endswith("word")


def test_web_search_disabled():
    client = WebSearchClient(api_key=None)
    assert client.search("anything") == []


def test_web_search_mocked():
    client = WebSearchClient(api_key="dummy")
    client._client = MagicMock()
    client._client.search.return_value = {"results": [{"title": "A"}]}

    results = client.search("test query")
    assert len(results) == 1
    assert results[0]["title"] == "A"


def test_build_web_query_removes_fluff():
    msg = "hey rick can you check the weather in toronto?"
    q = build_web_query(msg)
    assert "hey" not in q
    assert "can you check" not in q
    assert "rick" not in q
    assert "weather" in q
    assert "latest" in q


def test_build_web_query_sentence_extraction():
    msg = "first sentence. second sentence? third!"
    q = build_web_query(msg)
    assert q.startswith("third")


def test_build_web_query_adds_latest():
    msg = "toronto weather"
    q = build_web_query(msg)
    assert q.endswith("latest")


def test_score_result_basic():
    result = {
        "title": "Toronto Weather Today",
        "content": "Temperature in Toronto is rising",
    }
    score = score_result(result, "toronto weather")
    assert score > 0


def test_score_result_no_match():
    result = {
        "title": "Snake spotted in Ontario",
        "content": "Venomous snake warning",
    }
    score = score_result(result, "toronto weather")
    assert score == 0


def test_filter_relevant_results():
    results = [
        {"title": "Toronto Weather", "content": "Sunny"},
        {"title": "Snake News", "content": "Danger"},
        {"title": "Toronto Sports", "content": "Score"},
    ]

    filtered = filter_relevant_results(results, "toronto weather")
    assert len(filtered) == 2
    assert filtered[0]["title"] == "Toronto Weather"


def test_summarize_web_results_basic():
    results = [
        {"title": "Toronto Weather", "content": "Sunny", "source": "A"},
        {"title": "Snake News", "content": "Danger", "source": "B"},
    ]

    summary = summarize_web_results(results, "toronto weather")
    assert "Toronto Weather" in summary
    assert "Snake" not in summary
    assert "Sunny" in summary


def test_summarize_web_results_trim():
    long_content = "x" * 5000
    results = [{"title": "Toronto Weather", "content": long_content}]
    summary = summarize_web_results(results, "toronto weather", max_chars=100)
    assert len(summary) <= 103


def test_should_use_web_yes(monkeypatch):
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    mock_tokenizer.decode.return_value = "yes"
    mock_model.generate.return_value = [[1, 2, 3]]

    monkeypatch.setattr("backend.services.model.reply_service.get_model", lambda: (mock_model, mock_tokenizer))

    assert should_use_web("what is the weather today") is True


def test_should_use_web_no(monkeypatch):
    mock_model = MagicMock()
    mock_tokenizer = MagicMock()

    mock_tokenizer.decode.return_value = "no"
    mock_model.generate.return_value = [[1, 2, 3]]

    monkeypatch.setattr("backend.services.model.reply_service.get_model", lambda: (mock_model, mock_tokenizer))

    assert should_use_web("tell me about rick sanchez") is False
