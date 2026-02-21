from pydicate.lang.tupilang.pos.adverb import Adverb
from pydicate.lang.tupilang.pos.verb import Verb
from pydicate.lang.tupilang.pos.noun import Noun
from pydicate.lang.tupilang.pos.deverbal import Deverbal
from tupi import Noun as TupiNoun, AnnotatedString


class Postposition(Adverb):
    def __init__(
        self, value, definition="", tag="[POSTPOSITION]", category="postposition"
    ):
        """Initialize a Postposition object."""
        super().__init__(value, definition=definition, tag=tag, category=category)
        self.min_args = 1
        self.max_args = 1
        self.pluriforme = "(t)" in definition.lower()
        self.arg0 = None  # This will be set when the first argument is a verb

    @property
    def noun(self):
        if self.arguments:
            return TupiNoun(self.eval(True), self.functional_definition, noroot=True)
        return TupiNoun(self.verbete, self.functional_definition, noroot=True)

    @property
    def n(self):
        return Noun(self.noun.verbete(True), definition=self.definition)

    def morphology(self, annotated=False):
        arg0_object = self.arg0
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
            return (
                (
                    TupiNoun(self.verbete, self.definition)
                    .possessive(
                        arg0_object.inflection(),
                        None if arg0_object.category == "pronoun" else arg0,
                    )
                    .latest_verbete.drop_all_last_tags()
                    + (self.tag)
                )
                .strip()
                .verbete(annotated=annotated)
            )
        return (
            f"{arg0} {self.verbete}{self.tag}"
            if annotated
            else f"{arg0} {self.verbete}"
        ).strip()

    def preval(self, annotated=False):
        pre_adjuncts = (
            " ".join([x.eval(annotated=annotated) for x in reversed(self.pre_adjuncts)])
            + " "
        )
        post_adjuncts = " " + (
            " ".join([x.eval(annotated=annotated) for x in self.post_adjuncts])
        )
        """Evaluate the Postposition object."""
        if len(self.arguments) == 1:
            return (
                pre_adjuncts + self.morphology(annotated=annotated) + post_adjuncts
            ).strip()
        return (
            pre_adjuncts
            + (f"{self.verbete}{self.tag}" if annotated else self.verbete)
            + post_adjuncts
        ).strip()

    def __mul__(self, other):
        """
        Multiply a Postposition with another object.
        :param other: The object to multiply with.
        :return: A new Postposition with the added argument.
        """
        cop = self.copy()
        arg0 = other.copy()
        if isinstance(arg0, Verb):
            arg0 = arg0.base_nominal(True)
        cop.arguments.append(other.copy())
        cop.arg0 = arg0
        return cop


class Locative(Postposition):
    def __init__(self, definition="in, at, on, to"):
        """Initialize a Locative object."""
        super().__init__("pe", definition=definition, tag="[POSTPOSITION:LOCATIVE]")

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        tn = (
            TupiNoun(self.arg0.eval(annotated), self.arg0.definition)
            .pe()
            .verbete(annotated)
        )
        return (tn + (self.tag if annotated else "")).strip()


class Dative(Postposition):
    def __init__(self, definition="to, for, in favor of"):
        """Initialize a Dative object."""
        super().__init__("supé", definition=definition, tag="[POSTPOSITION:DATIVE]")
        self.variation_id = 0

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        tn = (
            TupiNoun(self.arg0.eval(annotated), self.arg0.definition, noroot=True)
            .supe(variation_id=self.variation_id)
            .verbete(annotated)
        )
        return tn + (self.tag if annotated else "")


class Temporal(Postposition):
    def __init__(self, definition="during, when, at the time of, on"):
        """Initialize a Temporal object."""
        super().__init__("eme", definition=definition, tag="[POSTPOSITION:TEMPORAL]")

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        tn = (
            TupiNoun(self.arg0.eval(annotated), self.arg0.definition)
            .reme()
            .verbete(annotated)
        )
        return tn + (self.tag if annotated else "")


