"""Small interpreter for the AST in parser.py.

Run: python interpreter.py source.txt
"""

import sys
from functools import wraps
from lexer import tokenize
from parser import ( # Imports all AST nodes classes
    Parser, Program, VariableSection, Declaration, Assignment,
    TypecastStmt, TypecastExpr, PrintStmt, InputStmt, Conditional, Switch,
    Loop, FuncDef, FuncCall, Return, Break, Literal, VarRef, Comment,
    ArithExpr, BoolExpr, NotExpr, InfiniteBool, CompareExpr, Concatenation,
)

# These signals tell the interpreter to stop executing a particular block

class ReturnSignal(Exception): # When FOUND YR is encountered, ReturnSignal is raised with the resulting value 
    def __init__(self, value):
        self.value = value


class BreakSignal(Exception): # Exits a loop
    pass


def attaches_runtime_location(method):
    """Preserve the innermost failing AST node's real source location.

    The interpreter is otherwise unaware of the workbench; CLI callers without
    source spans retain the same behavior and exception messages.
    """
    @wraps(method)
    def wrapped(self, node, *args, **kwargs):
        try:
            return method(self, node, *args, **kwargs)
        except (RuntimeError, ZeroDivisionError, ValueError) as error:
            if getattr(error, "start_offset", None) is None:
                location = self.node_spans.get(id(node))
                if location:
                    for key, value in location.items():
                        setattr(error, key, value)
            raise
    return wrapped


