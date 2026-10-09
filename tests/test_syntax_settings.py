import re

from scope_selectors import CFS_SCRIPT, matches
from test_input_maps import load_json_with_comments


def triggers(file_name):
    return load_json_with_comments('settings/' + file_name)['auto_complete_triggers']


def test_cfs_files_get_the_completion_triggers_of_script():
    cfml = triggers('CFML.sublime-settings')
    cfs = triggers('CFScript (CFML).sublime-settings')
    assert all(trigger in cfml for trigger in cfs)
    for trigger in cfml:
        if trigger not in cfs:
            # a trigger left out does not apply in script, even where the
            # scope it is for is found in script
            first_name = re.match(r'[\w.]+', trigger['selector']).group()
            assert not matches(CFS_SCRIPT + first_name, trigger['selector'])
