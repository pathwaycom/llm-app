import functools
import os
from abc import ABC

import diskcache
import pathway as pw


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
    def __init__(self):
        self.cache = _Cache()

    def __call__(self, text: str, **kwargs):
        raise NotImplementedError()

    def apply(
        self,
        text: pw.ColumnExpression | str,
        **kwargs,
    ) -> pw.ColumnExpression:
        return pw.apply_async(self.cache(self.__call__), text=text, **kwargs)
