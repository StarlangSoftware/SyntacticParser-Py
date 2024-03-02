from __future__ import annotations
from ParseTree.ParseNode import ParseNode

from ProbabilisticContextFreeGrammar.ProbabilisticParseNode import ProbabilisticParseNode


class PartialParseList:

    __partial_parses: list[ParseNode]

    def __init__(self):
        self.__partial_parses = []

    def addPartialParse(self, node: ParseNode):
        self.__partial_parses.append(node)

    def updatePartialParse(self, parse_node: ProbabilisticParseNode):
        found = False
        for i in range(0, len(self.__partial_parses)):
            partial_parse = self.__partial_parses[i]
            if partial_parse.getData().getName() == parse_node.getData().getName():
                if isinstance(partial_parse, ProbabilisticParseNode):
                    if partial_parse.getLogProbability() < parse_node.getLogProbability():
                        self.__partial_parses.pop(i)
                        self.__partial_parses.append(parse_node)
                found = True
                break
        if not found:
            self.__partial_parses.append(parse_node)

    def getPartialParse(self, index: int) -> ParseNode:
        return self.__partial_parses[index]

    def size(self) -> int:
        return len(self.__partial_parses)
