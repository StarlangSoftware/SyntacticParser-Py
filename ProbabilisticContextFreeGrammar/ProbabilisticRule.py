from __future__ import annotations

from ParseTree.Symbol import Symbol

from ContextFreeGrammar.Rule import Rule
from ContextFreeGrammar.RuleType import RuleType


class ProbabilisticRule(Rule):

    __probability: float
    __count: int

    def constructor6(self, rule: str):
        prob = rule[rule.find("[") + 1:rule.find("]")].strip()
        left = rule[0:rule.find("->")].strip()
        right = rule[rule.find("->") + 2:rule.find("[")].strip()
        self.left_hand_side = Symbol(left)
        rightSide = right.split(" ")
        self.right_hand_side = []
        for i in range(0, len(rightSide)):
            self.right_hand_side.append(Symbol(rightSide[i]))
        self.__probability = float(prob)
        self.__count = 0

    def __init__(self,
                 param1: Symbol | str = None,
                 param2: list[Symbol] = None,
                 param3: RuleType = None,
                 param4: float = None):
        super().__init__()
        self.__count = 0
        self.__probability = 0.0
        if isinstance(param1, Symbol) and param3 is None:
            super().__init__(param1, param2)
        elif isinstance(param1, Symbol) and param3 is not None:
            super().__init__(param1, param2, param3)
            self.__probability = param4
        elif isinstance(param1, str):
            self.constructor6(param1)

    def getProbability(self) -> float:
        return self.__probability

    def increment(self):
        self.__count = self.__count + 1

    def normalizeProbability(self, total: int):
        self.__probability = self.__count / total

    def getCount(self) -> int:
        return self.__count

    def __str__(self) -> str:
        return super().__str__() + "[" + str(self.__probability) + "]"
