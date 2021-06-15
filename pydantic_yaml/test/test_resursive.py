from __future__ import annotations

from pathlib import Path
from typing import Optional

import pytest
from pydantic_yaml import YamlModel


class Outer(YamlModel):
    a: int
    inner: Optional[Outer]


Outer.update_forward_refs()


def test_recursive_yaml():
    """Test how we react to (unsupported) recursive YAML documents."""

    from typing import Optional

    from pydantic_yaml import YamlModel

    file = Path(__file__).parent / "recursive.yaml"

    class A(YamlModel):
        """Recursive model."""

        a: int
        inner: Optional[A]

    A.update_forward_refs()

    with pytest.raises(ValueError):
        A.parse_file(file)
