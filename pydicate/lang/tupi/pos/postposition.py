from .adverb import Adverb
from .verb import Verb
from .deverbal import Deverbal
import sys
import re

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Noun as TupiNoun, AnnotatedString


class Postposition(Adverb):
    def __init__(self, value, definition="", tag="[POSTPOSITION]"):
        """Initialize a Postposition object."""
        super().__init__(value, definition=definition, tag=tag)
        self.category = "postposition"
        self.min_args = 1
        self.max_args = 1
        self.pluriforme = "(t)" in definition.lower()
    
    def morphology(self, annotated=False):
        arg0_object = self.arguments[0]
        arg0 = arg0_object.verbete
        found = False
        for val, infl in TupiNoun.personal_inflections.items():
            if arg0.lower() == infl[0]:
                arg0 = infl[1]
                found = True
                break
        if not found:
            arg0 = arg0_object.eval(annotated=annotated)
        if self.pluriforme:
            return (TupiNoun(self.verbete, self.definition).possessive(
                arg0_object._inflection,
                None if arg0_object.category == "pronoun" else arg0,
            ).verbete(annotated)).strip()
        return (
            f"{arg0} {self.verbete}{self.tag}"
            if annotated
            else f"{arg0} {self.verbete}"
        ).strip()

    def preval(self, annotated=False):
        pre_adjuncts = " ".join([x.eval(annotated=annotated) for x in reversed(self.pre_adjuncts)]) + " "
        post_adjuncts = " " + (" ".join([x.eval(annotated=annotated) for x in self.post_adjuncts]))
        """Evaluate the Postposition object."""
        if len(self.arguments) == 1:
            return (pre_adjuncts + self.morphology(annotated=annotated) + post_adjuncts).strip()
        return (pre_adjuncts + (f"{self.verbete}{self.tag}" if annotated else self.verbete) + post_adjuncts).strip()


class Locative(Postposition):
    def __init__(self, definition="in, at, on, to"):
        """Initialize a Locative object."""
        super().__init__("pe", definition=definition, tag="[POSTPOSITION:LOCATIVE]")

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        tn = TupiNoun(self.arguments[0].eval(annotated), self.arguments[0].definition).pe().verbete(annotated)
        return (tn + (self.tag if annotated else "")).strip()

class Dative(Postposition):
    def __init__(self, definition="to, for, in favor of"):
        """Initialize a Dative object."""
        super().__init__("supé", definition=definition, tag="[POSTPOSITION:DATIVE]")

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        tn = TupiNoun(self.arguments[0].eval(annotated), self.arguments[0].definition).supe().verbete(annotated)
        return tn + (self.tag if annotated else "")

class Temporal(Postposition):
    def __init__(self, definition="during, when, at the time of, on"):
        """Initialize a Temporal object."""
        super().__init__("eme", definition=definition, tag="[POSTPOSITION:TEMPORAL]")

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        tn = TupiNoun(self.arguments[0].eval(annotated), self.arguments[0].definition).reme().verbete(annotated)
        return tn + (self.tag if annotated else "")

# -(r)amo (posp. átona - sua forma nasalizada é -namo): 1) como, na condição de; em [Com o verbo ikó / ekó (t) forma locução correspondente ao verbo ser do português.]: ...Ybyramo i moingó-ukare'yma. - Em terra não os fazendo transformar. (Ar., Cat., 179v); ...Serekoaramo ûitekóbo... - Estando como seu guardião (ou sendo seu guardião). (Anch., Teatro, 4); Pitangamo seni Maria îybápe. - Como criança está sentado nos braços de Maria. (Anch., Poemas, 108); Nde manhanamo t'oîkóne! - Ele há de ser (ou há de estar na condição de) teu espião! (Anch., Teatro, 32); ...Xe boîáramo pabẽ xe pópe arekó-katu. - Como meus súditos em minhas mãos bem os tenho a todos. (Anch., Teatro, 34); Pitangĩnamo ereîkó… - Uma criancinha és (ou na condição de uma criancinha estás). (Anch., Poemas, 100); 2) segundo, conforme: Xe anama, erimba'e, tekó-ypyramo sekóû. - Minha nação, outrora, estava segundo a lei primeira. (Anch., Poemas, 114); 3) Forma o gerúndio de predicados nominais: ...o mba'epûeramo... - sendo coisa antiga (Ar., Cat., 74); O angaîpabamo... - Sendo mau. (Ar., Cat., 27); Xe katuramo. - Sendo eu bom; Nde katuramo. - Sendo tu bom. (Anch., Arte, 29); 4) Forma o modo indicativo circunstancial dos verbos da segunda classe: Koromõ xe rorybamo. - Logo eu estou feliz. (Anch., Arte, 40)
class Simulational(Postposition):
    def __init__(self, definition="as, in the condition of, in the duty of"):
        """Initialize a Locative object."""
        super().__init__("amo", definition=definition, tag="[POSTPOSITION:SIMULATIONAL]")

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        arg0 = self.arguments[0]
        while not isinstance(arg0, Deverbal):
            if len(arg0.arguments) == 0:
                break
            arg0 = arg0.arguments[0]
        tn = TupiNoun(self.arguments[0].eval(annotated), arg0.definition).ramo().verbete(annotated)
        return tn + (self.tag if annotated else "")

