from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Segment:
    start: float
    end: float
    text: str
    language: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Chunk:
    id: str
    start: float
    end: float
    transcript_start: float
    transcript_end: float
    transcript: List[Segment] = field(default_factory=list)
    keyframes: List[str] = field(default_factory=list)
    topic_hint: str = ""
    status: str = "pending"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["transcript"] = [item.to_dict() for item in self.transcript]
        return data
