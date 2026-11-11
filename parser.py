from dataclasses import dataclass, field
from functools import wraps
from pprint import pprint
from typing import Any, List, Optional
from lexer import tokenize, read_input

# --- Operator and Keyword Sets ---
ARITHMETIC_OPERATORS = {
    "SUM_OF", "DIFF_OF", "PRODUKT_OF", "QUOSHUNT_OF", "MOD_OF", "BIGGR_OF", "SMALLR_OF"
}

BOOLEAN_OPERATORS = {
    "BOTH_OF", "EITHER_OF", "WON_OF"
}

INFINITE_OPERATORS = {
    "ANY_OF", "ALL_OF"
}

COMPARISON_OPERATORS = {
    "BOTH_SAEM", "DIFFRINT"
}

# Build this once instead of checking every operator group for each value.
EXPRESSION_STARTERS = (
    ARITHMETIC_OPERATORS | BOOLEAN_OPERATORS | INFINITE_OPERATORS
    | COMPARISON_OPERATORS | {"SMOOSH", "MAEK", "NOT"}
)

LITERAL_TYPES = {
    "NUMBR", "NUMBAR", "YARN", "TROOF", "TYPE", "NOOB"
}

BLOCK_END_KEYWORDS = {
    "KTHXBYE", "OIC", "MEBBE", "NO_WAI", "OMG", "OMGWTF",
    "IM_OUTTA_YR", "IF_U_SAY_SO", "BUHBYE"
}

STATEMENT_KEYWORDS = {
    "WAZZUP", "I_HAS_A", "VISIBLE", "GIMMEH", "O_RLY?", "WTF?",
    "IM_IN_YR", "HOW_IZ_I", "I_IZ", "FOUND_YR", "GTFO", "BTW", "OBTW"
}


# --- AST Node Classes ---

@dataclass
class ASTNode:
    pass


@dataclass
class Program(ASTNode):
    body: List[Any] = field(default_factory=list)
    functions: List[Any] = field(default_factory=list)


@dataclass
class VariableSection(ASTNode):
    declarations: List[Any] = field(default_factory=list)


@dataclass
class Declaration(ASTNode):
    name: str
    value: Optional[Any] = None


@dataclass
class Assignment(ASTNode):
    name: str
    value: Any = None


@dataclass
class TypecastStmt(ASTNode):
    name: str
    cast_type: str = ""


@dataclass
class TypecastExpr(ASTNode):
    value: Any = None
    cast_type: str = ""


@dataclass
class PrintStmt(ASTNode):
    values: List[Any] = field(default_factory=list)
    suppress_newline: bool = False


@dataclass
class InputStmt(ASTNode):
    name: str = ""


@dataclass
class Conditional(ASTNode):
    body: List[Any] = field(default_factory=list)
    condition: Optional[Any] = None
    elseifs: List[Any] = field(default_factory=list)
    else_body: List[Any] = field(default_factory=list)


@dataclass
class Switch(ASTNode):
    cases: List[Any] = field(default_factory=list)
    default: List[Any] = field(default_factory=list)


@dataclass
class Loop(ASTNode):
    label: str
    body: List[Any] = field(default_factory=list)
    op: Optional[Any] = None
    condition: Optional[Any] = None


@dataclass
class FuncDef(ASTNode):
    name: str
    params: List[str] = field(default_factory=list)
    body: List[Any] = field(default_factory=list)


@dataclass
class FuncCall(ASTNode):
    name: str
    args: List[Any] = field(default_factory=list)


@dataclass
class Return(ASTNode):
    value: Any = None


@dataclass
class Break(ASTNode):
    pass


@dataclass
class Literal(ASTNode):
    kind: str
    value: Any = None


@dataclass
class VarRef(ASTNode):
    name: str = ""


@dataclass
class Comment(ASTNode):
    text: str = ""

@dataclass
class ArithExpr(ASTNode):
    op: str
    left: Any
    right: Any


@dataclass
class BoolExpr(ASTNode):
    op: str
    left: Any
    right: Any


@dataclass
class NotExpr(ASTNode):
    value: Any


@dataclass
class InfiniteBool(ASTNode):
    op: str
    values: List[Any] = field(default_factory=list)


@dataclass
class CompareExpr(ASTNode):
    op: str
    left: Any
    right: Any


