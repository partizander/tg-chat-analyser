from pathlib import Path
from typing import Any, Dict, List


class BaseProcessor:
    def __init__(self, output_dir: Path, **kwargs: Any):
        self.output_dir = output_dir
        self.ctx = kwargs

    def run(self, messages: List[Dict[str, Any]], **kwargs: Any) -> None:
        raise NotImplementedError
