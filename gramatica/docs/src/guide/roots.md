# Roots

In Tupi Antigo, it can often be unproductive to try to think of _"words of content"_ in terms of being inherently nouns or verbs. We will refer to the most basic form of lema in tupi by the word **Root**.

## Charectaristics of Roots

Each root has certain attributes about it which will affect the ways and places in which we can inflect and use this root. 

### Transitivity

A root can be either __Transitive__ or __Intransitive__.

When a verb is transitive, it accepts an object. 

| **Subject** | **Verb** | **Object** |
|-------------|----------|------------|
| <root root=Ixé />         | <root type=verb root=aûsub proDrop=true subjectTense=1ps objectTense=3p />  | <root root="a'e" entryNumber=2 />        |
| I           | love     | him        |

When a verb is intransitive, it does not accept an object.

| **Subject** | **Verb** | **Object** |
|-------------|----------|------------|
| <root root=Ixé />         | <root type=verb root=nhan proDrop=true subjectTense=1ps />  | ø       |
| I           | ran     | ø        |

What does that look like in practice? Well, it means that __transitive__ verbs _someone or something_ to recieve the action. On the other hand, __intransitive__ verbs are more independent; they can happen with only a subject involved.

### First Class (Active)

Tupi Antigo is considered to have an *Active/Stative* split by many academics. This means that there is a difference between a verb of action, which we refer to as _first class verbs_. First class verbs may be transitive or intransitive, meaning they may accept an object or not. 

The first class verbs like <root root=ker /> _(to sleep)_ use these prefixes:

| Lema | Person | Subject Pronoun | Subject Prefix | Conjugation | Translation |
|------|--------|-----------------|----------------|-------------|-------------|
| I    | 1ps    | <py>n.personal_inflections["1ps"][0]</py>|<py>n.personal_inflections["1ps"][2]</py> | <py>n.conjugate("1ps")</py> | I slept |
| You  | 2ps    |<py>n.personal_inflections["2ps"][0]</py>|<py>n.personal_inflections["2ps"][2]</py>  | <py>n.conjugate("2ps")</py> | You slept |
| We _(Exclusive)_ | 1ppe |<py>n.personal_inflections["1ppe"][0]</py>|<py>n.personal_inflections["1ppe"][2]</py>| <py>n.conjugate("1ppe")</py>| We _(not you)_ slept |
| We _(Inclusive)_ | 1ppi |<py>n.personal_inflections["1ppi"][0]</py>|<py>n.personal_inflections["1ppi"][2]</py> | <py>n.conjugate("1ppi")</py> | We all slept |
| Y'all | 2pp   |<py>n.personal_inflections["2pp"][0]</py>|<py>n.personal_inflections["2pp"][2]</py>   | <py>n.conjugate("2pp")</py> | You all slept |
| They  | 3p    |<py>n.personal_inflections["3p"][0]</py>|<py>n.personal_inflections["3p"][2]</py>    | <py>n.conjugate("3p")</py> | They slept |

### Second Class (Stative)

:::tip
Second class verbs are ___never transitive___. 
:::

Verbs like <root root="ma'enduar" /> _(to remember)_ are stative, meaning they are always intransitive and describe a state _(often like adjectives)_. Second class verbs will recieve the following pronouns:

| Lema | Person | Prefix _(Pluriform)_ | Conjugation | Translation |
|------|-----------------|--------|-------------|-------------|
| I    | 1ps             |   <py>Noun.personal_inflections["1ps"][1]</py>(r)   | <py>n.conjugate("1ps")</py> | I remember |
| You  | 2ps            | <py>Noun.personal_inflections["2ps"][1]</py>(r)    | <py>n.conjugate("2ps")</py> | You remember |
| We _(Exclusive)_ | 1ppe    | <py>Noun.personal_inflections["1ppe"][1]</py>(r)  | <py>n.conjugate("1ppe")</py> | We _(not you)_ remember |
| We _(Inclusive)_ | 1ppi  | <py>Noun.personal_inflections["1ppi"][1]</py>(r)   | <py>n.conjugate("1ppi")</py> | We all remember |
| Y'all | 2pp           | <py>Noun.personal_inflections["2pp"][1]</py>(r)     | <py>n.conjugate("2pp")</py> | You all remember |
| They  | 3p            | <py>Noun.personal_inflections["3p"][1]</py>/(s)      | <py>n.conjugate("3p")</py> | They remember |

### Pluriform
Any root may be what is called a _pluriform_ meaning that it will recieve specific prefixes governed based on it's class of plurformality.

| **Pluriform Type** | **_Absolute_** | **_Possession_** | **_3p_** |
|--------------------|----------------|------------------|----------|
| _None_             |              ø |                ø |        ø |
| _(r, s)_           |              ø |               r- |       s- |
| _(t)_              |             t- |               r- |       s- |
| _(t, t)_           |             t- |               r- |       t- |
| _(s, r, s)_        |             s- |               r- |       s- |

In addition to these pluriforms, some roots which begin with `p-` in the possessive and 3p cases will shift to `m-` in the absolute cases:

| **_Possessive_** | **_Absolute_**    |
|------------------|-------------------|
| xe porombo'esara |     morombo'esara |
| My teacher       | Teacher _(in general)_ |

## Conclusion

These concepts will be discussed in further detail in later sections, feel free to skip around :)
