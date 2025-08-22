
from collections.abc import Callable, Set
from dataclasses import dataclass
from enum import StrEnum
from typing import Union
from pyparsing import Forward, ParseResults, Regex, alphas, alphanums, Group, delimited_list, infix_notation, opAssoc, Optional, Suppress, Word

class RuleOp(StrEnum):
    AND = "&"
    OR = "|"

    def get_has(self):
        match self:
            case RuleOp.AND:
                return "all"
            case RuleOp.OR:
                return "any"

@dataclass(frozen=True)
class FuncCall:
    name: str
    args: str

    def __str__(self) -> str:
        return f"self.common_rules[\"{self.name}\"]({self.args})"

@dataclass(frozen=True)
class CountItem:
    names: Set[str]
    count: str
    op: RuleOp = RuleOp.AND

    def to_string(
        self,
        item_name_map: Callable[[str], str]
    ) -> str:
        if len(self.names) > 1:
            centre = ", ".join(map(self.names, item_name_map)) # type: ignore
            match self.op:
                case RuleOp.AND:
                    ext = "all_counts"
                case RuleOp.OR:
                    ext = "any_count"
            return f"state.has_{ext}({centre}, self.player, {self.count})"
        else:
            for item in self.names:
                break
            return f"state.has({item_name_map(item)}, self.player, {self.count})" # type: ignore

@dataclass(frozen=True)
class Rule:
    items: Set[Union["Rule", str, FuncCall]]
    op: RuleOp = RuleOp.AND

    def add_dependent_items(self, base = set()):
        for ele in self.items:
            if isinstance(ele, str):
                base.add(ele)
            elif isinstance(ele, Rule):
                ele.add_dependent_items(base)
            elif isinstance(ele, CountItem):
                base |= ele.names

    def to_string(
        self,
        item_set: Set[str],
        item_name_map: Callable[[str], str],
        parent_op: RuleOp | None = None,
    ) -> str:
        if parent_op is None and len(self.items) == 1:
            for item in self.items:
                break
            if isinstance(item, FuncCall): # type: ignore
                return str(item)
            elif item not in item_set and isinstance(item, str): # type: ignore
                return f"self.common_rules[\"{item}\"]" # type: ignore
        str_items: Set[str] = self.items & item_set # type: ignore
        match len(str_items):
            case 0:
                exprs = []
            case 1:
                for item in str_items:
                    break
                exprs = [f"state.has({item_name_map(item)}, self.player)"] # type: ignore
            case _:
                exprs = [f"state.has_{self.op.get_has()}([{", ".join(map(item_name_map, str_items))}], self.player)"]
        for val in self.items - item_set:
            if isinstance(val, str):
                exprs.append(f"self.common_rules[\"{val}\"](state)")
            elif isinstance(val, Rule):
                exprs.append(val.to_string(item_set, item_name_map, self.op))
            elif isinstance(val, FuncCall):
                exprs.append(f"{val}(state)")
            elif isinstance(val, CountItem):
                exprs.append(val.to_string(item_name_map))
        centre = f" {self.op.name.lower()} ".join(exprs)
        if parent_op is None:
            return "lambda state : " + centre
        elif parent_op is RuleOp.AND and self.op is RuleOp.OR and len(exprs) > 1:
            return f"({centre})"
        else:
            return centre

LPAR, RPAR, LS, RS, LC, RC, COLON, AST = map(Suppress, "()[]{}:*")
NAME = Word(alphas + "_", alphanums + "_")
name_str = Word(alphas + "_", alphanums + "_").set_parse_action(lambda s : f"\"{s[0]}\"")
integer = Regex(r"[+-]?(0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+|[0-9]+)")
func_arg = Forward()
arg_dict = LC + Optional(delimited_list(Group(name_str + COLON + func_arg))) + RC
arg_dict.set_parse_action(lambda val : f"{{{", ".join(map(lambda arr : f"{arr[0]}: {arr[1]}", val))}}}")
arg_seq = LS + Optional(delimited_list(func_arg)) + RS
arg_seq.set_parse_action(lambda val : f"[{", ".join(val)}]")
arg_set = LC + Optional(delimited_list(func_arg)) + RC
arg_set.set_parse_action(lambda val : f"{{{", ".join(val)}}}")
func_arg <<= name_str | integer | arg_seq | arg_dict | arg_set
func_args = Optional(delimited_list(func_arg)).set_parse_action(getattr(", ", "join"))
func_call = (NAME + LPAR + func_args + RPAR).set_parse_action(lambda v : FuncCall(*v))
rule_expr = Forward()

count_seq_and = LS + delimited_list(NAME, delim='&', min=1) + RS
count_seq_and.set_parse_action(lambda val : (frozenset(val), RuleOp.AND))
count_seq_or = LS + delimited_list(NAME, delim='|', min=1) + RS
count_seq_or.set_parse_action(lambda val : (frozenset(val), RuleOp.OR))
count_name = Word(alphas + "_", alphanums + "_").set_parse_action(lambda val : (frozenset([val[0]]), RuleOp.AND))
count_v = (count_name | count_seq_and | count_seq_or) + AST + integer
count_v.set_parse_action(lambda v : CountItem(v[0][0], v[1], v[0][1])) # type: ignore

operand = count_v | func_call | NAME

def make_rule_parse_action(op: RuleOp) -> Callable[[ParseResults], Rule]:
    def parse_action(res: ParseResults) -> Rule:
        [res] = res
        vals = set()
        for v in res[::2]:
            if isinstance(v, Rule) and v.op == op:
                vals |= v.items
            else:
                vals.add(v)
        return Rule(frozenset(vals), op)
    return parse_action
rule_expr <<= infix_notation(operand, [
    ("&", 2, opAssoc.LEFT, make_rule_parse_action(RuleOp.AND)),
    ("|", 2, opAssoc.LEFT, make_rule_parse_action(RuleOp.OR)),
])

def parse_rule(val: str) -> Rule:
    ret = rule_expr.parse_string(val, parseAll=True)[0]
    if not isinstance(ret, Rule):
        return Rule(frozenset([ret])) # type: ignore
    else:
        return ret
