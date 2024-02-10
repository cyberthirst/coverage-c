import pytest
from unittest.mock import mock_open, patch, MagicMock

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


@pytest.fixture
def mock_args():
    return MagicMock()

@patch('os.path.isdir', return_value=False)
@patch('shutil.copy2')
def test_preprocess_files_input_file_only(mock_copy2, mock_isdir, mock_args):
    mock_args.input_file = 'path/to/input_file.c'
    mock_args.output_file = None
    mock_args.output_dir = None
    mock_args.input_dir = None

    source_dir, path_to_process, file_translation = preprocess_files(mock_args)

    assert source_dir == 'path/to'
    assert path_to_process == 'path/to/input_file.c'
    assert file_translation == {}

@patch('os.path.isdir', return_value=False)
@patch('shutil.copy2')
def test_preprocess_files_input_and_output_file(mock_copy2, mock_isdir, mock_args):
    mock_args.input_file = 'path/to/input_file.c'
    mock_args.output_file = 'path/to/output_file.c'
    mock_args.output_dir = None
    mock_args.input_dir = None

    source_dir, path_to_process, file_translation = preprocess_files(mock_args)

    assert source_dir == 'path/to'
    assert path_to_process == 'path/to/output_file.c'
    assert file_translation == {'path/to/output_file.c': 'input_file.c'}

@patch('os.path.isdir', return_value=False)
@patch('shutil.copy2')
def test_preprocess_files_input_file_and_output_dir(mock_copy2, mock_isdir, mock_args):
    mock_args.input_file = 'path/to/input_file.c'
    mock_args.output_dir = 'path/to/output'
    mock_args.output_file = None
    mock_args.input_dir = None

    source_dir, path_to_process, file_translation = preprocess_files(mock_args)

    expected_output_path = 'path/to/output/input_file.c'
    assert source_dir == 'path/to'
    assert path_to_process == expected_output_path
    assert file_translation == {}


@patch('os.path.isdir', return_value=True)
def test_preprocess_files_input_dir_only(mock_isdir, mock_args):
    mock_args.input_file = None
    mock_args.output_file = None
    mock_args.output_dir = None
    mock_args.input_dir = 'path/to/input_dir'

    source_dir, path_to_process, file_translation = preprocess_files(mock_args)

    assert source_dir == 'path/to/input_dir'
    assert path_to_process == 'path/to/input_dir'
    assert file_translation == {}


@patch('src.cov.copy_tree')
@patch('os.path.isdir', return_value=True)
def test_preprocess_files_input_dir_and_output_dir(mock_isdir, mock_copy_tree, mock_args):
    mock_args.input_file = None
    mock_args.output_file = None
    mock_args.output_dir = 'path/to/output_dir'
    mock_args.input_dir = 'path/to/input_dir'

    source_dir, path_to_process, file_translation = preprocess_files(mock_args)

    mock_copy_tree.assert_called_once_with('path/to/input_dir', 'path/to/output_dir')
    assert source_dir == 'path/to/input_dir'
    assert path_to_process == 'path/to/output_dir'
    assert file_translation == {}


@patch('builtins.print')
@patch('os.path.isdir', return_value=True)
def test_preprocess_files_input_dir_no_output_dir_warning(mock_isdir, mock_print, mock_args):
    mock_args.input_file = None
    mock_args.output_file = None
    mock_args.output_dir = None
    mock_args.input_dir = 'path/to/input_dir'

    source_dir, path_to_process, file_translation = preprocess_files(mock_args)

    mock_print.assert_called_with(
        "Warning: No output dir specified. The dir path/to/input_dir will be modified in-place.")
    assert source_dir == 'path/to/input_dir'
    assert path_to_process == 'path/to/input_dir'
    assert file_translation == {}
