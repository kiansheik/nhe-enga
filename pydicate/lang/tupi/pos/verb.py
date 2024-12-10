from ....predicate import Predicate
import sys

sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Verb as TupiVerb


class Verb(Predicate):
    def __init__(self, value, verb_class="", definition=""):
        """Initialize a Verb object."""
        super().__init__(verbete=value, category="verb", min_args=1, max_args=2, definition=definition)
        self.verb = TupiVerb(value, verb_class, self.definition)

    def subject(self):
        if self.verb.transitivo:
            return self.arguments[0]

    def refresh_verbete(self, new_verbete):
        self.verbete = new_verbete
        self.verb = TupiVerb(self.verbete, self.verb.verb_class, self.definition)

    def eval(self, mood="indicativo"):
        """Evaluate the Verb object."""
        retval = ""
        arglen = len(self.arguments)
        if mood == "indicativo":
            mood = self.indicative()
        if arglen == 0:
            retval = self.verb.verbete
        elif arglen == 1:
            obj = self.arguments[0]
            arg0 = None if obj.pro_drop else obj.eval()
            infl0 = obj.inflection()
            if self.verb.transitivo:
                # TODO: render "nominal form"
                if infl0:  # if the verb has a personal inflection then it's a pronoun
                    retval = self.verb.conjugate(
                        "3p", infl0, pro_drop=True, mode=mood, negative=self.negated
                    )
                else:  # otherwise it's a direct object
                    retval = self.verb.conjugate(
                        "3p",
                        "3p",
                        dir_obj_raw=arg0,
                        pro_drop=True,
                        mode=mood,
                        negative=self.negated,
                    )
            else:  # intransitive
                suj = self.arguments[0]
                if infl0:
                    retval = self.verb.conjugate(
                        infl0, mode=mood, negative=self.negated, pro_drop=suj.pro_drop
                    )
                else:
                    retval = self.verb.conjugate(
                        "3p",
                        dir_subj_raw=arg0,
                        mode=mood,
                        negative=self.negated,
                        pro_drop=suj.pro_drop,
                    )
        elif arglen == 2:  # transitive
            suj = self.arguments[0]
            obj = self.arguments[1]
            arg0 = suj.eval()
            infl0 = suj.inflection()
            arg1 = None if obj.pro_drop else obj.eval()
            infl1 = obj.inflection()
            obj_delocated = ""
            if obj.category == "conjunction":
                arg1 = None
                obj_delocated = None if obj.pro_drop else obj.eval()
            retval = self.verb.conjugate(
                infl0,
                infl1,
                dir_subj_raw=arg0,
                dir_obj_raw=arg1,
                mode=mood,
                negative=self.negated,
                pro_drop=suj.pro_drop,
            )
            if obj_delocated:
                retval = retval + " " + obj_delocated
        # deal with adverbs
        # We need to know if the adverb was added before the verb or after: `go * Noun("Endé") + Adverb("koritei")` or `Adverb("koritei") + go * Noun("Endé")`
        for adj in self.pre_adjuncts:
            retval = adj.eval() + " " + retval
        for adj in self.post_adjuncts:
            retval = retval + " " + adj.eval()
        return retval

    # first arg is the subject, second arg is the object

    def __repr__(self):
        return f"Verb({self.verbete})"

    def indicative(self):
        if self.pre_adjuncts:
            return "circunstancial"
        return "indicativo"
