"""Tests for basic functionality."""

from typing import Type

import pytest

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as, to_yaml_str
from pydantic_yaml.examples.models import A, Empty, Recursive, UsesRefs, root


@pytest.mark.parametrize(
    ["fn", "model_type"],
    [
        ("a.yaml", A),
        ("a-1.1.yaml", A),
        ("a-1.2.yaml", A),
        ("a.yaml", Empty),
        ("uses_refs.yaml", UsesRefs),
    ],
)
def test_load_simple_files(fn: str, model_type: Type[BaseModel]):
    """Test simple file loading."""
    file = root / fn
    parse_yaml_file_as(model_type, file)


def test_no_load_recursive():
    """Test properly rejecting loading a recursive model."""
    with pytest.raises(ValueError):
        parse_yaml_file_as(Recursive, root / "recursive.yaml")


@pytest.mark.parametrize("model", [A(a="aaa")])
def test_write_simple_model(model: BaseModel):
    """Test output of simple models."""
    to_yaml_str(model)  # TODO: Check output vs expected?
