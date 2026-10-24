"""Fail-closed shadow-only reliability gate. No human or network authority."""
from .gate import evaluate, POLICY_VERSION
from .ledger import LocalLedger, IntegrityError
__all__ = ["evaluate", "POLICY_VERSION", "LocalLedger", "IntegrityError"]
