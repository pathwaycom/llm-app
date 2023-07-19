import functools
import os
from abc import ABC, abstractmethod
from typing import Union

import diskcache
import pathway as pw
from model_wrappers.api_clients.clients import APIClient


class _Cache:
    """A simple cache"""

    def __init__(self) -> None:
        if cache_dir := os.environ.get("PATHWAY_CACHE_DIR"):
            self.cache = diskcache.Cache(cache_dir)
        else:
            self.cache = {}

    def __call__(self, fun):
        base_name = f"{fun.__module__}_{fun.__qualname__}"

        @functools.wraps(fun)
        def wrapper(*args, **kwargs):
            key = f"{base_name}({(args, kwargs)})"
            if key not in self.cache:
                self.cache[key] = fun(*args, **kwargs)
            return self.cache[key]

        return wrapper


class BaseModel(ABC):
    def __init__(self, **kwargs):
        self.config = kwargs
        self.cache = _Cache()

    def __call__(self, text: str, **kwargs):
        raise NotImplementedError()

    def apply(
        self,
        text: Union[pw.ColumnExpression, str],
        **kwargs,
    ) -> pw.ColumnExpression:

        return pw.apply_async(self.cache(self.__call__), text=text, **kwargs)


class APIModel(BaseModel):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(**kwargs)
        self.api_client = self.get_client(api_key)

    @abstractmethod
    def get_client(self, api_key: str) -> APIClient:
        pass
