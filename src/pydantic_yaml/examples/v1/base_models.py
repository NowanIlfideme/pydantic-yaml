"""Models used for testing, just normal `pydantic.BaseModel` objects."""

# mypy: ignore-errors

from typing import List, Optional, Union

from pydantic import BaseModel, Field
from pydantic.types import SecretBytes, SecretStr

from pydantic_yaml.examples.common import MyIntEnum, MyStrEnum


class Empty(BaseModel):
    """Empty model."""


class A(BaseModel):
    """Class A."""

    a: str


class B(BaseModel):
    """Class B."""

    b: str


class Recursive(BaseModel):
    """Recursive model, which is actually unsupported."""

    inner: Optional["Recursive"]
    a: int  # Doesn't work!


Recursive.update_forward_refs()


class SecretTstModel(BaseModel):
    """Normal model with secret fields. This can't be roundtripped."""

    ss: SecretStr
    sb: SecretBytes


def _encode_secret(obj: Union[SecretStr, SecretBytes, None]) -> Union[str, bytes, None]:
    """Encode secret value."""
    if obj is None:
        return None
    return obj.get_secret_value()


class SecretTstModelDumpable(SecretTstModel):
    """Round-trippable model. This will save secret fields as the raw values."""

    class Config:
        """Configuration."""

        json_encoders = {SecretStr: _encode_secret, SecretBytes: _encode_secret}


class HasEnums(BaseModel):
    """Base model with enums."""

    opts: MyStrEnum
    vals: List[MyIntEnum]


# pydantic v1


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


class CustomRootListStr(BaseModel):
    """Model with a custom root type.

    See Also
    --------
    https://docs.pydantic.dev/usage/models/#custom-root-types
    """

    __root__: List[str]


class CustomRootListObj(BaseModel):
    """Model with a custom root type, list of objects.

    See Also
    --------
    https://docs.pydantic.dev/usage/models/#custom-root-types
    """

    __root__: List[Union[A, B]]
