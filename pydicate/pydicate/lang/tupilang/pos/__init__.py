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

abé = Conjunction("abé", tag="[CONJUNCTION:AND]")  # Tupi for "and"
erimbae = Adverb("erimba'e", tag="[ADVERB]")  # Tupi for "also" or "too"
ne = YFix(Adverb("ne", tag="[FUTURE]"))
mo = YFix(Adverb("mo", tag="[IRREALIS_SUFIX]"))  # Make into a irreal particle
umã = Adverb("umã", tag="[PRETERITE]")
mã = YFix(Adverb("mã", tag="[EXHALTIVE_SUFIX]"))  # Make into a irreal particle
temõ = YFix(Adverb("temõ", tag="[WISHFUL_SUFIX]"))  # Make into a irreal particle
peQ = YFix(Postposition("pe", tag="[INTERROGATIVE]"))
