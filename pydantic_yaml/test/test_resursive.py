from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest

from pydantic_yaml import YamlModel


class A(YamlModel):
    """Recursive model."""

    a: int
    inner: Optional["A"]


A.update_forward_refs()


def test_recursive_yaml():
    """Test how we react to (unsupported) recursive YAML documents."""

    file = Path(__file__).parent / "recursive.yaml"

    with pytest.raises(ValueError):
        A.parse_file(file, content_type="application/yaml")
