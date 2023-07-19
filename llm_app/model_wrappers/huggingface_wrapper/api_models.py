from model_wrappers.api_clients.clients import HuggingFaceClient
from model_wrappers.base import APIModel


class HuggingFaceAPIModel(APIModel):
    def get_client(self, api_key: str) -> HuggingFaceClient:
        return HuggingFaceClient(api_key=api_key)

    def call_api(self, **kwargs):
        """
        Makes a request to the Hugging Face API and returns the result.

        The method accepts arguments as keyword arguments (**kwargs).
        The expected arguments are 'model' and others that depend on the specific task.
        Please check [HuggingFace Inference API](https://huggingface.co/docs/api-inference/detailed_parameters)
        'model' is a string representing the pre-trained model to use for the call.

        Examples:

        1) Question-Answering Task usage:

        model = HuggingFaceModel(api_key=token)
        result = model.call(
            inputs=dict(
                context="Pathway is a realtime stream data processing framework. It has a python api",
                question="Does Pathway have a python API ?"
            ),
            model='deepset/roberta-base-squad2'
        )
        The expected output for the example above is:
        {
            'score': 0.41046786308288574,
            'start': 56,
            'end': 75,
            'answer': 'It has a python api'
        }

        2) Sentiment analysis model usage:

        result = model.call(
            inputs="What a performance that was!",
            model='distilbert-base-uncased-finetuned-sst-2-english'
        )
        The expected output for the example above is:
        [
            [
                {'label': 'POSITIVE', 'score': 0.9988183379173279},
                {'label': 'NEGATIVE', 'score': 0.0011816363548859954}
            ]
        ]

        Args:
            **kwargs: The arguments for the model call. 'inputs' and 'model' keys are expected.

        Returns:
            The response from the Hugging Face API, the format depends on the model being used.
        """
        return self.api_client.make_request(**kwargs)


class HFApiFeatureExtractionTask(HuggingFaceAPIModel):
    def __call__(
        self, text: str, locator="sentence-transformers/all-MiniLM-L6-v2", **kwargs
    ):
        response = self.call_api(inputs=[text], model=locator, **kwargs)
        return response


class HFApiTextGenerationTask(HuggingFaceAPIModel):
    """
    A class that represents a text generation task using the Hugging Face API.

    It inherits from the HuggingFaceModel class and overrides the call method to
    specifically work with text generation models.

    This class allows users to simply pass a text string and get a generated
    text in return.

    Args:
        api_key (str): The API key to access the Hugging Face API.

    Example:

    # >>> model = HFTextGenerationTask(api_key=token)
    # >>> text = "Once upon a time"
    # >>> generated_text = model(text, locator="gpt2")
    # >>> print(generated_text)
    'Once upon a time in a land far away...'

    """

    def __call__(self, text: str, locator="gpt2", **kwargs):
        response = self.call_api(inputs=text, model=locator, **kwargs)
        return response[0]["generated_text"]
