"""Tests for basic functionality."""

from typing import Type

import pytest

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as
from pydantic_yaml.examples.models import A, Empty, root


@pytest.mark.parametrize(
    ["fn", "model"],
    [("a.yaml", A), ("a-1.1.yaml", A), ("a-1.2.yaml", A), ("a.yaml", Empty)],
)
def test_simple_files(fn: str, model: Type[BaseModel]):
    """Test simple file loading."""
    file = root / fn
    parse_yaml_file_as(model, file)
