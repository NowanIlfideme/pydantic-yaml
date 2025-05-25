"""Comments options."""

from textwrap import dedent
from typing import Literal


CommentsOptions = Literal["fields-only", "models-only"] | bool


def as_yaml_comment(value: str | None) -> str | None:
    """Convert a value (e.g. docstring) into a YAML comment."""
    if value is None:
        return None
    lines = dedent(value.lstrip("\n").rstrip()).split("\n")
    return "\n".join([f"# {v}".strip() for v in lines])
