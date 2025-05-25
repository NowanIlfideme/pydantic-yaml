"""Test the comment functionality."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from pydantic_yaml import parse_yaml_file_as, to_yaml_str
from pydantic_yaml._internals.comments import CommentsOptions
from pydantic_yaml.examples.base_models import UsesRefs, commented, root

sub_ps: dict[CommentsOptions, Path] = {
    False: commented / "false",
    True: commented / "true",
    "fields-only": commented / "fields",
    "models-only": commented / "models",
}


@pytest.mark.parametrize(
    ["model_type", "fn"],
    [
        (UsesRefs, "uses_refs.yaml"),
    ],
)
def test_load_rt_simple_files(model_type: type[BaseModel], fn: str):
    """Test simple file loading and roundtripping."""
    # Load usual file
    in_file = root / fn
    obj = parse_yaml_file_as(model_type, in_file)
    # Compare
    for add_c, sub_p in sub_ps.items():
        got_i = to_yaml_str(obj, add_comments=add_c)
        expected_i = (commented / sub_p / fn).read_text()
        assert got_i == expected_i, "Comments not as expected."
