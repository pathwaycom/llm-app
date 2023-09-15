import logging
from abc import ABC, abstractmethod
from typing import Optional

import requests

logfun = logging.debug


class APIClient(ABC):
    @abstractmethod
    def make_request(self, **kwargs):
        pass


class OpenAIClient(APIClient):
    def __init__(
        self,
        api_key: str,
        api_type: Optional[str] = None,
        api_base: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        import openai

        openai.api_key = api_key
        if api_type:
            openai.api_type = api_type
        if api_base:
            openai.api_base = api_base
        if api_version:
            openai.api_version = api_version

        self.api = openai


class OpenAIChatCompletionClient(OpenAIClient):
    def make_request(self, **kwargs):
        logfun("Calling OpenAI chat completion service %s", str(kwargs)[:100])
        return self.api.ChatCompletion.create(**kwargs)


class OpenAIEmbeddingClient(OpenAIClient):
    def make_request(self, **kwargs):
        logfun("Calling OpenAI embedding service %s", str(kwargs)[:100])
        return self.api.Embedding.create(**kwargs)


class HuggingFaceClient(APIClient):
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api-inference.huggingface.co/models",
    ) -> None:
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.api_url_prefix = api_base

    def make_request(self, **kwargs):
        logfun("Calling HuggingFace %s", str(kwargs)[:100])
        endpoint = kwargs.pop("model")
        url = f"{self.api_url_prefix}/{endpoint}"
        response = requests.post(url, headers=self.headers, json=kwargs)
        return response.json()
