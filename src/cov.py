import os
import argparse
import shutil
import subprocess

from utils import copy_tree, HASH
from instrumentation import instrument_files, construct_c_helpers


# prepares the output files/directory and copies the inputs to them
# - later the output files will be modified in place
# - if only input_file (or input_dir) are provided, they are not copied and will be modified in place
def preprocess_files(args):
    # if input and output files are given by the user, then this technique of
    # copying files and modifying them in-place runs into the following problem:
    #  - we generate the lcov.info based on the target paths, however we place
    #    it to the origin destination
    #  - the lcof.info contains the SF attribute, which starts a section for one given C file,
    #    and we generate it based on the target path and thus there will be a discrepancy
    #    between the origin name and the actual C file that being "coveraged"
    #  - thus we use the translation dict
    file_translation = {}
    path_to_process = None
    # save source_dir, we will write there the lcov.info file later
    source_dir = None
    if args.input_file:
        assert not os.path.isdir(args.input_file), "Provided input file is a directory!"
        source_dir = os.path.dirname(args.input_file)
        if args.output_file:
            file_translation[args.output_file] = os.path.basename(args.input_file)
            shutil.copy2(args.input_file, args.output_file)
            path_to_process = args.output_file

        elif args.output_dir:
            output_file_path = os.path.join(args.output_dir, os.path.basename(args.input_file))
            shutil.copy2(args.input_file, output_file_path)
            path_to_process = output_file_path

        else:
            print("Warning: No output file or dir specified. The input file will be modified in-place.")
            path_to_process = args.input_file

    elif args.input_dir:
        assert os.path.isdir(args.input_dir), "Provided input directory is not a directory!"
        source_dir = args.input_dir
        try:
            if args.output_file:
                raise ValueError("Error: Cannot specify an input directory and an output file.")
            elif args.output_dir:
                # No longer removing the output directory, instead merging contents
                copy_tree(args.input_dir, args.output_dir)
                path_to_process = args.output_dir
            else:
                print(f"Warning: No output dir specified. The dir {args.input_dir} will be modified in-place.")
                path_to_process = args.input_dir

        except ValueError as e:
            print(f"Error: {e}")
            return None

    return source_dir, path_to_process, file_translation


def compile_and_run(c_files, output_path, executable_args=[], executable_name=f"a.out_{HASH}"):
    # full path to the output executable
    executable_path = os.path.join(output_path, executable_name)

    command = ["gcc", "-O0", "-o", executable_path] + c_files
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    stdout, stderr = process.communicate()

    if process.returncode != 0:
        print(f"Compilation failed with error code {process.returncode}.")
        print(stderr.decode("utf-8"))
    else:
        print(f"Compilation successful. Executable named '{executable_name}' has been created at '{output_path}'.")

    # changing to the output directory to run the executable
    original_working_directory = os.getcwd()
    os.chdir(output_path)

    command = [f"./{executable_name}"] + executable_args
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    print("Output from the executable:")
    print(stdout.decode("utf-8"))

    if stderr:
        print("Errors/warnings from the executable:")
        print(stderr.decode("utf-8"))

    os.chdir(original_working_directory)


def convert_to_lcov(source_dir, output_path, file_to_lf, file_translation):
    input_file = os.path.join(output_path, f"instrumentation_info_{HASH}.txt")
    output_file = os.path.join(source_dir, "lcov.info")

    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        lines = infile.readlines()

        for line in lines:
            file_path, coverage_info = line.strip().split(":")
            file_path_normalized = file_path.replace(output_path, '', 1).lstrip('/') if not file_translation else file_translation[file_path]
            coverage_data = coverage_info.split(',')

            if any(int(hits) > 0 for hits in coverage_data):
                outfile.write(f"TN:test\n")
                outfile.write(f"SF:{file_path_normalized}\n")

                for i, hits in enumerate(coverage_data):
                    if int(hits) > 0:  # Write only lines with non-zero hits
                        outfile.write(f"DA:{i + 1},{hits}\n")

                lh = sum(1 for hits in coverage_data if int(hits) > 0)
                lf = file_to_lf[file_path]
                outfile.write(f"LH:{lh}\n")
                outfile.write(f"LF:{lf}\n")
                outfile.write("end_of_record\n")
    print(f"The coverage report is available at: {output_file}")


def get_cli_args():
    parser = argparse.ArgumentParser(description='Instrument C files.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--input-file', help='specifies an input C file with a main function')
    group.add_argument('-d', '--input-dir', help='specifies an input directory containing C files')

    parser.add_argument('-D', '--output-dir', help='specifies the output directory for instrumented C files')
    parser.add_argument('-F', '--output-file', help='specifies the output file for the instrumented C file')

    parser.add_argument('-i', '--input-args', nargs='*', default=[],
                        help='specifies input arguments to be passed to the C binary during execution')

    args = parser.parse_args()
    return args


def main():
    args = get_cli_args()

    source_dir, path, file_translation = preprocess_files(args)

    assert path is not None, "Error: No input file or directory specified."

    c_files, file_lens, file_to_lf = instrument_files(path)
    # we need to gather all the relevant .c files to perform compilation, this includes
    # the helper .c file which includes the definitions of functions for writing the coverage
    # info to the file
    c_files.append(construct_c_helpers(c_files, file_lens, path))

    output_path = path if os.path.isdir(path) else os.path.dirname(path)

    compile_and_run(c_files, output_path, args.input_args)

    convert_to_lcov(source_dir, output_path, file_to_lf, file_translation)


if __name__ == '__main__':
    main()
