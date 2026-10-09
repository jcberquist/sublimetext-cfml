def test_attributes(custom_tag_index):
    tag = custom_tag_index.parse_cfm_file_string(
        '<cfparam name="attributes.Size" default="1">'
        '#attributes.size# #attributes.label# #attributes.format()#'
    )
    # lower cased, unique and sorted, and a method call is not an attribute
    assert tag['attributes'] == ['label', 'size']
    assert tag['has_end_tag'] is False


def test_end_tag_from_execution_mode(custom_tag_index):
    tag = custom_tag_index.parse_cfm_file_string(
        '<cfif thisTag.executionMode is "end">done</cfif>'
    )
    assert tag['has_end_tag'] is True


def test_end_tag_from_cfcase(custom_tag_index):
    tag = custom_tag_index.parse_cfm_file_string(
        '<cfswitch expression="#thistag.executionmode#">'
        '<cfcase value="end">done</cfcase></cfswitch>'
    )
    assert tag['has_end_tag'] is True


def test_index(tmp_path, custom_tag_index):
    (tmp_path / 'nested').mkdir()
    (tmp_path / 'box.cfm').write_text('#attributes.size#', encoding='utf-8')
    (tmp_path / 'nested' / 'row.cfc').write_text('#attributes.id#', encoding='utf-8')
    (tmp_path / 'readme.md').write_text('#attributes.no#', encoding='utf-8')

    index = custom_tag_index.index(str(tmp_path))
    tags = {path.rsplit('/', 1)[1]: tag for path, tag in index.items()}
    assert set(tags) == {'box.cfm', 'row.cfc'}
    assert tags['box.cfm']['tag_name'] == 'box'
    assert tags['row.cfc']['attributes'] == ['id']


def test_project_file_update(tmp_path, project, custom_tags):
    (tmp_path / 'tags').mkdir()
    (tmp_path / 'tags' / 'box.cfm').write_text('#attributes.size#', encoding='utf-8')
    project_name = project({'custom_tag_folders': [{'path': 'tags', 'prefix': 'ui'}]})
    custom_tags.reindex_project(project_name)
    assert custom_tags.get_index_by_tag_name(project_name, 'ui:box')[1][
        'attributes'
    ] == ['size']

    row = tmp_path / 'tags' / 'row.cfm'
    row.write_text('#attributes.id#', encoding='utf-8')
    custom_tags.project_event_handler(
        'project_file_updated', project_name, row.as_posix()
    )
    assert custom_tags.get_tag_attribute_completions(project_name, 'ui:row') is not None
    assert custom_tags.get_tag_attribute_completions(project_name, 'ui:box') is not None


def test_only_tag_files_are_indexed_on_save(tmp_path, project, custom_tags):
    (tmp_path / 'tags').mkdir()
    project_name = project({'custom_tag_folders': [{'path': 'tags'}]})
    custom_tags.reindex_project(project_name)

    readme = tmp_path / 'tags' / 'readme.md'
    readme.write_text('#attributes.no#', encoding='utf-8')
    custom_tags.project_event_handler(
        'project_file_updated', project_name, readme.as_posix()
    )
    assert custom_tags.data[project_name]['index'] == {}


def test_a_file_that_cannot_be_read_is_removed_on_save(tmp_path, project, custom_tags):
    (tmp_path / 'tags').mkdir()
    box = tmp_path / 'tags' / 'box.cfm'
    box.write_text('#attributes.size#', encoding='utf-8')
    project_name = project({'custom_tag_folders': [{'path': 'tags'}]})
    custom_tags.reindex_project(project_name)
    assert custom_tags.get_index_by_tag_name(project_name, 'cf_box')[0] is not None

    # a Windows-1252 file is not valid UTF-8
    box.write_bytes(b'#attributes.caf\xe9#')
    custom_tags.project_event_handler(
        'project_file_updated', project_name, box.as_posix()
    )
    assert custom_tags.data[project_name]['index'] == {}
    assert custom_tags.get_index_by_tag_name(project_name, 'cf_box') == (None, None)


def test_tags_in_a_sibling_folder_with_the_same_prefix(tmp_path, project, custom_tags):
    for folder, name in [('tags', 'box'), ('tags-old', 'legacy')]:
        (tmp_path / folder).mkdir()
        (tmp_path / folder / (name + '.cfm')).write_text('', encoding='utf-8')
    project_name = project(
        {
            'custom_tag_folders': [
                {'path': 'tags', 'prefix': 'ui'},
                {'path': 'tags-old', 'prefix': 'old'},
            ]
        }
    )
    custom_tags.reindex_project(project_name)

    assert set(custom_tags.data[project_name]['tags']) == {'ui:box', 'old:legacy'}


def test_tag_folders_resolve_against_the_folder_of_the_project_file(
    tmp_path, project, custom_tags
):
    # a project name is a key, not a path to take the folder of
    (tmp_path / 'tags').mkdir()
    (tmp_path / 'tags' / 'box.cfm').write_text('', encoding='utf-8')
    project_name = project(
        {'custom_tag_folders': [{'path': 'tags', 'prefix': 'ui'}]}, name='site'
    )
    custom_tags.reindex_project(project_name)

    assert set(custom_tags.data[project_name]['tags']) == {'ui:box'}
