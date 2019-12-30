#!/usr/bin/env python
import ast
import os
import re

from setuptools import setup


here = os.path.dirname(__file__)
with open(os.path.join(here, "README.rst")) as f:
    long_description = f.read()

metadata = {}
with open(os.path.join(here, "btdualboot.py")) as f:
    rx = re.compile("(__version__|__author__|__url__|__licence__) = (.*)")
    for line in f:
        m = rx.match(line)
        if m:
            metadata[m.group(1)] = ast.literal_eval(m.group(2))
version = metadata["__version__"]

setup(
    name="btdualboot",
    version=version,
    author="Marius Gedminas",
    author_email="marius@gedmin.as",
    url="https://github.com/mgedmin/btdualboot",
    description="Synchronize Bluetooth pairing keys between Windows and Linux",
    long_description=long_description,
    keywords="bluetooth linux windows",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: POSIX",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    license="licence",
    python_requires=">=3.6",

    py_modules=["btdualboot"],
    zip_safe=False,
    install_requires=[
        "python-registry",
    ],
    entry_points={
        "console_scripts": [
            "btdualboot = btdualboot:main",
        ],
    },
)
