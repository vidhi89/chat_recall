from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ChatMessage:
    id: str
    timestamp: str
    sender: str
    text: str
    message_type: str = "text"
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    forwarded: bool = False
    media_type: Optional[str] = None

    def to_dict(self):
        return asdict(self)