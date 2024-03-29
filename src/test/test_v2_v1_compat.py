"""Tests for Pydantic v2-v1 compatibility."""

import pytest

from pydantic.version import VERSION as PYDANTIC_VERSION
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as


@pytest.mark.skipif(PYDANTIC_VERSION < "2", reason="Only supported for Pydantic v2.")
def test_pydantic_v2_v1_compat() -> None:
    """Test v1-compatibility in pydantic v2."""
    from pydantic.v1 import BaseModel

    class MyModel(BaseModel):
        """Simple model for dumping."""

        v: str = "vee"

    yml = to_yaml_str(MyModel(v="tree"))  # type: ignore
    obj = parse_yaml_raw_as(MyModel, yml)  # type: ignore
    assert obj.v == "tree"
