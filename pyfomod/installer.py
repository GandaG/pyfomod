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
This module provides a full installer coroutine.
"""

import os
import uuid
from collections import ChainMap, OrderedDict
from shutil import Error, copy2, copystat

from packaging.version import parse as parse_ver

from .parser import parse
from .tree import Root


class MissingDependency(Exception):
    """
    Exception raised whenever there is a missing dependency
    in a dependency network related element container.
    """
    def __init__(self, miss_deps):
        if len(miss_deps) == 1:
            missed_dep = miss_deps[0]
            message = 'Missing {}Dependency {} {}'.format(*missed_dep)
        else:
            message = 'Missing Dependencies:'
            for miss in miss_deps:
                message += '\n\t{} {} {}'.format(*miss)
        super().__init__(self, message)


class PluginNumberError(Exception):
    """
    Exception raised whenever the user has selected a wrong number
    of plugins for a given group.
    """
    def __init__(self, group_type, plugin_number):
        msg = 'Group has {} type but ' \
              'only {} plugins were selected'.format(group_type, plugin_number)
        super().__init__(self, msg)


class NotUsablePluginError(Exception):
    """
    Exception raised whenever the user has chosen a plugin that is NotUsable.
    """
    def __init__(self, name):
        msg = 'Plugin {} was selected but is NotUsable'.format(name)
        super().__init__(self, msg)


# pylint: disable=R0913
def _copytree(src, dst, symlinks=False, ignore=None, copy_function=copy2,
              ignore_dangling_symlinks=False):  # pragma: no cover
    """
    A monkey-patched version of shutil's copytree function that allows
    **dst** to already exist. It literally took one argument change -.-
    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    os.makedirs(dst, exist_ok=True)  # <- THIS WAS THE CHANGE
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.islink(srcname):
                linkto = os.readlink(srcname)
                if symlinks:
                    # We can't just leave it to `copy_function` because legacy
                    # code with a custom `copy_function` may rely on copytree
                    # doing the right thing.
                    os.symlink(linkto, dstname)
                    copystat(srcname, dstname, follow_symlinks=not symlinks)
                else:
                    # ignore dangling symlink if the flag is on
                    if not os.path.exists(linkto) and ignore_dangling_symlinks:
                        continue
                    # otherwise let the copy occurs. copy2 will raise an error
                    if os.path.isdir(srcname):
                        _copytree(srcname, dstname, symlinks, ignore,
                                  copy_function)
                    else:
                        copy_function(srcname, dstname)
            elif os.path.isdir(srcname):
                _copytree(srcname, dstname, symlinks, ignore, copy_function)
            else:
                # Will raise a SpecialFileError for unsupported file types
                copy_function(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
        except OSError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        copystat(src, dst)
    except OSError as why:
        # Copying file access times may fail on Windows
        if getattr(why, 'winerror', None) is None:
            errors.append((src, dst, str(why)))
    if errors:
        raise Error(errors)
    return dst


def _assert_dependencies(depend, flag_states, dest=None, game_version=None):
    """
    Runs through all dependencies in **depend** and if it is found to be
    lacking, MissingDependency is raised. **And** operators are shortcut
    while **Or** operators must be looked at all the way.

    Anything that the user doesn't provide is assumed to be met.
    """
    if depend is None:
        return
    operator = depend.get('operator', 'And')

    false_dependencies = []
    checks = depend.findall('*')

    for check in checks:
        if check.tag == 'gameDependency':
            if game_version is None:
                continue
            elif parse_ver(game_version) < parse_ver(check.get('version')):
                false_dependencies.append(('game', game_version, ''))

        elif check.tag == 'fileDependency':
            if dest is None:
                continue
            else:
                file_state = os.path.exists(os.path.join(dest,
                                                         check.get('file')))
                if check.get('state') == 'Missing' and file_state:
                    false_dependencies.append(('file',
                                               'missing',
                                               check.get('file')))
                elif check.get('state') in ('Active',
                                            'Inactive') and not file_state:
                    false_dependencies.append(('file',
                                               'active',
                                               check.get('file')))

        elif check.tag == 'flagDependency':
            if check.get('value') != flag_states.get(check.get('flag'), ''):
                false_dependencies.append(('flag',
                                           check.get('flag'),
                                           check.get('value')))

        elif check.tag == 'dependencies':
            _assert_dependencies(check, flag_states, dest, game_version)

        # short-circuiting
        if operator == 'And' and false_dependencies:
            raise MissingDependency(false_dependencies)

    if operator == 'Or' and len(false_dependencies) == len(checks):
        raise MissingDependency(false_dependencies)


def _collect_files(file_list, collected_files, source_path=None):
    """
    Collects all files from **file_list** and adds them to **collected_files**
    chain mapping. If **file_list** is ``None``, add an empty dict anyway to
    keep parity among install steps (no need to track which install steps added
    files this way).
    """
    file_dict = {}

    if file_list is not None:
        items = file_list.findall('*')

        for item in items:
            source = item.get('source')
            dest = item.get('destination', '')
            prio = item.get('priority', '0')
            prio_dict = file_dict.get(prio, {})

            if source_path is not None:
                source = os.path.join(source_path, source)
            prio_dict[source] = dest

            file_dict[prio] = prio_dict

    collected_files.maps.insert(0, file_dict)


def _collect_flags(flag_list, flag_states):
    """
    Much like ``_collect_files`` above, except with flags.
    """
    flag_dict = {}
    if flag_list is not None:
        flags = flag_list.findall('*')
        for flag in flags:
            flag_dict[flag.get('name')] = flag.text or ''
    flag_states.maps.insert(0, flag_dict)


def _explicit_list(root):
    """
    Very simply, return a list of all elements below **root**,
    excluding comments.
    """
    if root is None:
        return []
    return root.findall('*')


def _ordered_list(root):
    """
    Returns a list of all element with an attribute ``"name"`` under root
    which must contain an attribute ``"order"`` which determines the order
    of the list.
    """
    if root is None:
        return []
    order = root.get('order', 'Ascending')
    if order == 'Explicit':
        return _explicit_list(root)
    elif order == 'Ascending':
        reverse = False
    else:
        reverse = True
    return sorted(root.findall('*'),
                  key=lambda x: x.get('name'),
                  reverse=reverse)


class _NestedChainMap(ChainMap):
    """
    Subclass of stdlib's ChainMap that allows chaining nested dictionaries
    one level deep only.
    """
    def __getitem__(self, key):
        values = []
        for mapping in self.maps:
            try:
                values.append(mapping[key])
            except KeyError:
                pass

        if not values:
            raise KeyError(key)

        if not isinstance(values[0], dict):
            return values[0]
        result = {}
        for value in reversed(values):
            if isinstance(value, dict):
                result.update(value)
        return result


class Installer(object):
    """
    Creates an installer for the fomod in **source**. This argument can be
    either a :class:`~pyfomod.tree.Root` object or any acceptable argument
    to :func:`~pyfomod.parse`.

    **source_path** refers to the path to the source package, **dest** should
    be the target destination directory where the mod will be installed and
    **game_version** the game version. These three arguments are all optional.

    If both **source_path** and **dest** are provided, the mod files will be
    automatically installed to the target directory. Otherwise, the user will
    have to check :meth:`~pyfomod.Installer.collected_files` for the files to
    install.

    If **dest** is not provided, all *fileDependency* tags are assumed to be
    met (meaning it will be ignored and never raise
    :class:`~pyfomod.MissingDependency`). The same can be applied to
    **game_version** and *gameDependency*.

    The following pseudo-code illustrates basic usage::

        >>> from pyfomod.installer import install_fomod, MissingDependency
        >>> fomod = 'path/to/fomod'
        >>> source = 'path/to/source'
        >>> target = 'path/to/target'
        >>> game_version = '1.0.0'
        >>> installer = Installer(fomod, source, target, game_version)
        >>> # prime it (checking for dependencies, first item collection, etc.)
        >>> try:
        ...     installer.send(None)
        ... except MissingDependency:
        ...     # handle missing dependency
        ...
        >>> for step in installer:
        ...     # process info in step
        ...     # make group and plugin choices
        ...     if user_requested(previous_step):
        ...         # if you need to go back to a previous step
        ...         # just send this dict as answer
        ...         installer.send({'previous_step': True})
        ...     else:
        ...         # when you're done processing, send the resulting answer
        ...         installer.send(answer)
        ...
        >>> # whenever the loop exits the installer is done

    When the installer is primed you should always check for missing
    dependencies on *moduleDependencies* and handle the exception in some way.

    If any exception is raised by this object, the installer is completely
    stopped and considered finished. You'll need to restart the installer by
    re-instancing this class.

    The example loop provides you with a ``step`` variable. This variable is a
    dictionary that holds all the required info for each installation step.
    An example of this::

        {'name': 'Step Name',
         'groups': [{'name': 'Group Name',
                     'id': 'Unique Group ID',
                     'type': 'Group Type',
                     'plugins': [{'name': 'Plugin Name',
                                  'id': 'Unique Plugin ID',
                                  'description': 'Plugin Description',
                                  'image': 'path/to/plugin/image.png',
                                  'type': 'Plugin Type'},
                                 ...]}
                    ...]}

    The user's choices should be comunicated through the ``send`` method of the
    installer.

    To request a previous step the answer should take the form of the dict::

        {'previous_step': True}

    Be aware that the installer will interpret a request for a previous step
    whenever that specific mapping is included in the answer, regardless of
    other content.

    To answer with the user's choices of plugins, a dictionary of this form
    should be sent::

        {'Group ID': ['Plugin ID', 'Plugin ID', ...],
         ...}

    With each ``id`` corresponding to a user's choice (or in the case of group
    ID, the group in which the choice is present). Care should be taken for
    group and plugin types.

    The mod's metadata can be accessed through several properties of the
    installer. The properties :meth:`~pyfomod.Installer.flag_states` and
    :meth:`~pyfomod.Installer.collected_files` can be accessed at any time
    before, during or after the installation process to keep track of flag and
    file changes, respectively.
    """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, source, source_path=None, dest=None, game_version=None):
        if not isinstance(source, Root):
            source = parse(source)

        # setup the installer
        self.gen = self._installer(source, source_path, dest, game_version)
        self.send = self.gen.send

        # read metadata
        self._name = source.name
        self._author = source.author
        self._version = source.version
        self._description = source.description
        self._website = source.website
        self._image = source.image

        # setup flags and files chain maps
        self._flag_states = ChainMap()
        self._collected_files = _NestedChainMap()

    @property
    def name(self):
        """
        str: Returns the name of the mod.
        """
        return self._name

    @property
    def author(self):
        """
        str: Returns the author of the mod.
        """
        return self._author

    @property
    def version(self):
        """
        str: Returns the version of the mod.
        """
        return self._version

    @property
    def description(self):
        """
        str: Returns the description of the mod.
        """
        return self._description

    @property
    def website(self):
        """
        str: Returns the website of the mod.
        """
        return self._website

    @property
    def image(self):
        """
        str: Returns the cover image of the mod.
        """
        return self._image

    @property
    def flag_states(self):
        """
        dict: The current mapping of ("flag name": "flag value").
        """
        return self._flag_states

    @property
    def collected_files(self):
        """
        dict: The current mapping of ("file/folder source": "destination").
        """
        sorted_keys = sorted(self._collected_files.keys(), reverse=True)
        final = ChainMap()
        for key in sorted_keys:
            final.maps.append(self._collected_files[key])
        return final

    def __iter__(self):
        return self.gen

    def __next__(self):
        return next(self.gen)

    def _installer(self, root, source_path, dest, game_version):
        """
        install steps should be processed in a "x yield x/yield" pattern

        handle metadata in init.

        -> start
        assert dependencies are ok (raise MissingDependencies otherwise) ...
        collect requiredInstallFiles ...
        yield
        install_step_list = ...
        index = 0
        while True:
            answer = yield install_step_list[index]
            # stop here so .send() returns nothing and loop can work.
            # yield needs to be before index processing so
            # user loop can deal with StopIteration
            yield
            process answer ...
            if user_requested_previous_step:
                index = previous_index
                # pop off latest flags and files
                continue
            previous_index = index
            try:
                while True:
                    index += 1
                    if install_step_is_visible(install_step_list[index], ...):
                        break
            except IndexError:
                break  # exit loop when install steps are over
        process conditionalFileInstalls ...
        -> end
        """

        _assert_dependencies(root.find('moduleDependencies'),
                             self.flag_states,
                             dest,
                             game_version)

        _collect_files(root.find('requiredInstallFiles'),
                       self._collected_files,
                       source_path)
        # stop here to allow user to catch raised missing dependencies
        yield

        step_list = _ordered_list(root.find('installSteps'))
        previous_index = [0]
        index = -1
        while True:
            # get next visible index
            try:
                while True:
                    index += 1
                    try:
                        _assert_dependencies(step_list[index].find('visible'),
                                             self._flag_states,
                                             dest,
                                             game_version)
                    except MissingDependency:
                        pass
                    else:
                        break
            except IndexError:
                break  # exit loop when install steps are over

            # id -> plugin element dictionary
            id_dict = {}

            # step processing
            step_dict = {'name': step_list[index].get('name'), 'groups': []}
            groups = _ordered_list(step_list[index].find('optionalFileGroups'))

            # group processing
            for group in groups:
                group_dict = {'name': group.get('name'),
                              'type': group.get('type'),
                              'id': str(uuid.uuid4()),
                              'plugins': []}
                plugins = _ordered_list(group.find('plugins'))

                # plugin processing
                for plugin in plugins:
                    plugin_dict = {}
                    plugin_dict['id'] = str(uuid.uuid4())
                    plugin_dict['name'] = plugin.get('name')
                    plugin_dict['description'] = plugin.findtext('description',
                                                                 default='')

                    image = plugin.find('image')
                    if image is not None:
                        plugin_dict['image'] = image.get('path')
                    else:
                        plugin_dict['image'] = ''

                    type_elem = plugin.find('typeDescriptor')
                    plugin_type = type_elem.find('type')
                    if plugin_type is not None:
                        plugin_dict['type'] = plugin_type.get('name')
                    else:
                        default_type = type_elem.find('dependencyType/de'
                                                      'faultType').get('name')
                        patterns = type_elem.find('dependencyType/patterns')
                        pattern_list = _explicit_list(patterns)
                        for pattern in pattern_list:
                            try:
                                _assert_dependencies(
                                    pattern.find('dependencies'),
                                    self._flag_states,
                                    dest,
                                    game_version)
                            except MissingDependency:
                                pass
                            else:
                                plugin_dict['type'] = \
                                    pattern.find('type').get('name')
                                break
                        else:
                            plugin_dict['type'] = default_type

                    group_dict['plugins'].append(plugin_dict)
                    id_dict[plugin_dict['id']] = plugin

                step_dict['groups'].append(group_dict)

            answer = yield step_dict
            yield

            # check if previous step was requested
            if answer.pop('previous_step', False):
                try:
                    index = previous_index.pop() - 1
                except IndexError:
                    index = -1
                # pop off latest flags and files
                # no need to check if last step added any of this
                # because an empty dict will be added to the chainmap anyway
                if len(self._flag_states.maps) > 1:
                    self._flag_states.maps.pop(0)
                if len(self._collected_files.maps) > 2:  # first + reqinstfiles
                    self._collected_files.maps.pop(0)
                continue
            previous_index.append(index)

            # sort groups and plugins in answer
            def from_id(dict_, type_, id_):
                """
                Grabs group/plugin from step_dict via id.
                """
                return next(a for a in dict_[type_] if a['id'] == id_)

            def id_sort(dict_, type_, id_):
                """
                Sorts out plugins/groups via id.
                """
                elem = from_id(dict_, type_, id_)
                return dict_[type_].index(elem)

            # validate answer
            for group_id in answer:
                group = from_id(step_dict, 'groups', group_id)

                if (group['type'] in ('SelectAtMostOne', 'SelectExactlyOne')
                        and len(answer[group_id]) > 1):
                    raise PluginNumberError(group['type'],
                                            len(answer[group_id]))
                elif (group['type'] in ('SelectAtLeastOne', 'SelectExactlyOne')
                      and len(answer[group_id]) < 1):
                    raise PluginNumberError(group['type'],
                                            len(answer[group_id]))

                for plugin_id in answer[group_id]:
                    plugin = from_id(group, 'plugins', plugin_id)
                    if plugin['type'] == 'NotUsable':
                        raise NotUsablePluginError(plugin['name'])

            for group in step_dict['groups']:
                if group['type'] == 'SelectAll':
                    answer[group['id']] = [p['id'] for p in group['plugins']]

                for plugin in group['plugins']:
                    if plugin['type'] == 'Required':
                        answer.setdefault(group['id'], []).append(plugin['id'])

            for group_id in answer:
                group = from_id(step_dict, 'groups', group_id)
                answer[group_id] = list(set(answer[group_id]))
                answer[group_id] = sorted(answer[group_id],
                                          key=lambda x: id_sort(group,
                                                                'plugins',
                                                                x))
            answer = OrderedDict(sorted(answer.items(),
                                        key=lambda x: id_sort(step_dict,
                                                              'groups',
                                                              x[0])))

            # collect files and flags
            step_file_chain = ChainMap()
            step_flag_chain = ChainMap()
            for _, plugin_ids in answer.items():
                for plugin_id in plugin_ids:
                    _collect_files(id_dict[plugin_id].find('files'),
                                   step_file_chain,
                                   source_path)
                    _collect_flags(id_dict[plugin_id].find('conditionFlags'),
                                   step_flag_chain)
            self._collected_files.maps.insert(0, dict(step_file_chain))
            self._flag_states.maps.insert(0, dict(step_flag_chain))

        # process conditionalFileInstalls
        pattern_list = _explicit_list(root.find('conditionalFile'
                                                'Installs/patterns'))
        for pattern in pattern_list:
            try:
                _assert_dependencies(pattern.find('dependencies'),
                                     self._flag_states,
                                     dest,
                                     game_version)
            except MissingDependency:
                pass
            else:
                _collect_files(pattern.find('files'),
                               self._collected_files,
                               source_path)

        # install files
        if None in (source_path, dest):
            return
        for src in self.collected_files:
            dest_path = os.path.join(dest, self.collected_files[src])
            if os.path.isdir(src):
                _copytree(src, dest_path)
            else:
                copy2(src, dest_path)
