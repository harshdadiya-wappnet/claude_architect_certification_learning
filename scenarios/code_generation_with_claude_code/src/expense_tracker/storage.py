import json
from pathlib import Path

from .models import Expense

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "expenses.json"


class JsonStorage:
    """Persists expenses to a JSON file."""

    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = Path(path)

    def load(self) -> list[Expense]:
        if not self.path.exists():
            return []
        with open(self.path) as f:
            return [Expense.from_dict(d) for d in json.load(f)]

    def save(self, expenses: list[Expense]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump([e.to_dict() for e in expenses], f, indent=2)
