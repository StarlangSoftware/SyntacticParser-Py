from abc import abstractmethod

from Corpus.Sentence import Sentence
from ParseTree.ParseTree import ParseTree
from ContextFreeGrammar.ContextFreeGrammar import ContextFreeGrammar


class SyntacticParser:

    @abstractmethod
    def parse(self, cfg: ContextFreeGrammar, sentence: Sentence) -> [ParseTree]:
        pass
