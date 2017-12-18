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
.. image:: https://img.shields.io/coveralls/github/GandaG/pyfomod/master.svg?style=flat-square&label=Coverage
	:target: https://coveralls.io/github/GandaG/pyfomod?branch=master


*Parse, create and modify fomod installers.*

**pyfomod** makes it easy to work on fomod installers:

- No need to deal with non-human-readable formats;
- No need to copy/paste from other installers;
- No need for trial-and-error changes;
- No need to know how to write xml;
- No need to modify complex files to get what you want.

**pyfomod** lets you create your own installer with minimal knowledge of fomod or even xml.


Quick Examples
--------------

- Create a new installer:

  .. code-block:: python

    >>> from pyfomod import new, to_string
    >>> new_installer = new()
    >>> info_content, conf_content = to_string(new_installer)
    >>> print(info_content.decode('utf8'))  # pyfomod always serializes to utf-8
    <?xml version='1.0' encoding='utf-8'?>
    <fomod/>

    >>> print(conf_content.decode('utf8'))
    <?xml version='1.0' encoding='utf-8'?>
    <config xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">
      <moduleName/>
    </config>


- Validate other installers:

  .. code-block:: python

    >>> from pyfomod import validate
    >>> validate("path/to/info.xml")
    True

    >>> validate("path/to/ModuleConfig.xml")
    False


- Writing a brand new installer:

  .. code-block:: bash

    example
    └── mod_file.dat


  .. code-block:: python

    >>> from pyfomod import new, write
    >>> new_installer = new()
    >>> write(new_installer, 'path/to/example')


  .. code-block:: bash

    example
    ├── fomod
    │   ├── info.xml
    │   └── ModuleConfig.xml
    └── mod_file.dat


Installation
------------

To install *pyfomod*, use pip::
    
    pip install pyfomod

Simple as that! You now have *pyfomod* available in your environment.


Overview
--------

The high-level API is meant for users looking to do quick and common operations on an installer:

- No prior knowledge of fomod or xml needed;
- Simple, intuitive functions and methods;
- All operations are based on the commonly used installer UI.

The low-level API is meant for users that need more control than the high-level offers.
It's based on the `lxml package <http://lxml.de/tutorial.html>`_ and all its features are available
(the only overwritten methods are copy/deepcopy). However, it is recommended to only use
functions/methods that do not modify the xml tree - more info on this topic on the documentation.

- Full control over the xml trees.
- Validation occurs on every method/function that modifies the trees, ensuring a perfect end result;
- **lxml**'s and **pyfomod**'s API's can be used side-by-side with no risk due to the previous point;
- Ability to check which attributes/children are valid for each element before modifying.


Issues
------

Please use the `GitHub issue tracker <https://github.com/GandaG/pyfomod/issues>`_ to submit bugs or request features.


Documentation
-------------

For more information check out *pyfomod*'s documentation at `pyfomod.rtfd.io <https://pyfomod.rtfd.io>`_
