from datetime import datetime
from typing import Any, Dict

from db.mongodb import notifications


class NotificationService:
    @staticmethod
    def emit(
        event_type: str,
        title: str,
        message: str,
        channel: str = "log",
        metadata: Dict[str, Any] | None = None,
        user_id: str | None = None,
    ) -> Dict[str, Any]:
        payload = {
            "event_type": event_type,
            "title": title,
            "message": message,
            "channel": channel,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
        }
        if user_id:
            payload["user_id"] = user_id
        notifications.insert_one(payload)
        return payload
