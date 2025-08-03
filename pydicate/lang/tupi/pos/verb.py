from ....predicate import Predicate
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Verb as TupiVerb
from tupi import Noun as TupiNoun
from .noun import pronoun_verbetes
from .adverb import Adverb
from .y_fix import YFix
import gzip, json

# load /Users/kian/code/nhe-enga/docs/dict-conjugated.json.gz into an object
with gzip.open("/Users/kian/code/nhe-enga/docs/dict-conjugated.json.gz", "rt") as f:
    dict_conjugated = [x for x in json.load(f) if "c" in x.keys()]


class Verb(Predicate):
    def __init__(self, value=None, verb_class="", definition="", vid=None):
        """Initialize a Verb object."""
        super().__init__(
            verbete=value,
            category="verb",
            min_args=1,
            max_args=2,
            definition=definition,
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
        self.mood = "indicativo"

    def raw_noun(self):
        """Return the noun form of the verb."""
        return TupiNoun(self.verbete, self.definition)

    def subject(self):
        return self.arguments[0]

    def object(self):
        return self.arguments[1]

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
                if infl0:  # if the verb has a personal inflection then it's a pronoun
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
                if infl0:
                    retval = self.verb.conjugate(
                        anotar=annotated,
                        subject_tense=infl0,
                        mode=self.mood,
                        negative=self.negated,
                        pro_drop=suj.pro_drop,
                    )
                else:
                    retval = self.verb.conjugate(
                        anotar=annotated,
                        subject_tense="3p",
                        dir_subj_raw=arg0,
                        mode=self.mood,
                        negative=self.negated,
                        pro_drop=suj.pro_drop,
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
            return self.raw_noun().substantivo(annotated)
        if len(self.arguments) < 2:
            if self.verb.transitivo:
                obj_tense = self.arguments[0].inflection()
                obj = self.arguments[0].eval(annotated=annotated) if self.arguments[0].category != "pronoun" else None
                subj_tense = None
                subj = None
            else:
                obj_tense = "3p"
                obj = None
                subj_tense = self.arguments[0].inflection()
                subj = self.arguments[0].eval(annotated=annotated) if self.arguments[0].category != "pronoun" else None
        else:
            obj_tense = self.arguments[1].inflection()
            obj = self.arguments[1].eval(annotated=annotated) if self.arguments[1].category != "pronoun" else None
            subj_tense = self.arguments[0].inflection()
            subj = self.arguments[0].eval(annotated=annotated) if self.arguments[0].category != "pronoun" else None
        nom = self.verb.conjugate(
            subject_tense=subj_tense if subj_tense else "3p",
            object_tense=obj_tense,
            dir_obj_raw=obj,
            dir_subj_raw=subj,
            mode="nominal",
            pos="anteposto",
            pro_drop=self.arguments[0].pro_drop or not subj_tense,
            negative=False,
            anotar=annotated,
        )
        return TupiNoun(nom, self.definition)


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

    def indicative(self):
        for adj in self.pre_adjuncts:
            if isinstance(adj, Adverb):
                return "circunstancial"
            if isinstance(adj, Verb):
                if len(adj.arguments) == 2:
                    # Gerund does not force circumstancial mood
                    if adj.subject() != self.subject():
                        return "circunstancial" 
        return "indicativo"

só = Verb("só", definition="to go")
aûsub = Verb("aûsub", definition="to love")