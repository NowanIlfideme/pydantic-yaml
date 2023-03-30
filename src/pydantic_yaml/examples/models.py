"""Models used for testing."""

from pathlib import Path

from pydantic import BaseModel

root = Path(__file__).resolve().parent / "data"


class Empty(BaseModel):
    """Empty model."""


class A(BaseModel):
    """Class A."""

    a: str
