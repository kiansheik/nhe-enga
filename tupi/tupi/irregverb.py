from .verb import Verb


class IrregVerb(Verb):
    """
    Class for irregular verbs in Tupi language.
    """

    def __str__(self):
        return f"Irregular Verb: {self.verbete}"
