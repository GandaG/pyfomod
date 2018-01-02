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
This module holds the the key classes necessary for the high-level api.
"""

from lxml import etree

from .base import FomodElement


class Root(FomodElement):
    """
    This class is used with the 'config' tag.

    It provides access to all values from the 'info.xml' file via properties
    as well as high-level functions and properties to read and modify the
    'ModuleConfig.xml' file.
    """
    @property
    def info_root(self):
        """
        FomodElement:
            Returns the root of the 'info' xml tree. Used exclusively for
            accessing the low-level api for the other tree.
        """
        return etree.ElementTree(self).parser.info_root

    @property
    def name(self):
        """
        str: Returns the name of the mod.
        """
        name_elem = self.find('moduleName')
        return name_elem.text or ''

    @name.setter
    def name(self, name):
        name_elem = self.find('moduleName')
        name_elem.text = name

    @property
    def author(self):
        """
        str: Returns the author of the mod.
        """
        return self._info_root_getter('Author')

    @author.setter
    def author(self, author):
        self._info_root_setter('Author', author)

    @property
    def version(self):
        """
        str: Returns the version of the mod.
        """
        return self._info_root_getter('Version')

    @version.setter
    def version(self, version):
        self._info_root_setter('Version', version)

    @property
    def description(self):
        """
        str: Returns the description of the mod.
        """
        return self._info_root_getter('Description')

    @description.setter
    def description(self, description):
        self._info_root_setter('Description', description)

    @property
    def website(self):
        """
        str: Returns the website of the mod.
        """
        return self._info_root_getter('Website')

    @website.setter
    def website(self, website):
        self._info_root_setter('Website', website)

    @property
    def image(self):
        """
        str: Returns the cover image of the mod.
        """
        image_elem = self.find('moduleImage')
        if image_elem is None:
            return ''
        return image_elem.get_attribute('path')

    @image.setter
    def image(self, path):
        image_elem = self.find('moduleImage')
        if image_elem is None:
            image_elem = self.add_child('moduleImage')
        image_elem.set_attribute('path', path)

    def _info_root_getter(self, tag):
        elem = self.info_root.find(tag)
        if elem is None:
            return ''
        return elem.text or ''

    def _info_root_setter(self, tag, value):
        elem = self.info_root.find(tag)
        if elem is None:
            elem = self.info_root.add_child(tag)
        elem.text = value


class InstallPattern(FomodElement):
    """
    This class is used with the 'pattern' tag under
    'conditionalFileInstalls'.

    It provides access to each pattern's files to be installed
    as well as the corresponding dependency network.
    """
    pass


class Dependencies(FomodElement):
    """
    This class is used with the 'dependencies', 'visible', and
    'moduleDependencies' tags.

    It provides access to a dependencies network. The truth value
    of this class is influenced by its dependency type ('And' or 'Or')
    and by its actual dependencies.
    """
    pass


class InstallStep(FomodElement):
    """
    This class is used with the 'installStep' tag.

    Provides access to a single install step.
    """
    pass


class Group(FomodElement):
    """
    This class is used with the 'group' tag.

    Provides access to a plugin group within an install step.
    """
    pass


class Plugin(FomodElement):
    """
    This class is used with the 'plugin' tag.

    Provides access to a singular plugin and its properties.
    """
    pass


class TypeDependency(FomodElement):
    """
    This class is used with the 'dependencyType' tag.

    Provides access to a list of patterns that determine the
    plugin's type, based on dependencies.
    """
    pass


class TypePattern(FomodElement):
    """
    This class is use with the 'pattern' tag under 'dependencyType'.

    Provides access to a dependency network and the type it sets.
    """
    pass
