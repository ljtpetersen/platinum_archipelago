# data_gen_rules.py
#
# Copyright (C) 2025-2026 James Petersen <m@jamespetersen.ca>
# Licensed under MIT. See LICENSE

from collections.abc import Callable, MutableMapping, MutableSequence, Sequence, Set
from dataclasses import dataclass
from enum import StrEnum
from typing import Tuple, Union
from pyparsing import Forward, MatchFirst, ParseResults, Regex, alphas, alphanums, Group, delimited_list, infix_notation, opAssoc, Optional, Suppress, Word

integer = Regex(r"[+-]?(0[xX][0-9a-fA-F]+|0[bB][01]+|0[oO][0-7]+|[0-9]+)")

def is_integer(val: str) -> bool:
    return integer.matches(val)

class RuleOp(StrEnum):
    AND = "&"
    OR = "|"

    def get_has(self):
        match self:
            case RuleOp.AND:
                return "all"
            case RuleOp.OR:
                return "any"

class Comparison(StrEnum):
    EQ = "=="
    NE = "!="
    LE = "<="
    GE = ">="
    LT = "<"
    GT = ">"

    def inverted(self) -> "Comparison":
        match self:
            case Comparison.EQ:
                return Comparison.NE
            case Comparison.NE:
                return Comparison.EQ
            case Comparison.LE:
                return Comparison.GT
            case Comparison.GE:
                return Comparison.LT
            case Comparison.LT:
                return Comparison.GE
            case Comparison.GT:
                return Comparison.LE

def triage_cond_cmp_side(val: str) -> str:
    if val.startswith("option_"):
        return "OPT_VAL"
    elif is_integer(val):
        return "INT"
    else:
        return "OPT_NAME"

def get_other_side(name: str, other_side: str, other_side_triage: str) -> str:
    if other_side_triage == "OPT_VAL":
        return f"self.opts.{name}.{other_side}"
    elif other_side_triage == "INT":
        return other_side
    else:
        raise Exception("this should be unreachable")

def get_name_side(name: str) -> str:
    return f"self.opts.{name}.value"

@dataclass(frozen=True)
class ConditionNode:
    left: str
    op: Comparison = Comparison.NE
    right: str = "0"

    def __str__(self) -> str:
        left_triage = triage_cond_cmp_side(self.left)
        right_triage = triage_cond_cmp_side(self.right)
        if left_triage == right_triage:
            raise ValueError(f"condition comparison cannot have two values of the same type on both sides. comparison: {self.left} {self.op} {self.right}")
        if left_triage == "OPT_NAME":
            left = get_name_side(self.left)
            right = get_other_side(self.left, self.right, right_triage)
        elif right_triage == "OPT_NAME":
            right = get_name_side(self.right)
            left = get_other_side(self.right, self.left, left_triage)
        else:
            raise ValueError(f"condition comparison must have an option name (identifier that does not start with option_). comparison: {self.left} {self.op} {self.right}")
        return f"{left} {self.op} {right}"

@dataclass(frozen=True)
class Condition:
    conds: Sequence[Union[ConditionNode, "Condition"]]
    op: RuleOp = RuleOp.AND
    invert: bool = False

    @staticmethod
    def none_of(conds) -> Union["Condition", None]:
        if conds:
            return Condition(list(conds), RuleOp.OR, True)
        else:
            return None

    @staticmethod
    def none_of_and(prev_conds, cond) -> "Condition":
        if prev_conds:
            return Condition([Condition(list(prev_conds), RuleOp.OR, True), cond])
        else:
            return cond

    def __str__(self) -> str:
        def inner_str(cond: ConditionNode | Condition) -> str:
            if isinstance(cond, Condition) and cond.op != self.op and len(cond.conds) > 1 and not cond.invert:
                return f"({cond})"
            return str(cond)
        centre = f" {self.op.name.lower()} ".join(map(inner_str, self.conds))
        if self.invert:
            if len(self.conds) > 1:
                return f"not ({centre})"
            else:
                return f"not {centre}"
        else:
            return centre

class ItemConditions:
    base: MutableMapping[str, MutableSequence[Condition] | None]

    def __init__(self):
        self.base = {}

    def add(self, item: str, cond: Condition | None):
        if cond is None:
            self.base[item] = None
        elif item in self.base:
            conds = self.base[item]
            if conds is not None:
                conds.append(cond)
        else:
            self.base[item] = [cond]

    def add_all(self, items):
        for item in items:
            self.base[item] = None

    def restrict(self, items):
        for k in self.base.keys() - items:
            del self.base[k]

    def get_cond_str(self, item: str | Sequence[str]) -> str | None:
        if not isinstance(item, str) or item not in self.base:
            return None
        cond = self.base[item] # type: ignore
        if cond is not None:
            return str(Condition(cond, RuleOp.OR))
        else:
            return "True"

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

    def add_dependent_items(self, conds: ItemConditions, cond: Condition | None = None):
        for item in self.names:
            conds.add(item, cond)

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

    def add_dependent_items(self, conds: ItemConditions, cond: Condition | None = None):
        for ele in self.items:
            if isinstance(ele, str):
                conds.add(ele, cond)
            elif isinstance(ele, Rule) or isinstance(ele, CountItem):
                ele.add_dependent_items(conds, cond)

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
                exprs = [f"state.has_{self.op.get_has()}([{', '.join(map(item_name_map, str_items))}], self.player)"]
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

