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
This module holds the exceptions for this package.
"""


class InvalidArgument(Exception):
    """
    Used when an argument would invalidate the current document.
    """
    def __init__(self):
        msg = "The arguments used would invalidate the document."
        super(InvalidArgument, self).__init__(msg)
