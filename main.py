# Things to check
# - https://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang
# - libclang python bindings
# . https://stackoverflow.com/questions/36808565/using-libclang-to-parse-in-c-in-python
# - https://pypi.org/project/libclang/
import json
import os
import sys

import yaml as yaml
from pycparser import parse_file, c_ast
import pycparser

import pycparser_fake_libc
import db
from model import *

class BaseNodeVisitor(c_ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename

    def is_defined_here(self, node):
        return node.coord.file == self.filename


class TypeVisitor(BaseNodeVisitor):

    def __init__(self, filename):
        super().__init__(filename)
        self.types = []

    def visit_TypeDecl(self, node):
        # This is for functions... and probably inside structs
        # print("==> type decl", node)
        pass

    def visit_Union(self, node):
        print("==> union", node)
        # raise Exception("Union not supported")

    def visit_Enum(self, node):
        print("==> enum", node)
        # raise Exception("Enum not supported")

    def visit_Typedef(self, node):
        if not self.is_defined_here(node):
            return

        # print("==> typedef", node)
        name = node.name
        visitor = TypeVisitor.StructVisitor(name)
        visitor.visit(node.type)
        self.types.append(visitor.to_struct())

    class StructVisitor(c_ast.NodeVisitor):

        def __init__(self, name):
            self.name = name
            self.fields = []

        def to_struct(self):
            return StructType(self.name, self.fields)

        def visit_Struct(self, node):
            print("==> struct", node)
            if node.decls is None:
                print("Node with decls None")
                return

            for dcl in node.decls:
                name = dcl.name
                type = None
                self.fields.append(Field(name, type))


class FuncDefVisitor(BaseNodeVisitor):
    def __init__(self, filename):
        super().__init__(filename)
        self.global_variables = []
        self.functions = []

    def visit_FuncCall(self, node):
        print("==> func call", node)

    def visit_FuncDef(self, node):
        print("==> func def", node)
        # if node.coord.file == self.filename
        # I think this is not needed
        # self.functions.append(node)
        self.functions.append(Function(node.decl.name, None, None))  # , node.decl.type, node.decl.type.args.params))
        # node.storage
        print('%s at %s' % (node.decl.name, node.decl.coord))
        print(type(node.decl.coord))

    def visit_Typedef(self, node):
        if node.coord.file != self.filename:
            return

        # print("==> typedef", node)

    def visit_Decl(self, node):
        print("==> dcl", node)

        if self.is_defined_here(node):
            if isinstance(node.type, c_ast.TypeDecl):
                name = node.name
                type_name = node.type.type.names[0]
                if len(node.type.type.names) != 1:
                    raise Exception("Unspported number of type names")

                self.global_variables.append(Variable(name, type_name))
            elif isinstance(node.type, c_ast.FuncDecl):
                # This is what we get in .h files. Details are in .type
                f = Function(node.name, None, None)
                self.functions.append(f)


class ExternalFunctionVisitor(c_ast.NodeVisitor):

    def __init__(self, local_functions):
        self.local_functions = local_functions
        self.external_functions_names = []

    def visit_FuncCall(self, node):
        function_name = node.name.name
        if not self.is_locally_defined(function_name):
            self.external_functions_names.append(function_name)

    def is_locally_defined(self, function_name):
        for function in self.local_functions:
            if function.name == function_name:
                return True
        return False


def get_all_c_files(input_folder):
    ignore = [
        "src/Applications/SipAddon/CEVT_xDM/Appl/Swc/HBrM",
        # "src/Applications/SipAddon/CEVT_xDM/Appl/Swc/VCfg", # Because it works only on windows...
        # "src/Applications/SipAddon/CEVT_xDM/Appl/Swc/CarM" # Because it works only on windows...
    ]

    for (dirpath, dirnames, filenames) in os.walk(input_folder, topdown=True, followlinks=False):
        for filename in filenames:
            if any([i in dirpath for i in ignore]):
                continue

            if filename.endswith(".c") or filename.endswith(".h"):
                yield os.path.join(dirpath, filename)


from json import JSONEncoder


class MyEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__


def process_all_c_files(folder, includes: list):
    c_files = []
    for c_file in get_all_c_files(folder):
        print("Processing %s" % c_file)
        c_file_obj = process_file(c_file, includes)
        c_files.append(c_file_obj)

    return c_files


def process_file(filename, includes):
    fake_libc_arg = ["-I" + pycparser_fake_libc.directory]
    libs = ["-I" + lib for lib in includes]
    all_libs = fake_libc_arg + libs

    # more_args = ["-DMICROSAR_DISABLE_MEMMAP"]
    more_args = ["-DUNIT_TESTING", "-DDEBUG", "-DCPU_S32K148HAT0MLLT", "-DRTE_PTR2ARRAYBASETYPE_PASSING",
                 "-DCPU_S32K148HAT0MLLT"]

    all_args = all_libs + more_args

    try:
        ast = parse_file(filename, use_cpp=True,
                         cpp_path='cpp',
                         cpp_args=all_args)
    except pycparser.plyparser.ParseError:
        print("Error!")
        return CFile(filename, [], [], [])

    # r'-Iutils/fake_libc_include'
    # ast.show()
    v = FuncDefVisitor(filename)
    v.visit(ast)
    global_variables = v.global_variables
    local_functions = v.functions

    type_visitor = TypeVisitor(filename)
    type_visitor.visit(ast)

    v = ExternalFunctionVisitor(local_functions)
    v.visit(ast)

    # ast.show()
    return CFile(filename, local_functions, global_variables, type_visitor.types)


def main(folder, sources, includes):
    all_c_files = []
    if len(sources) == 0:
        c_files = process_all_c_files(folder, includes)
        all_c_files.extend(c_files)
    else:
        for src in sources:
            c_files = process_all_c_files(os.path.join(folder, src), includes)
            all_c_files.extend(c_files)

    catalogue = ProjectCatalogue(all_c_files)

    dump("/tmp/data.json", catalogue)
    db.dump("/tmp/data.db", catalogue)

def dump(filename, all_symbols):
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_symbols, f, cls=MyEncoder, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    file = sys.argv[1]
    conf = yaml.load(open(sys.argv[2]), Loader=yaml.FullLoader)
    includes = conf["includes"] if "includes" in conf else []
    main(file, conf["sources"], includes)
