from typing import Dict, Type
from .base import BaseProcessor

REGISTRY: Dict[str, Type[BaseProcessor]] = {}


def register(name: str):
    def deco(cls: Type[BaseProcessor]):
        REGISTRY[name] = cls
        return cls

    return deco
