import unicodedata
from .tupi import TupiAntigo

nasal_prefix_map = {
    "p": "mb",
    "k": "ng",
    "t": "nd",
    "s": "nd",
}

class AnnotatedString:
    def __init__(self, annotated: str):
        self.original = annotated
        self._rebuild_maps()

    def _rebuild_maps(self):
        self.clean = ""
        self.map_clean_to_annotated = []
        i = 0
        while i < len(self.original):
            if self.original[i] == "[":
                while i < len(self.original) and self.original[i] != "]":
                    i += 1
                i += 1  # skip the closing ']'
            else:
                self.map_clean_to_annotated.append(i)
                self.clean += self.original[i]
                i += 1

    def __getitem__(self, key):
        if isinstance(key, int):
            if key < 0:
                key += len(self.clean)
            if key < 0 or key >= len(self.clean):
                raise IndexError("Index out of range")
            i = self.map_clean_to_annotated[key]
            return self.original[i]
        elif isinstance(key, slice):
            indices = self.map_clean_to_annotated[key]
            if not indices:
                return ""
            start = indices[0]
            end = indices[-1] + 1
            return self.original[start:end]
        else:
            raise TypeError("Invalid argument type")

    def __str__(self):
        return self.original

    def __repr__(self):
        return f"AnnotatedString({self.original!r})"

    def __len__(self):
        return len(self.clean)

    def get_clean(self):
        return self.clean

    def get_annotated(self):
        return self.original
    
    def verbete(self, annotated=False):
        """Return the verbete of the annotated string."""
        if annotated:
            return self.original
        return self.clean

    def endswith(self, suffix):
        return self.clean.endswith(suffix)

    def startswith(self, prefix):
        return self.clean.startswith(prefix)

    def replace(self, old, new):
        start = self.clean.find(old)
        if start == -1:
            return False
        end = start + len(old)
        i1 = self.map_clean_to_annotated[start]
        i2 = self.map_clean_to_annotated[end - 1] + 1
        self.original = self.original[:i1] + new + self.original[i2:]
        self._rebuild_maps()
        return True

    def insert_prefix(self, prefix):
        self.original = prefix + self.original
        self._rebuild_maps()

    def insert_suffix(self, suffix):
        self.original += suffix
        self._rebuild_maps()

    def replace_clean(self, start: int, length: int = 1, replacement: str = ""):
        clean_len = len(self.clean)

        # Normalize negative start
        if start < 0:
            start += clean_len
        if not (0 <= start <= clean_len):
            raise IndexError(f"Invalid start index: {start}")

        # Normalize length
        if length is None:
            end = clean_len
        else:
            end = start + length
            if not (0 <= end <= clean_len):
                raise IndexError(f"Invalid length: {length}")

        # Map to annotated string indices
        annotated_start = (
            self.map_clean_to_annotated[start]
            if start < clean_len
            else len(self.original)
        )
        annotated_end = self.map_clean_to_annotated[end - 1] + 1

        # Replace in original
        self.original = (
            self.original[:annotated_start]
            + replacement
            + self.original[annotated_end:]
        )
        self._rebuild_maps()

    def remove_accent_last_vowel(self):
        vowels = "áéíýóú"
        # Check if the last character is an accented vowel
        if self[-1] in vowels:
            # Remove the accent from the last vowel
            self.replace_clean(-1, 1, TupiAntigo.accent_map[self[-1]])
        return self

    def accent_last_vowel(self):
        vowels = "aeiyou"
        # Check if the last character is a vowel
        if self[-1] in vowels:
            # Accent the last vowel
            accented = self[-1] + "́"
            normalized = unicodedata.normalize("NFC", accented)
            self.replace_clean(-1, 1, normalized)
        return self

    def nasaliza_final(self):
        # Check if the last character is an accented vowel
        if self[-1] in TupiAntigo.nasal_map.keys():
            # Remove the accent from the last vowel
            self.replace_clean(-1, 1, TupiAntigo.nasal_map[self[-1]])
        return self
    
    def nasaliza_prefixo(self):
        if self[0] in nasal_prefix_map.keys():
            return self.replace_clean(0, 1, nasal_prefix_map[self[0]])
        return self

    def remove_ending_if_any(self, endings):
        for ending in endings:
            if self.endswith(ending):
                self.replace_clean(-len(ending), len(ending), "")
                # exit the loop after the first match
                return self
        return self