@dataclass
class Concatenation(ASTNode):
    values: List[Any] = field(default_factory=list)

def tracks_source_span(method):
    """Attach a token-derived source span to a parsed AST node when requested.

    Only metadata is added. The parser's node values, grammar, and existing
    three-element token contract remain unchanged. The span covers exactly the
    tokens consumed by the node-producing parse method.
    """
    @wraps(method)
    def wrapped(self, *args, **kwargs):
        start = self.position
        node = method(self, *args, **kwargs)
        if self.locations is None or not isinstance(node, ASTNode):
            return node
        # Outer dispatchers (parse_value/statement/expression) must not replace
        # a location already recorded by the actual node constructor.
        if id(node) in self.node_spans:
            return node
        stop = self.position
        if start >= stop or stop > len(self.locations):
            return node
        # Keep newlines between meaningful tokens, but do not extend a node's
        # selection past its last actual token just because the parser consumed
        # a trailing line break while exiting a block.
        indices = [i for i in range(start, stop) if self.tokens[i][0] != "NEWLINE"]
        if not indices:
            return node
        first = self.locations[indices[0]]
        last = self.locations[indices[-1]]
        span = {"line": first["line"], "column": first["column"],
                "end_line": last["end_line"], "end_column": last["end_column"],
                "start_offset": first["start_offset"],
                "end_offset": last["end_offset"]}
        # O RLY? can attach an immediately preceding expression as its
        # condition. Its source range should cover that expression as well.
        if isinstance(node, Conditional) and node.condition is not None:
            condition_span = self.node_spans.get(id(node.condition))
            if condition_span and condition_span["start_offset"] < span["start_offset"]:
                span.update(line=condition_span["line"],
                            column=condition_span["column"],
                            start_offset=condition_span["start_offset"])
        self.node_spans[id(node)] = span
        return node
    return wrapped


