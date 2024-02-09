import os
from unittest.mock import mock_open, patch, call

import pytest

from src.instrumentation import construct_c_helpers, normalize_filename
from src.utils import HASH

@pytest.fixture
def c_files():
    return ['main.c', 'utils.c']


@pytest.fixture
def file_lens(c_files):
    return {c_file: len(c_file) + 10 for c_file in c_files}  # Just a sample logic


@pytest.fixture
def path():
    return '/fake/path'


def test_construct_c_helpers(c_files, file_lens, path):
    mock_open_c = mock_open()

    with patch('os.path.isdir', return_value=True), \
         patch('src.instrumentation.open', mock_open_c):

        returned_file_name = construct_c_helpers(c_files, file_lens, path)

        # Check if the resulting filename is correct
        assert returned_file_name == os.path.join(path, f'instrumentation_{HASH}.c')

        write_calls_c = ''.join(call.args[0] for call in mock_open_c().write.call_args_list)

        assert 'int instrumentation_main_c[16]' in write_calls_c
        assert 'int instrumentation_utils_c[17]' in write_calls_c


