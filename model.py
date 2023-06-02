from typing import List


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
    type_type = "struct"

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields


# The symbols that are globally visible in a file
class Symbols:
    def __init__(self, declared_functions: List[Function], defined_local_functions: List[Function], global_variables, types):
        self.declared_functions = declared_functions
        self.defined_functions = defined_local_functions
        self.global_variables = global_variables
        self.types = types

    def has_function(self, function_name):
        for function in (self.defined_functions + self.declared_functions):
            if function.name == function_name:
                return True
        return False


class DependencySet:
    def __init__(self, all_dependencies):
        self.all_dependencies = all_dependencies
        self.used_dependencies = set()

    def to_json(self):
        unused_dependencies = [dep.name for dep in self.all_dependencies if dep.name not in self.used_dependencies]
        return {"used": list(self.used_dependencies), "unused": unused_dependencies}

    def __repr__(self):
        return "DependencySet(dependencies=%s)" % (self.dependencies)

    def add_used_function(self, function_name):
        self.used_dependencies.add(function_name)


class CFile:
    def __init__(self, filename, symbols: Symbols, dependencies: DependencySet):
        self.filename = filename
        self.symbols = symbols
        self.dependencies = dependencies

    def add_used_function(self, function_name):
        if not self.symbols.has_function(function_name):
            self.dependencies.add_used_function(function_name)


class ProjectCatalogue:
    def __init__(self, c_files):
        self.files = c_files