@dataclass(frozen=True)
class RuleWithOpts:
    rules: Sequence[Tuple[Condition | None, Rule]]

    def add_dependent_items(self, conds: ItemConditions):
        accum = []
        for cond, rule in reversed(self.rules):
            if cond is None:
                rule.add_dependent_items(conds, Condition.none_of(accum))
            else:
                rule.add_dependent_items(conds, Condition.none_of_and(accum, cond))
                accum.append(cond)

    def to_string(self, item_set: Set[str], item_name_map: Callable[[str], str]):
        accum = ""
        for cond, rule in reversed(self.rules):
            if cond is None:
                return f"{accum}({rule.to_string(item_set, item_name_map)})"
            accum += f"({rule.to_string(item_set, item_name_map)}) if {cond} else "
        return f"{accum}always_true"

LPAR, RPAR, LS, RS, LC, RC, COLON, AST = map(Suppress, "()[]{}:*")
IF = Suppress("if")
ELSE = Suppress("else")
NAME = Word(alphas + "_", alphanums + "_")
name_str = Word(alphas + "_", alphanums + "_").set_parse_action(lambda s : f"\"{s[0]}\"")
func_arg = Forward()
arg_dict = LC + Optional(delimited_list(Group(name_str + COLON + func_arg))) + RC
arg_dict.set_parse_action(lambda val : f"{{{', '.join(map(lambda arr : f'{arr[0]}: {arr[1]}', val))}}}")
arg_seq = LS + Optional(delimited_list(func_arg)) + RS
arg_seq.set_parse_action(lambda val : f"[{', '.join(val)}]")
arg_set = LC + Optional(delimited_list(func_arg)) + RC
arg_set.set_parse_action(lambda val : f"{{{', '.join(val)}}}")
arg_opt = (Suppress("opt:") + NAME).set_parse_action(lambda s : f"self.opts.{s[0]}.value")
func_arg <<= arg_opt | name_str | integer | arg_seq | arg_dict | arg_set
func_args = Optional(delimited_list(func_arg)).set_parse_action(", ".join)
func_call = (NAME + LPAR + func_args + RPAR).set_parse_action(lambda v : FuncCall(*v))
rule_expr = Forward()

comparisons = MatchFirst(Comparison).set_parse_action(lambda s : s[0]) # type: ignore
opt_str = Word(alphas + "_", alphanums + "_").set_parse_action(lambda s : ConditionNode(str(s[0])))
opt_cmp_ele = (NAME | integer).set_parse_action(lambda s : str(s[0]))
opt_cmp = opt_cmp_ele + comparisons + opt_cmp_ele
opt_cmp.set_parse_action(lambda v : ConditionNode(*v)) # type: ignore
opt_operand = opt_cmp | opt_str

def make_opt_parse_action(op: RuleOp) -> Callable[[ParseResults], Condition]:
    def parse_action(res: ParseResults) -> Condition:
        [res] = res
        vals = []
        for v in res[::2]:
            if isinstance(v, Condition) and v.op == op and not v.invert:
                vals.extend(v.conds)
            else:
                vals.append(v)
        return Condition(vals, op)
    return parse_action

def opt_not_parse_action(res: ParseResults) -> Condition | ConditionNode:
    [[res]] = res
    if isinstance(res, Condition):
        return Condition(res.conds, res.op, not res.invert)
    else:
        return ConditionNode(res.left, res.op.inverted(), res.right) # type: ignore

opt = infix_notation(opt_operand, [
    (Suppress("!"), 1, opAssoc.RIGHT, opt_not_parse_action),
    ("&", 2, opAssoc.LEFT, make_opt_parse_action(RuleOp.AND)),
    ("|", 2, opAssoc.LEFT, make_opt_parse_action(RuleOp.OR)),
])

def opt_parse_action(res: ParseResults) -> Condition:
    [res] = res
    if not isinstance(res, Condition):
        return Condition(frozenset([res]), RuleOp.AND) # type: ignore
    else:
        return res

opt.set_parse_action(opt_parse_action)

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
def rule_parse_action(res: ParseResults) -> Rule:
    [res] = res
    if not isinstance(res, Rule):
        return Rule(frozenset([res])) # type: ignore
    else:
        return res
rule_expr.set_parse_action(rule_parse_action)

rule_with_opt_expr = Forward()
rule_with_opt_expr <<= rule_expr + Optional(IF + opt + Optional(ELSE + rule_with_opt_expr))

def rule_with_opt_parse_action(res: ParseResults) -> RuleWithOpts:
    current = res
    l = len(current)
    seq: Sequence[Tuple[Condition, Rule]] = []
    if l >= 2:
        cond = current[1]
        if l == 3:
            seq = current[2].rules # type: ignore
    else:
        cond = None
    seq.append((cond, current[0])) # type: ignore
    return RuleWithOpts(seq) # type: ignore
rule_with_opt_expr.set_parse_action(rule_with_opt_parse_action)

def parse_rule(val: str) -> RuleWithOpts:
    return rule_with_opt_expr.parse_string(val, parse_all=True)[0] # type: ignore

def main():
    conds = ["unown == option_vanilla", "!(key_items > 2 & nonzero) | bruh"]
    for cond in conds:
        print(f"{cond} converts to {opt.parse_string(cond, parse_all=True)[0]}")
    rule_with_opt_expr.parse_string("unowns if unown == option_vanilla else up_unown * 26 if unown == option_items else true", parse_all=True).pprint()

if __name__ == "__main__":
    main()
