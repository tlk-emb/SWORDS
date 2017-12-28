# -*- coding: utf-8 -*-
import logging
from operator import itemgetter, or_

from clang.cindex import Config, CursorKind, Index

class AnalyzerError(Exception):
    pass


class Prototype(object):
    def __init__(self, node):
        self.node = node

    @property
    def code(self):
        return_type = self.node.type.get_result().kind.spelling.lower()
        function_name = self.node.displayname
        return "%s %s;" % (return_type, function_name)


class FunctionDefinition(object):
    def __init__(self, node, body_node):
        self.node = node
        self.body_node = body_node
        self.is_software = False
        self.is_hardware = False
        self.pragmas = []

    def __lt__(self, other):
        if not isinstance(other, FunctionDefinition):
            raise TypeError

        return (
            self.node.extent.start.line < other.node.extent.start.line
            or self.node.extent.start.column < other.node.extent.start.column
            or self.node.extent.end.line < other.node.extent.end.line
            or self.node.extent.end.column < other.node.extent.end.column)

    @property
    def calling_function_names(self):
        """この関数が呼び出している関数名の集合を返す"""
        def visit(node):
            if node.kind == CursorKind.CALL_EXPR:
                return {node.spelling}
            return reduce(or_, [visit(n) for n in node.get_children()], set())

        return visit(self.node)


class DesignAnalysis(object):
    def __init__(self, filename, llvm_libdir=None, llvm_libfile=None):
        self.prototypes = []
        self.functions = {}

        self.filename = filename

        if llvm_libdir is not None:
            Config.set_library_path(llvm_libdir)

        if llvm_libfile is not None:
            Config.set_library_file(llvm_libfile)

        self._parse()

    def _parse(self):
        self.prototypes = []
        self.functions = {}

        def visit_compound(node):
            if node.kind == CursorKind.COMPOUND_STMT:
                return node
            for n in node.get_children():
                result = visit_compound(n)
                if result is not None:
                    return result
            return None

        def visit(node):
            if node.kind == CursorKind.FUNCTION_DECL:
                if str(node.extent.start.file) != self.filename:
                    # Function is not declared in the source file
                    return
#                elif node.is_definition():
                elif node.location == node.get_definition().location: 
                    body_node = visit_compound(node)
                    if body_node is None:
                        raise AnalyzerError
                    definition = FunctionDefinition(node, body_node)
                    self.functions[node.spelling] = definition
                else:
                    self.prototypes.append(Prototype(node))

            for n in node.get_children():
                visit(n)

        visit(Index.create().parse(self.filename).cursor)

    def calc_set_of_hardware_functions(self, initial):
        """ハードウェア化される関数名の集合を求める"""
        names = initial
        count = 0
        while count != len(names):
            count = len(names)
            for name in names.copy():
                for callee in self.functions[name].calling_function_names:
                    if callee not in self.functions:
                        logging.info("cannot infer %s, skipping", callee)
                        continue
                    names.add(callee)
        return names

    def analyze_hardware_functions(self, config):
        """ハードウェア化される関数の情報を求める"""
        initial = set(config.hardware_tasks.keys())
        for name in self.calc_set_of_hardware_functions(initial):
            self.functions[name].is_hardware = True

    def calc_set_of_software_functions(self, soft_initial, hard_initial):
        """ソフトウェア化される関数名の集合を求める"""
        names = soft_initial
        count = 0
        while count != len(names):
            count = len(names)
            for name in names.copy():
                for callee in self.functions[name].calling_function_names:
                    if callee not in self.functions:
                        logging.info("cannot infer %s, skipping", callee)
                    elif callee in hard_initial:
                        pass
                    else:
                        names.add(callee)
        return names

    def analyze_software_functions(self, config):
        """ソフトウェア化される関数の情報を求める"""
        s_initial = set(config.software_tasks.keys())
        h_initial = set(config.hardware_tasks.keys())
        for name in self.calc_set_of_software_functions(s_initial, h_initial):
            self.functions[name].is_software = True

    def validate_division(self, config):
        all_names = set(self.functions.keys())
        soft_names = set(
            map(itemgetter(0),
                filter(lambda (n, f): f.is_software, self.functions.items())))
        hard_names = set(
            map(itemgetter(0),
                filter(lambda (n, f): f.is_hardware, self.functions.items())))

        logging.debug("all: %s", all_names)
        logging.debug("soft: %s", soft_names)
        logging.debug("hard: %s", hard_names)

        not_implemented_names = all_names - (soft_names | hard_names)
        if not_implemented_names != set():
            logging.error("some functions are not implemented: %s",
                          not_implemented_names)
            return False

        initial_hard_names = set(config.hardware_tasks.keys())
        both_implemented_names = soft_names & initial_hard_names
        if both_implemented_names != set():
            logging.error("cannot implement these functions in software: %s",
                          both_implemented_names)
            return False

        return True

    def analyze(self, config):
        self.analyze_hardware_functions(config)
        self.analyze_software_functions(config)
        if not self.validate_division(config):
            raise AnalyzerError

    def generate_output(self):
        output = []

        with open(self.filename) as f:
            source = map(lambda s: s.rstrip(), f.readlines())

        for line in source:
            if line.startswith("#include"):
                output.append((False, True, line))
                continue
            elif not ((line.startswith("#define") or line.startswith("typedef")) and line != "\n") or line.startswith("#pragma HLS") :
                continue
            output.append((True, True, line))

        for p in self.prototypes:
            output.append((True, True, p.code))

        for f in sorted(self.functions.values()):
            first_part = source[f.node.extent.start.line - 1:
                                f.body_node.extent.start.line]
            first_part[-1] = first_part[-1][:f.body_node.extent.start.column]

            second_part = source[f.body_node.extent.start.line - 1:
                                 f.node.extent.end.line]
            second_part[0] = second_part[0][f.body_node.extent.start.column:]

            for line in first_part:
                output.append((f.is_hardware, f.is_software, line))

            for pragma in f.pragmas:
                output.append((True, False, pragma))

            for line in second_part:
                output.append((f.is_hardware, f.is_software, line))

        return output
