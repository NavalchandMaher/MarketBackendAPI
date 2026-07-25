import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.common.v3_service import V3Service
import services.common.v3_service as v3_module


class FakeLearningLogsCollection:
    def __init__(self):
        self.docs = []
        self._query = {}

    @staticmethod
    def _matches(doc, query):
        for key, value in query.items():
            if isinstance(value, dict):
                if "$gte" in value and doc.get(key) < value["$gte"]:
                    return False
            elif doc.get(key) != value:
                return False
        return True

    def find(self, query):
        self._query = query
        return self

    def sort(self, *args):
        return self

    def limit(self, *args):
        return self

    def __iter__(self):
        return iter([doc for doc in self.docs if self._matches(doc, self._query)])

    def find_one(self, query, sort=None):
        return next((doc for doc in self.docs if self._matches(doc, query)), None)

    def insert_one(self, doc):
        doc_id = f"log-{len(self.docs) + 1}"
        stored = dict(doc, _id=doc_id)
        self.docs.append(stored)
        return SimpleNamespace(inserted_id=doc_id)

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc is None:
            return SimpleNamespace(matched_count=0)
        doc.update(update["$set"])
        return SimpleNamespace(matched_count=1)

    def delete_one(self, query):
        doc = self.find_one(query)
        if doc is None:
            return SimpleNamespace(deleted_count=0)
        self.docs.remove(doc)
        return SimpleNamespace(deleted_count=1)


def test_manual_learning_log_crud_is_user_scoped(monkeypatch):
    collection = FakeLearningLogsCollection()
    monkeypatch.setattr(v3_module, "learning_logs", collection)

    created = V3Service.create_learning_log(
        {
            "title": "  EMA lesson  ",
            "description": "  Wait for confirmation.  ",
            "category": "lesson",
            "metadata": {"symbol": "BTCUSDT"},
        },
        user_id="user-1",
    )

    assert created["id"] == "log-1"
    assert created["title"] == "EMA lesson"
    assert created["user_id"] == "user-1"
    assert V3Service.learning_history(user_id="user-2") == []

    updated = V3Service.update_learning_log(
        "log-1",
        {
            "title": "EMA lesson updated",
            "description": "Use the higher-timeframe trend.",
            "category": "insight",
            "metadata": {},
        },
        user_id="user-1",
    )
    assert updated["category"] == "insight"
    assert V3Service.get_learning_log("log-1", user_id="user-2") is None

    assert V3Service.delete_learning_log("log-1", user_id="user-2")["success"] is False
    assert V3Service.delete_learning_log("log-1", user_id="user-1")["success"] is True
