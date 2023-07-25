"""Test for dataclasses in Pydantic v2."""

import pytest

from pydantic.version import VERSION as PYDANTIC_VERSION
from pydantic.dataclasses import dataclass
from pydantic_yaml import to_yaml_str


@dataclass
class ExampleDataclass:
    """Example dataclass."""

    foo: str = "bar"


@pytest.mark.skipif(PYDANTIC_VERSION < "2", reason="Only supported for Pydantic v2.")
def test_pydantic_v2_dataclass():
    """Test doc-explained Dataclass support in Pydantic V2."""
    from pydantic import RootModel

    obj = ExampleDataclass(foo="wuz")
    assert to_yaml_str(RootModel[ExampleDataclass](obj)) == "foo: wuz\n"
