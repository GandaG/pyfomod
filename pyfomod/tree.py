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

import re
from contextlib import suppress

from lxml import etree

from .base import FomodElement


class TreeCompatibilityError(Exception):
    """
    To be raised whenever there is an incompatibility of the tree
    with this API.
    """
    pass


class Root(FomodElement):
    """
    This class is used with the 'config' tag.

    It provides access to all values from the 'info.xml' file via properties
    as well as high-level functions and properties to read and modify the
    'ModuleConfig.xml' file.
    """
    # these expressions are for evaluating when a tree is completely
    # incompatible with this API
    hard_incompat = ['//installSteps[not(@order)]',
                     '//installSteps[@order="Ascending"]',
                     '//installSteps[@order="Descending"]',
                     '//optionalFileGroups[not(@order)]',
                     '//optionalFileGroups[@order="Ascending"]',
                     '//optionalFileGroups[@order="Descending"]',
                     '//plugins[not(@order)]',
                     '//plugins[@order="Ascending"]',
                     '//plugins[@order="Descending"]',
                     '//dependencyType']

    # these expressions are for specific values that will be
    # ignored/interpreted differently by this API
    soft_incompat = ['//moduleName[@position]',
                     '//moduleName[@colour]',
                     '//moduleImage[@showImage]',
                     '//moduleImage[@showFade]',
                     '//moduleImage[@height]',
                     '//fommDependency',
                     '//fileDependency[@state="Inactive"]',
                     '//file[@alwaysInstall]',
                     '//file[@installIfUsable]',
                     '//file[@priority]',
                     '//folder[@alwaysInstall]',
                     '//folder[@installIfUsable]',
                     '//folder[@priority]',
                     '//typeDescriptor/type[@type="CouldBeUsable"]']

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

    def _xpath_to_message(self, *error_expressions):
        """
        To be used with hard_incompat and soft_incompat.
        Sort of parses them and transforms them into a human-readable
        message
        """
        tag_regex = r'//([\w/]*)'
        attr_regex = r'//([\w/]*)\[(?:@|not\(@)(\w*)'
        value_regex = r'//([\w/]*)\[@(\w*)=[\'"](\w*)[\'"]'

        init_msg = 'The following {} incompatibilities have been found:'
        soft_msg = init_msg.format('soft')
        hard_msg = init_msg.format('hard')

        soft_msgs = []
        hard_msgs = []

        for error_exp in error_expressions:
            # the order of the regexs matter
            for regex in (value_regex, attr_regex, tag_regex):
                match = re.match(regex, error_exp)
                if match is None:
                    continue

                error_msg = '    The '
                with suppress(IndexError):
                    error_msg += 'value {} of '.format(match.group(3))
                with suppress(IndexError):
                    error_msg += 'attribute {} in '.format(match.group(2))
                with suppress(IndexError):
                    error_msg += 'element {};'.format(match.group(1))

                if error_exp in self.soft_incompat:
                    soft_msgs.append(error_msg)
                elif error_exp in self.hard_incompat:
                    hard_msgs.append(error_msg)
                else:
                    raise AssertionError('Couldn\'t find expression.')

        final_msg = ''
        if soft_msgs:
            final_msg += '\n'.join((soft_msg, *soft_msgs))
            final_msg += '\n'
        if hard_msgs:
            final_msg += '\n'.join((hard_msg, *hard_msgs))
        return final_msg

    def is_tree_compatible(self, raise_error=False):
        """
        Checks whether this fomod tree is compatible with the usage of this
        API. Please note that the FomodElement, validation and installer API's
        are always available and compatible with any fomod tree.

        If **raise_error** is ``True`` then a
        :class:`~pyfomod.tree.TreeCompatibilityError` is raised with a
        descriptive error message instead of returning False. In this case
        soft incompatibilities are also checked.

        Soft incompatibilities are attribute values, attributes or elements
        that this API can't work with and that are safe to ignore or give a
        different meaning to. Below is a list of all soft incompatibilties and
        the action taken by this API:

        * ``position`` attribute in ``moduleName`` element - ignored;
        * ``colour`` attribute in ``moduleName`` element - ignored;
        * ``showImage`` attribute in ``moduleImage`` element - ignored;
        * ``showFade`` attribute in ``moduleImage`` element - ignored;
        * ``height`` attribute in ``moduleImage`` element - ignored;
        * ``fommDependency`` element - ignored;
        * ``Inactive`` value of ``state`` attribute in ``fileDependency``
          element - same meaning as ``Active``;
        * ``alwaysInstall`` attribute in ``file`` element - ignored;
        * ``installIfUsable`` ttribute in ``file`` element - ignored;
        * ``priority`` attribute in ``file`` element - ignored;
        * ``alwaysInstall`` attribute in ``folder`` element - ignored;
        * ``installIfUsable`` ttribute in ``folder`` element - ignored;
        * ``priority`` attribute in ``folder`` element - ignored;
        * ``CouldBeUsable`` value in ``type`` attribute in
          ``typeDescriptor/type`` element - same meaning as ``NotUsable``.

        Hard incompatibilities are attribute values or elements that, unlike
        soft incompatibilites, are not safe to ignore or change meaning on the
        fly. Therefore, as long as they're present in the tree this API will
        not be safe to work with. Please note that there is no actual barrier
        to API usage, meaning you can use it freely even with hard
        incompatibilites present - it will raise the appropriate error when it
        can no longer function.

        * The values ``Ascending`` or ``Descending`` in order attribute in
          ``installSteps`` element;
        * No order attribute in ``installSteps`` element;
        * The values ``Ascending`` or ``Descending`` in order attribute in
          optionalFilleGroups element;
        * No order attribute in ``optionalFileGroups`` element;
        * The values ``Ascending`` or ``Descending`` in order attribute in
          ``plugins`` element;
        * No order attribute in ``plugins`` element;
        * ``dependencyType`` element;

        Returns:
            bool: True if compatible, False otherwise.
        """
        xpath_eval = etree.XPathEvaluator(self)
        errored_exps = []

        # soft first
        for exp in self.soft_incompat:
            if raise_error and xpath_eval(exp):
                errored_exps.append(exp)

        # hard next
        for exp in self.hard_incompat:
            if xpath_eval(exp):
                if raise_error:
                    errored_exps.append(exp)
                else:
                    return False
        if raise_error and errored_exps:
            raise TreeCompatibilityError(self._xpath_to_message(*errored_exps))
        return True


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
