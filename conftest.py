import os

import pytest
import requests


@pytest.fixture
def valid_fomod(tmpdir):
    """
    Very simply, return the path to the root of a valid
    fomod-containing package.
    """
    fomod_path = os.path.join(str(tmpdir), 'fomod')
    os.mkdir(fomod_path)

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
