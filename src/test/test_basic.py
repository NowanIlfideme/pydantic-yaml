"""Tests for the basic functionality advertised in README."""


def test_import():
    """Ensure pydantic_yaml can be imported."""
    from pydantic_yaml import __version__

    assert __version__ != "0.0.0"
