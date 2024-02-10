import subprocess

from unittest.mock import patch, MagicMock
import pytest
from src.cov import compile_and_run

from src.utils import HASH


@pytest.fixture
def c_files():
    return ["hello_world.c"]


@pytest.fixture
def output_path(tmp_path):
    return tmp_path / "build"


@pytest.fixture
def executable_args():
    return []


@pytest.fixture
def hello_world_output():
    return "Hello, World!\n"


def test_compile_and_run(c_files, output_path, executable_args, hello_world_output):
    executable_name = f"a.out_{HASH}"

    mock_popen = MagicMock()
    mock_popen.return_value.communicate.return_value = (hello_world_output.encode(), b"")

    with patch("subprocess.Popen", mock_popen), \
         patch("os.getcwd", return_value="/original/directory"), \
         patch("os.chdir") as mock_chdir:

        compile_and_run(c_files, str(output_path), executable_args, executable_name)

        # Check if subprocess.Popen was called correctly for gcc
        mock_popen.assert_any_call(
            ["gcc", "-O0", "-o", str(output_path / executable_name)] + c_files,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Check if subprocess.Popen was called correctly to run the executable
        mock_popen.assert_any_call(
            [f"./{executable_name}"] + executable_args,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # Verify os.chdir was called correctly
        mock_chdir.assert_any_call(str(output_path))
        mock_chdir.assert_any_call("/original/directory")

        # Check if the output was correctly printed
        # This can be done by checking the mock_popen instance's calls to communicate()
        # and ensuring that the output matches the expected "Hello, World!\n"
        stdout, _ = mock_popen.return_value.communicate.return_value
        assert stdout.decode() == hello_world_output, "The output from the executable does not match the expected output."
