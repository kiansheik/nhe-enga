import spacy


class TupiAntigo(spacy.language.Language):
    personal_inflections = {
        "1ps": ["ixé", "xe", "a"],
        "1ppi": ["îandé", "îandé", "îa"],
        "1ppe": ["oré", "oré", "oro"],
        "2ps": ["endé", "nde", "ere"],
        "2pp": ["pe'ẽ", "pe", "pe"],
        "3p": ["a'e", "i", "o"],
        "4p": ["asé", "asé", "o"],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def inflect_verb(self, verb, inflection):
        inf = self.personal_inflections[inflection]
        return f"{inf[0]} {inf[2]}{verb}"

class Verb:
    def __init__(self, verbete, verb_class, transitive, raw_definition):
        self.verbete = verbete  # The name of the verb in its dictionary form
        self.verb_class = verb_class  # Class of the verb (string)
        self.transitive = transitive  # Whether the verb is transitive (boolean)
        self.raw_definition = raw_definition  # Raw definition of the verb (string)

    def conjugate(self, person_tense='1ps'):
        # A simple conjugation function (you can expand this based on language rules)
        if self.verb_class == "adj.: ":
            return f"{TupiAntigo.personal_inflections[person_tense][1]} {self.verbete}"
        else:
            return "Invalid/Unimplemented tense"



if __name__ == "__main__":
    lang = TupiAntigo()
    # Example usage:
    verb_example = Verb("apysyk", "adj.: ", True, "gostar")
    print(lang.inflect_verb("nhe'eng", "1ppi"))
    print(verb_example.conjugate('1ps'))
    print(verb_example.conjugate('1ppi'))
    print(verb_example.conjugate('1ppe'))
    print(verb_example.conjugate('2ps'))
    print(verb_example.conjugate('2pp'))
    print(verb_example.conjugate('3p'))
    print(verb_example.conjugate('4p'))
