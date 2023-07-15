"""Common types used in examples."""

from enum import Enum


class MyStrEnum(str, Enum):
    """String enumeration for testing."""

    option1 = "option1"
    option2 = "option2"


class MyIntEnum(int, Enum):
    """Integer enumeration for testing."""

    v1 = 1
    v2 = 2
