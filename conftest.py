import os
import subprocess

from lxml import etree
from copy import deepcopy

import pytest
from pyfomod import io, parser
import pyfomod


@pytest.fixture(scope='session')
def example_fomod(tmpdir_factory):
    """
    Very simply, return the path to the root of a valid
    fomod-containing package.
    """
    tmpdir = tmpdir_factory.mktemp('fomod_package')
    fomod_path = os.path.join(str(tmpdir), 'fomod')
    os.mkdir(fomod_path)

    svn_cmd = "svn export --force " \
              "https://github.com/fomod-lang/fomod/trunk/examples/02 " + \
              str(tmpdir)
    command = subprocess.Popen(svn_cmd, stdout=subprocess.PIPE,
                               shell=True, stderr=subprocess.STDOUT)
    stdout, stderr = command.communicate()

    if "Unable to connect to a repository" in str(stdout):
        pytest.skip("No internet connection.")
    elif "svn: not found" in str(stdout):
        pytest.skip("Subversion is required to download the valid installer.")

    return str(tmpdir)


@pytest.fixture(scope='session')
def simple_parse(example_fomod):
    """
    A simple parse of valid fomod files.
    Returns an *info*, *config* tuple.
    """
    fomod_files = io.get_installer_files(example_fomod)
    info = etree.parse(fomod_files[0], parser=parser.FOMOD_PARSER).getroot()
    config = etree.parse(fomod_files[1], parser=parser.FOMOD_PARSER).getroot()
    return info, config

@pytest.fixture(scope='function')
def info_tree(simple_parse):
    """
    A function-scoped fixture that returns a copy of the info tree.
    """
    return deepcopy(simple_parse[0])

@pytest.fixture(scope='function')
def conf_tree(simple_parse):
    """
    A function-scoped fixture that returns a copy of the conf tree.
    """
    return deepcopy(simple_parse[1])

@pytest.fixture(scope='session')
def simple_parser():
    """
    A session-scoped fixture that returns a simple parser with no class lookup.
    """
    s_parser = etree.XMLParser(remove_blank_text=True)
    s_parser.set_element_class_lookup(
            parser._SpecialLookup(parser._FomodLookup()))
    return s_parser

@pytest.fixture(scope='function')
def schema_mod():
    """
    A funcion-scoped fixture that sets up a modifiable schema in
    pyfomod.__init__ so that the FOMOD_PARSER will use that instead
    of the regular one. This will be reverted at the end of the function.
    """
    schema_orig = pyfomod.FOMOD_SCHEMA_TREE
    pyfomod.FOMOD_SCHEMA_TREE = deepcopy(schema_orig)
    # tests should still access the schema via 'import pyfomod'
    yield
    pyfomod.FOMOD_SCHEMA_TREE = schema_orig
