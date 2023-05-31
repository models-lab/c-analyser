# Things to check
# - https://eli.thegreenplace.net/2011/07/03/parsing-c-in-python-with-clang
# - libclang python bindings
# . https://stackoverflow.com/questions/36808565/using-libclang-to-parse-in-c-in-python
# - https://pypi.org/project/libclang/

import os
import sys
from pycparser import parse_file, c_ast

import pycparser_fake_libc


class CFile:
    def __init__(self, filename, functions, global_variables, types):
        self.filename = filename
        self.functions = functions
        self.global_variables = global_variables
        self.types = types

class Variable:
    def __init__(self, name, type):
        self.name = name
        self.type = type

    def __repr__(self):
        return "Variable(name=%s, type=%s)" % (self.name, self.type)


class Function:
    def __init__(self, name, type, parameters):
        self.name = name
        self.type = type
        self.parameters = parameters


class Parameter(Variable):
    def __init__(self, name, type):
        super().__init__(name, type)

class Field(Variable):
    def __init__(self, name, type):
        super().__init__(name, type)

class StructType:
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

# ast = pycparser.parse_file("c_file_to_parse.c", use_cpp=True, cpp_args=fake_libc_arg)

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
        raise Exception("Union not supported")

    def visit_Enum(self, node):
        print("==> enum", node)
        raise Exception("Enum not supported")

    def visit_Typedef(self, node):
        if not self.is_defined_here(node):
            return

        #print("==> typedef", node)
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
        #self.functions.append(node)
        self.functions.append(Function(node.decl.name, None, None)) #, node.decl.type, node.decl.type.args.params))
        # node.storage
        print('%s at %s' % (node.decl.name, node.decl.coord))
        print(type(node.decl.coord))

    def visit_Typedef(self, node):
        if node.coord.file != self.filename:
            return

        #print("==> typedef", node)

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
    for (dirpath, dirnames, filenames) in os.walk(input_folder, topdown=True, followlinks=False):
        for filename in filenames:
            if filename.endswith(".c") or filename.endswith(".h"):
                yield os.path.join(dirpath, filename)


from json import JSONEncoder
class MyEncoder(JSONEncoder):
    def default(self, obj):
        return obj.__dict__

def process_all_c_files(folder):
    all_symbols = []
    for c_file in get_all_c_files(folder):
        print("Processing %s" % c_file)
        c_file_obj = process_file(c_file)
        all_symbols.append(c_file_obj)

    # serialize all_symbols to a file as json
    # https://stackoverflow.com/questions/12309269/how-do-i-write-json-data-to-a-file
    import json
    with open('/tmp/data.json', 'w', encoding='utf-8') as f:
        json.dump(all_symbols, f, cls=MyEncoder, ensure_ascii=False, indent=4)


def process_file(filename):
    fake_libc_arg = ["-I" + pycparser_fake_libc.directory]
    # You can add more -I here as part of the list

    ast = parse_file(filename, use_cpp=True,
                     cpp_path='cpp',
                     cpp_args=fake_libc_arg)
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

def main(folder):
    process_all_c_files(folder)


if __name__ == '__main__':
    file = sys.argv[1]
    main(file)
