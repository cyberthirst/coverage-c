#-----------------------------------------------------------------
# pycparser: dump_ast.py
#
# Basic example of parsing a file and dumping its parsed AST.
#
# Eli Bendersky [https://eli.thegreenplace.net/]
# License: BSD
#-----------------------------------------------------------------
import argparse
import sys

# This is not required if you've installed pycparser into
# your site-packages/ with setup.py
sys.path.extend(['.', '..'])

from pycparser import parse_file

if __name__ == "__main__":
    """
    argparser = argparse.ArgumentParser('Dump AST')
    argparser.add_argument('filename',
                           default='src/c_files/basic.c',
                           nargs='?',
                           help='name of file to parse')
    argparser.add_argument('--coord', help='show coordinates in the dump',
                           action='store_true')
    args = argparser.parse_args()

    ast = parse_file(args.filename, use_cpp=False)
    ast.show(showcoord=args.coord)
    """

    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = 'src/c_files/suite2/test1.c'

    ast = parse_file(filename, use_cpp=True,
                     cpp_path='gcc',
                     cpp_args=['-E', r'-Ipycparser/utils/fake_libc_include'])
    ast.show(showcoord=True)