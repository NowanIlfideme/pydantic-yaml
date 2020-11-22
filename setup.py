import os
import re
import sys
from importlib.machinery import SourceFileLoader
from pathlib import Path

from setuptools import setup

from pydantic_yaml import __version__

path_readme = Path(__file__).parent / "README.md"

description = "Adds some YAML functionality to the excellent `pydantic` library."

with path_readme.open() as f:
    long_description = f.read()

setup(
    name="pydantic_yaml",
    version=str(__version__),
    description=description,
    long_description=long_description,
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
        "ruamel-old": ["ruamel.yaml<0.15"],  # In-place repalcement
        "ruamel-new": ["ruamel.yaml>=0.15"],  # Using new API starting 0.15
        "development": ["black", "flake8", "bump2version"],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet",
    ],
)
