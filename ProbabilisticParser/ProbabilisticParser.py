from abc import abstractmethod

from Corpus.Sentence import Sentence
from ParseTree.ParseTree import ParseTree
from ProbabilisticContextFreeGrammar.ProbabilisticContextFreeGrammar import ProbabilisticContextFreeGrammar


class ProbabilisticParser:

    @abstractmethod
    def parse(self, pcfg: ProbabilisticContextFreeGrammar, sentence: Sentence) -> [ParseTree]:
        pass
