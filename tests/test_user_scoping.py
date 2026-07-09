from services.paper_trading import PaperTrading
from services.learning_engine import LearningEngine
import services.paper_trading as paper_module
import services.learning_engine as learning_module


class FakeCollection:
    def __init__(self, docs=None):
        self.docs = docs or []
        self.last_query = None

    def find(self, query=None):
        self.last_query = query
        return self

    def sort(self, *args, **kwargs):
        return self

    def limit(self, *args, **kwargs):
        return self

    def __iter__(self):
        return iter(self.docs)


def test_paper_trades_are_filtered_by_user(monkeypatch):
    fake_collection = FakeCollection([
        {"_id": "1", "trade_id": "T1", "status": "OPEN", "user_id": "user-1"}
    ])
    monkeypatch.setattr(paper_module, "paper_trades", fake_collection)
    monkeypatch.setattr(paper_module, "closed_trades", FakeCollection())

    trades = PaperTrading.get_open_trades(user_id="user-1")

    assert fake_collection.last_query == {"status": "OPEN", "user_id": "user-1"}
    assert len(trades) == 1
    assert trades[0]["trade_id"] == "T1"


def test_learning_logs_are_filtered_by_user(monkeypatch):
    fake_collection = FakeCollection([
        {"_id": "1", "title": "test", "user_id": "user-1"}
    ])
    monkeypatch.setattr(learning_module, "learning_logs", fake_collection)
    monkeypatch.setattr(learning_module, "closed_trades", FakeCollection())
    monkeypatch.setattr(learning_module, "strategies", FakeCollection())
    monkeypatch.setattr(learning_module, "market_snapshots", FakeCollection())

    logs = LearningEngine.logs(user_id="user-1")

    assert fake_collection.last_query == {"user_id": "user-1"}
    assert len(logs) == 1
    assert logs[0]["title"] == "test"
