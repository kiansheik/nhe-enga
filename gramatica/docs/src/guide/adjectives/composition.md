# Composition

Sometimes instead of saying something like _That woman is **beautiful**_ we will say _She is a **beautiful woman**_.

| Tupi | English | Explanation |
|------|-----------------|--------|
| <root root="kunhã" /> <root root=i entryNumber=4 /> <root root='poranga' /> | (that) woman is beautiful | using the _"adjective"_ as a second class verb |
| <root root=i entryNumber=4 /> <root root="kunhã" /><root type=noun root='poranga' /> | She is a beautiful woman | using the _"adjective"_ in composition with the base noun to create a *new root* |

There are some rules to compositions which we need to take into account


def compose(self, modifier):
        frame = inspect.currentframe()
        func_name = frame.f_code.co_name
        args, _, _, values = inspect.getargvalues(frame)
        args_str = ', '.join(f"{arg}={repr(values[arg])}" for arg in args if 'self' != arg)
        ret_noun = copy.deepcopy(self)
        ret_noun.aglutinantes[-1] = self
        vbt = ret_noun.verbete()
        vbt_an = ret_noun.verbete(anotated=True)
        mod_vbt = modifier.verbete()
        mod_vbt_an = modifier.verbete(anotated=True)
        # Define some useful groups
        vogais_orais = "á e é i í y ý o ó u ú".split(" ")
        vogais_nasais =  "ã ẽ ĩ ỹ õ ũ".split(" ")
        nasais = "m n ng nh mb nd".split(" ")
        consoantes = "p b t s k r gû û î ŷ".split(" ")

        if ends_with_any(vbt, vogais_orais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            start = self.remove_accent_last_vowel(start)
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{mod_vbt_an}"
        elif ends_with_any(vbt, nasais) and starts_with_any(mod_vbt, vogais_orais+vogais_nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{mod_vbt_an}"
        elif ends_with_any(vbt, nasais+consoantes) and starts_with_any(mod_vbt, ["'"]):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{mod_vbt_an[1:]}"
        elif ends_with_any(vbt, nasais) and starts_with_any(mod_vbt, consoantes+nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            semivogal = '' if start[-2:].lower() != 'nh' else 'î'
            start = remove_ending_if_any(start, nasais)
            second_last_letter = self.nasal_map.get(start[-1], start[-1])
            first_nasal = self.nasal_prefix_map.get(mod_vbt_an[0], mod_vbt_an[0]) if not self.is_nasal(mod_vbt) else mod_vbt_an[0]
            ret_noun.latest_verbete = f"{start[:-1]}{second_last_letter}{semivogal}[{parts[-1]}{first_nasal}{mod_vbt_an[1:]}"
        elif ends_with_any(vbt, vogais_nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            second_last_letter = self.nasal_map.get(start[-2], start[-2])
            first_nasal = self.nasal_prefix_map.get(mod_vbt_an[0], mod_vbt_an[0]) if not self.is_nasal(mod_vbt) else mod_vbt_an[0]
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{first_nasal}{mod_vbt_an[1:]}"
        elif ends_with_any(vbt, consoantes) and starts_with_any(mod_vbt, vogais_orais+vogais_nasais):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{mod_vbt_an}"
        elif ends_with_any(vbt, consoantes) and starts_with_any(mod_vbt, consoantes):
            parts = ret_noun.latest_verbete.split("[")
            start = "[".join(parts[:-1])
            start = remove_ending_if_any(start, consoantes)
            ret_noun.latest_verbete = f"{start}[{parts[-1]}{mod_vbt_an}"

        ret_noun.aglutinantes.append(ret_noun)
        ret_noun.recreate += f".{func_name}({args_str})"
        return ret_noun