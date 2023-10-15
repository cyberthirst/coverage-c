import re
import os
import argparse


from pycparser import parse_file
from pycparser.c_ast import NodeVisitor

#keccak256("instrumentation-skrabmir")
# - used to avoid name collissions with the instrumented code
INS_PREFIX = "98b30b1e82017f82d4388ed4555f8f7c4053e3d1f456b1baf24e402e015a0f21"[:8]

class InstrumentationVisitor(NodeVisitor):
    def __init__(self):
        self.files_to_lines = {}
        self.main_def_line = None
        self.inside_fun = False

    def add_line(self, node):
        if node.coord.file not in self.files_to_lines:
            self.files_to_lines[node.coord.file] = set()
        self.files_to_lines[node.coord.file].add(node.coord.line)

    def visit_FuncCall(self, node):
        self.add_line(node)
        self.generic_visit(node)

    def visit_Return(self, node):
        self.add_line(node)
        self.generic_visit(node)

    """
    def visit_FuncDef(self, node):
        #name = getattr(node, 'name', None)
        self.inside_fun = True
        self.generic_visit(node)
        self.inside_fun = False


    def visit_FuncDecl(self, node):
        if self.inside_fun:
           self.generic_visit(node)
        else:
            self.inside_fun = True
            self.generic_visit(node)
            self.inside_fun = False

    def visit_Compound(self, node):
        self.add_line(node)
        self.generic_visit(node)
    """

    def visit_Assignment(self, node):
        self.add_line(node)
        self.generic_visit(node)

    def visit_BinaryOp(self, node):
        self.add_line(node)
        self.generic_visit(node)


    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for child_name, child in node.children():
            self.visit(child)


class MainFunctionVisitor(NodeVisitor):
    def __init__(self):
        self.main_body_coords = []

    def visit_FuncDef(self, node):
        function_name = node.decl.name
        if function_name == "main":
            compound_node = node.body
            coords = compound_node.coord
            self.main_body_coords.append(coords)
        self.generic_visit(node)


def find_main_function_bodies(ast_root):
    visitor = MainFunctionVisitor()
    visitor.visit(ast_root)
    return visitor.main_body_coords



def instrument_file(input_file, main_coords=None, files_to_lines=None, output_file=None):
    if not files_to_lines:
        files_to_lines, main_coords = get_instrumentation_info(input_file)
        assert len(main_coords) == 1, "There should be exactly one main function."


    lines_to_modify = files_to_lines.get(input_file, set())

    # Reading the content of the input file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    file_len = len(lines)

    # Modifying the lines as per the instrumentation
    #for i in range(len(lines)):
    #    if i+1 in lines_to_modify:
    #        lines[i] = f"instrumentation_{normalize_filename(input_file)}[{i}] += 1;{lines[i].rstrip()}\n"
    for ln in lines_to_modify:
        lines[ln-1] = f"instrumentation_{normalize_filename(input_file)}[{ln-1}] += 1;{lines[ln-1].rstrip()}\n"


    if main_coords != None:
        lines.insert(main_coords.line, f"if (atexit(write_instrumentation_info_{INS_PREFIX})) return EXIT_FAILURE;\n")


    # Including the arrays at the top of the file
    lines.insert(0, f'#include "instrumentation_{INS_PREFIX}.h"\n')

    # Writing the modified content back to the file
    output_file_path = output_file or input_file
    with open(output_file_path, 'w') as file:
        file.writelines(lines)

    return file_len



def instrument_directory(input_dir, output_directory=None):
    # Get a list of all .c files in the directory
    c_files = [os.path.join(root, file)
               for root, dirs, files in os.walk(input_dir)
               for file in files if file.endswith('.c')]

    files_to_lines = {}
    file_lens = {}
    main_coords = [None]*len(c_files)

    # Instrument each .c file
    for i, c_file in enumerate(c_files):
        ftl, mc = get_instrumentation_info(c_file)
        files_to_lines.update(ftl)
        main_coords[i] = mc

        if output_directory:
            # Get the relative path of the c_file with respect to input_dir
            relative_path = os.path.relpath(c_file, input_dir)
            # Join the relative path with output_directory
            output_file = os.path.join(output_directory, relative_path)
            # Ensure the directory for the output file exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
        else:
            output_file = None

        file_len = instrument_file(c_file, main_coords=main_coords[i], files_to_lines=files_to_lines, output_file=output_file)
        file_lens[c_file] = file_len

    assert sum(x is not None for x in main_coords) == 1,"There should be exactly one main function."
    construct_c_helpers(files_to_lines, file_lens, output_directory=output_directory)

