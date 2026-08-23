"""Shared helpers for extracting docstring/description comments from Pydantic models.

These are engine-agnostic: both the `ruamel` and `yamlrocks` backends use them to decide
*what* text to attach as a comment, while the engine-specific code decides *how* to attach it.
"""

from typing import Any, Literal

from pydantic import BaseModel
from pydantic.fields import FieldInfo

__all__ = ["CommentsOptions", "get_doc"]

CommentsOptions = Literal["fields-only", "models-only"] | bool


def get_doc(obj: BaseModel | FieldInfo | Any, opts: CommentsOptions) -> str | None:
    """Get documentation for the model or field, taking options into account."""
    if isinstance(obj, BaseModel):
        if opts in (True, "models-only"):
            return getattr(obj, "__doc__", None)
        return None
    elif isinstance(obj, FieldInfo):
        if opts in (True, "fields-only"):
            return obj.description
        return None
    return None
