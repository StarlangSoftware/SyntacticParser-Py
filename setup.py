from setuptools import setup

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='nlptoolkit_syntacticparser',
    version='1.0.1',
    packages=['ContextFreeGrammar', 'ProbabilisticContextFreeGrammar', 'ProbabilisticParser', 'SyntacticParser'],
    url='https://github.com/StarlangSoftware/SyntacticParser-Py',
    license='',
    author='olcaytaner',
    author_email='olcay.yildiz@ozyegin.edu.tr',
    description='Syntactic Parsing Algorithms',
    install_requires=['NlpToolkit-ParseTree', 'NlpToolkit-Corpus', 'Nlptoolkit-DataStructure'],
    long_description=long_description,
    long_description_content_type='text/markdown'
)
