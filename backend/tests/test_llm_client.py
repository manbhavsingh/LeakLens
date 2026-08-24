from app.llm_client import OpenAICompatibleClient


def test_client_configuration_is_runtime_only() -> None:
    client = OpenAICompatibleClient(
        api_key="test-key",
        model="test-model",
        base_url="https://example.test/v1",
    )
    assert client.model == "test-model"
    assert client.base_url == "https://example.test/v1"
