from pydicate import Predicate
from typing import TYPE_CHECKING
import copy

# if TYPE_CHECKING:
# from .deverbal import Deverbal  # only used for type checking, not at runtime
from tupi import Verb as TupiVerb
from tupi import Noun as TupiNoun
from tupi import AnnotatedString
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
        self.v_adjuncts = []
        self.v_adjuncts_pre = []
        self.circumstancial = None
        self.reduplicated = False
        self._subject = None

    def raw_noun(self):
        """Return the noun form of the verb."""
        return TupiNoun(self.verbete, self.raw_definition)

    def redup(self):
        cop = self.copy()
        cop.reduplicated = True
        return cop

    def subject(self):
        if self._subject is not None:
            return self._subject
        return (
            self.arguments[0]
            if (
                len(self.arguments) >= 2
                or (len(self.arguments) == 1 and not self.verb.transitivo)
            )
            else None
        )

    def __lshift__(self, other):
        if other.category != "verb":
            cop = self.copy()
            cop.v_adjuncts.append(other.copy())
            return cop
        return super().__lshift__(other)

    # def __rshift__(self, other):
    #     if other.category != "verb":
    #         cop = self.copy()
    #         cop.v_adjuncts_pre.append(other.copy())
    #         return cop
    #     return super().__rshift__(other)

    def object(self):
        return (
            self.arguments[1]
            if len(self.arguments) >= 2
            else self.arguments[0]
            if (len(self.arguments) == 1 and self.verb.transitivo)
            else None
        )

    def refresh_verbete(self, new_verbete):
        self.verbete = new_verbete
        self.verb = TupiVerb(self.verbete, self.verb.verb_class, self.definition)

    def preval(self, annotated=False):
        """Evaluate the Verb object."""
        vadjs = ""
        vadjs_pre = ""
        if self.v_adjuncts:
            vadj_strs = []
            for x in self.v_adjuncts:
                val = x.eval(annotated=annotated)
                # If it's a YFix, check if we need to insert 'y' between consonants
                if isinstance(x, YFix):
                    # Get the last char of retval so far (or verbete if empty)
                    prev = retval if "retval" in locals() and retval else self.verbete
                    prev_last = (
                        self.verb.remove_brackets_and_contents(prev).strip()[-1]
                        if prev
                        else ""
                    )
                    # Get the first char of val
                    val_first = val[0] if val else ""
                    # If both are consonants, insert 'y'
                    if (
                        prev_last
                        and val_first
                        and prev_last not in (TupiVerb.vogais + TupiVerb.semi_vogais)
                        and val_first not in (TupiVerb.vogais + TupiVerb.semi_vogais)
                    ):
                        val = "y" + ("[CONSONANT_CLASH]" if annotated else "") + val
            vadj_strs.append(val)
            vadjs = " ".join(vadj_strs)
        if self.v_adjuncts_pre:
            vadjs_pre = " ".join(
                [x.eval(annotated=annotated) for x in reversed(self.v_adjuncts_pre)]
            )
        if self.v_adjuncts_pre:
            vadjs_pre = " ".join(
                [x.eval(annotated=annotated) for x in reversed(self.v_adjuncts_pre)]
            )
        retval = ""
        obj_delocated = ""
        arglen = len(self.arguments)
        gerund_composto = None
        base_verb = self.copy()
        if base_verb.is_subordinated():
            if base_verb.mood == "indicativo":
                if base_verb.same_subject():
                    base_verb.mood = "gerundio"
                elif base_verb.subject() and base_verb.subject().inflection() == "suj":
                    base_verb._subject = base_verb.principal.subject()
                    base_verb.mood = "gerundio"
                else:
                    base_verb.mood = "conjuntivo"
                    ger = base_verb.is_gerund_composto()
                    if ger:
                        base_verb = ger.copy()
                        base_verb.mood = "conjuntivo"
                        gerund_composto = self.copy()
            elif base_verb.mood == "imperativo":
                base_verb.mood = "permissivo"
        elif base_verb.mood == "indicativo":
            base_verb.mood = base_verb.indicative()
        if arglen == 0:
            retval = base_verb.verb.verbete
        elif arglen == 1:
            arg0_obj = base_verb.arguments[0]
            arg0 = None if arg0_obj.pro_drop else arg0_obj.eval(annotated=annotated)
            infl0 = arg0_obj.inflection()
            if base_verb.verb.transitivo:
                # TODO: render "nominal form"
                if (
                    arg0_obj.category == "pronoun"
                ):  # if the verb has a personal inflection then it's a pronoun
                    retval = base_verb.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        object_tense=infl0,
                        pro_drop=True,
                        mode=base_verb.mood,
                        negative=base_verb.negated,
                        vadjs=vadjs,
                        vadjs_pre=vadjs_pre,
                        redup=base_verb.reduplicated,
                        pos=arg0_obj.posto,
                    )
                else:  # otherwise it's a direct object
                    retval = base_verb.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        object_tense="3p",
                        dir_obj_raw=arg0,
                        pro_drop=True,
                        mode=base_verb.mood,
                        negative=base_verb.negated,
                        vadjs=vadjs,
                        vadjs_pre=vadjs_pre,
                        redup=base_verb.reduplicated,
                        pos=arg0_obj.posto,
                    )
            else:  # intransitive
                suj = base_verb.subject()
                if suj.category == "pronoun":
                    retval = base_verb.verb.conjugate(
                        anotar=annotated,
                        subject_tense=infl0,
                        mode=base_verb.mood,
                        negative=base_verb.negated,
                        pro_drop=suj.pro_drop,
                        pos=suj.posto,
                        vadjs=vadjs,
                        vadjs_pre=vadjs_pre,
                        redup=base_verb.reduplicated,
                    )
                else:
                    retval = base_verb.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        dir_subj_raw=arg0,
                        mode=base_verb.mood,
                        negative=base_verb.negated,
                        pro_drop=suj.pro_drop,
                        pos=suj.posto,
                        vadjs=vadjs,
                        vadjs_pre=vadjs_pre,
                        redup=base_verb.reduplicated,
                    )
        elif arglen == 2:  # transitive
            suj = base_verb.subject()
            obj = base_verb.object()
            arg0 = (
                suj.eval(annotated=annotated) if not suj.category == "pronoun" else None
            )
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
            use_obj_posto = infl1 in ["refl", "mut", "suj"] and (
                infl1 == "3p" or infl0 != "3p"
            )
            use_obj_posto = use_obj_posto or suj.pro_drop
            if "1" in infl1 and "2" in infl0:
                use_obj_posto = False
            if "2" in infl1 and "1" in infl0:
                use_obj_posto = False
            if "3" not in infl1 and "3" in infl0:
                use_obj_posto = False
            retval = base_verb.verb.conjugate(
                anotar=annotated,
                subject_tense=infl0 if infl0 else "3p",
                object_tense=infl1 if infl1 else "3p",
                dir_subj_raw=arg0,
                dir_obj_raw=arg1,
                mode=base_verb.mood,
                negative=base_verb.negated,
                pro_drop=suj.pro_drop,
                pro_drop_obj=obj.pro_drop,
                pos=obj.posto if use_obj_posto else suj.posto,
                vadjs=vadjs,
                vadjs_pre=vadjs_pre,
                redup=base_verb.reduplicated,
            )
        if obj_delocated:
            retval = retval + " " + obj_delocated
        # deal with adverbs
        # We need to know if the adverb was added before the verb or after: `go * Noun("Endé") + Adverb("koritei")` or `Adverb("koritei") + go * Noun("Endé")`
        if gerund_composto:
            gerund_composto.v_adjuncts = []
            gerund_composto.v_adjuncts_pre = []
            retval = f"{gerund_composto.base_nominal(True).verbete} {retval}"
            # filter self.pre_adjuncts and self.post_adjuncts to not render the gerund again
            filtered_pre_adjuncts = [
                adj for adj in self.pre_adjuncts if adj.verbete != base_verb.verbete
            ]
            filtered_post_adjuncts = [
                adj for adj in self.post_adjuncts if adj.verbete != base_verb.verbete
            ]
        else:
            filtered_pre_adjuncts = [adj for adj in self.pre_adjuncts]
            filtered_post_adjuncts = [adj for adj in self.post_adjuncts]
        for adj in filtered_pre_adjuncts:
            retval = adj.eval(annotated=annotated) + " " + retval
        for adj in filtered_post_adjuncts:
            sepchar = " "
            # remove [*] from end of retval and get last character
            lastchar = self.verb.remove_brackets_and_contents(retval).strip()[-1]
            if type(adj) == YFix and (
                lastchar not in (TupiVerb.vogais + TupiVerb.semi_vogais)
            ):
                sepchar = "y" + ("[CONSONANT_CLASH]" if annotated else "")
            # elif type(adj) == YFix: #TODO: fix this for any predicate, not just verbs
            #     sepchar = ""
            retval = retval + sepchar + adj.eval(annotated=annotated)
        return retval if annotated else self.verb.remove_brackets_and_contents(retval)

    def base_nominal(self, annotated=False):
        vadjs = ""
        vadjs_pre = ""
        if self.v_adjuncts:
            vadjs = " ".join([x.eval(annotated=annotated) for x in self.v_adjuncts])
        if self.v_adjuncts_pre:
            vadjs_pre = " ".join(
                [x.eval(annotated=annotated) for x in reversed(self.v_adjuncts_pre)]
            )
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
                redup=self.reduplicated,
                vadjs=vadjs,
                vadjs_pre=vadjs_pre,
            )
            tn = TupiNoun(nom, self.raw_definition)
            final = Noun(
                tn.verbete(True),
                definition=self.definition,
                inflection="3p",
                pro_drop=False,
            )
            final.noun.pluriforme = self.verb.pluriforme
            final.pre_adjuncts = [x.copy() for x in self.pre_adjuncts]
            final.post_adjuncts = [x.copy() for x in self.post_adjuncts]
            return final
        if len(self.arguments) == 1:
            if self.verb.transitivo:
                obj_tense = self.object().inflection()
                obj_obj = self.object() if self.object().category != "pronoun" else None
                obj = (
                    obj_obj.eval(annotated=annotated)
                    if self.object().category != "pronoun"
                    else None
                )
                subj_tense = None
                subj = None
                subj_obj = None
            else:
                obj_tense = None
                obj = None
                subj_tense = self.subject().inflection()
                subj_obj = (
                    self.subject() if self.subject().category != "pronoun" else None
                )
                subj = (
                    subj_obj.eval(annotated=annotated)
                    if self.subject().category != "pronoun"
                    else None
                )
        else:
            obj_tense = self.object().inflection()
            obj_obj = self.object() if self.object().category != "pronoun" else None
            obj = (
                obj_obj.eval(annotated=annotated)
                if self.object().category != "pronoun"
                else None
            )
            subj_tense = self.subject().inflection()
            subj_obj = self.subject() if self.subject().category != "pronoun" else None
            subj = (
                subj_obj.eval(annotated=annotated)
                if self.subject().category != "pronoun"
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
            vadjs=vadjs,
            vadjs_pre=vadjs_pre,
            redup=self.reduplicated,
        )
        tn = TupiNoun(nom, self.raw_definition)
        final = Noun(
            tn.verbete(True),
            definition=self.definition,
            inflection="3p",
            pro_drop=subj_obj.pro_drop if subj_obj else False,
        )
        final.pre_adjuncts = [x.copy() for x in self.pre_adjuncts]
        final.post_adjuncts = [x.copy() for x in self.post_adjuncts]
        final.v_adjuncts = [x.copy() for x in self.v_adjuncts]
        final.v_adjuncts_pre = [x.copy() for x in self.v_adjuncts_pre]
        final.arguments = [arg.copy() for arg in self.arguments]
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

    def circ(self, val=True):
        cop = self.copy()
        cop.circumstancial = val
        return cop

    def indicative(self):
        if self.circumstancial is not None:
            return "circunstancial" if self.circumstancial else "indicativo"
        pre_adj = copy.deepcopy(self.pre_adjuncts)
        if self.subject() and self.subject().posto != "anteposto":
            pre_adj += copy.deepcopy(self.v_adjuncts_pre)
        for adj in pre_adj:
            if isinstance(adj, Adverb):
                return "circunstancial"
            if isinstance(adj, Verb):
                if len(adj.arguments) >= 1:
                    # # Gerund does not force circumstancial mood
                    # if adj.subject() and self.subject():
                    #     if adj.subject().eval(True) != self.subject().eval(True):
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


