from dataclasses import dataclass
from typing import Any, Dict, Union


@dataclass
class Experiment:
    """
    convenience dataclass to represent a completed experiment
    """

    id: str
    config: Dict[str, Any]
    result: Union[Any, Dict[str, Any]]
    metadata: Dict[str, Any] = None
