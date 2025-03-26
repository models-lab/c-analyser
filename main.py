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
import argparse

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
    def __init__(self, filename, c_file: CFile):
        super().__init__(filename)
        self.c_file = c_file

    def visit_FuncDef(self, node):
        if not self.is_defined_here(node):
            return

        # Since definitions are after declarations, we can remove a declaration from external dependencies
        # if we find its definition
        self.c_file.dependencies.remove_dependency(node.decl.name)
        f = Function(node.decl.name, None, None)
        self.c_file.symbols.add_defined_function(f)
        UsedExternalElementVisitor(f).visit(node)

    def visit_Typedef(self, node):
        if node.coord.file != self.filename:
            return

    def visit_Decl(self, node):
        if self.is_defined_here(node):
            dcl = self.create_declaration(node)
            if isinstance(node.type, c_ast.TypeDecl):
                self.c_file.symbols.add_variable(dcl)
            elif isinstance(node.type, c_ast.FuncDecl):
                self.c_file.symbols.add_declared_function(dcl)
        else:
            dcl = self.create_declaration(node)
            self.c_file.dependencies.add_dependency(dcl)

    def create_declaration(self, node):
        if isinstance(node.type, c_ast.TypeDecl):
            name = node.name
            type_name = node.type.type.names[0]
            if len(node.type.type.names) != 1:
                raise Exception("Unuspported number of type names")

            return Variable(name, type_name)
        elif isinstance(node.type, c_ast.FuncDecl):
            # This is what we get in .h files. Details are in .type
            f = Function(node.name, None, None)
            return f
        elif isinstance(node.type, c_ast.ArrayDecl):
            v = Variable(node.name, None) # TODO: Set the type
            return v
        elif isinstance(node.type, c_ast.PtrDecl):
            v = Variable(node.name, None)  # TODO: Set the type
            return v
        elif isinstance(node.type, c_ast.Enum):
            v = Variable(node.name, None)  # TODO: Set the type
            return v
        elif isinstance(node.type, c_ast.Struct):
            v = Variable(node.name, None)  # TODO: Set the type
            return v
        else:
            raise Exception("Unsupported declaration type", node)


class UsedExternalElementVisitor(c_ast.NodeVisitor):
    """
    This visitor is used to find all the external elements that are used inside a module
    """

    def __init__(self, scope: WithDependencies):
        self.scope = scope

    def visit_FuncCall(self, node):
        # This means that it is likely a call to a function pointer
        if not isinstance(node.name, c_ast.ID):
            return

        function_name = node.name.name
        assert isinstance(function_name, str)
        self.scope.add_used_function(function_name)


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
        # check if object respond to a method
        if hasattr(obj, 'to_json'):
            return obj.to_json()
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
    #more_args = ["-DUNIT_TESTING", "-DDEBUG", "-DCPU_S32K148HAT0MLLT", "-DRTE_PTR2ARRAYBASETYPE_PASSING",
    #             "-DCPU_S32K148HAT0MLLT"]
    # TODO: Pass this as part of the configuration given in main
    more_args = []


    all_args = all_libs + more_args

    try:
        ast = parse_file(filename, use_cpp=True,
                         cpp_path='cpp',
                         cpp_args=all_args)
    except pycparser.plyparser.ParseError:
        print("Error! Could not parse file %s" % filename)
        symbols_set = Symbols([], [], [], [])
        dependency_set = DependencySet([])
        # TODO: Mark as error
        return CFile(filename)

    # r'-Iutils/fake_libc_include'
    # ast.show()

    #symbols_set = Symbols(declared_local_functions, defined_local_functions, global_variables, type_visitor.types)
    #dependency_set = DependencySet(v.all_dependencies)
    c_file = CFile(filename) #, symbols_set, dependency_set)


    v = FuncDefVisitor(filename, c_file)
    v.visit(ast)
    #global_variables = v.global_variables
    #defined_local_functions = v.defined_functions
    #declared_local_functions = v.declared_functions

    type_visitor = TypeVisitor(filename)
    type_visitor.visit(ast)

    v = UsedExternalElementVisitor(c_file)
    v.visit(ast)

    # ast.show()
    return c_file


def main(folder, args, conf):
    sources = conf["sources"]
    includes = conf["includes"] if "includes" in conf else []
    
    all_c_files = []
    if len(sources) == 0:
        c_files = process_all_c_files(folder, includes)
        all_c_files.extend(c_files)
    else:
        for src in sources:
            c_files = process_all_c_files(os.path.join(folder, src), includes)
            all_c_files.extend(c_files)

    catalogue = ProjectCatalogue(all_c_files)

    if args.output_json:
        dump(args.output_json, catalogue)
    if args.output:
        db.dump(args.output, catalogue)


def dump(filename, all_symbols):
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(all_symbols, f, cls=MyEncoder, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # Parse with arpgarse. option 1: input folder, option 2: configuration file (--config), option 3: output file
    argparser = argparse.ArgumentParser()
    argparser.add_argument('folder', help='The folder where the sources are located')
    argparser.add_argument('--config', help='The configuration file')
    argparser.add_argument('--output', help='The output file')
    argparser.add_argument('--output-json', required=False, help='The output file')

    args = argparser.parse_args()

    file = args.folder
    with open(args.config) as f:
        conf = yaml.load(f, Loader=yaml.FullLoader)
    
    main(file, args, conf)

