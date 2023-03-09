from pathlib import Path

import pytest
from pydantic import ValidationError

try:
    import semver  # noqa

    INSTALLED_SEMVER = True
except ImportError:
    INSTALLED_SEMVER = False


@pytest.mark.skip(not INSTALLED_SEMVER, reason="`semver` is not installed.")
def test_versioned_yaml():
    """Test VersionedYamlModel."""
    from pydantic_yaml.ext.versioned_model import VersionedYamlModel

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


@pytest.mark.skip(not INSTALLED_SEMVER, reason="semver not installed.")
def test_versioned_docs():
    """Test docs for versioned model."""
    from pydantic_yaml.ext.semver import SemVer
    from pydantic_yaml.ext.versioned_model import VersionedYamlModel

    class A(VersionedYamlModel):
        """Model with min, max constraints as None."""

        foo: str = "bar"

    class B(VersionedYamlModel):
        """Model with a maximum version set."""

        foo: str = "bar"

        class Config:
            min_version = "2.0.0"

    ex_yml = """
    version: 1.0.0
    foo: baz
    """

    a = A.parse_raw(ex_yml)
    assert a.version == SemVer("1.0.0")
    assert a.foo == "baz"

    with pytest.raises(ValidationError):
        B.parse_raw(ex_yml)
