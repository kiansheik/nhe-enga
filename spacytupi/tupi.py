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

    def conjugate(self, person_tense='1ps', object_tense='3p', mode='indicativo', pos='posposto', pro_drop=False):
        # A simple conjugation function (you can expand this based on language rules)
        if self.verb_class in ["adj.: "]:
            result = f"{TupiAntigo.personal_inflections[person_tense][1]} {self.verbete}"
        if self.verb_class in ["(v. intr.)"]:
            subj = TupiAntigo.personal_inflections[person_tense][0] if not pro_drop else ''
            result = f"{subj} {TupiAntigo.personal_inflections[person_tense][2]}-{self.verbete}"
        elif self.verb_class in ["(v.tr.)"]:
            if pos not in ['posposto', 'incorporado', 'anteposto']:
                raise Error("Postposition Not Valid")
            if object_tense in TupiAntigo.personal_inflections.keys():
                if object_tense == '3p':
                    subj = TupiAntigo.personal_inflections[person_tense][0] if not pro_drop else ''
                    pref = TupiAntigo.personal_inflections[person_tense][2]
                    dir_obj = TupiAntigo.personal_inflections['3p'][0]
                    if pos == 'posposto':
                        result = f"{subj} {pref}-î-{self.verbete} {dir_obj}"
                    elif pos == 'anteposto':
                        result = f"{subj} {dir_obj} {pref}-î-{self.verbete}"
                    elif pos == 'incorporado':
                        result = f"{subj} {pref}-î-{self.verbete}"
                if object_tense == == 
        else:
            return "Invalid/Unimplemented tense"
        return result.strip()



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
