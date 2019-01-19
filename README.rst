=======
pyfomod
=======
.. image:: https://img.shields.io/pypi/v/pyfomod.svg?style=flat-square&label=PyPI
    :target: https://pypi.org/project/pyfomod/
.. image:: https://img.shields.io/pypi/pyversions/pyfomod.svg?style=flat-square&label=Python%20Versions
    :target: https://pypi.org/project/pyfomod/
.. image:: https://img.shields.io/travis/GandaG/pyfomod/master.svg?style=flat-square&label=Linux%20Build
    :target: https://travis-ci.org/GandaG/pyfomod
.. image:: https://img.shields.io/appveyor/ci/GandaG/pyfomod/master.svg?style=flat-square&label=Windows%20Build
    :target: https://ci.appveyor.com/project/GandaG/pyfomod/branch/master

*A high-level fomod library written in Python.*

*pyfomod* makes it easy to work on fomod installers:

- Pythonic data struture
- Easy data extraction and modification
- No need to deal with complex xml schemas or trial and error changes

*pyfomod* automatically ignores any schema errors in an installer and corrects them
when writing - you can fix most schema errors simply by parsing then writing the
installer with *pyfomod*.

Installation
------------

To install *pyfomod*, use pip::

    pip install pyfomod

Quick Examples
--------------

Use an existing installer::

   >>> root = pyfomod.parse("path/to/package")

Get the installer metadata::

   >>> root.name
   Example Name
   >>> root.author
   Example Author
   >>> root.description
   This is an example of metadata!
   >>> root.version
   1.0.0
   >>> root.website
   https://www.nexusmods.com/example/mods/1337

Create a new installer::

   >>> root = pyfomod.Root()

Save the installer::

   >>> pyfomod.write(root, "path/to/package")

Documentation
-------------

For more information check out *pyfomod*'s documentation at `pyfomod.rtfd.io <https://pyfomod.rtfd.io>`_

Issues
------

Please use the `GitHub issue tracker <https://github.com/GandaG/pyfomod/issues>`_ to submit bugs or request features.

What Is Fomod Anyway?
---------------------

Fomod is a package format for mod installers. It's game-agnostic, meaning it
works on any game. It follows a specific package struture with a mandatory
xml file in a subfolder that follows a specific xml schema and an optional
xml file that does not. For more information visit the
`fomod documentation <https://github.com/GandaG/fomod-docs>`_

Development
-----------

Setup a virtualenv, install `flit` and run::

    flit install -s

This will install an editable version of *pyfomod* and all dev packages.
To publish::

    flit publish
