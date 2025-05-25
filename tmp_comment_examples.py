"""Test stuff."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, RootModel
from pydantic_yaml import to_yaml_str


class ModelA(BaseModel):
    """My model A."""

    a: int = 1
    b: str = "b"
    c: Annotated[float, Field(description="See description...")] = 3


ma = ModelA()
print(to_yaml_str(ma, add_comments=True))


class ModelB(BaseModel):
    """My model A."""

    model_config = ConfigDict(use_attribute_docstrings=True)

    sub1: ModelA
    """Sub-model."""
    sub2: list[ModelA]
    """Sub-models as a list."""
    sub3: dict[str, ModelA]
    """Sub-models as a dict."""
    sub4: list[dict[str, ModelA]]
    """Even more crazy nested dict."""


mb = ModelB(
    sub1=ma,
    sub2=[ma],
    sub3={"ma": ma},
    sub4=[{"ma": ma}, {"mo": ma}, {"mia": ma}],
)
print(to_yaml_str(mb, add_comments=True))


class ModelR(RootModel[list[ModelA]]):
    """List of model A."""


mr = ModelR(root=[ma])
print(to_yaml_str(mr, add_comments=True))
