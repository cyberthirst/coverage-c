from pycparser.c_ast import NodeVisitor, FuncDef

#finds (recursively) the minimal column for the provided node
# why?
# - int y = x + 1;
# - this declarations has in the coordinates column 5 (and not 1)
# - little weirdness of the pycparser library
class MinColVisitor(NodeVisitor):
    def __init__(self):
        self.min = None

    def generic_visit(self, node):
        for child_name, child in node.children():
            self.min = min(self.min, child.coord.column)
            self.visit(child)

    def get_min_col(self, node):
        self.min = node.coord.column
        self.visit(node)
        return self.min


class InstrumentationVisitor(NodeVisitor):
    def __init__(self):
        self.instrumentation_info = {}
        self.min_col_visitor = MinColVisitor()

    def _get_min_col(self, node):
        return self.min_col_visitor.get_min_col(node)

    def _add_info(self, node, col=None):
        line = node.coord.line
        if not col:
            col = self._get_min_col(node)
        if line not in self.instrumentation_info:
            self.instrumentation_info[line] = set()
        self.instrumentation_info[line].add(col)

    def get_instrumentation_info(self):
        for line in self.instrumentation_info.keys():
            #update to point to the minimal column
            self.instrumentation_info[line] = min(self.instrumentation_info[line])
        return self.instrumentation_info

    def visit_FuncCall(self, node):
        self._add_info(node)
        self.generic_visit(node)

    def visit_Return(self, node):
        self._add_info(node)
        self.generic_visit(node)

    def visit_Decl(self, node):
        self._add_info(node)
        self.generic_visit(node)

    def visit_Assignment(self, node):
        self._add_info(node)
        self.generic_visit(node)

    def visit_For(self, node):
        self._add_info(node, node.coord.column)
        #we don't care about the for loop header, the declarations in the header
        # would cause us to instrument the header, so we intentionally skip it
        self.generic_visit(node.stmt)

    def visit_If(self, node):
        self._add_info(node, node.coord.column)
        self.generic_visit(node)


    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for child_name, child in node.children():
            self.visit(child)
