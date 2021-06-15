from pathlib import Path

import pytest

from pydantic_yaml import VersionedYamlModel


def test_versioned_yaml():
    """Test VersionedYamlModel."""

    file = Path(__file__).parent / "versioned.yaml"

    class A(VersionedYamlModel):
        foo: str = "bar"

    class B(VersionedYamlModel):
        foo: str = "bar"

        class Config:
            min_version = "2.0.0"

    A.parse_file(file)
    with pytest.raises(ValueError):
        B.parse_file(file)
