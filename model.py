from typing import List


class WithDependencies:
    def __init__(self, symbols, dependencies):
        self.symbols = symbols
        self.dependencies = dependencies

    def add_used_function(self, function_name):
        if not self.symbols.has_function(function_name):
            self.dependencies.add_used_function(function_name)


class Variable:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        assert self.type is None or isinstance(self.type, str)

    def __repr__(self):
        return "Variable(name=%s, type=%s)" % (self.name, self.type)


class Function(WithDependencies):
    def __init__(self, name, type, parameters):
        super().__init__(symbols=Symbols(), dependencies=DependencySet())
        self.name = name
        self.type = type
        self.parameters = parameters
        assert isinstance(self.name, str)

    def to_json(self):
        # TODO: Distinguish between declared and defined functions because declared functions do not have used dependencies
        return {
            "name": self.name,
            "type": self.type,
            "parameters": self.parameters,
            "used_dependencies": list(self.dependencies.used_dependencies),
        }


class Parameter(Variable):
    def __init__(self, name, type):
        super().__init__(name, type)
        assert isinstance(self.name, str)


class Field(Variable):
    def __init__(self, name, type):
        super().__init__(name, type)
        assert isinstance(self.name, str)


class StructType:
    type_type = "struct"

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields
        assert isinstance(self.name, str)


# The symbols that are declared in a certain module
class Symbols:
    def __init__(self):
        self.declared_functions = []
        self.defined_functions = []
        self.variables = []
        self.types = []

    def add_declared_function(self, function):
        self.declared_functions.append(function)

    def add_defined_function(self, function):
        self.defined_functions.append(function)

    def add_variable(self, variable):
        self.variables.append(variable)

    def add_type(self, type):
        self.types.append(type)

    def all_functions(self):
        return self.defined_functions + self.declared_functions

    def has_function(self, function_name):
        for function in (self.defined_functions + self.declared_functions):
            if function.name == function_name:
                return True
        return False


class DependencySet:
    def __init__(self):
        self.all_dependencies = []
        self.used_dependencies = set()

    def add_dependency(self, dependency):
        self.all_dependencies.append(dependency)

    def remove_dependency(self, name):
        self.all_dependencies = [dcl for dcl in self.all_dependencies if dcl.name != name]

    def to_json(self):
        unused_dependencies = [dep.name for dep in self.all_dependencies if dep.name not in self.used_dependencies]
        return {"used": list(self.used_dependencies), "unused": unused_dependencies}

    def __repr__(self):
        return "DependencySet(dependencies=%s)" % (self.dependencies)

    def add_used_function(self, function_name: str):
        assert isinstance(function_name, str)
        self.used_dependencies.add(function_name)


class CFile(WithDependencies):
    def __init__(self, filename):
        super().__init__(Symbols(), DependencySet())
        self.filename = filename


class ProjectCatalogue:
    def __init__(self, c_files):
        self.files = c_files
