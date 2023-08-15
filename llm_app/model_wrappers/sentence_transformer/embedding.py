from llm_app.model_wrappers.base import BaseModel


class SentenceTransformerTask(BaseModel):
    def __init__(self, model: str, device: str = "cpu", **kwargs):
        """
        Wrapper for sentence-transformers.
        Arguments:
            model: model name or path
        """
        from sentence_transformers import SentenceTransformer

        super().__init__(**kwargs)
        self.model = SentenceTransformer(model_name_or_path=model, device=device)

    def __call__(self, text: str, **kwargs) -> str:
        """
        Arguments:
            text: input text string.
            **kwargs: Check out https://www.sbert.net/
        """
        return self.model.encode(text, **kwargs).tolist()
