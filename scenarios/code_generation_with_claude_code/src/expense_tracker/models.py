from dataclasses import dataclass, asdict
from datetime import date

CATEGORIES = ("food", "transport", "rent", "utilities", "entertainment", "other")


@dataclass
class Expense:
    id: int
    amount: float
    category: str
    description: str
    date: str  # ISO format YYYY-MM-DD

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(**data)

    @staticmethod
    def today() -> str:
        return date.today().isoformat()