def normalize_filename(filename):
    """
    Normalize filename to be used as a C variable.
    Replace characters like '.', '/', '-', etc. with '_'
    """
    # Replace non-alphanumeric characters (except underscores) with '_'
    return re.sub(r'[^a-zA-Z0-9_]', '_', filename)


def construct_c_helpers(files_to_lines, file_lens, output_directory=None):
    contents_h = f"#ifndef INSTRUMENTATION_{INS_PREFIX}_H\n#define INSTRUMENTATION_{INS_PREFIX}_H\n"
    contents_c = f"#include \"instrumentation_{INS_PREFIX}.h\"\n"

    for file  in files_to_lines.keys():
        contents_h += f"extern int instrumentation_{normalize_filename(file)}[{file_lens[file]}];\n"

    contents_h += f"void write_instrumentation_info_{INS_PREFIX}(char* file, int* arr, int len);\n"
    contents_h += f"void write_instrumentation_info_{INS_PREFIX}();\n"

    contents_h += "#endif\n"

    #instrumentation_inf.txt will have the following format:
    # <file_name1>:arr1[0],arr1[1],...,arr1[len(arr1)-1]
    # <file_name2>:arr2[0],arr2[1],...,arr2[len(arr2)-1]
    fun1 = """
    void write_instrumentation_info(char* file, int* arr, int len) {
        FILE* f = fopen("instrumentation_info.txt", "a");
        fprintf(f, "%s:", file);
        for (int i = 0; i < len; i++) {
            fprintf(f, "%d", arr[i]);
            if (i < len - 1) {
                fprintf(f, ",");
            }
        }
        fprintf(f, "\\n");
        fclose(f);
    }
    """

    contents_c += fun1

    fun2 = f"void write_instrumentation_info_{INS_PREFIX}() {{\n"
    for file in files_to_lines.keys():
        normalized = normalize_filename(file)
        fun2 += f"    write_instrumentation_info_{INS_PREFIX}(\"{file}\", instrumentation_{normalized}, {file_lens[file]}));\n"
    fun2 += "}\n"

    contents_c += fun2

    filename_prefix = os.path.join(output_directory or "", f"instrumentation_{INS_PREFIX}")

    with open(f"{filename_prefix}.h", "w") as f:
        f.write(contents_h)

    with open(f"{filename_prefix}.c", "w") as f:
        f.write(contents_c)

    return

def get_instrumentation_info(input_file):
    """
    algorithm:

    gather instrumentation information:
    0. initialize files_to_lines = {}, example: {path/file0 : set(line_to_instrument1, line_to_instrument2, ...)}
    1. visit all the relevant nodes
    2. for each relevant node add: files_to_lines[node.coord.file].append(node.coord.line)

    instrumentation:
    0. declare instrumentation_{filename}[num_of_lines{filename}] statically alocated variable
    1. include funtion for writing the instrumentation information to a file
    2. - the function will take all the instrumentation_{filename} arrays and write them to a file
    """

    ast = parse_file(input_file, use_cpp=True,
                     cpp_path='gcc',
                     cpp_args=['-E', r'-Ipycparser/utils/fake_libc_include'])

    lv = InstrumentationVisitor()
    lv.visit(ast)


    main_coords = find_main_function_bodies(ast)
    assert len(main_coords) <= 1, "There should be at most one main function."

    #ast.show(showcoord=True)

    print(lv.files_to_lines)

    return lv.files_to_lines, next(iter(main_coords), None)


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

