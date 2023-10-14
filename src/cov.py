import re
import os
import argparse


from pycparser import parse_file


def find_main_function(directory):
    """
    Find the file containing the main function in the given directory.
    """
    main_files = []

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.c'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    contents = f.read()
                    # Using regex to find the main function signature
                    if re.search(r'int\s+main\s*\(', contents) or \
                       re.search(r'void\s+main\s*\(', contents):
                        main_files.append(file_path)

    if len(main_files) != 1:
        print("There should be exactly one file with a main function. Currently, there are: ")
        for file in main_files:
            print(file)
        raise ValueError("Too many main functions found.")

    return main_files[0]


def instrument_file(input_file, output_file=None):
    """
    algorithm:

    gather instrumentation information:
    0. initilize files_to_lines = {}, example: {path/file0 : [line_to_instrument1, line_to_instrument2, ...]}
    1. visit all the relevant nodes
    2. for each relevant node add: files_to_lines[node.coord.file].append(node.coord.line)

    instrumentation:
    0. declare instrumentation_{filename}[num_of_lines{filename}] statically alocated variable
    1. include funtion for writing the instrumentation information to a file
    """

    ast = parse_file(input_file, use_cpp=True,
                     cpp_path='gcc',
                     cpp_args=['-E', r'-Ipycparser/utils/fake_libc_include'])
    ast.show(showcoord=True)


def main():
    parser = argparse.ArgumentParser(description='Instrument C files.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--input-file', help='specifies an input C file with a main function')
    group.add_argument('-d', '--input-dir', help='specifies an input directory containing C files')

    parser.add_argument('-D', '--output-dir', help='specifies the output directory for instrumented C files')
    parser.add_argument('-F', '--output-file', help='specifies the output file for the instrumented C file')

    args = parser.parse_args()

    if args.input_file:
        if args.output_file:
            instrument_file(args.input_file, args.output_file)
        else:
            print("Warning: No output file specified. The input file will be modified in-place.")
            instrument_file(args.input_file)

    elif args.input_dir:
        try:
            main_file_path = find_main_function(args.input_dir)
            if args.output_file:
                instrument_file(main_file_path, args.output_file)
            else:
                print(f"Warning: No output file specified. The file {main_file_path} will be modified in-place.")
                instrument_file(main_file_path)
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()

