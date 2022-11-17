from dataclasses import dataclass
from typing import Any, Dict, Union


@dataclass
class Experiment:
    id: str
    config: Dict[str, Any]
    results: Union[Any, Dict[str, Any]]
    metadata: Dict[str, Any] = None
