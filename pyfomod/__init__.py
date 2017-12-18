#!/usr/bin/env python

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
The main API module. Should contain everything the user needs.
"""

from .installer import Installer, MissingDependency
from .parser import from_string, new, parse, to_string, write
from .validation import (EmptyInstError, EmptySourceError, ErrorChecker,
                         FlagLabelMismatchError, FlagValueMismatchError,
                         MissingFileError, MissingFolderError,
                         MissingImageError, NoAuthorError, NoNameError,
                         NoVersionError, NoWebsiteError, UnusedFilesError,
                         assert_valid, check_for_errors, validate)

__all__ = ['assert_valid', 'validate', 'from_string',
           'to_string', 'parse', 'write', 'new',
           'ErrorChecker', 'check_for_errors',
           'NoNameError', 'NoAuthorError', 'NoVersionError',
           'NoWebsiteError', 'EmptyInstError',
           'EmptySourceError', 'UnusedFilesError',
           'MissingFolderError', 'MissingFileError',
           'MissingImageError', 'FlagLabelMismatchError',
           'FlagValueMismatchError', 'Installer', 'MissingDependency']
