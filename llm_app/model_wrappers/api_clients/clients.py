import logging
from abc import ABC
from typing import Optional
import requests


logfun = logging.debug


class APIClient(ABC):
    def __init__(self, base_url: Optional[str], api_key: Optional[str] = None):
        self.base_url = base_url
        self.headers = dict()

        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"

    def make_post_request(self, **kwargs):
        logfun("Calling %s %s", str(self.__class__.__name__), str(kwargs)[:100])
        endpoint = kwargs.pop("model", "")
        url = f"{self.base_url}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=kwargs)
        return response.json()


class HuggingFaceClient(APIClient):
    def __init__(self, api_key: str) -> None:
        super().__init__(
            base_url="https://api-inference.huggingface.co/models", api_key=api_key
        )


class OpenAIClient(APIClient):
    def __init__(self, api_key: str):
        import openai

        self.api = openai
        self.api.api_key = api_key


class OpenAIChatCompletionClient(OpenAIClient):
    def make_post_request(self, **kwargs):
        logfun("Calling OpenAI chat completion service %s", str(kwargs)[:100])
        return self.api.ChatCompletion.create(**kwargs)


class OpenAIEmbeddingClient(OpenAIClient):
    def make_post_request(self, **kwargs):
        logfun("Calling OpenAI embedding service %s", str(kwargs)[:100])
        return self.api.Embedding.create(**kwargs)
