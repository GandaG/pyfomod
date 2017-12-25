from collections import ChainMap

from lxml import etree
from pyfomod import installer

import pytest


def test_assert_dependencies(tmpdir):
    test_func = installer._assert_dependencies

    # fail nested
    depend = etree.fromstring('<dependencies operator="And">'
                              '<dependencies>'
                              '<flagDependency flag="a" value="on"/>'
                              '</dependencies>'
                              '</dependencies>')
    flag_states = {}
    with pytest.raises(installer.MissingDependency):
        test_func(depend, flag_states)

    # missing flag states
    depend = etree.fromstring('<dependencies operator="And">'
                              '<flagDependency flag="a" value="on"/>'
                              '</dependencies>')
    flag_states = {}
    with pytest.raises(installer.MissingDependency):
        test_func(depend, flag_states)

    # ok flag states
    flag_states = {'a': 'on'}
    test_func(depend, flag_states)

    # fail flag states
    flag_states = {'a': 'off'}
    with pytest.raises(installer.MissingDependency):
        test_func(depend, flag_states)

    # ok active dest file
    tmpdir.join('test_file').write('test')
    depend = etree.fromstring('<dependencies operator="And">'
                              '<fileDependency file="test_file" '
                              'state="Active"/>'
                              '</dependencies>')
    test_func(depend, {}, str(tmpdir))

    # fail missing dest file
    depend = etree.fromstring('<dependencies operator="And">'
                              '<fileDependency file="test_file" '
                              'state="Missing"/>'
                              '</dependencies>')
    with pytest.raises(installer.MissingDependency):
        test_func(depend, {}, str(tmpdir))

    # ok missing dest file
    tmpdir.join('test_file').remove()
    depend = etree.fromstring('<dependencies operator="And">'
                              '<fileDependency file="test_file" '
                              'state="Missing"/>'
                              '</dependencies>')
    test_func(depend, {}, str(tmpdir))

    # fail active dest file
    depend = etree.fromstring('<dependencies operator="And">'
                              '<fileDependency file="test_file" '
                              'state="Active"/>'
                              '</dependencies>')
    with pytest.raises(installer.MissingDependency):
        test_func(depend, {}, str(tmpdir))

    # ok game version
    depend = etree.fromstring('<dependencies operator="And">'
                              '<gameDependency version="1.0.1"/>'
                              '</dependencies>')
    test_func(depend, {}, game_version='1.2')

    # fail game version
    depend = etree.fromstring('<dependencies operator="And">'
                              '<gameDependency version="1.0.1"/>'
                              '</dependencies>')
    with pytest.raises(installer.MissingDependency):
        test_func(depend, {}, game_version='1.0')

    # fail or
    depend = etree.fromstring('<dependencies operator="Or">'
                              '<gameDependency version="1.0.1"/>'
                              '<flagDependency flag="a" value="on"/>'
                              '</dependencies>')
    with pytest.raises(installer.MissingDependency):
        test_func(depend, {}, game_version='1.0')


def test_collect_files(tmpdir):
    test_func = installer._collect_files

    plugin = tmpdir.join('example.plugin')
    plugin.write('example')
    folder = tmpdir.mkdir('example_folder')
    file_list = etree.fromstring('<requiredInstallFiles>'
                                 '<file source="example.plugin"/>'
                                 '<folder source="example_folder"/>'
                                 '</requiredInstallFiles>')

    test_chain = ChainMap()
    expected = {'0': {'example.plugin': '', 'example_folder': ''}}

    test_func(file_list, test_chain)
    assert test_chain == expected

    test_chain = ChainMap()
    expected = {'0': {str(plugin): '', str(folder): ''}}

    test_func(file_list, test_chain, str(tmpdir))
    assert test_chain == expected


def test_collect_flags():
    test_func = installer._collect_flags

    flag_states = ChainMap()
    flag_list = etree.fromstring('<conditionFlags>'
                                 '<flag name="a">on</flag>'
                                 '<flag name="b">off</flag>'
                                 '<flag name="c"/>'
                                 '</conditionFlags>')
    expected = {'a': 'on', 'b': 'off', 'c': ''}
    test_func(flag_list, flag_states)
    assert flag_states == expected


def test_explicit_list():
    test_func = installer._explicit_list
    root = etree.fromstring('<patterns>'
                            '<pattern/>'
                            '<pattern/>'
                            '<pattern/>'
                            '<pattern/>'
                            '<pattern/>'
                            '</patterns>')
    assert test_func(root) == list(root)
    assert test_func(None) == []


