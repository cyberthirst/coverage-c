import re
import os
import argparse
import shutil


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


def normalize_filename(filename):
    """
    Normalize filename to be used as a C variable.
    Replace characters like '.', '/', '-', etc. with '_'
    """
    # Replace non-alphanumeric characters (except underscores) with '_'
    return re.sub(r'[^a-zA-Z0-9_]', '_', filename)


def instrument_file(input_file, root, main_coords, files_to_lines):
    lines_to_modify = files_to_lines.get(input_file, set())

    # Reading the content of the input file
    with open(input_file, 'r') as file:
        lines = file.readlines()

    file_len = len(lines)

    for ln in lines_to_modify:
        lines[ln-1] = f"instrumentation_{normalize_filename(input_file)}[{ln-1}] += 1;{lines[ln-1].rstrip()}\n"

    if main_coords != None:
        lines.insert(main_coords.line, f"if (atexit(write_instrumentation_info_{INS_PREFIX})) return EXIT_FAILURE;\n")

    include_path = f'instrumentation_{INS_PREFIX}.h'
    input_file_dir = os.path.dirname(input_file)
    # normalizing the paths to be relative
    include_path = os.path.join(os.path.relpath(root, start=input_file_dir), include_path)

    # Including the instrumentation .h file at the top of the file
    lines.insert(0, f'#include "{include_path}"\n')

    output_file_path = input_file
    with open(output_file_path, 'w') as file:
        file.writelines(lines)

    return file_len


def get_instrumentation_info(input_file):
    """
    algorithm:

    gather instrumentation information:
    0. initialize files_to_lines = {}, after visiting: {path/file0 : set(line_to_instrument1, line_to_instrument2, ...)}
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

    #for main_coords returns either None or the first element of the list
    return lv.files_to_lines, next(iter(main_coords), None)


def construct_c_helpers(files_to_lines, file_lens, path):
    contents_h = f"#ifndef INSTRUMENTATION_{INS_PREFIX}_H\n#define INSTRUMENTATION_{INS_PREFIX}_H\n"
    contents_h += "#include<stdio.h>\n"
    contents_h += "#include<stdlib.h>\n\n"
    contents_c = f"#include \"instrumentation_{INS_PREFIX}.h\"\n"

    for file  in files_to_lines.keys():
        contents_h += f"extern int instrumentation_{normalize_filename(file)}[{file_lens[file]}];\n"

    contents_h += f"void write_file_instrumentation_info_{INS_PREFIX}(char* file, int* arr, int len);\n"
    contents_h += f"void write_instrumentation_info_{INS_PREFIX}();\n"

    contents_h += "#endif\n"

    #instrumentation_inf.txt will have the following format:
    # <file_name1>:arr1[0],arr1[1],...,arr1[len(arr1)-1]
    # <file_name2>:arr2[0],arr2[1],...,arr2[len(arr2)-1]
    fun1 = """
void write_file_instrumentation_info(char* file, int* arr, int len) {
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
        fun2 += f"  write_file_instrumentation_info_{INS_PREFIX}(\"{file}\", instrumentation_{normalized}, {file_lens[file]});\n"
    fun2 += "}\n"

    contents_c += fun2

    output_directory = path if os.path.isdir(path) else os.path.dirname(path)
    filename = os.path.join(output_directory, f"instrumentation_{INS_PREFIX}")
    with open(f"{filename}.h", "w") as f:
        f.write(contents_h)

    with open(f"{filename}.c", "w") as f:
        f.write(contents_c)

    return


def instrument_files(path):
    # Determine if the input is a file or directory
    if os.path.isfile(path):
        root = os.path.dirname(path)
        c_files = [path]
    else:
        root = path
        c_files = [os.path.join(root, file)
                   for root, dirs, files in os.walk(path)
                   for file in files if file.endswith('.c')]

    files_to_lines = {}
    file_lens = {}
    main_coords = [None] * len(c_files)

    # Instrument each .c file
    # - we must do so because even though we run the preprocessor on all
    #   the files, the .c files are not aware of each other
    for i, c_file in enumerate(c_files):
        ftl, mc = get_instrumentation_info(c_file)
        files_to_lines.update(ftl)
        main_coords[i] = mc

        file_len = instrument_file(c_file, root, main_coords[i], files_to_lines)
        file_lens[c_file] = file_len

    assert sum(x is not None for x in main_coords) == 1, "There should be exactly one main function."

    construct_c_helpers(files_to_lines, file_lens, path)


def copy_tree(src_dir, dst_dir):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)

    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)

        if os.path.isdir(src_item):
            copy_tree(src_item, dst_item)
        else:
            shutil.copy2(src_item, dst_item)


#prepares the output files/direcotory
# copies the inputs to output
#then the output files will be modified in place
def preprocess_files(args):
    source_path = None

    if args.input_file:
        if args.output_file:
            shutil.copy2(args.input_file, args.output_file)
            source_path = args.output_file

        elif args.output_dir:
            output_file_path = os.path.join(args.output_dir, os.path.basename(args.input_file))
            shutil.copy2(args.input_file, output_file_path)
            source_path = output_file_path

        else:
            print("Warning: No output file or dir specified. The input file will be modified in-place.")
            source_path = args.input_file

    elif args.input_dir:
        try:
            if args.output_file:
                raise ValueError("Error: Cannot specify an input directory and an output file.")
            elif args.output_dir:
                # No longer removing the output directory, instead merging contents
                copy_tree(args.input_dir, args.output_dir)
                source_path = args.output_dir
            else:
                print(f"Warning: No output dir specified. The dir {args.input_dir} will be modified in-place.")
                source_path = args.input_dir

        except ValueError as e:
            print(f"Error: {e}")
            return None

    return source_path



def main():
    parser = argparse.ArgumentParser(description='Instrument C files.')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-f', '--input-file', help='specifies an input C file with a main function')
    group.add_argument('-d', '--input-dir', help='specifies an input directory containing C files')

    parser.add_argument('-D', '--output-dir', help='specifies the output directory for instrumented C files')
    parser.add_argument('-F', '--output-file', help='specifies the output file for the instrumented C file')

    args = parser.parse_args()

    path = preprocess_files(args)

    if path:
        instrument_files(path)


if __name__ == '__main__':
    main()


"""
TODO:
1. unify the output path - handle the case of output file and output dir (and input file) in unified way
2. we need to write the .c and .h helpers to correct destination for all combinations
  a. only input file
  b. output file
  c. output dir
3. parse the output of the run of the instrumented code
4. create lcov report


"""