from model_wrappers.base import BaseModel


class HFPipelineTask(BaseModel):
    def __init__(self, model, device="cpu", **kwargs):
        """
    A wrapper class for Hugging Face's `Pipeline` class.

    The `pipeline` function from Hugging Face is a utility factory method that creates
    a Pipeline to handle different tasks.
    It supports tasks like text classification, translation, summarization, and many more.

    This wrapper class simplifies the process of initializing the pipeline and allows the user
    to easily change the underlying model used for computations.

    Parameters:
    -----------
    model : str, required
        The model identifier from Hugging Face's model hub.
    device : str, default='cpu'
        The device where the computations will be performed.
        Supports 'cpu' or 'gpu'. Default is 'cpu'.
    **kwargs : optional
        Additional arguments form HF.
        Please check out https://huggingface.co/docs/transformers/main/main_classes/pipelines
        for more information on the models and available arguments.

    Attributes:
    -----------
    pipeline : transformers.Pipeline
        The Hugging Face pipeline object.
    tokenizer : transformers.PreTrainedTokenizer
        The tokenizer associated with the pipeline.

    Example:
    --------
    >>> pipe = HFPipelineTask('gpt2')
    >>> result = pipe('Hello world')
    """
        from transformers import pipeline
        super().__init__(**kwargs)
        self.pipeline = pipeline(model=model, device=device)
        self.tokenizer = self.pipeline.tokenizer

    def crop_to_max_length(self, input_string, max_length=500):
        tokens = self.tokenizer.tokenize(input_string)
        if len(tokens) > max_length:
            tokens = tokens[:max_length]
        return self.tokenizer.convert_tokens_to_string(tokens)


class HFFeatureExtractionTask(HFPipelineTask):
    def __init__(self, model, device="cpu", max_length=500, **kwargs):
        super().__init__(model, device=device, **kwargs)
        self.max_length = max_length

    def __call__(self, text, **kwargs):
        """
        This method computes feature embeddings for the given text.
        HuggingFace Feature extraction models return embeddings per token.
        To get the embedding vector of a text, we simply take the average.

        Args:
            text (str): The text for which we compute the embedding.
            **kwargs: Additional arguments to be passed to the pipeline.

        Returns:
            List[float]: The average feature embeddings computed by the model.
        """

        text = self.crop_to_max_length(text, max_length=self.max_length)
        # This will return a list of lists (one list for each word in the text)
        embedding = self.pipeline(text, **kwargs)[0]

        # For simplicity, we'll just average all word vectors to get a sentence embedding
        avg_embedding = [sum(col) / len(col) for col in zip(*embedding)]

        return avg_embedding


class HFTextGenerationTask(HFPipelineTask):
    def __init__(
        self,
        model,
        device="cpu",
        max_prompt_length=500,
        max_new_tokens=500,
        **kwargs
    ):
        super().__init__(model, device=device, **kwargs)
        self.max_prompt_length = max_prompt_length
        self.max_new_tokens = max_new_tokens

    def __call__(self, text, **kwargs):
        """
        Run the model to complete the text.
        Args:
            text (str): prompt to complete.
            return_full_text (bool, optional, defaults to True):
                If True, returns the full text, if False, only added text is returned.
                Only significant if return_text is True.
            clean_up_tokenization_spaces (bool, optional, defaults to False):
                If True, removes extra spaces in text output.
            prefix (str, optional): Adds prefix to prompt.
            handle_long_generation (str, optional): By default, doesn't handle long generation.
                Provides strategies to address this based on your use case:
                    None: Does nothing special
                    "hole": Truncates left of input, leaving a gap for generation.
                        Might truncate a lot of the prompt, not suitable when generation exceeds model capacity.
            Other arguments from transformers.TextGenerationPipeline.__call__ are supported as well. Link:
            https://huggingface.co/docs/transformers/main/main_classes/pipelines#transformers.TextGenerationPipeline.__call__

        """
        text = self.crop_to_max_length(text, self.max_prompt_length)

        max_new_tokens = kwargs.pop("max_new_tokens", self.max_new_tokens)

        output = self.pipeline(text, max_new_tokens=max_new_tokens, **kwargs)
        return output[0]["generated_text"]
