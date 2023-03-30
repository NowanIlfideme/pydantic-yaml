"""Models used for testing."""

from pathlib import Path

from pydantic import BaseModel, Field

root = Path(__file__).resolve().parent / "data"


class Empty(BaseModel):
    """Empty model."""


class A(BaseModel):
    """Class A."""

    a: str


class _Name(BaseModel):
    """First/last names."""

    given: str
    family: str


class UsesRefs(BaseModel):
    """Example for the reference data."""

    bill_to: _Name = Field(alias="bill-to")
    ship_to: _Name = Field(alias="ship-to")

    class Config:
        """Pydantic configuration class."""

        allow_population_by_field_name = True
