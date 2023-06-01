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

    type_type = "struct"

    def __init__(self, name, fields):
        self.name = name
        self.fields = fields


class ProjectCatalogue:
    def __init__(self, c_files):
        self.files = c_files
