"""Models used for testing, just normal `pydantic.BaseModel` objects."""

from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

import pydantic
from pydantic import BaseModel, Field
from pydantic.types import SecretBytes, SecretStr

root = Path(__file__).resolve().parent / "base_models"


class Empty(BaseModel):
    """Empty model."""


class A(BaseModel):
    """Class A."""

    a: str


class B(BaseModel):
    """Class B."""

    b: str


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


class MyStrEnum(str, Enum):
    """String enumeration for testing."""

    option1 = "option1"
    option2 = "option2"


class MyIntEnum(int, Enum):
    """Integer enumeration for testing."""

    v1 = 1
    v2 = 2


class HasEnums(BaseModel):
    """Base model with enums."""

    opts: MyStrEnum
    vals: List[MyIntEnum]


if pydantic.VERSION < "2":

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

else:
    # pydantic v2

    from pydantic import root_validator, model_serializer

    class CustomRootListStr(BaseModel):  # type: ignore[no-redef]
        """Model with a custom root type.

        See Also
        --------
        https://docs.pydantic.dev/blog/pydantic-v2-alpha/#changes-to-basemodel
        https://github.com/pydantic/pydantic/blob/2b9459f20d094a46fa3093b43c34444240f03646/tests/test_parse.py#L95-L113
        """

        root: List[str]

        @root_validator(pre=True)
        @classmethod
        def _populate_root(cls, values):
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

        @root_validator(pre=True)
        @classmethod
        def _populate_root(cls, values):
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
