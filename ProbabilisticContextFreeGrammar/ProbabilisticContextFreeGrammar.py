from __future__ import annotations

from functools import cmp_to_key
from math import log

from DataStructure.CounterHashMap import CounterHashMap
from ParseTree.ParseNode import ParseNode
from ParseTree.ParseTree import ParseTree
from ParseTree.Symbol import Symbol
from ParseTree.TreeBank import TreeBank

from ContextFreeGrammar.ContextFreeGrammar import ContextFreeGrammar
from ContextFreeGrammar.RuleType import RuleType
from ProbabilisticContextFreeGrammar.ProbabilisticRule import ProbabilisticRule


class ProbabilisticContextFreeGrammar(ContextFreeGrammar):

    def constructor2(self,
                     rule_file_name: str,
                     dictionary_file_name: str,
                     min_count: int):
        self.rules = []
        self.rules_right_sorted = []
        self.dictionary = CounterHashMap()
        input_file = open(rule_file_name, "r", encoding="utf8")
        lines = input_file.readlines()
        for line in lines:
            new_rule = ProbabilisticRule(line)
            self.rules.append(new_rule)
            self.rules_right_sorted.append(new_rule)
        input_file.close()
        self.rules.sort(key=cmp_to_key(self.ruleComparator))
        self.rules_right_sorted.sort(key=cmp_to_key(self.ruleRightComparator))
        self.readDictionary(dictionary_file_name)
        self.updateTypes()
        self.min_count = min_count

    def constructor3(self, tree_bank: TreeBank, min_count: int):
        self.rules = []
        self.rules_right_sorted = []
        self.dictionary = CounterHashMap()
        self.constructDictionary(tree_bank)
        for i in range(0, tree_bank.size()):
            parse_tree = tree_bank.get(i)
            self.updateTree(parse_tree, min_count)
            self.addRules(parse_tree.getRoot())
        variables = self.getLeftSide()
        for variable in variables:
            candidates = self.getRulesWithRightSideX(variable)
            total = 0
            for candidate in candidates:
                if isinstance(candidate, ProbabilisticRule):
                    total += candidate.getCount()
            for candidate in candidates:
                if isinstance(candidate, ProbabilisticRule):
                    candidate.normalizeProbability(total)
        self.updateTypes()
        self.min_count = min_count

    def __init__(self,
                 param1: str | TreeBank = None,
                 param2: str | int = None,
                 param3: int = None):
        if param1 is None:
            super().__init__()
        elif isinstance(param1, str) and isinstance(param2, str):
            super().__init__()
            self.constructor2(param1, param2, param3)
        elif isinstance(param1, TreeBank) and isinstance(param2, int):
            super().__init__()
            self.constructor3(param1, param2)

    @staticmethod
    def toRule(parse_node: ParseNode, trim: bool) -> ProbabilisticRule:
        right = []
        if trim:
            left = parse_node.getData().trimSymbol()
        else:
            left = parse_node.getData()
        for i in range(0, parse_node.numberOfChildren()):
            child_node = parse_node.getChild(i)
            if child_node.getData() is not None:
                if child_node.getData().isTerminal():
                    right.append(child_node.getData())
                else:
                    right.append(child_node.getData().trimSymbol())
            else:
                return None
        return ProbabilisticRule(left, right)

    def addRules(self, parse_node: ParseNode):
        new_rule = ProbabilisticContextFreeGrammar.toRule(parse_node, True)
        if new_rule is not None:
            existed_rule = self.searchRule(new_rule)
            if existed_rule is None:
                self.addRule(new_rule)
                new_rule.increment()
            else:
                if isinstance(existed_rule, ProbabilisticRule):
                    existed_rule.increment()
        for i in range(0, parse_node.numberOfChildren()):
            child_node = parse_node.getChild(i)
            if child_node.numberOfChildren() > 0:
                self.addRules(child_node)

    def probabilityOfParseNode(self, parse_node: ParseNode) -> float:
        _sum = 0.0
        if parse_node.numberOfChildren() > 0:
            rule = ProbabilisticContextFreeGrammar.toRule(parse_node, True)
            existed_rule = self.searchRule(rule)
            if isinstance(existed_rule, ProbabilisticRule):
                _sum = log(existed_rule.getProbability())
                if existed_rule.type != RuleType.TERMINAL:
                    for i in range(0, parse_node.numberOfChildren()):
                        child_node = parse_node.getChild(i)
                        _sum += self.probabilityOfParseNode(child_node)
        return _sum

    def probabilityOfParseTree(self, parse_tree: ParseTree) -> float:
        return self.probabilityOfParseNode(parse_tree.getRoot())

    def removeSingleNonTerminalFromRightHandSide(self):
        non_terminal_list = []
        remove_candidate = self.getSingleNonTerminalCandidateToRemove(non_terminal_list)
        while remove_candidate is not None:
            rule_list = self.getRulesWithRightSideX(remove_candidate)
            for rule in rule_list:
                candidate_list = self.getRulesWithLeftSideX(remove_candidate)
                for candidate in candidate_list:
                    clone = []
                    for symbol in candidate.right_hand_side:
                        clone.append(symbol)
                    if isinstance(rule, ProbabilisticRule) and isinstance(candidate, ProbabilisticRule):
                        self.addRule(ProbabilisticRule(rule.left_hand_side, clone, candidate.type, rule.getProbability() * candidate.getProbability()))
                self.removeRule(rule)
            non_terminal_list.append(remove_candidate)
            remove_candidate = self.getSingleNonTerminalCandidateToRemove(non_terminal_list)

    def updateMultipleNonTerminalFromRightHandSide(self):
        new_variable_count = 0
        update_candidate = self.getMultipleNonTerminalCandidateToUpdate()
        while update_candidate is not None:
            new_right_hand_side = []
            new_symbol = Symbol("X" + str(new_variable_count))
            new_right_hand_side.append(update_candidate.right_hand_side[0])
            new_right_hand_side.append(update_candidate.right_hand_side[1])
            self.updateAllMultipleNonTerminalWithNewRule(update_candidate.right_hand_side[0], update_candidate.right_hand_side[1], new_symbol)
            self.addRule(ProbabilisticRule(new_symbol, new_right_hand_side, RuleType.TWO_NON_TERMINAL, 1.0))
            update_candidate = self.getMultipleNonTerminalCandidateToUpdate()
            new_variable_count = new_variable_count + 1

    def convertToChomskyNormalForm(self):
        self.removeSingleNonTerminalFromRightHandSide()
        self.updateMultipleNonTerminalFromRightHandSide()
        self.rules.sort(key=cmp_to_key(self.ruleComparator))
        self.rules_right_sorted.sort(key=cmp_to_key(self.ruleRightComparator))
