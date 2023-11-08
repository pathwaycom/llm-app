import logging
from abc import ABC, abstractmethod

import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential

logfun = logging.debug


class APIClient(ABC):
    @abstractmethod
    def make_request(self, **kwargs):
        pass


class OpenAIClient(APIClient):
    def __init__(
        self,
        api_key: str,
        api_type: str | None = None,
        api_base: str | None = None,
        api_version: str | None = None,
    ):
        import openai

        openai.api_requestor.TIMEOUT_SECS = 90

        openai.api_key = api_key
        if api_type:
            openai.api_type = api_type
        if api_base:
            openai.api_base = api_base
        if api_version:
            openai.api_version = api_version

        self.api = openai


class OpenAIChatCompletionClient(OpenAIClient):
    @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
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


class LiteLLMClient(APIClient):
    """
    A wrapper for the LiteLLM.

    Attributes:
        task_fn (Callable): Function reference for the specified task.

    Args:
        task (str, optional): Type of task to be executed. Defaults to "completion".
            Supported tasks are:
                - "completion"
                - "embedding"

    Raises:
        ValueError: If the provided task is not supported.
    """

    def __init__(self, task: str = "completion") -> None:
        """
        Initializes the client with the specified task type.

        Args:
            task (str, optional): Type of task. Defaults to "completion".
            Supported are 'completion' and 'embedding'.
        """
        from litellm import completion, embedding

        if task == "completion":
            self.task_fn = completion
        elif task == "embedding":
            self.task_fn = embedding
        else:
            raise ValueError("Supported tasks are (completion, embedding).")

    def make_request(self, **kwargs):
        """
        Makes a request to the LLM service using the specified task function.
        """
        return self.task_fn(**kwargs)
