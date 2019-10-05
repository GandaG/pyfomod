# pyfomod

[![PyPi](https://img.shields.io/pypi/v/pyfomod.svg?style=flat-square&label=PyPI)](https://pypi.org/project/pyfomod/)
![Python Versions](https://img.shields.io/pypi/pyversions/pyfomod.svg?style=flat-square&label=Python%20Versions)
[![Build Status](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Factions-badge.atrox.dev%2FGandaG%2Fpyfomod%2Fbadge%3Fref%3Dmaster&style=flat-square)](https://actions-badge.atrox.dev/GandaG/pyfomod/goto?ref=master)

*A high-level fomod library written in Python.*

> :warning: **Note**: This is a mature library with all planned features added and no known bugs - do not be alarmed by the lack of commits.

*pyfomod* makes it easy to work on fomod installers:

- Pythonic data struture
- Easy data extraction and modification
- No need to deal with complex xml schemas or trial and error changes

*pyfomod* automatically ignores any schema errors in an installer and corrects them
when writing - you can fix most schema errors simply by parsing then writing the
installer with *pyfomod*.

## Installation

To install *pyfomod*, use pip:

    pip install pyfomod

## Quick Examples

Use an existing installer:

``` python
>>> root = pyfomod.parse("path/to/package")
```

Get the installer metadata::

``` python
>>> root.name
'Example Name'
>>> root.author
'Example Author'
>>> root.description
'This is an example of metadata!'
>>> root.version
'1.0.0'
>>> root.website
'https://www.nexusmods.com/example/mods/1337'
```

Create a new installer:

``` python
>>> root = pyfomod.Root()
```

Save the installer:

``` python
>>> pyfomod.write(root, "path/to/package")
```

## Documentation

For more information check out *pyfomod*'s documentation at [pyfomod.rtfd.io](https://pyfomod.rtfd.io)

## Issues

Please use the [GitHub issue tracker](https://github.com/GandaG/pyfomod/issues)
to submit bugs or request features.

## What Is Fomod Anyway?

Fomod is a package format for mod installers. It's game-agnostic, meaning it
works on any game. It follows a specific package struture with a mandatory
xml file in a subfolder that follows a specific xml schema and an optional
xml file that does not. For more information visit the
[fomod documentation](https://github.com/GandaG/fomod-docs).

## Development

*pyfomod* uses poetry to manage package versions:

    path/to/python.exe -m pip install poetry
    path/to/python.exe -m poetry install

Ensure that everything is correct before committing:

    path/to/python.exe -m poetry run check
    path/to/python.exe -m poetry run test

When you're done with a feature/fix, bump the version:

    path/to/python.exe -m poetry run bump2version {major|minor|patch}

To finally publish to PYPI:

    path/to/python.exe -m poetry publish --build -u $PYPI_USER -p $PYPI_PASS