class Parser:
    def __init__(self, tokens: list, locations=None):
        self.tokens = tokens
        if locations is not None and len(locations) != len(tokens):
            raise ValueError("Token locations must align with tokens.")
        self.locations = locations
        self.node_spans = {}
        self.position = 0
        #ensures proper usage for keywords like gtfo or found yr i.e
        self.loop_depth = 0
        self.switch_depth = 0
        self.func_depth = 0

    def is_at_end(self) -> bool:#checks all tokens have been used
        return self.position >= len(self.tokens)

    def peek(self, offset: int = 0) -> Optional[tuple]:#"peeks" the upcoming tokens
        index = self.position + offset
        if index < len(self.tokens):
            return self.tokens[index]
        return None

    def advance(self) -> Optional[tuple]:#consumes and moves forward
        token = self.peek()
        if token:
            self.position += 1
        return token

    def is_identifier_token(self, offset: int = 0) -> bool:
        #Checks if its an identifier or not to prevent splitting i.e R in ROBOT
        token = self.peek(offset)
        if not token:
            return False
        if token[0] == "IDENTIFIER":
            return True
        next_token = self.peek(offset + 1)
        if token[0] in ("R", "A") and next_token and next_token[0] == "IDENTIFIER":
            return True
        return False

    def consume_identifier(self) -> str:
        token = self.peek()
        if not token:
            raise SyntaxError("Expected IDENTIFIER, reached EOF.")

        if token[0] == "IDENTIFIER":
            self.advance()
            return token[1]

        #recombine the split identifiers
        next_token = self.peek(1)
        if token[0] in ("R", "A") and next_token and next_token[0] == "IDENTIFIER":
            self.advance()  
            self.advance() 
            return token[1] + next_token[1]
        line = token[2]
        raise SyntaxError(f"Line {line}: Expected IDENTIFIER, found '{token[1]}' ({token[0]})")

    def check(self, *expected_types: str) -> bool:#makes sure the next token matches any expected type
        token = self.peek()
        if not token:
            return False
        #edge case for AN
        if "AN" in expected_types:
            next_token = self.peek(1)
            if token[0] == "A" and next_token and next_token[0] == "IDENTIFIER" and next_token[1] == "N":
                return True
        return token[0] in expected_types or token[1] in expected_types

    def match(self, *expected_types: str) -> Optional[tuple]: #advances if it maches else a NONE
        if "AN" in expected_types:
            token = self.peek()
            next_token = self.peek(1)
            if token and token[0] == "A" and next_token and next_token[0] == "IDENTIFIER" and next_token[1] == "N":
                self.advance()  # consume 'A'
                self.advance()  # consume 'N'
                return ("AN", "AN", token[2])
        if self.check(*expected_types):
            return self.advance()
        return None

    def consume(self, expected_type: str, message: Optional[str] = None) -> tuple:
       #if it doesnt match, return a syntax error
        if expected_type == "AN":
            token = self.peek()
            next_token = self.peek(1)
            if token and token[0] == "A" and next_token and next_token[0] == "IDENTIFIER" and next_token[1] == "N":
                self.advance() 
                self.advance() 
                return ("AN", "AN", token[2])
            if token and (token[0] == "AN" or token[1] == "AN"):
                return self.advance()
            line = token[2] if token else "EOF"
            found = f"'{token[1]}' ({token[0]})" if token else "EOF"
            raise SyntaxError(message or f"Line {line}: Expected 'AN', but found {found}")
        token = self.peek()
        if token and (token[0] == expected_type or token[1] == expected_type):
            return self.advance()
        line = token[2] if token else "EOF"
        found = f"'{token[1]}' ({token[0]})" if token else "EOF"
        msg = message or f"Line {line}: Expected '{expected_type}', but found {found}"
        raise SyntaxError(msg)

    def skip_newlines(self) -> int:
        #ignore back to back newlines
        count = 0
        while self.check("NEWLINE", "COMMA"):
            self.advance()
            count += 1
        return count

    def can_start_value(self) -> bool:
        #if the next token can be a value
        token = self.peek()
        if not token:
            return False
        if token[0] in ("NEWLINE", "COMMA", "EXCLAMATION", "MKAY", "AN"):
            return False
        if token[0] in BLOCK_END_KEYWORDS or token[1] in BLOCK_END_KEYWORDS:
            return False
        if token[0] in LITERAL_TYPES or token[0] in ("I_IZ", "NOT", "SMOOSH", "MAEK"):
            return True
        if token[0] in EXPRESSION_STARTERS:
            return True
        if self.is_identifier_token():
            if token[1] in STATEMENT_KEYWORDS or token[1] in BLOCK_END_KEYWORDS:
                return False
            return True
        return False

    #all the grammar methods based on the milestone
    @tracks_source_span
    def parse(self) -> Program:
        return self.parse_program()
    
    #<program> ::= <function-definition>* HAI NEWLINE <program-body> KTHXBYE <function-definition>*
    @tracks_source_span
    def parse_program(self) -> Program:
        self.skip_newlines()
        #get the top level functions before HAI or defined after KTHXBYE
        pre_funcs = []
        while self.check("HOW_IZ_I"):
            pre_funcs.append(self.parse_function_definition())
            self.skip_newlines()

        self.consume("HAI")
        self.skip_newlines()
        body = self.parse_program_body()
        self.consume("KTHXBYE")
        self.skip_newlines()
        while self.check("HOW_IZ_I"):
            pre_funcs.append(self.parse_function_definition())
            self.skip_newlines()

        return Program(body=body, functions=pre_funcs)
    #<program-body> ::= <statement-list> | empty/ future lexeme
    def parse_program_body(self) -> List[Any]:
        return self.parse_statement_list()
    
    #<statement-list> ::= <statement> NEWLINE <statement-list> | <statement> NEWLINE | NEWLINE <statement-list>
    def parse_statement_list(self) -> List[Any]:
        statements = []
        self.skip_newlines()
        while not self.is_at_end():
            token = self.peek()
            if not token:
                break
            #terminate statement list parsing if we encounter a block-closing keyword
            if token[0] in BLOCK_END_KEYWORDS or token[1] in BLOCK_END_KEYWORDS:
                break

            #handle O RLY being preceded by an expression whose evaluation sets the implicit IT register.
            if token[0] == "O_RLY?":
                prev_expr = None
                if statements and isinstance(statements[-1], (
                    ArithExpr, BoolExpr, NotExpr, InfiniteBool,
                    CompareExpr, Concatenation, TypecastExpr, VarRef, FuncCall, Literal
                )):
                    prev_expr = statements.pop() 
                stmt = self.parse_conditional(condition=prev_expr)
            else:
                stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)
            self.skip_newlines()
        return statements
    
    #<statement> ::= <variable-section> | <assignment> | <typecast-statement> | <print> | <input> | <conditional> | <switch> | <loop> | <function-call> | <return> | <break> | <expression> | <comment>
    @tracks_source_span
    def parse_statement(self) -> Optional[Any]:
        #<break>  i.e GTFO is only allowed in statements is handled by the parse_break func
        token = self.peek()
        if not token:
            return None

        #variable declarations block 
        if token[0] == "WAZZUP" or token[1] == "WAZZUP":
            return self.parse_variable_section()
        #standalone variable declaration
        if token[0] == "I_HAS_A":
            return self.parse_declaration()
        #identifiers
        if self.is_identifier_token():
            offset = 2 if token[0] in ("R", "A") else 1
            next_token = self.peek(offset)
            if next_token and next_token[0] == "R":
                return self.parse_assignment()
            if next_token and next_token[0] == "IS_NOW_A":
                return self.parse_typecast_statement()
            #if it's just a bare variable on its own line, consume it and return the var ref so it updates the register.
            name = self.consume_identifier()
            return VarRef(name=name)

        #i/o
        if token[0] == "VISIBLE":
            return self.parse_print()
        if token[0] == "GIMMEH":
            return self.parse_input()
        #control
        if token[0] == "O_RLY?":
            return self.parse_conditional()
        if token[0] == "WTF?":
            return self.parse_switch()
        if token[0] == "IM_IN_YR":
            return self.parse_loop()
        #function declarations
        if token[0] == "I_IZ":
            return self.parse_function_call()
        if token[0] == "FOUND_YR":
            return self.parse_return()
        if token[0] == "GTFO":
            return self.parse_break()
        #comments
        if token[0] in ("BTW", "OBTW") or token[1] in ("BTW", "OBTW"):
            return self.parse_comment()
        #expression statements evaluated for side effects
        if token[0] in EXPRESSION_STARTERS:
            return self.parse_expression()
        raise SyntaxError(f"Line {token[2]}: Unexpected token '{token[1]}' ({token[0]})")
    
    #<variable-section> ::= WAZZUP NEWLINE <declaration-list> BUHBYE
    @tracks_source_span
    def parse_variable_section(self) -> VariableSection:
        self.consume("WAZZUP")
        self.skip_newlines()
        declarations = self.parse_declaration_list()
        self.consume("BUHBYE")
        return VariableSection(declarations=declarations)
    
    #<declaration-list> ::= <declaration> NEWLINE <declaration-list> | <declaration> NEWLINE | empty
    def parse_declaration_list(self) -> List[Declaration]:
        declarations = []
        self.skip_newlines()
        while not self.is_at_end():
            token = self.peek()
            if not token or token[0] == "BUHBYE" or token[1] == "BUHBYE":
                break
            # Always consume a declaration or raise an error. Skipping only
            # newlines would loop forever on an unexpected token here.
            declarations.append(self.parse_declaration())
            self.skip_newlines()
        return declarations
    #<declaration> ::= I_HAS_A IDENTIFIER | I_HAS_A IDENTIFIER ITZ <value>
    @tracks_source_span
    def parse_declaration(self) -> Declaration:
        self.consume("I_HAS_A")
        name = self.consume_identifier()
        val = None
        if self.match("ITZ"):
            val = self.parse_value()
        return Declaration(name=name, value=val)
    #<assignment> ::= IDENTIFIER R <value>
    @tracks_source_span
    def parse_assignment(self) -> Assignment:
        name = self.consume_identifier()
        self.consume("R")
        val = self.parse_value()
        return Assignment(name=name, value=val)
    #<typecast-statement> ::= IDENTIFIER IS_NOW_A TYPE
    @tracks_source_span
    def parse_typecast_statement(self) -> TypecastStmt:
        name = self.consume_identifier()
        self.consume("IS_NOW_A")
        type_token = self.consume("TYPE")
        return TypecastStmt(name=name, cast_type=type_token[1])
    #<print> ::= VISIBLE <print-list> [!]
    @tracks_source_span
    def parse_print(self) -> PrintStmt:
        self.consume("VISIBLE")
        values = self.parse_print_list()
    #allow either an ! or + to suppress the newline
        suppress_newline = bool(self.match("EXCLAMATION", "PLUS"))
        return PrintStmt(values=values, suppress_newline=suppress_newline)
    #<print-list> ::= <value> | <value> <print-list>
    def parse_print_list(self) -> List[Any]:
        values = [self.parse_value()]
        while True:
            #get + separator if it exists
            self.match("PLUS")
            #if there's another value parse it, else we're done
            if self.can_start_value():
                values.append(self.parse_value())
            else:
                break
        return values
    #<input> ::= GIMMEH IDENTIFIER
    @tracks_source_span
    def parse_input(self) -> InputStmt:
        self.consume("GIMMEH")
        name = self.consume_identifier()
        return InputStmt(name=name)
    #parses an O RLY? conditional block including YA RLY, MEBBE, and NO WAI.
    @tracks_source_span
    def parse_conditional(self, condition: Optional[Any] = None) -> Conditional:
        self.consume("O_RLY?")
        self.skip_newlines()
        self.consume("YA_RLY")
        self.skip_newlines()
        body = self.parse_statement_list()

        elseifs = self.parse_else_if_list()
        else_body = self.parse_else_clause()
        self.consume("OIC")

        return Conditional(
            condition=condition,
            body=body,
            elseifs=elseifs,
            else_body=else_body
        )
    #else-if-list> ::= MEBBE <value> NEWLINE <statement-list> <else-if-list> | empty
    def parse_else_if_list(self) -> List[dict]:
        elseifs = []
        while self.match("MEBBE"):
            cond_val = self.parse_value()
            self.skip_newlines()
            body = self.parse_statement_list()
            elseifs.append({"condition": cond_val, "body": body})
        return elseifs
    #<else-clause> ::= NO_WAI NEWLINE <statement-list> | empty
    def parse_else_clause(self) -> List[Any]:
        if self.match("NO_WAI"):
            self.skip_newlines()
            return self.parse_statement_list()
        return []
    #parses a WTF? switch-case block
    @tracks_source_span
    def parse_switch(self) -> Switch:
        self.consume("WTF?")
        self.skip_newlines()
        self.switch_depth += 1
        try:
            cases = self.parse_case_list()
            default_clause = self.parse_default_clause()
        finally:
            self.switch_depth -= 1
        self.consume("OIC")
        return Switch(cases=cases, default=default_clause)
    #<case-list> ::= OMG <literal> NEWLINE <statement-list> <case-list> | empty
    def parse_case_list(self) -> List[dict]:
        cases = []
        while self.match("OMG"):
            lit = self.parse_literal()
            self.skip_newlines()
            body = self.parse_statement_list()
            cases.append({"value": lit, "body": body})
        return cases
    #default-clause> ::= OMGWTF NEWLINE <statement-list> | empty>
    def parse_default_clause(self) -> List[Any]:
        if self.match("OMGWTF"):
            self.skip_newlines()
            return self.parse_statement_list()
        return []
    #Parses an IM IN YR loop.
    @tracks_source_span
    def parse_loop(self) -> Loop:
        self.consume("IM_IN_YR")
        label = self.consume_identifier()

        #parse loop increment/decrement operation
        op = None
        if self.check("UPPIN", "NERFIN"):
            op_token = self.advance()
            self.consume("YR")
            var_name = self.consume_identifier()
            op = {"operation": op_token[0], "var": var_name}
        #then the termination condition
        cond = None
        if self.check("TIL", "WILE"):
            cond_type_token = self.advance()
            cond_val = self.parse_value()
            cond = {"type": cond_type_token[0], "value": cond_val}
        self.skip_newlines()
        self.loop_depth += 1
        try:
            body = self.parse_statement_list()
        finally:
            self.loop_depth -= 1
        self.consume("IM_OUTTA_YR")
        end_label = self.consume_identifier()
        if end_label != label:
            raise SyntaxError(
                f"Loop label mismatch: started with '{label}', ended with '{end_label}'"
            )

        return Loop(label=label, op=op, condition=cond, body=body)
    #Parses a HOW IZ I function declaration, tracking function scope depth.
    @tracks_source_span
    def parse_function_definition(self) -> FuncDef:
        self.consume("HOW_IZ_I")
        name = self.consume_identifier()
        params = self.parse_parameter_definition()
        self.skip_newlines()
        self.func_depth += 1
        try:
            body = self.parse_statement_list()
        finally:
            self.func_depth -= 1
        self.consume("IF_U_SAY_SO")
        return FuncDef(name=name, params=params, body=body)
    #<parameter-definition> ::= YR IDENTIFIER | YR IDENTIFIER AN <parameter-definition> | empty
    def parse_parameter_definition(self) -> List[str]:
        params = []
        if self.match("YR"):
            p = self.consume_identifier()
            params.append(p)
            while self.match("AN"):
                self.consume("YR")
                p = self.consume_identifier()
                params.append(p)
        return params
    #<function-call> ::= I_IZ IDENTIFIER <argument-list> MKAY
    @tracks_source_span
    def parse_function_call(self) -> FuncCall:
        self.consume("I_IZ")
        name = self.consume_identifier()
        args = self.parse_argument_list()
        if self.check("MKAY"):
            self.advance()
        return FuncCall(name=name, args=args)
    #<argument-list> ::= YR <value> | YR <value> AN <argument-list> | empty
    def parse_argument_list(self) -> List[Any]:
        args = []
        if self.match("YR"):
            args.append(self.parse_value())
            while self.match("AN"):
                self.consume("YR")
                args.append(self.parse_value())
        return args
    #parses a FOUND YR return statement
    @tracks_source_span
    def parse_return(self) -> Return:
        token = self.consume("FOUND_YR")
        if self.func_depth <= 0:
            line = token[2] if token else "EOF"
            raise SyntaxError(f"Line {line}: 'FOUND YR' is only allowed inside a function body.")
        val = self.parse_value()
        return Return(value=val)
    #parses a GTFO break statement
    @tracks_source_span
    def parse_break(self) -> Break:
        token = self.consume("GTFO")
        if self.loop_depth <= 0 and self.switch_depth <= 0 and self.func_depth <= 0:
            line = token[2] if token else "EOF"
            raise SyntaxError(f"Line {line}: 'GTFO' is not allowed outside loops, switch cases, or functions.")
        return Break()
    #<comment> ::= BTW <comment-text> | OBTW <comment-text> TLDR
    @tracks_source_span
    def parse_comment(self) -> Comment:
        if self.match("BTW"):
            text = ""
            if not self.check("NEWLINE") and not self.is_at_end():
                text = self.advance()[1]
            return Comment(text=text)
        if self.match("OBTW"):
            parts = []
            while not self.is_at_end() and not self.check("TLDR"):
                parts.append(self.advance()[1])
            self.consume("TLDR")
            return Comment(text=" ".join(parts))
        raise SyntaxError("Expected BTW or OBTW")

    #<value> ::= IDENTIFIER | <literal> | <expression> | <function-call>
    @tracks_source_span
    def parse_value(self) -> Any:
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input while expecting value.")

        if token[0] in LITERAL_TYPES:
            return self.parse_literal()

        if token[0] == "I_IZ":
            return self.parse_function_call()

        if token[0] in EXPRESSION_STARTERS:
            return self.parse_expression()

        if self.is_identifier_token():
            name = self.consume_identifier()
            return VarRef(name=name)
        raise SyntaxError(f"Line {token[2]}: Expected value, but found '{token[1]}' ({token[0]})")
    #<literal> ::= NUMBR | NUMBAR | YARN | TROOF | TYPE | NOOB
    @tracks_source_span
    def parse_literal(self) -> Literal:
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input while expecting literal.")

        if token[0] == "NUMBR":
            self.advance()
            return Literal(kind="NUMBR", value=int(token[1]))
        if token[0] == "NUMBAR":
            self.advance()
            return Literal(kind="NUMBAR", value=float(token[1]))
        if token[0] == "YARN":
            self.advance()
            text = token[1]
            #strip surrounding quotation marks from literals
            if len(text) >= 2 and text.startswith('"') and text.endswith('"'):
                text = text[1:-1]
            return Literal(kind="YARN", value=text)
        if token[0] == "TROOF":
            self.advance()
            return Literal(kind="TROOF", value=(token[1] == "WIN"))
        if token[0] == "TYPE":
            self.advance()
            return Literal(kind="TYPE", value=token[1])
        if token[0] == "NOOB":
            self.advance()
            return Literal(kind="NOOB", value="NOOB")

        raise SyntaxError(f"Line {token[2]}: Expected literal, found '{token[1]}' ({token[0]})")
    #<expression> ::= <arithmetic-expression> | <boolean-expression> | <comparison-expression> | ...
    @tracks_source_span
    def parse_expression(self) -> Any:
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input while expecting expression.")
        if token[0] in ARITHMETIC_OPERATORS:
            return self.parse_arithmetic_expression()
        if token[0] in BOOLEAN_OPERATORS or token[0] in INFINITE_OPERATORS or token[0] == "NOT":
            return self.parse_boolean_expression()
        if token[0] in COMPARISON_OPERATORS:
            return self.parse_comparison_expression()
        if token[0] == "SMOOSH":
            return self.parse_concatenation()
        if token[0] == "MAEK":
            return self.parse_typecast_expression()
        raise SyntaxError(f"Line {token[2]}: Expected expression, found '{token[1]}' ({token[0]})")
    #<arithmetic-expression> ::= <arithmetic-operator> <value> AN <value>
    @tracks_source_span
    def parse_arithmetic_expression(self) -> ArithExpr:
        op_token = self.advance()
        left = self.parse_value()
        self.consume("AN")
        right = self.parse_value()
        return ArithExpr(op=op_token[0], left=left, right=right)
    #<boolean-expression> ::= <binary-boolean> | <unary-boolean> | <infinite-boolean>
    @tracks_source_span
    def parse_boolean_expression(self) -> Any:
        token = self.peek()
        if not token:
            raise SyntaxError("Unexpected end of input while expecting boolean expression.")

        if token[0] in BOOLEAN_OPERATORS:
            return self.parse_binary_boolean()
        if token[0] == "NOT":
            return self.parse_unary_boolean()
        if token[0] in INFINITE_OPERATORS:
            return self.parse_infinite_boolean()

        raise SyntaxError(f"Line {token[2]}: Invalid boolean operator '{token[1]}'")
    #<binary-boolean> ::= <boolean-operator> <value> AN <value>
    @tracks_source_span
    def parse_binary_boolean(self) -> BoolExpr:
        op_token = self.advance()
        left = self.parse_value()
        self.consume("AN")
        right = self.parse_value()
        return BoolExpr(op=op_token[0], left=left, right=right)
    #<unary-boolean> ::= NOT <value>
    @tracks_source_span
    def parse_unary_boolean(self) -> NotExpr:
        self.consume("NOT")
        val = self.parse_value()
        return NotExpr(value=val)
    #<infinite-boolean> ::= <infinite-operator> <value-list> MKAY
    @tracks_source_span
    def parse_infinite_boolean(self) -> InfiniteBool:
        
        op_token = self.advance()
        values = self.parse_value_list()
        if self.check("MKAY"):
            self.advance()
        return InfiniteBool(op=op_token[0], values=values)
    #<comparison-expression> ::= <comparison-operator> <value> AN <value>
    #handle the numbr/numbar restriction during interpretation or potential syntax analysis
    @tracks_source_span
    def parse_comparison_expression(self) -> CompareExpr:
        op_token = self.advance()
        left = self.parse_value()
        self.consume("AN")
        right = self.parse_value()
        return CompareExpr(op=op_token[0], left=left, right=right)
    #<concatenation> ::= SMOOSH <value-list> MKAY
    @tracks_source_span
    def parse_concatenation(self) -> Concatenation:
        self.consume("SMOOSH")
        values = self.parse_value_list()
        if self.check("MKAY"):
            self.advance()
        return Concatenation(values=values)
    #<typecast-expression> ::= MAEK <value> A TYPE | MAEK <value> TYPE
    @tracks_source_span
    def parse_typecast_expression(self) -> TypecastExpr:
        self.consume("MAEK")
        val = self.parse_value()
        if self.check("A"):
            self.advance()
        type_token = self.consume("TYPE")
        return TypecastExpr(value=val, cast_type=type_token[1])
    #        <value-list> ::= <value> AN <value> | <value> AN <value-list>

    def parse_value_list(self) -> List[Any]:
        values = [self.parse_value()]
        while self.match("AN"):
            values.append(self.parse_value())
        return values

def parse(tokens: list) -> Program:
    return Parser(tokens).parse()

if __name__ == "__main__":
    source_file = "source.txt"
    source_code = read_input(source_file)
    tokens = tokenize(source_code)
    parser = Parser(tokens)
    ast = parser.parse()
    pprint(ast)
