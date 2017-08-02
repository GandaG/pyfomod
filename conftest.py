import os
import subprocess

from lxml import etree

import pytest
from pyfomod import io, parser


@pytest.fixture
def valid_fomod(tmpdir):
    """
    Very simply, return the path to the root of a valid
    fomod-containing package.
    """
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


@pytest.fixture
def missing_info_fomod(valid_fomod):
    """
    Returns a fomod-containing package with a missing
    info.xml file.
    """
    info_path = os.path.join(valid_fomod, 'fomod', 'info.xml')
    os.remove(info_path)
    return valid_fomod


@pytest.fixture
def missing_config_fomod(valid_fomod):
    """
    Returns a fomod-containing package with a missing
    ModuleConfig.xml file.
    """
    config_path = os.path.join(valid_fomod, 'fomod', 'ModuleConfig.xml')
    os.remove(config_path)
    return valid_fomod

@pytest.fixture
def single_parse(valid_fomod):
    """
    A simple parse of valid fomod files.
    Returns an *info*, *config* tuple.
    """
    fomod_files = io.get_installer_files(valid_fomod)
    info = etree.parse(fomod_files[0], parser=parser.FOMOD_PARSER).getroot()
    config = etree.parse(fomod_files[1], parser=parser.FOMOD_PARSER).getroot()
    return info, config
