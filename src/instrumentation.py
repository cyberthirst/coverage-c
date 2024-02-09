import os

from pycparser.c_ast import FuncDef
from pycparser import parse_file


from utils import normalize_filename, HASH
from visitors import InstrumentationVisitor


def instrument_file(input_file, root, main_coords, instrumentation_info):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    file_len = len(lines)

    for line, col in instrumentation_info.items():
        line_index = line - 1
        col_index = col - 1
        instr_text = f"instrumentation_{normalize_filename(input_file)}[{line_index}] += 1;"
        lines[line_index] = lines[line_index][:col_index-1] + instr_text + lines[line_index][col_index-1:]

    if main_coords is not None:
        lines.insert(main_coords.line, f"   if (atexit(write_instrumentation_info_{HASH})) return EXIT_FAILURE;\n")

    include_path = f'instrumentation_{HASH}.h'
    input_file_dir = os.path.dirname(input_file)
    # normalizing the paths to be relative
    include_path = os.path.join(os.path.relpath(root, start=input_file_dir), include_path)

    # Including the instrumentation .h file at the top of the file
    lines.insert(0, f'#include "{include_path}"\n')

    output_file_path = input_file
    with open(output_file_path, 'w') as file:
        file.writelines(lines)

    return file_len


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

    file_lens = {}
    file_to_lf = {}
    main_coords = [None] * len(c_files)

    # Instrument each .c file
    # - we must do so because even though we run the preprocessor on all
    #   the files, the .c files are not aware of each other
    for i, c_file in enumerate(c_files):
        instrumentation_info, mc = get_instrumentation_info(c_file)
        file_to_lf[c_file] = len(instrumentation_info)
        main_coords[i] = mc

        file_len = instrument_file(c_file, root, main_coords[i], instrumentation_info)
        file_lens[c_file] = file_len

    assert sum(x is not None for x in main_coords) == 1, "There should be exactly one main function."

    return c_files, file_lens, file_to_lf


def get_instrumentation_info(input_file):
    ast = parse_file(input_file, use_cpp=True,
                     cpp_path='gcc',
                     cpp_args=['-E', r'-Ifake_libc_include'])

    lv = InstrumentationVisitor()
    main_coords = []
    #visit only the bodies of the function definitions
    for node in ast.ext:
        if isinstance(node, FuncDef):
            lv.visit(node.body)
            if node.decl.name == "main":
                main_coords.append(node.body.coord)

    assert len(main_coords) <= 1, "There should be at most one main function."

    #ast.show(showcoord=True)

    #for main_coords returns either None or the first element of the list
    return lv.get_instrumentation_info(), next(iter(main_coords), None)


def construct_c_helpers(c_files, file_lens, path):
    contents_h = f"#ifndef INSTRUMENTATION_{HASH}_H\n#define INSTRUMENTATION_{HASH}_H\n"
    contents_h += "#include<stdio.h>\n"
    contents_h += "#include<stdlib.h>\n\n"
    contents_c = f"#include \"instrumentation_{HASH}.h\"\n"

    for file in c_files:
        contents_h += f"int instrumentation_{normalize_filename(file)}[{file_lens[file]}];\n"

    contents_h += f"void write_file_instrumentation_info_{HASH}(char* file, int* arr, int len);\n"
    contents_h += f"void write_instrumentation_info_{HASH}();\n"

    contents_h += "#endif\n"

    #instrumentation_inf.txt will have the following format:
    # file_name1:arr1[0],arr1[1],...,arr1[len(arr1)-1]
    # file_name2:arr2[0],arr2[1],...,arr2[len(arr2)-1]
    output_directory = path if os.path.isdir(path) else os.path.dirname(path)
    fun1 = f"""
void write_file_instrumentation_info_{HASH}(char* file, int* arr, int len) {{
    FILE* f = fopen("instrumentation_info_{HASH}.txt", "a");
    fprintf(f, "%s:", file);
    for (int i = 0; i < len; i++) {{
        fprintf(f, "%d", arr[i]);
        if (i < len - 1) {{
            fprintf(f, ",");
        }}
    }}
    fprintf(f, "\\n");
    fclose(f);
}}

"""

    contents_c += fun1

    fun2 = f"void write_instrumentation_info_{HASH}() {{\n"
    for file in c_files:
        normalized = normalize_filename(file)
        fun2 += f"  write_file_instrumentation_info_{HASH}(\"{file}\", instrumentation_{normalized}, {file_lens[file]});\n"
    fun2 += "}\n"

    contents_c += fun2

    filename = os.path.join(output_directory, f"instrumentation_{HASH}")
    with open(f"{filename}.h", "w") as f:
        f.write(contents_h)

    with open(f"{filename}.c", "w") as f:
        f.write(contents_c)

    return filename + '.c'
