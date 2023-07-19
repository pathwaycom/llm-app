from model_wrappers.base import BaseModel
from transformers import pipeline


class HFPipelineTask(BaseModel):
    def __init__(self, model_name, device="cpu", **kwargs):
        super().__init__(**kwargs)
        self.pipeline = pipeline(model=model_name, device=device)
        self.tokenizer = self.pipeline.tokenizer

    def crop_to_max_length(self, input_string, max_length=500):
        tokens = self.tokenizer.tokenize(input_string)
        if len(tokens) > max_length:
            tokens = tokens[:max_length]
        return self.tokenizer.convert_tokens_to_string(tokens)


class HFFeatureExtractionTask(HFPipelineTask):
    def __init__(self, max_length=500, **kwargs):
        super().__init__(**kwargs)
        self.max_length = max_length

    def __call__(self, text, **kwargs):

        text = self.crop_to_max_length(text, max_length=self.max_length)
        # This will return a list of lists (one list for each word in the text)
        embedding = self.pipeline(text, **kwargs)[0]

        # For simplicity, we'll just average all word vectors to get a sentence embedding
        avg_embedding = [sum(col) / len(col) for col in zip(*embedding)]

        return avg_embedding


class HFTextGenerationTask(HFPipelineTask):
    def __init__(self, max_prompt_length=500, max_new_tokens=500, **kwargs):
        super().__init__(**kwargs)
        self.max_prompt_length = max_prompt_length
        self.max_new_tokens = max_new_tokens

    def __call__(self, text, **kwargs):
        text = self.crop_to_max_length(text, self.max_prompt_length)

        max_new_tokens = kwargs.pop("max_new_tokens", self.max_new_tokens)

        output = self.pipeline(text, max_new_tokens=max_new_tokens, **kwargs)
        return output[0]["generated_text"]
