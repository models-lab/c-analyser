import sqlite3

import os
from model import ProjectCatalogue


def create_tables(cur):
    cur.execute("CREATE TABLE IF NOT EXISTS functions(name VARCHAR(255), filename TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS types(name VARCHAR(255), type VARCHAR(128), filename TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS global_variables(name VARCHAR(255), type VARCHAR(128), filename TEXT)")

    cur.execute("CREATE TABLE IF NOT EXISTS function_dependencies(symbol_name VARCHAR(255), function VARCHAR(255))")

def dump(filename: str, catalogue: ProjectCatalogue):
    if os.path.exists(filename):
        os.remove(filename)

    con = sqlite3.connect(filename)
    cur = con.cursor()
    create_tables(cur)

    for c_file in catalogue.files:
        for func in c_file.symbols.all_functions():
            cur.execute("INSERT INTO functions VALUES (?, ?)", (func.name, c_file.filename))

        for type in c_file.symbols.types:
            cur.execute("INSERT INTO types VALUES (?, ?, ?)", (type.name, type.type_type, c_file.filename))

        for global_variable in c_file.symbols.variables:
            cur.execute("INSERT INTO global_variables VALUES (?, ?, ?)",
                        (global_variable.name, global_variable.type, c_file.filename))

        for function in c_file.symbols.defined_functions:
            for dependency in function.dependencies.used_dependencies:
                dependency_name = dependency
                cur.execute("INSERT INTO function_dependencies VALUES (?, ?)", (dependency_name, function.name))

    con.commit()

    return None

# https://docs.python.org/3/library/sqlite3.html
