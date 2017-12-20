# Copyright 2016 Daniel Nunes
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This module handles all IO (including parsing and serializing).
"""

import errno
import os


def get_installer_files(search_path, create_missing=False):
    """
    Searches and returns the installer files from a package or sub path.

    Args:
        search_path (str): The path to search for these files at.
            `search_path` must point to a folder.

            Both a subfolder named *fomod* in the `search_path` and
            `search_path` itself being the *fomod* folder are supported.
            Priority is given to *fomod* subfolder.
            `search_path`. Examples:

            * `folder/somefolder/` - *somefolder* contains a *fomod* subfolder;
            * `folder/somefolder/fomod`.
        create_missing (boolean, optional): If ``True``, instead of raising an
            exception if there are no fomod files, the file structure is
            created and the file paths for the newly created structure are
            returned.

    Returns:
        tuple(str, str): Paths to info.xml and ModuleConfig.xml, respectively.

    Raises:
        FileNotFoundError: If there are issues with finding files or folder.
    """

    # normalize path to get rid of trailing stuff and properly set slashes
    os.path.normpath(search_path)

    # if the path doesn't exist just raise FileNotFoundError
    if not os.path.isdir(search_path):
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                search_path)

    # look for a fomod subfolder
    fomod_path = os.path.join(search_path, 'fomod')
    if not os.path.isdir(fomod_path):
        fomod_path = ''  # not found, reset and continue

    # check if the search_path is a fomod folder
    if os.path.basename(search_path) == 'fomod' and not fomod_path:
        fomod_path = search_path

    # if fomod_path hasn't been found, error out
    if not fomod_path:
        if create_missing:
            fomod_path = os.path.join(search_path, 'fomod')
            os.makedirs(fomod_path)
        else:
            raise FileNotFoundError(errno.ENOENT,
                                    os.strerror(errno.ENOENT),
                                    'fomod')

    # grab the files and check if they exist
    info_path = os.path.join(fomod_path, 'info.xml')
    if not os.path.isfile(info_path) and not create_missing:
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                'info.xml')

    config_path = os.path.join(fomod_path, 'ModuleConfig.xml')
    if not os.path.isfile(config_path) and not create_missing:
        raise FileNotFoundError(errno.ENOENT,
                                os.strerror(errno.ENOENT),
                                'ModuleConfig.xml')

    # both files exist, life is good
    return info_path, config_path
