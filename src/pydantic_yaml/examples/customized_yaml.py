"""Pydantic models with customized fields."""

from typing import Annotated, ClassVar

from pydantic import BaseModel, Field

from pydantic_yaml._config import YamlConfig


class ExampleA(BaseModel):
    """Example model A."""

    yaml_config: ClassVar[YamlConfig] = {}
    """YAML configuration."""

    opt1: Annotated[str, Field(description="Option 1.")] = "foo"
