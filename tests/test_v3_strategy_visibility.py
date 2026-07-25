import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.common.v3_service import V3Service
import services.common.v3_service as v3_module


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *args):
        return self

    def __iter__(self):
        return iter(self.docs)


class FakeStrategiesCollection:
    def __init__(self, docs):
        self.docs = docs

    def _matches(self, doc, query):
        for key, value in query.items():
            if key == "$or":
                if not any(self._matches(doc, item) for item in value):
                    return False
            elif key == "$and":
                if not all(self._matches(doc, item) for item in value):
                    return False
            elif doc.get(key) != value:
                return False
        return True

    def find(self, query):
        return FakeCursor([doc for doc in self.docs if self._matches(doc, query)])

    def find_one(self, query):
        return next((doc for doc in self.docs if self._matches(doc, query)), None)

    def update_many(self, *args, **kwargs):
        return None

    def update_one(self, query, update):
        doc = self.find_one(query)
        if doc is None:
            return type("Result", (), {"matched_count": 0})()
        doc.update(update["$set"])
        return type("Result", (), {"matched_count": 1})()


def test_trader_sees_own_and_only_published_system_strategies(monkeypatch):
    collection = FakeStrategiesCollection(
        [
            {"_id": "own", "user_id": "trader-1", "strategy_name": "My private", "strategy_type": "Scalping"},
            {"_id": "other", "user_id": "trader-2", "strategy_name": "Other private", "strategy_type": "Scalping"},
            {"_id": "public", "strategy_name": "Public system", "strategy_type": "System", "published": True},
            {"_id": "draft", "strategy_name": "Draft system", "strategy_type": "System", "published": False},
        ]
    )
    monkeypatch.setattr(v3_module, "strategies", collection)

    visible = V3Service.list_strategies(user_id="trader-1", role="Trader")

    assert {strategy["strategy_name"] for strategy in visible} == {
        "My private",
        "Public system",
    }
    assert V3Service.get_strategy("draft", user_id="trader-1", role="Trader") is None


def test_only_admin_can_update_global_system_strategies(monkeypatch):
    system_strategy = {
        "_id": "system-1",
        "strategy_name": "Global strategy",
        "strategy_type": "System",
        "published": True,
    }
    collection = FakeStrategiesCollection([system_strategy])
    monkeypatch.setattr(v3_module, "strategies", collection)

    assert (
        V3Service.update_strategy(
            "system-1", {"strategy_name": "Changed"}, user_id="trader-1", role="Trader"
        )
        is None
    )
    assert system_strategy["strategy_name"] == "Global strategy"

    updated = V3Service.update_strategy(
        "system-1", {"strategy_name": "Changed"}, user_id="admin-1", role="Admin"
    )
    assert updated["strategy_name"] == "Changed"
