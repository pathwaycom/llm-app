import logging
from abc import ABC, abstractmethod
import requests


logfun = logging.debug


class APIClient(ABC):
    @abstractmethod
    def make_request(self, **kwargs):
        pass


class OpenAIClient(APIClient):
    def __init__(self, api_key: str):
        import openai
        self.api = openai
        self.api.api_key = api_key


class OpenAIChatCompletionClient(OpenAIClient):
    def make_request(self, **kwargs):
        logfun("Calling OpenAI chat completion service %s", str(kwargs)[:100])
        return self.api.ChatCompletion.create(**kwargs)


class OpenAIEmbeddingClient(OpenAIClient):
    def make_request(self, **kwargs):
        logfun("Calling OpenAI embedding service %s", str(kwargs)[:100])
        return self.api.Embedding.create(**kwargs)


class HuggingFaceClient(APIClient):
    def __init__(self, api_key: str) -> None:
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.api_url_prefix = "https://api-inference.huggingface.co/models"

    def make_request(self, **kwargs):
        logfun("Calling HuggingFace %s", str(kwargs)[:100])
        endpoint = kwargs.pop("model")
        url = f"{self.api_url_prefix}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=kwargs)
        return response.json()
