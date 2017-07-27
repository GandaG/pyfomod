import os

import requests
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

    try:
        info_path = os.path.join(fomod_path, 'info.xml')
        info_url = ("https://raw.githubusercontent.com/fomod-lang/fomod/"
                    "master/examples/02/fomod/info.xml")
        with open(info_path, 'wb') as info_file:
            file_content = requests.get(info_url).content
            info_file.write(file_content)

        config_path = os.path.join(fomod_path, 'ModuleConfig.xml')
        config_url = ("https://raw.githubusercontent.com/fomod-lang/fomod/"
                      "master/examples/02/fomod/ModuleConfig.xml")
        with open(config_path, 'wb') as config_file:
            file_content = requests.get(config_url).content
            config_file.write(file_content)
    except requests.exceptions.ConnectionError:
        pytest.skip("No internet connection.")

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
