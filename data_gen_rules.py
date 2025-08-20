
from collections.abc import Callable, Sequence, Set
from dataclasses import dataclass
from enum import StrEnum
from typing import Union
from pyparsing import Forward, alphas, alphanums, Group, delimitedList, infixNotation, opAssoc, Optional, Suppress, Word

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
class Rule:
    items: Set[Union["Rule", str]]
    op: RuleOp = RuleOp.AND

    def add_dependent_items(self, base = set()):
        for ele in self.items:
            if isinstance(ele, str):
                base.add(ele)
            else:
                ele.add_dependent_items(base)

    def to_string(
        self,
        item_set: Set[str],
        item_name_map: Callable[[str], str],
        parent_op: RuleOp | None = None,
    ) -> str:
        if parent_op is None and len(self.items) == 1 and not self.items <= item_set:
            for item in self.items:
                break
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
                exprs = [f"state.has_{self.op.get_has()}({", ".join(map(item_name_map, str_items))}, self.player)"]
        for val in self.items - item_set:
            if isinstance(val, str):
                exprs.append(f"self.common_rules[\"{val}\"]")
            else:
                exprs.append(val.to_string(item_set, item_name_map, self.op))
        centre = f" {self.op.name.lower()} ".join(exprs)
        if parent_op is None:
            return "lambda state : " + centre
        elif parent_op is RuleOp.AND and self.op is RuleOp.OR and len(exprs) > 1:
            return f"({centre})"
        else:
            return centre

LPAR, RPAR = map(Suppress, "()")
NAME = Word(alphas + "_", alphanums + "_")
rule_expr = Forward()
rule_expr <<= infixNotation(NAME, [("&", 2, opAssoc.LEFT), ("|", 2, opAssoc.RIGHT)]) + Optional(LPAR + Group(Optional(delimitedList(rule_expr))) + RPAR)

ExprParseRes = str | Sequence["ExprParseRes"]

def split_to_rule(split: ExprParseRes) -> Rule | str:
    while not isinstance(split, str) and len(split) == 1:
        [split] = split
    if isinstance(split, str):
        return split
    else:
        return Rule({split_to_rule(inner) for inner in split[0::2]}, op = RuleOp(split[1]))

def parse_rule(val: str) -> Rule:
    split_up: ExprParseRes = rule_expr.parse_string(val, parseAll=True) # type: ignore
    parsed = split_to_rule(split_up)
    if isinstance(parsed, str):
        return Rule({parsed})
    else:
        return parsed
