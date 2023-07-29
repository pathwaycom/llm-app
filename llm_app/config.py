from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    app_variant: str
    rest_host: str
    rest_port: int
    api_key: str
    cache_dir: str
    model_locator: str
    data_dir: Optional[str] = None
    embedder_locator: Optional[str] = None
    embedding_dimension: Optional[int] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
