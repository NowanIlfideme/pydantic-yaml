from pathlib import Path

import pytest
from pydantic import ValidationError

from pydantic_yaml.ext.versioned_model import VersionedYamlModel


def test_versioned_yaml():
    """Test VersionedYamlModel."""

    file = Path(__file__).parent / "versioned.yaml"

    class A(VersionedYamlModel):
        foo: str = "bar"

    class B(VersionedYamlModel):
        foo: str = "bar"

        class Config:
            min_version = "2.0.0"

    class C(VersionedYamlModel):
        foo: str = "baz"

        class Config:
            max_version = "0.5.0"

    A.parse_file(file)

    with pytest.raises(ValidationError):
        B.parse_file(file)

    with pytest.raises(ValidationError):
        C.parse_file(file)

    with pytest.raises(ValueError):

        class BadVersionConstraint(VersionedYamlModel):
            class Config:
                min_version = "3.0.0"
                max_version = "2.1.0"
