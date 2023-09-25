import pathway as pw

from llm_app.model_wrappers.api_clients.clients import LiteLLMClient
from llm_app.model_wrappers.base import BaseModel


class LiteLLMChatModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.api_client = self.get_client()

    def get_client(
        self,
    ) -> LiteLLMClient:
        return LiteLLMClient(task="completion")

    def __call__(self, text: str, locator="gpt-3.5-turbo", **kwargs) -> str:
        """

        Example
        # >>> os.environ["OPENAI_API_KEY"] = ""
        # >>> model = LiteLLMChatModel()
        # >>> model(
        # ...     locator='gpt-4-0613',
        # ...     text="Tell me a joke about jokes",
        # ...     temperature=1.1
        # ... )
        """

        messages = [
            dict(role="system", content="You are a helpful assistant"),
            dict(role="user", content=text),
        ]
        response = self.api_client.make_request(
            messages=messages, model=locator, **kwargs
        )
        return response.choices[0].message.content

    def apply(
        self,
        *args,
        **kwargs,
    ) -> pw.ColumnExpression:
        """
        Applies the specified API model in `locator` to the provided text.
        Parameters
        ----------
        text : Union[pw.ColumnExpression, str]
            The input text on which the model will be applied. It can be a column expression or a string.
        locator : Union[pw.ColumnExpression, str, None]
            The model locator to use for applying the model.
            If provided, it should be a column expression or a string.
            Otherwise, the default chat completion model `gpt-3.5-turbo` is applied.
            Please visit https://docs.litellm.ai/docs/ to see the available models.
        **kwargs : dict
            Additional keyword arguments that will be used for the model application.
            These could include settings such as `temperature`, `max_tokens`, etc.
        Returns
        -------
        pw.ColumnExpression
            The result of the model application as a column expression or str.
            Please note that the output is `chat_completion.choices[0].message.content`
            where `chat_completion` is the api response.
        Example:
        # >>> os.environ["OPENAI_API_KEY"] = "<YOUR OPENAI TOKEN>"
        # >>> os.environ["COHERE_API_KEY"] = "<YOUR COHERE TOKEN>"
        # >>> model = LiteLLMChatModel()
        # >>> table = pw.debug.table_from_pandas(
        # ...     pd.DataFrame.from_records([
        # ...         {"text": "How to use pathway to process a kafka stream ?"},
        # ...         {"text": "How to apply a function to a pathway table ?"}
        # ...     ])
        # ... )
        # >>> table += table.select(
        # ...     openai_response = model.apply(
        # ...         pw.this.text,
        # ...         locator='gpt-4',
        # ...         temperature=1.5,
        # ...         max_tokens=1000
        # ...     )
        # ... )
        # >>> table += table.select(
        # ...     cohere_response = model.apply(
        # ...         pw.this.text,
        # ...         locator='command-nightly',
        # ...         temperature=1.5,
        # ...         max_tokens=1000
        # ...     )
        # ... )
        """
        return super().apply(*args, **kwargs)


class LiteLLMEmbeddingModel(BaseModel):
    def __init__(self):
        super().__init__()
        self.api_client = self.get_client()

    def get_client(self) -> LiteLLMClient:
        return LiteLLMClient(task="embedding")

    def __call__(self, text: str, locator="text-embedding-ada-002", **kwargs):
        """
        Example:

        # >>> os.environ["OPENAI_API_KEY"] = ""
        # >>> embedder = LiteLLMEmbeddingModel()
        # >>> embedder(
        # ...    text='Some random text'
        # ...    locator='text-embedding-ada-002'
        # ... )
        """

        response = self.api_client.make_request(input=[text], model=locator, **kwargs)
        return response["data"][0]["embedding"]

    def apply(
        self,
        *args,
        **kwargs,
    ) -> pw.ColumnExpression:
        """
        Applies the specified API model in `locator` to the provided text.
        Parameters
        ----------
        text : Union[pw.ColumnExpression, str]
            The input text on which the model will be applied. It can be a column expression or a constant value.
        locator : Union[pw.ColumnExpression, str, None]
            The model locator to use for applying the model.
            If provided, it should be a column expression or a constant value.
            Otherwise, the default chat completion model `gpt-3.5-turbo` is applied.
            Please visit https://docs.litellm.ai/docs/embedding/supported_embedding
            to see the available models.
        **kwargs : dict
            Additional keyword arguments that will be used for the model application.
            These could include settings such as `temperature`, `max_tokens`, etc.
        Returns
        -------
        pw.ColumnExpression
            The result of the model application as a column expression or constant of type list.
            Please note that the output is `results["data"][0]["embedding"]`
        Example:
        # >>> os.environ["OPENAI_API_KEY"] = ""
        # >>> embedder = LiteLLMEmbeddingModel()
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
