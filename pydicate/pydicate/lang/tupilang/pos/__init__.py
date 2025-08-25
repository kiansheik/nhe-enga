from .noun import *
from .adverb import *
from .postposition import *
from .verb import *
from .copula import *
from .y_fix import *
from .demonstrative import *
from .deverbal import *
from .particle import *
from .interjection import *
from .number import *
from .deadverbal import *

abé = Conjunction("abé", tag="[CONJUNCTION:AND]")  # Tupi for "and"
erimbae = Adverb("erimba'e", tag="[ADVERB]")  # Tupi for "also" or "too"
ne = YFix(Adverb("ne", tag="[FUTURE]"))
ymo = YFix(Adverb("mo", tag="[IRREALIS_SUFIX]"))  # Make into a irreal particle
umã = Adverb("umã", tag="[PRETERITE]")
mã = YFix(Adverb("mã", tag="[EXHALTIVE_SUFIX]"))  # Make into a irreal particle
temõ = YFix(Adverb("temõ", tag="[WISHFUL_SUFIX]"))  # Make into a irreal particle


def v(noun):
    pf = noun.noun.pluriform_prefix()
    vc = "(adj.)"
    if pf:
        vc = f"({pf})" + vc
    return Verb(
        noun.noun.verbete(anotated=True),
        verb_class=vc,
        definition=noun.noun.raw_definition,
    )
