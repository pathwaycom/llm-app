import logging

import pathway as pw

from llm_app.model_wrappers.api_clients.clients import (
    OpenAIChatCompletionClient,
    OpenAIClient,
    OpenAIEmbeddingClient,
)
from llm_app.model_wrappers.base import BaseModel

logfun = logging.debug


class MessagePreparer:
    @staticmethod
    def prepare_chat_messages(prompt: str):
        return [
            dict(role="system", content="You are a helpful assistant"),
            dict(role="user", content=prompt),
        ]


class OpenAIChatGPTModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__()
        self.api_client = self.get_client(**kwargs)

    def get_client(self, **kwargs) -> OpenAIClient:
        return OpenAIChatCompletionClient(**kwargs)

    def __call__(self, text: str, locator="gpt-3.5-turbo", **kwargs) -> str:
        """

        Example

        # >>> model = OpenAIChatGPTModel(api_key = api_key)
        # >>> model(
        # ...     locator='gpt-4-0613',
        # ...     text="Tell me a joke about jokes",
        # ...     temperature=1.1
        # ... )
        """
        if self.api_client.api.api_type == "azure":
            kwargs["engine"] = locator
        else:
            kwargs["model"] = locator

        messages = MessagePreparer.prepare_chat_messages(text)

        logfun(f"Calling OpenAI API with: {messages}\n")
        response = self.api_client.make_request(messages=messages, **kwargs)
        logfun(f"API Response: {response.choices[0].message.content}\n")
        return response.choices[0].message.content

    def apply(
        self,
        *args,
        **kwargs,
    ) -> pw.ColumnExpression:
        """
        Applies the specified model in `locator` from OpenAIChatGPT API to the provided text.
        Parameters
        ----------
        text : Union[pw.ColumnExpression, str]
            The input text on which the model will be applied. It can be a column expression or a string.
        locator : Union[pw.ColumnExpression, str, None]
            The model locator to use for applying the model.
            If provided, it should be a column expression or a string.
            Otherwise, the default chat completion model `gpt-3.5-turbo` is applied.
            Please check out https://platform.openai.com/docs/models/model-endpoint-compatibility
            to see the available models.
        **kwargs : dict
            Additional keyword arguments that will be used for the model application.
            These could include settings such as `temperature`, `max_tokens`, etc.
            Check https://platform.openai.com/docs/api-reference/chat/create for the official API Reference
        Returns
        -------
        pw.ColumnExpression
            The result of the model application as a column expression or str.
            Please note that the output is `chat_completion.choices[0].message.content`
            where `chat_completion` is the api response.
        Example:
        # >>> model = OpenAIChatGPTModel(api_key = api_key)
        # >>>
        # >>> table = pw.debug.table_from_pandas(
        # ...     pd.DataFrame.from_records([
        # ...         {"text": "How to use pathway to process a kafka stream ?"},
        # ...         {"text": "How to apply a function to a pathway table ?"}
        # ...     ])
        # ... )
        # >>> table += table.select(
        # ...     response = model.apply(
        # ...         pw.this.text,
        # ...         locator='gpt-4',
        # ...         temperature=1.5,
        # ...         max_tokens=1000
        # ...     )
        # ... )
        """
        return super().apply(*args, **kwargs)


class OpenAIEmbeddingModel(BaseModel):
    def __init__(self, **kwargs):
        super().__init__()
        self.api_client = self.get_client(**kwargs)

    def get_client(self, **kwargs) -> OpenAIClient:
        return OpenAIEmbeddingClient(**kwargs)

    def __call__(self, text: str, locator="text-embedding-ada-002", **kwargs):
        """
        Example:

        # >>> embedder = OpenAIEmbeddingModel(api_key)
        # >>>
        # >>> embedder(
        # ...    text='Some random text'
        # ...    locator='text-embedding-ada-002'
        # ... )
        """
        if self.api_client.api.api_type == "azure":
            kwargs["engine"] = locator
        else:
            kwargs["model"] = locator

        response = self.api_client.make_request(input=[text], **kwargs)
        return response["data"][0]["embedding"]

    def apply(
        self,
        *args,
        **kwargs,
    ) -> pw.ColumnExpression:
        """
        Applies the specified model in `locator` from OpenAIEmbeddingModel API to the provided text.
        Parameters
        ----------
        text : Union[pw.ColumnExpression, str]
            The input text on which the model will be applied. It can be a column expression or a constant value.
        locator : Union[pw.ColumnExpression, str, None]
            The model locator to use for applying the model.
            If provided, it should be a column expression or a constant value.
            Otherwise, the default chat completion model `gpt-3.5-turbo` is applied.
            Please check out https://platform.openai.com/docs/models/model-endpoint-compatibility
            to see the available models.
        **kwargs : dict
            Additional keyword arguments that will be used for the model application.
            These could include settings such as `temperature`, `max_tokens`, etc.
            You can check https://platform.openai.com/docs/api-reference/embeddings/create
            for the official API Reference.
        Returns
        -------
        pw.ColumnExpression
            The result of the model application as a column expression or constant of type list.
            Please note that the output is `results["data"][0]["embedding"]`
        Example:
        # >>> embedder = OpenAIEmbeddingModel(api_key)
        # >>>
        # >>> table = pw.debug.table_from_pandas(
        # ...     pd.DataFrame.from_records([
        # ...         {"text": "How to use pathway to process a kafka stream ?"},
        # ...         {"text": "How to apply a function to a pathway table ?"}
        # ...     ])
        # ... )
        # >>> table += table.select(
        # ...     embedding = embedder.apply(
        # ...         pw.this.text,
        # ...         locator='text-embedding-ada-002'
        # ...     )
        # ... )
        """
        return super().apply(*args, **kwargs)