class VerbAugmentor(Verb):
    def __init__(
        self,
        value="mo",
        definition="to make another do another verb",
        tag="[CAUSATIVE_PREFIX:MO]",
        category="verb_transitivizer",
        ero_switch=False,
    ):
        super().__init__(value=value, definition=definition, tag=tag, category=category)
        self._arguments = []
        self.ero_switch = ero_switch
        self._augmentee = None

    def __mul__(self, other):
        """
        Divide a Transitivizer with another object.
        :param other: The object to divide with.
        :return: A new Transitivizer with the added argument.
        """
        if self._augmentee is None:
            new_verb = VerbAugmentor.from_existing(other)
            new_verb.verb.verbete = f"{self.verbete}{self.tag}{other.verbete}"
            new_verb.verb.transitivo = True
            new_verb.verbete = new_verb.verb.verbete
            new_verb.verb.pluriforme = False
            new_verb.verb.t_type = False
            new_verb.verb.tr_type = False
            new_verb.verb.pluriforme_type = None
            new_verb.verb.segunda_classe = False
            new_verb.verb.ero = False
            if self.ero_switch:
                new_verb.verb.ero = True
                new_verb.verb.pluriforme = True
            new_verb.tag = f"{other.tag}"
            new_verb._augmentee = other
            new_verb._augmentor = self.copy()
            if hasattr(new_verb._augmentor, "_augmentee"):
                new_verb._augmentor._augmentee = None
            return new_verb
        return super().__mul__(other)

    def preval(self, annotated=False):
        if not self._augmentee or len(self._augmentee) == 0:
            return AnnotatedString(f"{self.verbete}{self.tag}").verbete(
                annotated=annotated
            )
        cop = self.copy()
        # return super function of preval for cop
        return super(VerbAugmentor, cop).preval(annotated=annotated)

    @classmethod
    def from_existing(cls, original: Verb):
        new_verb = cls.__new__(cls)  # create blank instance
        new_verb.__dict__ = copy.deepcopy(original.__dict__)
        return new_verb


só = Verb("só", definition="to go")
aûsub = Verb("aûsub", definition="to love")
mo = VerbAugmentor(
    value="mo",
    definition="to make someone perform target verb",
    tag="[CAUSATIVE_PREFIX:MO]",
    category="verb_transitivizer",
)  # TODO: Fix the phonetic rules for this
ero = VerbAugmentor(
    value="ero",
    definition="to do an action with something/someone else (object of verb as company or instrument in modified)",
    tag="[CAUSATIVE_PREFIX:ERO]",
    category="verb_transitivizer",
    ero_switch=True,
)  # TODO: Implement this properly
