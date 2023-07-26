from model_wrappers.base import BaseModel


class LlamaCPP(BaseModel):
    def __init__(self, model: str, **kwargs):
        """
        Wrapper of the Python Llama CPP model.
        Arguments:
            model: model path, the model needs to be downloaded (e.g. HuggingFace)
            **kwargs: Check out https://llama-cpp-python.readthedocs.io/en/latest/api-reference/
        """
        from llama_cpp import Llama

        super().__init__(**kwargs)
        self.model = Llama(model_path=model)

    def __call__(self, text: str, **kwargs) -> str:
        """ """
        return self.model(text, **kwargs)["choices"][0]["text"]
