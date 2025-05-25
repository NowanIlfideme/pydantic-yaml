"""Regression tests for when 'type' to parse as is not a class."""

import sys
from typing import Union

from pydantic_yaml import parse_yaml_raw_as
from pydantic import BaseModel


class MyStrModel(BaseModel):
    """String model."""

    my_prop: str


class MyListModel(BaseModel):
    """List of strings model."""

    my_prop: list[str]


def test_non_class_types_union() -> None:
    """Test non-class types."""
    inst1: MyStrModel | MyListModel = parse_yaml_raw_as(
        Union[MyStrModel, MyListModel],  # type: ignore  # noqa
        "my_prop: my_yaml_string",
    )
    assert isinstance(inst1, MyStrModel)
    inst2: MyStrModel | MyListModel = parse_yaml_raw_as(
        Union[MyStrModel, MyListModel],  # type: ignore  # noqa
        "my_prop: [my_yaml_string]",
    )
    assert isinstance(inst2, MyListModel)


if sys.version_info > (3, 10, 0):

    def test_non_class_types_uniontype() -> None:
        """Test non-class types."""
        inst1: MyStrModel | MyListModel = parse_yaml_raw_as(  # type: ignore
            MyStrModel | MyListModel,  # type: ignore
            "my_prop: my_yaml_string",
        )
        assert isinstance(inst1, MyStrModel)
        inst2: MyStrModel | MyListModel = parse_yaml_raw_as(  # type: ignore
            MyStrModel | MyListModel,  # type: ignore
            "my_prop: [my_yaml_string]",
        )
        assert isinstance(inst2, MyListModel)
