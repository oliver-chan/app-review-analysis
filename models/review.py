from dataclasses import dataclass
from datetime import datetime


@dataclass
class Review:
    id: str
    source: str  # "app_store" or "play_store"
    app_name: str
    rating: int  # 1-5
    title: str
    body: str
    date: datetime
    author: str
    version: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source": self.source,
            "app_name": self.app_name,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "date": self.date.isoformat(),
            "author": self.author,
            "version": self.version,
        }
