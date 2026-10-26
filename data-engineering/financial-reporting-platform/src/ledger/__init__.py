"""Double-entry ledger for the financial reporting platform."""
# Lazy import: importing the submodule would also run its __main__ block.
__all__ = [
    "Account",
    "JournalEntry",
    "Posting",
    "Ledger",
    "generate_workload",
    "trial_balance",
    "close_period",
    "income_statement",
    "balance_sheet",
]


def __getattr__(name):
    """Lazy attribute access so `import src.ledger` doesn't run journal.py."""
    if name in __all__:
        from . import journal as _journal
        return getattr(_journal, name)
    raise AttributeError(f"module 'src.ledger' has no attribute {name!r}")
