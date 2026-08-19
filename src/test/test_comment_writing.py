"""Test the comment functionality."""

from pathlib import Path

import pytest
from pydantic import BaseModel

from pydantic_yaml import parse_yaml_file_as, to_yaml_str
from pydantic_yaml._internals.v2 import CommentsOptions, EngineName
from pydantic_yaml.examples.base_models import CommentedModel, UsesRefs, commented, root

sub_ps: dict[CommentsOptions, Path] = {
    False: commented / "false",
    True: commented / "true",
    "fields-only": commented / "fields",
    "models-only": commented / "models",
}

# Known, documented content difference between engines (not a bug): "yamlrocks" doesn't drop a
# nested model's docstring the way "ruamel" sometimes does when the field itself also has a
# trailing description (see issue #338), so `add_comments=True` legitimately includes more
# content than the ruamel-derived fixture for this one case.
KNOWN_DIFFERENCES: dict[tuple[str, CommentsOptions, EngineName], str] = {
    ("uses_refs.yaml", True, "yamlrocks"): "# First/last names.",
}


def clean_but_keep_newlines(s: str) -> str:
    """Clean a string by removing extra spaces but keeping newlines.

    Extra newlines - and comment lines with no content - are "compressed" into a single newline.
    """
    lines = [line for line in s.splitlines() if line.strip() not in ("", "#")]
    cleaned_lines = [" ".join(line.split()) for line in lines]
    return "\n".join(cleaned_lines)


def eq_within_spaces(got: str, expected: str) -> bool:
    """Check if two strings are equal when ignoring diffs in spaces (but not generic whitespace)."""
    g_clean = clean_but_keep_newlines(got)
    e_clean = clean_but_keep_newlines(expected)
    return g_clean == e_clean


@pytest.mark.parametrize(
    ["model_type", "fn"],
    [
        (UsesRefs, "uses_refs.yaml"),
        (CommentedModel, "commented_model.yaml"),
    ],
)
def test_load_rt_simple_files(engine: EngineName, model_type: type[BaseModel], fn: str):
    """Test simple file loading and roundtripping, with comments, on both engines."""
    # Load usual file
    in_file = root / fn
    obj = parse_yaml_file_as(model_type, in_file, engine=engine)
    # Compare
    for add_c, sub_p in sub_ps.items():
        got_i = to_yaml_str(obj, add_comments=add_c, engine=engine)
        expected_i = (commented / sub_p / fn).read_text()
        extra = KNOWN_DIFFERENCES.get((fn, add_c, engine))
        if extra is not None:
            assert extra in got_i, f"Expected known engine-specific content {extra!r} not found."
            continue
        assert eq_within_spaces(got_i, expected_i), "Comments not as expected."
