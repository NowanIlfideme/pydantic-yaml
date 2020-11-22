import os
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import setup

from pydantic_yaml import __version__

description = "Blah"

setup(
    name="pydantic_yaml",
    version=str(__version__),
    description=description,
    long_description=description,
    long_description_content_type="text/markdown",
    author="Anatoly Makarevich",
    author_email="anatoly_mak@yahoo.com",
    url="https://github.com/nowanilfideme/pydantic_yaml",
    license="MIT",
    packages=["pydantic_yaml"],
    python_requires=">=3.6",
    zip_safe=False,
    install_requires=["pydantic"],
    extras_require={
        "pyyaml": ["pyyaml"],
        "ruamel-old": ["ruamel.yaml<0.15"],  # In-place 
        "ruamel-new": ["ruamel.yaml>=0.15"],  # Using new API starting 0.15
        "development": ["black", "flake8", "bump2version"],
    },
)
