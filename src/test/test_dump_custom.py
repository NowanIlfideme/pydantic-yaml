"""Test custom dumping behavior."""

import pytest
from pydantic import BaseModel

from pydantic_yaml import to_yaml_str
from pydantic_yaml.examples.base_models import HasEnums
from pydantic_yaml.examples.common import MyIntEnum, MyStrEnum

has_enums = HasEnums(opts=MyStrEnum.option1, vals=[MyIntEnum.v1, MyIntEnum.v2])


@pytest.mark.parametrize(
    ["mdl", "kwargs", "expected"],
    [
        [has_enums, dict(default_flow_style=False), "opts: option1\nvals:\n- 1\n- 2\n"],
        [has_enums, dict(default_flow_style=True), "{opts: option1, vals: [1, 2]}\n"],
        [has_enums, dict(indent=4), "opts: option1\nvals:\n    - 1\n    - 2\n"],
        [has_enums, dict(indent=6, map_indent=2), "opts: option1\nvals:\n      - 1\n      - 2\n"],
    ],
)
def test_dump_kwargs(mdl: BaseModel, kwargs: dict, expected: str):
    """Test dumping keyword arguments."""
    res = to_yaml_str(mdl, **kwargs)
    assert res == expected
