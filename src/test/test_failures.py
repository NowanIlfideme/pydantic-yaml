"""Bad behaviors that should cause errors."""

from typing import Any

import pytest
from pydantic import BaseModel

from pydantic_yaml import EngineName, parse_yaml_file_as, parse_yaml_raw_as, to_yaml_str
from pydantic_yaml.examples.base_models import A, B, Recursive, root


def test_no_load_recursive(engine: EngineName):
    """Test properly rejecting loading a recursive model."""
    with pytest.raises(ValueError):
        parse_yaml_file_as(Recursive, root / "recursive.yaml", engine=engine)


@pytest.mark.parametrize("obj", ["foo", {}, set(), ..., ["some-object", 1]])
def test_no_dump(engine: EngineName, obj: Any):
    """Ensure that we don't support dumping these objects."""
    with pytest.raises((ValueError, TypeError)):
        to_yaml_str(obj, engine=engine)


@pytest.mark.parametrize(
    ["model_type", "raw"],
    [
        (B, None),
        (A, 3),
        (B, "aaa"),
        (A, "aaaaaaaaaaa"),
    ],
)
def test_no_load(engine: EngineName, model_type: type[BaseModel], raw: Any):
    """Ensure that we don't support loading these objects."""
    with pytest.raises((ValueError, TypeError)):
        parse_yaml_raw_as(model_type, raw, engine=engine)
