import os
import pytest
from unittest.mock import mock_open, patch

from src.utils import HASH
from src.cov import convert_to_lcov
from src.cov import preprocess_files


@pytest.fixture
def mock_file_contents():
    return [
        'tmp/main.c:1,0,1,0',
        'tmp/another.c:0,1,1'
    ]


@pytest.fixture
def file_to_lf():
    return {'tmp/main.c': 4, 'tmp/another.c': 3}


@pytest.fixture
def file_translation():
    return {'tmp/main.c': 'src/main.c', 'tmp/another.c': 'src/another.c'}


def test_convert_to_lcov(mocker, mock_file_contents, file_to_lf, file_translation):
    output_path = 'some_path'
    source_dir = 'source_dir'

    read_mock = mock_open(read_data="\n".join(mock_file_contents))
    write_mock = mock_open()
    mocker.patch('builtins.open', side_effect=[read_mock.return_value, write_mock.return_value])

    convert_to_lcov(source_dir, output_path, file_to_lf, file_translation)

    # Verify the content written to output_file
    expected_calls = [
        mocker.call().write(f"TN:test\n"),
        mocker.call().write(f"SF:src/main.c\n"),
        mocker.call().write(f"DA:1,1\n"),
        mocker.call().write(f"DA:3,1\n"),
        mocker.call().write(f"LH:2\n"),
        mocker.call().write(f"LF:4\n"),
        mocker.call().write("end_of_record\n"),
        mocker.call().write(f"TN:test\n"),
        mocker.call().write(f"SF:src/another.c\n"),
        mocker.call().write(f"DA:2,1\n"),
        mocker.call().write(f"DA:3,1\n"),
        mocker.call().write(f"LH:2\n"),
        mocker.call().write(f"LF:3\n"),
        mocker.call().write("end_of_record\n"),
    ]

    write_mock.assert_has_calls(expected_calls, any_order=True)


# Fixture for common setup
'''
@pytest.fixture
def args(mocker):
    mock_args = mocker.MagicMock()
    mock_args.input_file = None
    mock_args.output_file = None
    mock_args.input_dir = None
    mock_args.output_dir = None
    return mock_args


def input_file_output_file(mocker, args):
    # Configure the mock arguments for this specific test
    args.input_file = 'path/to/input_file.c'
    args.output_file = 'path/to/output_file.c'

    # Mock the necessary functions
    mocker.patch('os.path.isdir', return_value=False)
    mocker.patch('os.path.dirname', return_value='path/to')
    mock_copy = mocker.patch('shutil.copy2')

    source_dir, path_to_process, file_translation = preprocess_files(args)

    mock_copy.assert_called_once_with('path/to/input_file.c', 'path/to/output_file.c')
    assert path_to_process == 'path/to/output_file.c'
    assert file_translation == {'path/to/output_file.c': 'input_file.c'}
    assert source_dir == 'path/to'
'''