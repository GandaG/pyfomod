########
Glossary
########

It's important to understand some base concepts about fomod and xml that are going to be used
extensively:

fomod
    **F**\ all\ **o**\ ut **mod**. This is the origin of the name and the format but today it can be
    used for any game.

fomod installer
    The fomod installer consists of the files *info.xml* and *ModuleConfig.xml*. *info.xml* contains
    all the base information for the installer while *ModuleConfig.xml* contains all the configuration
    needed to run the installer.

package
    ``Package`` is used in reference to the entire folder that contains the mod to be installed. It is
    in this folder that the *fomod* folder will be present if the ``package`` has an installer.

    An example::

        package
        ├── fomod
        │   ├── info.xml
        │   └── ModuleConfig.xml
        └── mod_file

tree
    This is the tree that represents the parsed installer files. So, essentially, it's the content
    of the installer files in python form.

oprhan element
    An element that is NOT the tree's root and does not a have a parent. Usually the result of a copy
    or removal operation.
