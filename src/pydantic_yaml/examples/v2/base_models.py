"""Models used for testing, just normal `pydantic.BaseModel` objects."""

# type: ignore

from typing import List, Optional, Union

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_serializer,
    model_validator,
)
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


Recursive.model_rebuild()


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

    @field_serializer("ss", "sb")
    def _serialize_secrets(self, secret: Union[SecretStr, SecretBytes], _info):
        """Serialize secret fields.

        See Also
        --------
        https://docs.pydantic.dev/latest/usage/serialization/#custom-serializers
        """
        return _encode_secret(secret)


class HasEnums(BaseModel):
    """Base model with enums."""

    opts: MyStrEnum
    vals: List[MyIntEnum]


class _Name(BaseModel):  # type: ignore[no-redef]
    """First/last names."""

    given: str
    family: str


class UsesRefs(BaseModel):  # type: ignore[no-redef]
    """Example for the reference data."""

    bill_to: _Name = Field(alias="bill-to")
    ship_to: _Name = Field(alias="ship-to")

    # Pydantic config
    model_config = ConfigDict(populate_by_name=True)


class CustomRootListStr(BaseModel):  # type: ignore[no-redef]
    """Model with a custom root type.

    See Also
    --------
    https://docs.pydantic.dev/blog/pydantic-v2-alpha/#changes-to-basemodel
    https://github.com/pydantic/pydantic/blob/2b9459f20d094a46fa3093b43c34444240f03646/tests/test_parse.py#L95-L113
    """

    root: List[str]

    @model_validator(mode="before")
    @classmethod
    def _populate_root(cls, values):
        if isinstance(values, CustomRootListStr):
            return values
        return {"root": values}

    @model_serializer(mode="wrap")
    def _serialize(self, handler, info):
        data = handler(self)
        if info.mode == "json":
            return data["root"]
        else:
            return data

    @classmethod
    def model_modify_json_schema(cls, json_schema):
        """JSON schema changer."""
        return json_schema["properties"]["root"]


class CustomRootListObj(BaseModel):  # type: ignore[no-redef]
    """Model with a custom root type, list of objects.

    See Also
    --------
    https://docs.pydantic.dev/blog/pydantic-v2-alpha/#changes-to-basemodel
    https://github.com/pydantic/pydantic/blob/2b9459f20d094a46fa3093b43c34444240f03646/tests/test_parse.py#L95-L113
    """

    root: List[Union[A, B]]

    @model_validator(mode="before")
    @classmethod
    def _populate_root(cls, values):
        if isinstance(values, CustomRootListObj):
            return values
        return {"root": values}

    @model_serializer(mode="wrap")
    def _serialize(self, handler, info):
        data = handler(self)
        if info.mode == "json":
            return data["root"]
        else:
            return data

    @classmethod
    def model_modify_json_schema(cls, json_schema):
        """JSON schema changer."""
        return json_schema["properties"]["root"]
