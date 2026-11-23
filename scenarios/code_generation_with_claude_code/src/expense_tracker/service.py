from collections import defaultdict

from .models import CATEGORIES, Expense
from .storage import JsonStorage


class ExpenseService:
    def __init__(self, storage: JsonStorage):
        self.storage = storage

    def add(self, amount: float, category: str, description: str = "", date: str | None = None) -> Expense:
        if amount <= 0:
            raise ValueError("amount must be positive")
        if category not in CATEGORIES:
            raise ValueError(f"unknown category: {category}")
        expenses = self.storage.load()
        next_id = max((e.id for e in expenses), default=0) + 1
        expense = Expense(next_id, amount, category, description, date or Expense.today())
        expenses.append(expense)
        self.storage.save(expenses)
        return expense

    def list(self, category: str | None = None) -> list[Expense]:
        expenses = self.storage.load()
        if category:
            expenses = [e for e in expenses if e.category == category]
        return expenses

    def delete(self, expense_id: int) -> bool:
        expenses = self.storage.load()
        remaining = [e for e in expenses if e.id != expense_id]
        if len(remaining) == len(expenses):
            return False
        self.storage.save(remaining)
        return True

    def total_by_category(self) -> dict[str, float]:
        totals: dict[str, float] = defaultdict(float)
        for e in self.storage.load():
            totals[e.category] += e.amount
        return dict(totals)

    # --- Practice stubs: implement / extend these with Claude Code ---

    def monthly_summary(self, year: int, month: int) -> dict:
        """TODO: return {'total': float, 'by_category': {...}, 'count': int} for the month."""
        raise NotImplementedError

    def export_csv(self, path: str) -> None:
        """TODO: write all expenses to a CSV file."""
        raise NotImplementedError

    def update(self, expense_id: int, **fields) -> Expense:
        """TODO: update fields of an existing expense, with validation."""
        raise NotImplementedError
