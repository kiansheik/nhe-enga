import spacy


class TupiAntigo(spacy.language.Language):
    personal_inflections = {
        "1ps": ["ixé", "xe", "a"],
        "1ppi": ["îandé", "îandé", "îa"],
        "1ppe": ["oré", "oré", "oro"],
        "2ps": ["endé", "nde", "ere", "oro", "îepé"],
        "2pp": ["pe'ẽ", "pe", "pe", "opo", "peîepé"],
        "3p": ["a'e", "i", "o"],
        # "4p": ["asé", "asé", "o"],
    }

    ipa_map = {'Obstruintes': 'p pʷ pʲ β t s sʷ k kʷ ʔ',

'Soantes': 'm mʷ n r ɲ ŋ mb mbʷ nd ndʷ ŋɡ ŋɡʷ w w j',

'Vogais': 'a ɛ i ɨ ɔ u ã ɛ̃ ĩ ɨ̃ ɔ̃ ũ',

'Obstruintes-graf': 'p pû pî b t s sû k kû ‘',

'Soantes-graf': 'm mû n r nh ng mb mbû nd ndû ng ngû gû û î',

'Vogais-graf': 'a e i y o u ã ẽ ĩ ỹ õ ũ'}

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

    def conjugate(self, subject_tense='1ps', object_tense='3p', dir_obj_raw=None, mode='indicativo', pos='anteposto', pro_drop=False, io_pref=False):

        # A simple conjugation function (you can expand this based on language rules)
        if self.verb_class in ["adj.: "]:
            result = f"{TupiAntigo.personal_inflections[subject_tense][1]} {self.verbete}"
        if self.verb_class in ["(v. intr.)"]:
            subj = TupiAntigo.personal_inflections[subject_tense][0] if not pro_drop else ''
            result = f"{subj} {TupiAntigo.personal_inflections[subject_tense][2]}-{self.verbete}"
        elif self.verb_class in ["(v.tr.)", '(s) (v.tr.)']:
            if pos not in ['posposto', 'incorporado', 'anteposto']:
                raise Error("Postposition Not Valid")
            if object_tense in TupiAntigo.personal_inflections.keys():
                if object_tense == subject_tense:
                    subj = TupiAntigo.personal_inflections[subject_tense][1] if not pro_drop else ''
                    result = f"{subj} {TupiAntigo.personal_inflections[subject_tense][2]}-{'îe' if not io_pref else 'îo'}-{self.verbete}"
                elif '3p' in object_tense:
                    subj = TupiAntigo.personal_inflections[subject_tense][0] if not pro_drop else ''
                    pref = TupiAntigo.personal_inflections[subject_tense][2]
                    dir_obj = TupiAntigo.personal_inflections['3p'][0] if dir_obj_raw is None else dir_obj_raw
                    pluriforme = 's' if self.verb_class == '(s) (v.tr.)' else 'î'
                    if pos == 'posposto':
                        result = f"{subj} {pref}-{pluriforme}-{self.verbete} {dir_obj}"
                    elif pos == 'anteposto':
                        result = f"{subj} {dir_obj} {pref}-{pluriforme}-{self.verbete}"
                    elif pos == 'incorporado':
                        result = f"{subj} {pref}-{pluriforme if dir_obj_raw is None else dir_obj}-{self.verbete}"
                if '2p' in object_tense:
                    if '1p' in subject_tense:
                        subj = TupiAntigo.personal_inflections[subject_tense][1] if not pro_drop else ''
                        obj = TupiAntigo.personal_inflections[object_tense][3]
                        result = f"{subj} {obj}-{self.verbete}"
                if '1p' in object_tense:
                    if '2p' in subject_tense:
                        subj = TupiAntigo.personal_inflections[subject_tense][4]
                        obj = TupiAntigo.personal_inflections[object_tense][1]
                        pluriforme = 'r-' if self.verb_class == '(s) (v.tr.)' else ''
                        result = f"{obj} {pluriforme}{self.verbete} {subj}"
                if '2p' in object_tense or '1p' in object_tense:
                    if '3p' in subject_tense or '4p' in subject_tense:
                        subj = TupiAntigo.personal_inflections[subject_tense][0] if dir_obj_raw is None else dir_obj_raw
                        obj = TupiAntigo.personal_inflections[object_tense][1]
                        pluriforme = 'r-' if self.verb_class == '(s) (v.tr.)' else ''
                        result = f"{obj} {pluriforme}{self.verbete} {subj}"
        else:
            return "Invalid/Unimplemented tense"
        print(f"({subject_tense} -> {object_tense}):",
                "\t",
                result.strip().replace('-', ''))
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
