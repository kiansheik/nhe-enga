from pydicate import Predicate
from typing import TYPE_CHECKING

# if TYPE_CHECKING:
# from .deverbal import Deverbal  # only used for type checking, not at runtime
from tupi import Verb as TupiVerb
from tupi import Noun as TupiNoun
from pydicate.lang.tupilang.pos.noun import pronoun_verbetes, Noun
from pydicate.lang.tupilang.pos.adverb import Adverb
from pydicate.lang.tupilang.pos.y_fix import YFix
import gzip, json
import io
import importlib.resources

path = importlib.resources.files("pydicate.lang.tupilang.data").joinpath(
    "dict-conjugated.json.gz"
)
with path.open("rb") as raw_file:  # Open in binary mode for gzip
    with gzip.open(raw_file, "rt", encoding="utf-8") as f:
        dict_conjugated = [x for x in json.load(f) if "c" in x]


class Verb(Predicate):
    def __init__(
        self,
        value=None,
        verb_class="",
        definition="",
        vid=None,
        tag="[VERB]",
        category="verb",
    ):
        """Initialize a Verb object."""
        super().__init__(
            verbete=value,
            category=category,
            min_args=1,
            max_args=2,
            definition=definition,
            tag=tag,
        )
        if not self.verbete and not vid:
            raise ValueError("Either value or vid must be provided.")
        # Try to find the verb in the conjugated dictionary
        if not verb_class or not definition:
            found = False
            if vid:
                for verb in dict_conjugated:
                    if verb["i"] == vid:
                        self.verbete = verb["f"]
                        verb_class = verb["v"]
                        definition = verb["d"]
                        found = True
                        break
                if not found:
                    raise ValueError(f"Verb with ID {vid} not found in the dictionary.")
            else:
                for verb in dict_conjugated:
                    if verb["f"] == self.verbete:
                        verb_class = verb["v"]
                        definition = verb["d"]
                        vid = verb["i"]
                        found = True
                        break

        self.verb = TupiVerb(self.verbete, verb_class, definition, vid=vid)
        self.user_definition = f"{self.definition} ".strip()
        self.raw_definition = definition
        self.mood = "indicativo"

    def raw_noun(self):
        """Return the noun form of the verb."""
        return TupiNoun(self.verbete, self.raw_definition)

    def subject(self):
        return (
            self.arguments[0]
            if (
                len(self.arguments) > 1
                or (len(self.arguments) > 0 and not self.verb.transitivo)
            )
            else None
        )

    def object(self):
        return (
            self.arguments[1]
            if len(self.arguments) > 1
            else self.arguments[0]
            if (len(self.arguments) > 0 and self.verb.transitivo)
            else None
        )

    def refresh_verbete(self, new_verbete):
        self.verbete = new_verbete
        self.verb = TupiVerb(self.verbete, self.verb.verb_class, self.definition)

    def preval(self, annotated=False):
        """Evaluate the Verb object."""
        retval = ""
        obj_delocated = ""
        arglen = len(self.arguments)
        if self.is_subordinated():
            if self.mood == "indicativo":
                if self.same_subject():
                    self.mood = "gerundio"
                else:
                    self.mood = "conjuntivo"
            elif self.mood == "imperativo":
                self.mood = "permissivo"
        elif self.mood == "indicativo":
            self.mood = self.indicative()
        if arglen == 0:
            retval = self.verb.verbete
        elif arglen == 1:
            obj = self.arguments[0]
            arg0 = None if obj.pro_drop else obj.eval(annotated=annotated)
            infl0 = obj.inflection()
            if self.verb.transitivo:
                # TODO: render "nominal form"
                if (
                    obj.category == "pronoun"
                ):  # if the verb has a personal inflection then it's a pronoun
                    retval = self.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        object_tense=infl0,
                        pro_drop=True,
                        mode=self.mood,
                        negative=self.negated,
                    )
                else:  # otherwise it's a direct object
                    retval = self.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        object_tense="3p",
                        dir_obj_raw=arg0,
                        pro_drop=True,
                        mode=self.mood,
                        negative=self.negated,
                    )
            else:  # intransitive
                suj = self.arguments[0]
                if suj.category == "pronoun":
                    retval = self.verb.conjugate(
                        anotar=annotated,
                        subject_tense=infl0,
                        mode=self.mood,
                        negative=self.negated,
                        pro_drop=suj.pro_drop,
                        pos=suj.posto,
                    )
                else:
                    retval = self.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        dir_subj_raw=arg0,
                        mode=self.mood,
                        negative=self.negated,
                        pro_drop=suj.pro_drop,
                        pos=suj.posto,
                    )
        elif arglen == 2:  # transitive
            suj = self.arguments[0]
            obj = self.arguments[1]
            arg0 = suj.eval(annotated=annotated)
            infl0 = suj.inflection()
            arg1 = (
                None
                if (obj.pro_drop or obj.eval(annotated=annotated) in pronoun_verbetes)
                else obj.eval(annotated=annotated)
            )
            infl1 = obj.inflection()
            if obj.category == "conjunction":
                arg1 = None
                obj_delocated = None if obj.pro_drop else obj.eval(annotated=annotated)
            retval = self.verb.conjugate(
                anotar=annotated,
                subject_tense=infl0 if infl0 else "3p",
                object_tense=infl1 if infl1 else "3p",
                dir_subj_raw=arg0,
                dir_obj_raw=arg1,
                mode=self.mood,
                negative=self.negated,
                pro_drop=suj.pro_drop,
                pro_drop_obj=obj.pro_drop,
                pos=obj.posto,
            )
        if obj_delocated:
            retval = retval + " " + obj_delocated
        # deal with adverbs
        # We need to know if the adverb was added before the verb or after: `go * Noun("Endé") + Adverb("koritei")` or `Adverb("koritei") + go * Noun("Endé")`
        for adj in self.pre_adjuncts:
            retval = adj.eval(annotated=annotated) + " " + retval
        for adj in self.post_adjuncts:
            sepchar = " "
            # remove [*] from end of retval and get last character
            lastchar = self.verb.remove_brackets_and_contents(retval).strip()[-1]
            if type(adj) == YFix and (
                lastchar not in (TupiVerb.vogais + TupiVerb.semi_vogais)
            ):
                sepchar = "y" + ("[CONSONANT_CLASH]" if annotated else "")
            retval = retval + sepchar + adj.eval(annotated=annotated)
        return retval if annotated else self.verb.remove_brackets_and_contents(retval)

    def base_nominal(self, annotated=False):
        if len(self.arguments) == 0:
            nom = self.verb.conjugate(
                subject_tense="3p",
                object_tense="absoluta",
                dir_obj_raw=None,
                dir_subj_raw=None,
                mode="nominal",
                pos="anteposto",
                pro_drop=True,
                negative=False,
                anotar=annotated,
            )
            tn = TupiNoun(nom, self.raw_definition)
            final = Noun(
                tn.substantivo(True),
                definition=self.definition,
                inflection="3p",
                pro_drop=False,
            )
            return final
        if len(self.arguments) < 2:
            if self.verb.transitivo:
                obj_tense = self.arguments[0].inflection()
                obj_obj = (
                    self.arguments[0]
                    if self.arguments[0].category != "pronoun"
                    else None
                )
                obj = (
                    obj_obj.eval(annotated=annotated)
                    if self.arguments[0].category != "pronoun"
                    else None
                )
                subj_tense = None
                subj = None
                subj_obj = None
            else:
                obj_tense = "3p"
                obj = None
                subj_tense = self.arguments[0].inflection()
                subj_obj = (
                    self.arguments[0]
                    if self.arguments[0].category != "pronoun"
                    else None
                )
                subj = (
                    subj_obj.eval(annotated=annotated)
                    if self.arguments[0].category != "pronoun"
                    else None
                )
        else:
            obj_tense = self.arguments[1].inflection()
            obj_obj = (
                self.arguments[1] if self.arguments[1].category != "pronoun" else None
            )
            obj = (
                obj_obj.eval(annotated=annotated)
                if self.arguments[1].category != "pronoun"
                else None
            )
            subj_tense = self.arguments[0].inflection()
            subj_obj = (
                self.arguments[0] if self.arguments[0].category != "pronoun" else None
            )
            subj = (
                subj_obj.eval(annotated=annotated)
                if self.arguments[0].category != "pronoun"
                else None
            )
        nom = self.verb.conjugate(
            subject_tense=subj_tense if subj_tense else "3p",
            object_tense=obj_tense,
            dir_obj_raw=obj,
            dir_subj_raw=subj,
            mode="nominal",
            pos="anteposto",
            pro_drop=(subj_obj.pro_drop if subj_obj else False) or not subj_tense,
            negative=self.negated,
            anotar=annotated,
        )
        tn = TupiNoun(nom, self.raw_definition)
        final = Noun(
            tn.substantivo(True),
            definition=self.definition,
            inflection="3p",
            pro_drop=subj_obj.pro_drop if subj_obj else False,
        )
        return final

    # first arg is the subject, second arg is the object

    def __repr__(self):
        return self.eval(annotated=False)

    def __pos__(self):
        """
        Mark noun as pro_drop the predicate using the + operator.
        :return: Self (to enable chaining).
        """
        dropped = self.copy()
        dropped.arguments[0].pro_drop = True
        return dropped

    def imp(self):
        imp_copy = self.copy()
        imp_copy.mood = "imperativo"
        return imp_copy

    def perm(self):
        perm_copy = self.copy()
        perm_copy.mood = "permissivo"
        return perm_copy

    def indicative(self):
        for adj in self.pre_adjuncts:
            if isinstance(adj, Adverb):
                return "circunstancial"
            if isinstance(adj, Verb):
                if len(adj.arguments) >= 1:
                    # Gerund does not force circumstancial mood
                    if adj.subject() and self.subject():
                        if adj.subject().eval(True) != self.subject().eval(True):
                            return "circunstancial"
        return "indicativo"

    def __mul__(self, other):
        fin = other.copy()
        vbt = self.copy()
        if isinstance(fin, Verb):
            if len(vbt.arguments) > len(fin.arguments):
                vbt = vbt.base_nominal(annotated=True)
                return vbt * fin
            fin = fin.base_nominal(annotated=True)
        # elif isinstance(fin, Deverbal):
        #     return fin * vbt
        return super().__mul__(fin)


só = Verb("só", definition="to go")
aûsub = Verb("aûsub", definition="to love")