class Beyond(Postposition):
    def __init__(self, definition="after, beyond, past", tag="[POSTPOSITION:BEYOND]"):
        """Initialize a Beyond object."""
        super().__init__("riré", definition=definition, tag=tag)

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        if isinstance(self.arguments[0], Verb):
            vbt = AnnotatedString(self.arguments[0].base_nominal(annotated=True).eval(True)).removesuffix_original("a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]")
        else:
            vbt = AnnotatedString(self.arguments[0].eval(True)).removesuffix_original("a[SUBSTANTIVE_SUFFIX:CONSONANT_ENDING]")
        suffix = "iré"
        if vbt[-1] in TupiNoun.vogais:
            suffix = "r" + suffix
        vbt.insert_suffix(suffix)
        vbt.insert_suffix(self.tag)
        return vbt.verbete(annotated=annotated)

class SoonAfter(Beyond):
    def __init__(self, definition="soon after, immediately after", tag="[ADVERB:SOON]"):
        """Initialize a SoonAfter object."""
        super().__init__(definition=definition, tag=tag)

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        retval = AnnotatedString((Beyond() * self.arguments[0]).preval(annotated=annotated))
        retval.replace_clean(-1, 1, "e")
        retval.insert_suffix("mẽ")
        retval.insert_suffix(self.tag)
        return retval.verbete(annotated=annotated)

sosé = Postposition("sosé", definition="above, better than, more than")
koty = Postposition("koty", definition="in the direction of, towards")
ndi = Postposition("ndi", definition="with, together with, in the company of") # (Se o sujeito for de 1ª ou 2ª pessoas, o verbo deverá sempre ir para o plural.)
ndibé = Postposition("ndibé", definition="with, together with, in the company of") # (leva o verbo para o plural)
bé = Postposition("bé", definition="since")
esé = Postposition("esé", definition="(t); about, in regard to, because of, for, in order to, during")
upi = Postposition("upi", definition="(t); according to, following")
porupi = Postposition("porupi", definition="alongside, parallel to, next to")
# pupé (posp.) - 1) dentro de: Mba'epe ererur nde karamemûã pupé? - Que trouxeste dentro de tua caixa? (Léry, Histoire, 342); 2) com (instr.): Oîeypyî 'y-karaíba pupé. - Asperge-se com água benta. (Ar., Cat., 24); ...Opîá o akangaobĩ pupé. - Cobrindo-o com seu véu. (Ar., Cat., 62); itá pupé - com uma pedra (VLB, I, 77) 3) em (temp.): kó semana pupé... - nesta semana (Ar., Cat., 4); 4) em, para, para dentro de: ...Apŷaba... mondóbo xe retama pupé. - Enviando homens para minha terra. (D'Abbeville, Histoire, 341v); Mba'e-tepe peseká kó xe retama pupé? - Mas que é que procurais nesta minha terra? (Anch., Teatro, 28); ...Ybyrá pupé omanõmo... - Morrendo na cruz. (Anch., Poemas, 90); ...Purgatório pupé osoba'e... - as que vão para o purgatório (Ar., Cat., 136, 1686); 5) dentro do mesmo lugar de; no mesmo lugar de; com (de companhia): A'ar nde pupé. - Embarco contigo. (Anch., Arte, 40v); A'a nde pupé. - Caí no mesmo lugar de ti (isto é, caí em teus costumes); 6) entre, no meio de, junto com: Arasó nde mba'e xe mba'e pupé. - Levei as tuas coisas entre as minhas coisas. (Anch., Arte, 40v) ● pupé-ndûara (ou pupé-sûara) - o que está dentro de; o que é interior, o interno (VLB, II, 13)
pupé = Postposition("pupé", definition="inside, within, in, into, inside of, using, with, during")
amo = Simulational()
iré = Beyond()
iremen = SoonAfter()
eme = Temporal()
# TODO: implement -bo like -pe


pe = Locative()
supé = Dative()