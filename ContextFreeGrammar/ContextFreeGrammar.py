from __future__ import annotations
import re
from functools import cmp_to_key

from Corpus.Sentence import Sentence
from DataStructure.CounterHashMap import CounterHashMap
from Dictionary.Word import Word
from ParseTree.NodeCollector import NodeCollector
from ParseTree.NodeCondition.IsLeaf import IsLeaf
from ParseTree.ParseNode import ParseNode
from ParseTree.ParseTree import ParseTree
from ParseTree.Symbol import Symbol
from ParseTree.TreeBank import TreeBank

from ContextFreeGrammar.Rule import Rule
from ContextFreeGrammar.RuleType import RuleType


class ContextFreeGrammar:
    dictionary: CounterHashMap
    rules: list[Rule]
    rules_right_sorted: list[Rule]
    min_count: int

    def constructor1(self):
        self.min_count = 1
        self.rules = []
        self.rules_right_sorted = []
        self.dictionary = CounterHashMap()

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
            new_rule = Rule(line)
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
        self.updateTypes()
        self.min_count = min_count

    def __init__(self,
                 param1: str | TreeBank = None,
                 param2: str | int = None,
                 param3: int = None):
        self.rules = []
        self.rules_right_sorted = []
        self.dictionary = CounterHashMap()
        if param1 is None:
            self.constructor1()
        elif isinstance(param1, str) and isinstance(param2, str):
            self.constructor2(param1, param2, param3)
        elif isinstance(param1, TreeBank) and isinstance(param2, int):
            self.constructor3(param1, param2)

    @staticmethod
    def ruleLeftComparator(ruleA: Rule, ruleB: Rule) -> int:
        if ruleA.left_hand_side.name < ruleB.left_hand_side.name:
            return -1
        elif ruleA.left_hand_side.name > ruleB.left_hand_side.name:
            return 1
        else:
            return 0

    @staticmethod
    def ruleRightComparator(ruleA: Rule, ruleB: Rule) -> int:
        i = 0
        while i < len(ruleA.right_hand_side) and i < len(ruleB.right_hand_side):
            if ruleA.right_hand_side[i] == ruleB.right_hand_side[i]:
                i = i + 1
            else:
                if ruleA.right_hand_side[i].name < ruleB.right_hand_side[i].name:
                    return -1
                elif ruleA.right_hand_side[i].name > ruleB.right_hand_side[i].name:
                    return 1
                else:
                    return 0
        if len(ruleA.right_hand_side) < len(ruleB.right_hand_side):
            return -1
        elif len(ruleA.right_hand_side) > len(ruleB.right_hand_side):
            return 1
        else:
            return 0

    @staticmethod
    def ruleComparator(ruleA: Rule, ruleB: Rule) -> int:
        if ruleA.left_hand_side == ruleB.left_hand_side:
            return ContextFreeGrammar.ruleRightComparator(ruleA, ruleB)
        else:
            return ContextFreeGrammar.ruleLeftComparator(ruleA, ruleB)

    def readDictionary(self, dictionary_file_name: str):
        input_file = open(dictionary_file_name, "r", encoding="utf8")
        lines = input_file.readlines()
        for line in lines:
            items = line.split(" ")
            self.dictionary.putNTimes(items[0], int(items[1]))
        input_file.close()

    def updateTypes(self):
        nonTerminals = set()
        for rule in self.rules:
            nonTerminals.add(rule.left_hand_side.getName())
        for rule in self.rules:
            if len(rule.right_hand_side) > 2:
                rule.type = RuleType.MULTIPLE_NON_TERMINAL
            elif len(rule.right_hand_side) == 2:
                rule.type = RuleType.TWO_NON_TERMINAL
            elif rule.right_hand_side[0].isTerminal() or \
                    Word.isPunctuationSymbol(rule.right_hand_side[0].getName()) or \
                    rule.right_hand_side[0].getName() not in nonTerminals:
                rule.type = RuleType.TERMINAL
            else:
                rule.type = RuleType.SINGLE_NON_TERMINAL

    def constructDictionary(self, tree_bank: TreeBank):
        for i in range(0, tree_bank.size()):
            parse_tree = tree_bank.get(i)
            node_collector = NodeCollector(parse_tree.getRoot(), IsLeaf())
            leaf_list = node_collector.collect()
            for parse_node in leaf_list:
                self.dictionary.put(parse_node.getData().getName())

    def updateTree(self, parse_tree: ParseTree, min_count: int):
        nodeCollector = NodeCollector(parse_tree.getRoot(), IsLeaf())
        leaf_list = nodeCollector.collect()
        pattern1 = re.compile("\\+?\\d+")
        pattern2 = re.compile("\\+?(\\d+)?\\.\\d*")
        for parse_node in leaf_list:
            data = parse_node.getData().getName()
            if pattern1.fullmatch(data) or (pattern2.fullmatch(data) and data != "."):
                parse_node.setData(Symbol("_num_"))
            elif self.dictionary.count(data) < min_count:
                parse_node.setData(Symbol("_rare_"))

    def removeExceptionalWordsFromSentence(self, sentence: Sentence):
        pattern1 = re.compile("\\+?\\d+")
        pattern2 = re.compile("\\+?(\\d+)?\\.\\d*")
        for i in range(0, sentence.wordCount()):
            word = sentence.getWord(i)
            if pattern1.fullmatch(word.getName()) or (pattern2.fullmatch(word.getName()) and word.getName() != "."):
                word.setName("_num_")
            elif self.dictionary.count(word.getName()) < self.min_count:
                word.setName("_rare_")

    def reinsertExceptionalWordsFromSentence(self, parse_tree: ParseTree, sentence: Sentence):
        nodeCollector = NodeCollector(parse_tree.getRoot(), IsLeaf())
        leaf_list = nodeCollector.collect()
        for i in range(0, len(leaf_list)):
            tree_word = leaf_list[i].getData().getName()
            sentence_word = sentence.getWord(i).getName()
            if tree_word == "_rare_" or tree_word == "_num_":
                leaf_list[i].setData(Symbol(sentence_word))

    @staticmethod
    def toRule(parse_node: ParseNode, trim: bool) -> Rule:
        right = []
        if trim:
            left = parse_node.getData().trimSymbol()
        else:
            left = parse_node.getData()
        for i in range(0, parse_node.numberOfChildren()):
            child_node = parse_node.getChild(i)
            if child_node.getData() is not None:
                if child_node.getData().isTerminal() or not trim:
                    right.append(child_node.getData())
                else:
                    right.append(child_node.getData().trimSymbol())
            else:
                return None
        return Rule(left, right)

    def addRules(self, parse_node: ParseNode):
        new_rule = ContextFreeGrammar.toRule(parse_node, True)
        if new_rule is not None:
            self.addRule(new_rule)
        for i in range(0, parse_node.numberOfChildren()):
            child_node = parse_node.getChild(i)
            if child_node.numberOfChildren() > 0:
                self.addRules(child_node)

    def binarySearch(self,
                     rules: list,
                     rule: Rule,
                     comparator) -> int:
        lo = 0
        hi = len(rules) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if comparator(rules[mid], rule) == 0:
                return mid
            if comparator(rules[mid], rule) <= 0:
                lo = mid + 1
            else:
                hi = mid - 1
        return -(lo + 1)

    def addRule(self, new_rule: Rule):
        pos = self.binarySearch(self.rules, new_rule, self.ruleComparator)
        if pos < 0:
            self.rules.insert(-pos - 1, new_rule)
            pos = self.binarySearch(self.rules_right_sorted, new_rule, self.ruleRightComparator)
            if pos >= 0:
                self.rules_right_sorted.insert(pos, new_rule)
            else:
                self.rules_right_sorted.insert(-pos - 1, new_rule)

    def removeRule(self, rule: Rule):
        pos = self.binarySearch(self.rules, rule, self.ruleComparator)
        if pos >= 0:
            self.rules.pop(pos)
            pos = self.binarySearch(self.rules_right_sorted, rule, self.ruleRightComparator)
            pos_up = pos
            while pos_up >= 0 and self.ruleRightComparator(self.rules_right_sorted[pos_up], rule) == 0:
                if self.ruleComparator(rule, self.rules_right_sorted[pos_up]) == 0:
                    self.rules_right_sorted.pop(pos_up)
                    return
                pos_up = pos_up - 1
            pos_down = pos + 1
            while pos_down < len(self.rules_right_sorted) \
                    and self.ruleRightComparator(self.rules_right_sorted[pos_down], rule) == 0:
                if self.ruleComparator(rule, self.rules_right_sorted[pos_down]) == 0:
                    self.rules_right_sorted.pop(pos_down)
                    return
                pos_down = pos_down + 1

    def getRulesWithLeftSideX(self, X: Symbol) -> list[Rule]:
        result = []
        dummy_rule = Rule(X, X)
        middle = self.binarySearch(self.rules, dummy_rule, self.ruleLeftComparator)
        if middle >= 0:
            middle_up = middle
            while middle_up >= 0 and self.rules[middle_up].left_hand_side.getName() == X.getName():
                result.append(self.rules[middle_up])
                middle_up = middle_up - 1
            middle_down = middle + 1
            while middle_down < len(self.rules) and self.rules[middle_down].left_hand_side.getName() == X.getName():
                result.append(self.rules[middle_down])
                middle_down = middle_down + 1
        return result

    def partOfSpeechTags(self) -> list[Symbol]:
        result = []
        for rule in self.rules:
            if rule.type == RuleType.TERMINAL and rule.left_hand_side not in result:
                result.append(rule.left_hand_side)
        return result

    def getLeftSide(self) -> list[Symbol]:
        result = []
        for rule in self.rules:
            if rule.left_hand_side not in result:
                result.append(rule.left_hand_side)
        return result

    def getTerminalRulesWithRightSideX(self, S: Symbol) -> list[Rule]:
        result = []
        dummy_rule = Rule(S, S)
        middle = self.binarySearch(self.rules_right_sorted, dummy_rule, self.ruleRightComparator)
        if middle >= 0:
            middle_up = middle
            while middle_up >= 0 and self.rules_right_sorted[middle_up].right_hand_side[0].getName() == S.getName():
                if self.rules_right_sorted[middle_up].type == RuleType.TERMINAL:
                    result.append(self.rules_right_sorted[middle_up])
                middle_up = middle_up - 1
            middle_down = middle + 1
            while middle_down < len(self.rules_right_sorted) and \
                    self.rules_right_sorted[middle_down].right_hand_side[0].getName() == S.getName():
                if self.rules_right_sorted[middle_down].type == RuleType.TERMINAL:
                    result.append(self.rules_right_sorted[middle_down])
                middle_down = middle_down + 1
        return result

    def getRulesWithRightSideX(self, S: Symbol) -> list[Rule]:
        result = []
        dummy_rule = Rule(S, S)
        pos = self.binarySearch(self.rules_right_sorted, dummy_rule, self.ruleRightComparator)
        if pos >= 0:
            pos_up = pos
            while pos_up >= 0 and \
                    self.rules_right_sorted[pos_up].right_hand_side[0].getName() == S.getName() and \
                    len(self.rules_right_sorted[pos_up].right_hand_side) == 1:
                result.append(self.rules_right_sorted[pos_up])
                pos_up = pos_up - 1
            pos_down = pos + 1
            while pos_down < len(self.rules_right_sorted) and \
                    self.rules_right_sorted[pos_down].right_hand_side[0].getName() == S.getName() and \
                    len(self.rules_right_sorted[pos_down].right_hand_side) == 1:
                result.append(self.rules_right_sorted[pos_down])
                pos_down = pos_down + 1
        return result

    def getRulesWithTwoNonTerminalsOnRightSide(self, A: Symbol, B: Symbol) -> list[Rule]:
        result = []
        dummy_rule = Rule(A, A, B)
        pos = self.binarySearch(self.rules_right_sorted, dummy_rule, self.ruleRightComparator)
        if pos >= 0:
            pos_up = pos
            while pos_up >= 0 and \
                    self.rules_right_sorted[pos_up].right_hand_side[0].getName() == A.getName() and \
                    self.rules_right_sorted[pos_up].right_hand_side[1].getName() == B.getName() and \
                    len(self.rules_right_sorted[pos_up].right_hand_side) == 2:
                result.append(self.rules_right_sorted[pos_up])
                pos_up = pos_up - 1
            pos_down = pos + 1
            while pos_down < len(self.rules_right_sorted) and \
                    self.rules_right_sorted[pos_down].right_hand_side[0].getName() == A.getName() and \
                    self.rules_right_sorted[pos_down].right_hand_side[1].getName() == B.getName() and \
                    len(self.rules_right_sorted[pos_down].right_hand_side) == 2:
                result.append(self.rules_right_sorted[pos_down])
                pos_down = pos_down + 1
        return result

    def getSingleNonTerminalCandidateToRemove(self, removed_list: list[Symbol]) -> Symbol:
        remove_candidate = None
        for rule in self.rules:
            if rule.type == RuleType.SINGLE_NON_TERMINAL and \
                    not rule.leftRecursive() and \
                    rule.right_hand_side[0] not in removed_list:
                remove_candidate = rule.right_hand_side[0]
                break
        return remove_candidate

    def getMultipleNonTerminalCandidateToUpdate(self) -> Rule:
        remove_candidate = None
        for rule in self.rules:
            if rule.type == RuleType.MULTIPLE_NON_TERMINAL:
                remove_candidate = rule
                break
        return remove_candidate

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
                    self.addRule(Rule(rule.left_hand_side, clone, candidate.type))
                self.removeRule(rule)
            non_terminal_list.append(remove_candidate)
            remove_candidate = self.getSingleNonTerminalCandidateToRemove(non_terminal_list)

    def updateAllMultipleNonTerminalWithNewRule(self,
                                                first: Symbol,
                                                second: Symbol,
                                                _with: Symbol):
        for rule in self.rules:
            if rule.type == RuleType.MULTIPLE_NON_TERMINAL:
                rule.updateMultipleNonTerminal(first, second, _with)

    def updateMultipleNonTerminalFromRightHandSide(self):
        new_variable_count = 0
        update_candidate = self.getMultipleNonTerminalCandidateToUpdate()
        while update_candidate is not None:
            new_right_hand_side = []
            new_symbol = Symbol("X" + str(new_variable_count))
            new_right_hand_side.append(update_candidate.right_hand_side[0])
            new_right_hand_side.append(update_candidate.right_hand_side[1])
            self.updateAllMultipleNonTerminalWithNewRule(update_candidate.right_hand_side[0], update_candidate.right_hand_side[1], new_symbol)
            self.addRule(Rule(new_symbol, new_right_hand_side, RuleType.TWO_NON_TERMINAL))
            update_candidate = self.getMultipleNonTerminalCandidateToUpdate()
            new_variable_count = new_variable_count + 1

    def convertToChomskyNormalForm(self):
        self.removeSingleNonTerminalFromRightHandSide()
        self.updateMultipleNonTerminalFromRightHandSide()
        self.rules.sort(key=cmp_to_key(self.ruleComparator))
        self.rules_right_sorted.sort(key=cmp_to_key(self.ruleRightComparator))

    def searchRule(self, rule: Rule) -> Rule:
        pos = self.binarySearch(self.rules, rule, self.ruleComparator)
        if pos >= 0:
            return self.rules[pos]
        else:
            return None

    def size(self) -> int:
        return len(self.rules)
