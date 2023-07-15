"""Models used for testing, just normal `pydantic.BaseModel` objects."""

# type: ignore

__all__ = [
    "Empty",
    "A",
    "B",
    "Recursive",
    "SecretTstModel",
    "SecretTstModelDumpable",
    "MyStrEnum",
    "MyIntEnum",
    "HasEnums",
    "UsesRefs",
    "CustomRootListStr",
    "CustomRootListObj",
    "root",
]

from pathlib import Path

import pydantic

from .common import MyIntEnum, MyStrEnum

root = Path(__file__).resolve().parent / "base_models"

if pydantic.version.VERSION < "2":
    from .v1.base_models import (
        A,
        B,
        CustomRootListObj,
        CustomRootListStr,
        Empty,
        HasEnums,
        Recursive,
        SecretTstModel,
        SecretTstModelDumpable,
        UsesRefs,
    )
else:
    from .v2.base_models import (
        A,
        B,
        CustomRootListObj,
        CustomRootListStr,
        Empty,
        HasEnums,
        Recursive,
        SecretTstModel,
        SecretTstModelDumpable,
        UsesRefs,
    )
