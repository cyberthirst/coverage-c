import re
import os
import argparse


from pycparser import parse_file
from pycparser.c_ast import NodeVisitor


class InstrumentationVisitor(NodeVisitor):
    def __init__(self):
        self.files_to_lines = {}

    def add_line(self, node):
        if node.coord.file not in self.files_to_lines:
            self.files_to_lines[node.coord.file] = set()
        self.files_to_lines[node.coord.file].add(node.coord.line)

    def visit_FuncCall(self, node):
        self.add_line(node)

    def visit_FuncDef(self, node):
        if node.coord.file.endswith('.c'):
            self.add_line(node)
            self.generic_visit(node)


    def visit_FuncDecl(self, node):
        if node.coord.file.endswith('.c'):
            self.add_line(node)
            self.generic_visit(node)

    def visit_Compound(self, node):
        self.add_line(node)
        self.generic_visit(node)

    def visit_Assignment(self, node):
        self.add_line(node)
        self.generic_visit(node)

    def visit_BinaryOp(self, node):
        self.add_line(node)
        self.generic_visit(node)

    # You can continue adding visit methods for other statement nodes like If, While, For, Return, etc.

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for child_name, child in node.children():
            self.visit(child)


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


def instrument_directory(input_dir, output_directory=None):

    main_file_path = find_main_function(input_dir)

    # Get a list of all .c files in the directory
    c_files = [os.path.join(root, file)
               for root, dirs, files in os.walk(input_dir)
               for file in files if file.endswith('.c')]

    # Instrument each .c file
    for c_file in c_files:
        output_file = None
        if output_directory:
            output_file = os.path.join(output_directory, os.path.basename(c_file))
        instrument_file(c_file, output_file)


def instrument_file(input_file, output_file=None):
    """
    algorithm:

    gather instrumentation information:
    0. initialize files_to_lines = {}, example: {path/file0 : set(line_to_instrument1, line_to_instrument2, ...)}
    1. visit all the relevant nodes
    2. for each relevant node add: files_to_lines[node.coord.file].append(node.coord.line)

    instrumentation:
    0. declare instrumentation_{filename}[num_of_lines{filename}] statically alocated variable
    1. include funtion for writing the instrumentation information to a file
    """

    ast = parse_file(input_file, use_cpp=True,
                     cpp_path='gcc',
                     cpp_args=['-E', r'-Ipycparser/utils/fake_libc_include'])

    lv = InstrumentationVisitor()
    lv.visit(ast)

    #ast.show(showcoord=True)

    print(lv.files_to_lines)


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
            if args.output_dir:
                instrument_directory(args.input_dir, args.output_dir)
            else:
                print(f"Warning: No output dir specified. The dir {args.output_dir} will be modified in-place.")
                instrument_directory(args.input_dir)
        except ValueError as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()