def test_ordered_list():
    test_func = installer._ordered_list
    root = etree.fromstring('<installSteps order="Ascending">'
                            '<installStep name="A"/>'
                            '<installStep name="C"/>'
                            '<installStep name="B"/>'
                            '</installSteps>')
    ascending = [root[0], root[2], root[1]]
    descending = [root[1], root[2], root[0]]
    explicit = list(root)

    assert test_func(None) == []

    assert test_func(root) == ascending
    root.set('order', 'Descending')
    assert test_func(root) == descending
    root.set('order', 'Explicit')
    assert test_func(root) == explicit


def test_installer(tmpdir):
    source_dir = tmpdir.mkdir('source')
    target_dir = tmpdir.mkdir('target')
    option_03 = source_dir.mkdir('option_03')
    test_plugin = source_dir.join('test.plugin')
    test_plugin.write('test')
    option_11 = source_dir.join('option_11')
    option_11.write('test')
    option_21 = source_dir.join('option_21')
    option_21.write('test')
    option_12 = source_dir.join('option_12')
    option_12.write('test')

    info_xml = ('<fomod>'
                '<Name>Test Mod</Name>'
                '<Author>Test Author</Author>'
                '<Version>1.0.0</Version>'
                '<Description>Test description.</Description>'
                '<Website>www.test.org</Website>'
                '</fomod>')
    conf_xml = ('<config xmlns:xsi="http://www.w3.org/2001/'
                'XMLSchema-instance" xsi:noNamespaceSchemaL'
                'ocation="http://qconsulting.ca/fo3/ModConfig5.0.xsd">'
                '<moduleName>Test Mod</moduleName>'
                '<moduleImage path="test_image.png"/>'
                '<moduleDependencies operator="And">'
                '<fileDependency file="depend1.plugin" state="Missing"/>'
                '<dependencies operator="Or">'
                '<fileDependency file="depend2v1.plugin" state="Active"/>'
                '<fileDependency file="depend2v2.plugin" state="Active"/>'
                '</dependencies>'
                '</moduleDependencies>'
                '<requiredInstallFiles>'
                '<file source="test.plugin"/>'
                '</requiredInstallFiles>'
                '<installSteps order="Explicit">'
                '<installStep name="First Step">'
                '<optionalFileGroups order="Explicit">'
                '<group name="First Option:" type="SelectExactlyOne">'
                '<plugins order="Explicit">'
                '<plugin name="Option 01">'
                '<description>Select this to install Option 01.</description>'
                '<image path="option_01.png"/>'
                '<conditionFlags>'
                '<flag name="option_01">selected</flag>'
                '</conditionFlags>'
                '<typeDescriptor>'
                '<type name="Recommended"/>'
                '</typeDescriptor>'
                '</plugin>'
                '<plugin name="Option 02">'
                '<description>Select this to install Option 02.</description>'
                '<image path="option_02.png"/>'
                '<conditionFlags>'
                '<flag name="option_02">selected</flag>'
                '</conditionFlags>'
                '<typeDescriptor>'
                '<type name="Optional"/>'
                '</typeDescriptor>'
                '</plugin>'
                '</plugins>'
                '</group>'
                '<group name="Mandatory Option:" type="SelectAll">'
                '<plugins order="Explicit">'
                '<plugin name="Option 03">'
                '<description>Option 03 is required by group.</description>'
                '<image path="option_03.png"/>'
                '<files>'
                '<folder source="option_03"/>'
                '</files>'
                '<typeDescriptor>'
                '<type name="Required"/>'
                '</typeDescriptor>'
                '</plugin>'
                '</plugins>'
                '</group>'
                '</optionalFileGroups>'
                '</installStep>'
                '<installStep name="Second Step 01">'
                '<visible>'
                '<flagDependency flag="option_01" value="selected"/>'
                '</visible>'
                '<optionalFileGroups order="Explicit">'
                '<group name="First Option:" type="SelectExactlyOne">'
                '<plugins order="Explicit">'
                '<plugin name="Option 11">'
                '<description>Select this to install Option 11.</description>'
                '<image path="option_11.png"/>'
                '<conditionFlags>'
                '<flag name="option_11">selected</flag>'
                '</conditionFlags>'
                '<typeDescriptor>'
                '<type name="Optional"/>'
                '</typeDescriptor>'
                '</plugin>'
                '<plugin name="Option 21">'
                '<description>Select this to install Option 21.</description>'
                '<image path="option_21.png"/>'
                '<conditionFlags>'
                '<flag name="option_21">selected</flag>'
                '</conditionFlags>'
                '<typeDescriptor>'
                '<type name="Required"/>'
                '</typeDescriptor>'
                '</plugin>'
                '</plugins>'
                '</group>'
                '</optionalFileGroups>'
                '</installStep>'
                '<installStep name="Second Step 02">'
                '<visible>'
                '<flagDependency flag="option_02" value="selected"/>'
                '</visible>'
                '<optionalFileGroups order="Explicit">'
                '<group name="First Option:" type="SelectExactlyOne">'
                '<plugins order="Explicit">'
                '<plugin name="Option 12">'
                '<description>Select this to install Option 12.</description>'
                '<image path="option_12.png"/>'
                '<conditionFlags>'
                '<flag name="option_12">selected</flag>'
                '</conditionFlags>'
                '<typeDescriptor>'
                '<type name="Optional"/>'
                '</typeDescriptor>'
                '</plugin>'
                '</plugins>'
                '</group>'
                '</optionalFileGroups>'
                '</installStep>'
                '<installStep name="Third Step">'
                '<optionalFileGroups order="Explicit">'
                '<group name="First Option:" type="SelectAtMostOne">'
                '<plugins order="Explicit">'
                '<plugin name="Option 3">'
                '<description>Select this to install Option 3.</description>'
                '<files>'
                '<file source="option_3.plugin"/>'
                '</files>'
                '<typeDescriptor>'
                '<dependencyType>'
                '<defaultType name="Optional"/>'
                '<patterns>'
                '<pattern>'
                '<dependencies operator="And">'
                '<flagDependency flag="option_02" value="selected"/>'
                '</dependencies>'
                '<type name="Optional"/>'
                '</pattern>'
                '<pattern>'
                '<dependencies operator="And">'
                '<flagDependency flag="option_01" value="selected"/>'
                '</dependencies>'
                '<type name="NotUsable"/>'
                '</pattern>'
                '</patterns>'
                '</dependencyType>'
                '</typeDescriptor>'
                '</plugin>'
                '</plugins>'
                '</group>'
                '</optionalFileGroups>'
                '</installStep>'
                '</installSteps>'
                '<conditionalFileInstalls>'
                '<patterns>'
                '<pattern>'
                '<dependencies operator="And">'
                '<flagDependency flag="option_11" value="selected"/>'
                '</dependencies>'
                '<files>'
                '<file source="option_11"/>'
                '</files>'
                '</pattern>'
                '<pattern>'
                '<dependencies operator="And">'
                '<flagDependency flag="option_12" value="selected"/>'
                '</dependencies>'
                '<files>'
                '<file source="option_12"/>'
                '</files>'
                '</pattern>'
                '<pattern>'
                '<dependencies operator="And">'
                '<flagDependency flag="option_21" value="selected"/>'
                '</dependencies>'
                '<files>'
                '<file source="option_21"/>'
                '</files>'
                '</pattern>'
                '</patterns>'
                '</conditionalFileInstalls>'
                '</config>')
    info_file = source_dir.join('info.xml')
    info_file.write(info_xml)
    conf_file = source_dir.join('ModuleConfig.xml')
    conf_file.write(conf_xml)

    install = installer.Installer([str(info_file), str(conf_file)],
                                  str(source_dir),
                                  str(target_dir))
    assert install.name == "Test Mod"
    assert install.author == "Test Author"
    assert install.version == "1.0.0"
    assert install.description == "Test description."
    assert install.website == "www.test.org"
    assert install.image == "test_image.png"
    with pytest.raises(installer.MissingDependency):
        install.send(None)

    target_dir.join('depend2v1.plugin').write('depend')

    install = installer.Installer([str(info_file), str(conf_file)],
                                  str(source_dir),
                                  str(target_dir))
    install.send(None)
    assert install._flag_states.maps == [{}]
    assert install._collected_files.maps == [{'0': {str(test_plugin): ''}},
                                             {}]

    # simulate loops with next()
    first_step = next(install)
    # need to compare dicts this way because id is random
    assert first_step['name'] == 'First Step'
    group0 = first_step['groups'][0]
    assert group0['name'] == 'First Option:'
    assert group0['type'] == 'SelectExactlyOne'
    plugin00 = group0['plugins'][0]
    assert plugin00['name'] == 'Option 01'
    assert plugin00['description'] == 'Select this to install Option 01.'
    assert plugin00['image'] == 'option_01.png'
    assert plugin00['type'] == 'Recommended'
    plugin01 = group0['plugins'][1]
    assert plugin01['name'] == 'Option 02'
    assert plugin01['description'] == 'Select this to install Option 02.'
    assert plugin01['image'] == 'option_02.png'
    assert plugin01['type'] == 'Optional'
    group1 = first_step['groups'][1]
    assert group1['name'] == 'Mandatory Option:'
    assert group1['type'] == 'SelectAll'
    plugin10 = group1['plugins'][0]
    assert plugin10['name'] == 'Option 03'
    assert plugin10['description'] == 'Option 03 is required by group.'
    assert plugin10['image'] == 'option_03.png'
    assert plugin10['type'] == 'Required'

    first_answer = {group0['id']: [plugin01['id']]}
    install.send(first_answer)

    second_step = next(install)
    assert install._flag_states.maps == [{'option_02': 'selected'}, {}]
    assert install._collected_files.maps == [{'0': {str(option_03): ''}},
                                             {'0': {str(test_plugin): ''}},
                                             {}]
    assert second_step['name'] == 'Second Step 02'
    group0 = second_step['groups'][0]
    assert group0['name'] == 'First Option:'
    assert group0['type'] == 'SelectExactlyOne'
    plugin00 = group0['plugins'][0]
    assert plugin00['name'] == 'Option 12'
    assert plugin00['description'] == 'Select this to install Option 12.'
    assert plugin00['image'] == 'option_12.png'
    assert plugin00['type'] == 'Optional'

    second_answer = {'previous_step': True}
    install.send(second_answer)

    # this should be the same as the first step with regened id's
    back_step = next(install)
    assert install._flag_states.maps == [{}]
    assert install._collected_files.maps == [{'0': {str(test_plugin): ''}},
                                             {}]
    assert back_step['name'] == 'First Step'
    group0 = back_step['groups'][0]
    assert group0['name'] == 'First Option:'
    assert group0['type'] == 'SelectExactlyOne'
    plugin00 = group0['plugins'][0]
    assert plugin00['name'] == 'Option 01'
    assert plugin00['description'] == 'Select this to install Option 01.'
    assert plugin00['image'] == 'option_01.png'
    assert plugin00['type'] == 'Recommended'
    plugin01 = group0['plugins'][1]
    assert plugin01['name'] == 'Option 02'
    assert plugin01['description'] == 'Select this to install Option 02.'
    assert plugin01['image'] == 'option_02.png'
    assert plugin01['type'] == 'Optional'
    group1 = back_step['groups'][1]
    assert group1['name'] == 'Mandatory Option:'
    assert group1['type'] == 'SelectAll'
    plugin10 = group1['plugins'][0]
    assert plugin10['name'] == 'Option 03'
    assert plugin10['description'] == 'Option 03 is required by group.'
    assert plugin10['image'] == 'option_03.png'
    assert plugin10['type'] == 'Required'

    back_answer = {group0['id']: [plugin00['id']]}
    install.send(back_answer)

    new_sec_step = next(install)
    assert install._flag_states.maps == [{'option_01': 'selected'}, {}]
    assert install._collected_files.maps == [{'0': {str(option_03): ''}},
                                             {'0': {str(test_plugin): ''}},
                                             {}]
    assert new_sec_step['name'] == 'Second Step 01'
    group0 = new_sec_step['groups'][0]
    assert group0['name'] == 'First Option:'
    assert group0['type'] == 'SelectExactlyOne'
    plugin00 = group0['plugins'][0]
    assert plugin00['name'] == 'Option 11'
    assert plugin00['description'] == 'Select this to install Option 11.'
    assert plugin00['image'] == 'option_11.png'
    assert plugin00['type'] == 'Optional'
    plugin01 = group0['plugins'][1]
    assert plugin01['name'] == 'Option 21'
    assert plugin01['description'] == 'Select this to install Option 21.'
    assert plugin01['image'] == 'option_21.png'
    assert plugin01['type'] == 'Required'

    new_sec_answer = {group0['id']: [plugin00['id']]}
    install.send(new_sec_answer)

    third_step = next(install)
    assert install._flag_states.maps == [{'option_11': 'selected',
                                          'option_21': 'selected'},
                                         {'option_01': 'selected'},
                                         {}]
    assert install._collected_files.maps == [{},
                                             {'0': {str(option_03): ''}},
                                             {'0': {str(test_plugin): ''}},
                                             {}]
    assert third_step['name'] == 'Third Step'
    group0 = third_step['groups'][0]
    assert group0['name'] == 'First Option:'
    assert group0['type'] == 'SelectAtMostOne'
    plugin00 = group0['plugins'][0]
    assert plugin00['name'] == 'Option 3'
    assert plugin00['description'] == 'Select this to install Option 3.'
    assert plugin00['image'] == ''
    assert plugin00['type'] == 'NotUsable'

    third_answer = {}
    install.send(third_answer)

    with pytest.raises(StopIteration):
        next(install)
    assert install._flag_states.maps == [{},
                                         {'option_11': 'selected',
                                          'option_21': 'selected'},
                                         {'option_01': 'selected'},
                                         {}]
    assert install._collected_files.maps == [{'0': {str(option_21): ''}},
                                             {'0': {str(option_11): ''}},
                                             {},
                                             {},
                                             {'0': {str(option_03): ''}},
                                             {'0': {str(test_plugin): ''}},
                                             {}]
    assert target_dir.join('option_21').check()
    assert target_dir.join('option_11').check()
    assert target_dir.ensure_dir('option_03')
    assert target_dir.join('test.plugin').check()