class Interpreter:
    def __init__(self, input_func=input, output_func=print):
        self.scopes = [{"IT": None}] # Where variables are stored
                                     # "IT" stores the result of the most recent relevant expression or operation
        self.node_spans = {}  # Optional parser metadata for precise runtime diagnostics
        self.functions = {} # Stores function definitions
                            # e.g. self.functions["PRE_ADD"] = function_definition
        self.input = input_func
        self.output = output_func

    @property # Combines the variables in all scopes into one dictionary
    def variables(self):
        result = {}
        for scope in self.scopes:
            result.update(scope)
        return result

    # This searches for a variable and returns its value
    def get(self, name):
        # reversed() call searches the most recently added scope first
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise RuntimeError(f"Undefined variable: {name}")

    # This updates the value if it already exists, if not then it creates in the innermost scope
    def set(self, name, value):
        for scope in reversed(self.scopes):
            if name in scope:
                scope[name] = value
                return
        self.scopes[-1][name] = value

    # This converts a value to a Boolean
    def truth(self, value):
        if value is None:
            return False
        if isinstance(value, (int, float, bool)):
            return value != 0
        return value != ""

    # Coerce values for arithmetic operations.
    def number(self, value):
        if value is None:
            return 0
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return value
        try:
            text = str(value).strip()
            return float(text) if "." in text else int(text)
        except ValueError:
            raise RuntimeError(f"Cannot convert {value!r} to a number.")

    # Format a value using LOLCODE literals.
    def display(self, value):
        if value is None:
            return "NOOB"
        if value is True:
            return "WIN"
        if value is False:
            return "FAIL"
        return str(value)

    # This handles the type target, and raises an exception when there is an unknown type
    def cast(self, value, target):
        target = target.upper()
        if target == "NOOB":
            return None
        if target == "TROOF":
            return self.truth(value)
        if target == "NUMBR":
            return int(self.number(value))
        if target == "NUMBAR":
            return float(self.number(value))
        if target == "YARN":
            return self.display(value)
        if target == "TYPE":
            if value is None:
                return "NOOB"
            if isinstance(value, bool):
                return "TROOF"
            if isinstance(value, int):
                return "NUMBR"
            if isinstance(value, float):
                return "NUMBAR"
            return "YARN"
        raise RuntimeError(f"Unknown type: {target}")

    # This produces the values of the expressions
    @attaches_runtime_location
    def evaluate(self, node):
        if isinstance(node, Literal):
            value = node.value
            if node.kind == "NOOB":
                value = None
            self.set("IT", value)
            return value

        if isinstance(node, VarRef):
            value = self.get(node.name)
            self.set("IT", value)
            return value

        if isinstance(node, TypecastExpr):
            value = self.cast(self.evaluate(node.value), node.cast_type)
        elif isinstance(node, FuncCall):
            value = self.call(node)
        elif isinstance(node, ArithExpr):
            a, b = self.number(self.evaluate(node.left)), self.number(self.evaluate(node.right))
            ops = {
                "SUM_OF": lambda: a + b,
                "DIFF_OF": lambda: a - b,
                "PRODUKT_OF": lambda: a * b,
                "QUOSHUNT_OF": lambda: a / b,
                "MOD_OF": lambda: a % b,
                "BIGGR_OF": lambda: max(a, b),
                "SMALLR_OF": lambda: min(a, b),
            }
            if node.op == "QUOSHUNT_OF" and b == 0:
                raise RuntimeError("Division by zero.")
            if node.op == "MOD_OF" and b == 0:
                raise RuntimeError("Modulo by zero.")
            if node.op not in ops:
                raise RuntimeError(f"Unknown arithmetic operator: {node.op}")
            value = ops[node.op]()
        elif isinstance(node, BoolExpr):
            a, b = self.truth(self.evaluate(node.left)), self.truth(self.evaluate(node.right))
            value = {
                "BOTH_OF": a and b,
                "EITHER_OF": a or b,
                "WON_OF": a != b,
            }[node.op]
        elif isinstance(node, NotExpr):
            value = not self.truth(self.evaluate(node.value))
        elif isinstance(node, InfiniteBool):
            values = [self.truth(self.evaluate(v)) for v in node.values]
            value = all(values) if node.op == "ALL_OF" else any(values)
        elif isinstance(node, CompareExpr):
            a, b = self.evaluate(node.left), self.evaluate(node.right)
            value = (a == b) if node.op == "BOTH_SAEM" else (a != b)
        elif isinstance(node, Concatenation):
            value = "".join(self.display(self.evaluate(v)) for v in node.values)
        else:
            raise RuntimeError(f"Unsupported expression: {type(node).__name__}")

        self.set("IT", value)
        return value

    # A list of statements
    def block(self, statements):
        for statement in statements:
            self.execute(statement)

    # This runs the statements
    @attaches_runtime_location
    def execute(self, node):
        if node is None or isinstance(node, Comment):
            return

        if isinstance(node, Program):
            self.functions = {fn.name: fn for fn in node.functions}
            self.block(node.body)
        elif isinstance(node, VariableSection):
            self.block(node.declarations)
        elif isinstance(node, Declaration):
            value = self.evaluate(node.value) if node.value is not None else None
            self.scopes[-1][node.name] = value
        elif isinstance(node, Assignment):
            self.set(node.name, self.evaluate(node.value))
        elif isinstance(node, TypecastStmt):
            self.set(node.name, self.cast(self.get(node.name), node.cast_type))
            self.set("IT", self.get(node.name))
        elif isinstance(node, PrintStmt):
            text = "".join(self.display(self.evaluate(v)) for v in node.values)
            if node.suppress_newline:
                self.output(text, end="")
            else:
                self.output(text)
        elif isinstance(node, InputStmt):
            self.set(node.name, self.input(f"{node.name}? "))
            self.set("IT", self.get(node.name))
        elif isinstance(node, Conditional):
            condition = self.get("IT") if node.condition is None else self.evaluate(node.condition)
            if self.truth(condition):
                self.block(node.body)
            else:
                for clause in node.elseifs:
                    if self.truth(self.evaluate(clause["condition"])):
                        self.block(clause["body"])
                        break
                else:
                    self.block(node.else_body)
        elif isinstance(node, Switch):
            target = self.get("IT")
            for case in node.cases:
                if target == self.evaluate(case["value"]):
                    try:
                        self.block(case["body"])
                    except BreakSignal:
                        pass
                    break
            else:
                try:
                    self.block(node.default)
                except BreakSignal:
                    pass
        elif isinstance(node, Loop):
            count = 0
            while True:
                if node.condition:
                    condition = self.truth(self.evaluate(node.condition["value"]))
                    if node.condition["type"] == "TIL" and condition:
                        break
                    if node.condition["type"] == "WILE" and not condition:
                        break
                count += 1
                if count > 1_000_000:
                    raise RuntimeError(f"Loop '{node.label}' exceeded the safety limit.")
                try:
                    self.block(node.body)
                except BreakSignal:
                    break
                if node.op:
                    name = node.op["var"]
                    value = self.number(self.get(name))
                    value += 1 if node.op["operation"] == "UPPIN" else -1
                    self.set(name, value)
        elif isinstance(node, FuncDef):
            self.functions[node.name] = node
        elif isinstance(node, FuncCall):
            self.set("IT", self.call(node))
        elif isinstance(node, Return):
            raise ReturnSignal(self.evaluate(node.value))
        elif isinstance(node, Break):
            raise BreakSignal()
        else:
            self.evaluate(node)

    # This calls the function
    @attaches_runtime_location
    def call(self, call):
        if call.name not in self.functions:
            raise RuntimeError(f"Undefined function: {call.name}")
        function = self.functions[call.name]
        if len(call.args) != len(function.params):
            raise RuntimeError(f"{call.name} expects {len(function.params)} argument(s).")

        local = {"IT": None}
        local.update(zip(function.params, [self.evaluate(arg) for arg in call.args]))
        self.scopes.append(local)
        try:
            try:
                self.block(function.body)
            except ReturnSignal as result:
                return result.value
            except BreakSignal:
                pass  # GTFO exits a function in this parser's language rules
            return self.get("IT")
        finally:
            self.scopes.pop()

    # These connect the lexer, parser, and interpreter
    def run_source(self, source):
        tokens = tokenize(source)
        parser = Parser(tokens)
        program = parser.parse()
        if not parser.is_at_end():
            token = parser.peek()
            raise SyntaxError(f"Line {token[2]}: Unexpected token '{token[1]}' after program.")
        return self.execute(program)

    def run_file(self, filename):
        with open(filename, encoding="utf-8") as file:
            return self.run_source(file.read())


if __name__ == "__main__":
    filename = sys.argv[1] if len(sys.argv) > 1 else "source.txt"
    try:
        Interpreter().run_file(filename)
    except (SyntaxError, RuntimeError, ZeroDivisionError) as error:
        print(f"LOLCODE error: {error}", file=sys.stderr)
        sys.exit(1)
