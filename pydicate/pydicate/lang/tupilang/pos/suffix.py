"""Attested size suffixes as composable predicate pieces."""

from .noun import Noun


class SizeSuffix(Noun):
    """A Navarro augmentative or diminutive, attached with ``base / suffix``.

    The spelling in ``value`` remains explicit: -ûasu and -gûasu are distinct
    editorial choices, even though Navarro cross-references them.
    """

    FORMS = {"-ûasu", "-gûasu", "-usu", "-'ĩ", "-ĩ", "mirĩ"}

    def __init__(self, value, definition=""):
        if value not in self.FORMS:
            raise ValueError("SizeSuffix requires an attested size-suffix form")
        super().__init__(
            value, definition=definition, category="size_suffix", tag="[SIZE_SUFFIX]"
        )

    def attach(self, base):
        from .verb import Verb

        if not isinstance(base, (Noun, Verb)) or isinstance(base, SizeSuffix):
            raise TypeError("size suffix requires a noun or verb base")
        stem = base.verbete
        if not isinstance(stem, str) or not stem or " " in stem:
            raise ValueError("size suffix requires a single lexical stem")
        ending = self.verbete.removeprefix("-")
        if ending in {"'ĩ", "ĩ"}:
            if stem[-1] in "aeiouyáéíóúâêîôûãẽĩõũỹ":
                if stem.endswith("a"):
                    stem = stem[:-1]
            if stem[-1] not in "aeiouyáéíóúâêîôûãẽĩõũỹ":
                ending = "ĩ"
        elif ending == "usu" and stem[-1] in "aeiouyáéíóúâêîôûãẽĩõũỹ":
            raise ValueError(
                "-usu is the consonant-stem variant; choose -ûasu or -gûasu"
            )
        elif ending in {"ûasu", "gûasu"} and stem[-1] not in "aeiouyáéíóúâêîôûãẽĩõũỹ":
            raise ValueError("-usu is the attested variant after a consonant stem")
        result = base.copy()
        result.compositions.append(self)
        result.refresh_verbete(stem + ending)
        return result
