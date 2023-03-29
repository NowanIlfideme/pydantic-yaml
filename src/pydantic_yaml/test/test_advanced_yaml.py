"""Tests for advanced YAML features."""

from typing import Type

import pytest
from pydantic import BaseModel, Field

from pydantic_yaml import YamlModel

uses_refs = """
# Thanks to https://stackoverflow.com/a/2063741
bill-to: &id001
    given  : Chris
    family : Dumars
ship-to: *id001
"""


class _Name(BaseModel):
    """First/last names."""

    given: str
    family: str


class UsesRefs(YamlModel):
    """Example for the reference data."""

    bill_to: _Name = Field(alias="bill-to")
    ship_to: _Name = Field(alias="ship-to")

    class Config:
        allow_population_by_field_name = True


@pytest.mark.parametrize(
    ("raw", "model_type"),
    [
        (uses_refs, UsesRefs),
    ],
)
def test_yaml_refs(raw: str, model_type: Type[YamlModel]):
    """Tests that references are properly parsed."""
    model_type.parse_raw(raw)