# -(r)amo (posp. átona - sua forma nasalizada é -namo): 1) como, na condição de; em [Com o verbo ikó / ekó (t) forma locução correspondente ao verbo ser do português.]: ...Ybyramo i moingó-ukare'yma. - Em terra não os fazendo transformar. (Ar., Cat., 179v); ...Serekoaramo ûitekóbo... - Estando como seu guardião (ou sendo seu guardião). (Anch., Teatro, 4); Pitangamo seni Maria îybápe. - Como criança está sentado nos braços de Maria. (Anch., Poemas, 108); Nde manhanamo t'oîkóne! - Ele há de ser (ou há de estar na condição de) teu espião! (Anch., Teatro, 32); ...Xe boîáramo pabẽ xe pópe arekó-katu. - Como meus súditos em minhas mãos bem os tenho a todos. (Anch., Teatro, 34); Pitangĩnamo ereîkó… - Uma criancinha és (ou na condição de uma criancinha estás). (Anch., Poemas, 100); 2) segundo, conforme: Xe anama, erimba'e, tekó-ypyramo sekóû. - Minha nação, outrora, estava segundo a lei primeira. (Anch., Poemas, 114); 3) Forma o gerúndio de predicados nominais: ...o mba'epûeramo... - sendo coisa antiga (Ar., Cat., 74); O angaîpabamo... - Sendo mau. (Ar., Cat., 27); Xe katuramo. - Sendo eu bom; Nde katuramo. - Sendo tu bom. (Anch., Arte, 29); 4) Forma o modo indicativo circunstancial dos verbos da segunda classe: Koromõ xe rorybamo. - Logo eu estou feliz. (Anch., Arte, 40)
class Translational(Postposition):
    def __init__(self, definition="as, in the condition of, in the duty of"):
        """Initialize a Locative object."""
        super().__init__(
            "amo", definition=definition, tag="[POSTPOSITION:TRANSLATIONAL]"
        )

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        arg0 = self.arg0
        # while not isinstance(arg0, Deverbal):
        #     if len(arg0.arguments) == 0:
        #         break
        #     arg0 = arg0.arguments[0]
        tn = (
            TupiNoun(arg0.eval(annotated), arg0.definition, noroot=True)
            .ramo()
            .verbete(annotated)
        )
        return tn + (self.tag if annotated else "")


class Beyond(Postposition):
    def __init__(self, definition="after, beyond, past", tag="[POSTPOSITION:BEYOND]"):
        """Initialize a Beyond object."""
        super().__init__("riré", definition=definition, tag=tag)

    def morphology(self, annotated=False):
        """Evaluate the Postposition object."""
        if len(self.arguments) == 0:
            return f"{self.verbete}{self.tag}"
        if isinstance(self.arg0, Verb):
            vbt = (
                AnnotatedString(self.arg0.base_nominal(annotated=True).eval(True))
                .drop_all_last_tags()
                .removesuffix_original("a")
            )
        else:
            vbt = (
                AnnotatedString(self.arg0.eval(True))
                .drop_all_last_tags()
                .removesuffix_original("a")
            )
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
        retval = AnnotatedString((Beyond() * self.ar0).preval(annotated=annotated))
        retval.replace_clean(-1, 1, "e")
        retval.insert_suffix("mẽ")
        retval.insert_suffix(self.tag)
        return retval.verbete(annotated=annotated)


sosé = Postposition("sosé", definition="above, better than, more than")
suí = Postposition(
    "suí", definition="from, of, since, away from, for, in favor of, more than"
)
koty = Postposition("koty", definition="versus, in the direction of, towards")
obaké = Postposition(
    "obaké",
    definition="(t) in front of, before, facing, in the presence of, in front of",
)
enondé = Postposition(
    "enondé", definition="(t) in front of, before, facing, in the presence of"
)
posé = Postposition("posé", definition="(m) alongside, next to, beside, with (person)")
ndi = Postposition(
    "ndi", definition="with, together with, in the company of"
)  # (Se o sujeito for de 1ª ou 2ª pessoas, o verbo deverá sempre ir para o plural.)
ndibé = Postposition(
    "ndibé", definition="with, together with, in the company of"
)  # (leva o verbo para o plural)
bé = Postposition("bé", definition="since")
esé = Postposition(
    "esé", definition="(t) about, in regard to, because of, for, in order to, during"
)
ri = Postposition(
    "ri",
    definition="for, because of, in order to, during, about, regarding, concerning",
)
upi = Postposition("upi", definition="(t) according to, following")
porupi = Postposition("porupi", definition="alongside, parallel to, next to")
îabé = Postposition("îabé", definition="like, as, similar to, in the same way as")
îá = Postposition("îá", definition="like, as, similar to, in the same way as")
pupé = Postposition(
    "pupé", definition="inside, within, in, into, inside of, using, with, during"
)
amo = Translational()
iré = Beyond()
iremen = SoonAfter()
eme = Temporal()
# TODO: implement -bo like -pe


pe = Locative()
supé = Dative()
