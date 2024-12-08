from ....predicate import Predicate
import sys
sys.path.append("/Users/kian/code/nhe-enga/tupi")
from tupi import Verb as TupiVerb

class Verb(Predicate):
    def __init__(self, value, verb_class="", define=""):
        """Initialize a Verb object."""
        super().__init__(verbete=value, category="verb", min_args=1)
        self.verb = TupiVerb(value, verb_class, define)

    def eval(self):
        """Evaluate the Verb object."""
        arglen = len(self.arguments)
        if arglen == 0:
            return self.verb.verbete
        elif arglen == 1: # intransitive
            arg0 = self.arguments[0].eval()
            infl0 = ""
            for val, infl in self.verb.personal_inflections.items():
                if arg0.lower() in infl:
                    infl0 = val
                    break
            if self.verb.transitivo:
                # TODO: render "nominal form"
                if infl0: # if the verb has a personal inflection then it's a pronoun
                    return self.verb.conjugate("3p", infl0, pro_drop=True)
                else: # otherwise it's a direct object
                    return self.verb.conjugate("3p", "3p", dir_obj_raw=arg0, pro_drop=True)
            else: # intransitive
                if infl0:
                    return self.verb.conjugate(infl0)
                else:
                    return self.verb.conjugate("3p", dir_subj_raw=arg0)

        return self.verb.verbete
    
    # first arg is the subject, second arg is the object


    def __repr__(self):
        return f"Verb({self.verbete})"

