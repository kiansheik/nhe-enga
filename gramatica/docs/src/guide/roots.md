# Roots

In Tupi Antigo, it can often be unproductive to try to think of _"words of content"_ in terms of being inherently nouns or verbs. We will refer to the most basic form of lema in tupi by the word **Root**.

## Charectaristics of Roots

Each root has certain attributes about it which will affect the ways and places in which we can inflect and use this root. First of all, there are two types of conjugation classes:

### First Class

The first class verbs like <root root=ker /> _(to sleep)_ use these prefixes:

| Lema | Person | Subject Pronoun | Subject Prefix | Conjugation |
|------|--------|-----------------|----------------|-------------|
| I    | 1ps    | <py>n.personal_inflections["1ps"][0]</py>|<py>n.personal_inflections["1ps"][2]</py> | <py>n.conjugate("1ps")</py> |
| You  | 2ps    |<py>n.personal_inflections["2ps"][0]</py>|<py>n.personal_inflections["2ps"][2]</py>  | <py>n.conjugate("2ps")</py> |
| We _(Exclusive)_ | 1ppe |<py>n.personal_inflections["1ppe"][0]</py>|<py>n.personal_inflections["1ppe"][2]</py>| <py>n.conjugate("1ppe")</py>|
| We _(Inclusive)_ | 1ppi |<py>n.personal_inflections["1ppi"][0]</py>|<py>n.personal_inflections["1ppi"][2]</py> | <py>n.conjugate("1ppi")</py> |
| Y'all | 2pp   |<py>n.personal_inflections["2pp"][0]</py>|<py>n.personal_inflections["2pp"][2]</py>   | <py>n.conjugate("2pp")</py> |
| They  | 3p    |<py>n.personal_inflections["3p"][0]</py>|<py>n.personal_inflections["3p"][2]</py>    | <py>n.conjugate("3p")</py> |

### Second Class

Second class verbs are ___never transitive___. Verbs like <root root="ma'enduar" /> _(to remember)_ will recieve the following pronouns.

| Lema | Person | Prefix _(Pluriform)_ | Conjugation |
|------|-----------------|--------|-------------|
| I    | 1ps             |   <py>Noun.personal_inflections["1ps"][1]</py>(r)   | <py>n.conjugate("1ps")</py> |
| You  | 2ps            | <py>Noun.personal_inflections["2ps"][1]</py>(r)    | <py>n.conjugate("2ps")</py> |
| We _(Exclusive)_ | 1ppe    | <py>Noun.personal_inflections["1ppe"][1]</py>(r)  | <py>n.conjugate("1ppe")</py> |
| We _(Inclusive)_ | 1ppi  | <py>Noun.personal_inflections["1ppi"][1]</py>(r)   | <py>n.conjugate("1ppi")</py> |
| Y'all | 2pp           | <py>Noun.personal_inflections["2pp"][1]</py>(r)     | <py>n.conjugate("2pp")</py> |
| They  | 3p            | <py>Noun.personal_inflections["3p"][1]</py>/(s)      | <py>n.conjugate("3p")</py> |

    - An intransitive root _may_ be a second class verb, these recieving special treatment in regards to conjugation.


### Transitivity
    - A root can be either Transitive or Intransitive



### Pluriform
    - Any root may be what is called a _pluriform_ meaning that it will recieve specific prefixes governed based on it's class of plurformality.

These concepts will be discussed in further detail in later sections, feel free to skip around :)
