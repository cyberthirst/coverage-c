import os
import pytest
from unittest.mock import mock_open, patch, call, MagicMock

from src.instrumentation import construct_c_helpers, instrument_file, get_instrumentation_info
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

        assert returned_file_name == os.path.join(path, f'instrumentation_{HASH}.c')

        write_calls_c = ''.join(call.args[0] for call in mock_open_c().write.call_args_list)

        assert 'int instrumentation_main_c[16]' in write_calls_c
        assert 'int instrumentation_utils_c[17]' in write_calls_c


@pytest.fixture
def input_params():
    input_file = "out/basic.c"
    root = "out/"
    main_coords = MagicMock(line=3, column=1)
    instrumentation_info = {4: 5, 5: 5}
    return input_file, root, main_coords, instrumentation_info


@pytest.fixture
def basic_c_content():
    return [
        '#include "foo.h"\n',
        '\n',
        'int main() {\n',
        '    foo();\n',
        '    return 0;\n',
    ]


@pytest.fixture
def expected_instrumented_content():
    return [
        '#include "./instrumentation_98b30b1e.h"\n',
        '#include "foo.h"\n',
        '\n',
        'int main() {\n',
        '   if (atexit(write_instrumentation_info_98b30b1e)) return EXIT_FAILURE;\n',
        '   instrumentation_out_basic_c[3] += 1; foo();\n',
        '   instrumentation_out_basic_c[4] += 1; return 0;\n',
    ]


def test_instrument_file(input_params, basic_c_content, expected_instrumented_content):
    input_file, root, main_coords, instrumentation_info = input_params

    m_open = mock_open(read_data=''.join(basic_c_content))
    mock_file = m_open.return_value
    mock_file.writelines = MagicMock()
    with patch('builtins.open', m_open):
        instrument_file(input_file, root, main_coords, instrumentation_info)

    written_lines = []
    for args, _ in mock_file.writelines.call_args_list:
        for arg in args[0]:
            written_lines.append(arg)

    actual_written_content = ''.join(written_lines)

    expected_content = ''.join(expected_instrumented_content)
    print(f"actual_written_content: {actual_written_content}")
    print(f"expected_content: {expected_content}")
    assert actual_written_content == expected_content, "The instrumented file content does not match the expected output."


c_file_content = """
#include <stdio.h>

int foo() {
    int x = 5;
    return 0;
}
"""

@pytest.fixture
def c_file(tmp_path):
    temp_c_file = tmp_path / "foo.c"
    temp_c_file.write_text(c_file_content)
    return str(temp_c_file)


def test_get_instrumentation_info_with_real_file(c_file):
    instrumentation_info, main_coords = get_instrumentation_info(c_file)

    assert instrumentation_info == {5: 5, 6: 5}, "Incorrect instrumentation_info"
    assert main_coords is None, "Expected main_coords to not be None"

