import os
import subprocess

from lxml import etree
from copy import deepcopy

import pytest
from pyfomod import io, parser


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
