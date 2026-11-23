import pytest

from expense_tracker.service import ExpenseService
from expense_tracker.storage import JsonStorage


@pytest.fixture
def service(tmp_path):
    return ExpenseService(JsonStorage(tmp_path / "expenses.json"))


def test_add_assigns_incrementing_ids(service):
    a = service.add(10, "food")
    b = service.add(5, "transport")
    assert (a.id, b.id) == (1, 2)


def test_add_rejects_non_positive_amount(service):
    with pytest.raises(ValueError):
        service.add(0, "food")


def test_add_rejects_unknown_category(service):
    with pytest.raises(ValueError):
        service.add(10, "gambling")


def test_total_by_category(service):
    service.add(10, "food")
    service.add(15, "food")
    service.add(4, "transport")
    assert service.total_by_category() == {"food": 25, "transport": 4}


def test_delete(service):
    e = service.add(10, "food")
    assert service.delete(e.id) is True
    assert service.delete(e.id) is False


# TODO: tests for monthly_summary, export_csv, update
