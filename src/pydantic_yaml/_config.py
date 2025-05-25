"""YAML options definition, analogous to the `pydantic.ConfigDict` implementation."""

from typing import Literal, TypedDict


CommentStyle = Literal["above", "inline"]
StringScalarStyle = Literal[None, "quoted", "plain", "literal", "folded"]


class YamlConfig(TypedDict, total=False):
    """A TypedDict for configuring Pydantic-YAML behaviour."""

    comment_style: CommentStyle
    """Where to place comments for fields: 'above' (default) or 'inline'."""

    string_scalar_style: StringScalarStyle
    """Preferred scalar style for string values.

    - None: automatic / default
    - 'quoted': always use double quotes
    - 'plain': bare values
    - 'literal': '|' block style for multi-line
    - 'folded': '>' folded style

    See Also
    --------
    https://yaml-multiline.info/
    """


DEFAULT_YAML_CONFIG = YamlConfig(
    comment_style="above",
    string_scalar_style=None,
)
