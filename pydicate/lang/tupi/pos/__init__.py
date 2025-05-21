from .noun import *
from .adverb import *
from .postposition import *
from .conjunction import *
from .verb import *
from .copula import *
from .y_fix import *

abé = Conjunction("abé")  # Tupi for "and"
ne = YFix(Adverb("ne")) # Make into a future particle
mo = YFix(Adverb("mo")) # Make into a irreal particle
umã = Adverb("umã")
mã = YFix(Adverb("mã")) # Make into a irreal particle
temõ = YFix(Adverb("temõ")) # Make into a irreal particle
pe = YFix(Postposition("pe")) # Make into a irreal particle