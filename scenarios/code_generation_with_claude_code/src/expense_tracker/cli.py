import argparse

from .service import ExpenseService
from .storage import JsonStorage


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="expenses", description="Track personal expenses")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Add an expense")
    add.add_argument("amount", type=float)
    add.add_argument("category")
    add.add_argument("-d", "--description", default="")
    add.add_argument("--date", default=None, help="YYYY-MM-DD (default: today)")

    ls = sub.add_parser("list", help="List expenses")
    ls.add_argument("-c", "--category", default=None)

    rm = sub.add_parser("delete", help="Delete an expense by id")
    rm.add_argument("id", type=int)

    sub.add_parser("summary", help="Totals per category")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = ExpenseService(JsonStorage())

    try:
        if args.command == "add":
            e = service.add(args.amount, args.category, args.description, args.date)
            print(f"Added #{e.id}: {e.amount:.2f} [{e.category}]")
        elif args.command == "list":
            for e in service.list(args.category):
                print(f"#{e.id} {e.date} {e.amount:>8.2f} {e.category:<14} {e.description}")
        elif args.command == "delete":
            print("Deleted" if service.delete(args.id) else "Not found")
        elif args.command == "summary":
            for cat, total in service.total_by_category().items():
                print(f"{cat:<14} {total:>10.2f}")
    except ValueError as err:
        print(f"Error: {err}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
