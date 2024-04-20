# Introduction

Nothing in Tupi Antigo is _strictly_ an adjective but __almost anything__ can be used as one. Second class verbs will imply the verbs _to have_ and _to be_ when we used them in conjunction with the personal perfixes

# Second Class Verbs

Many other Tupinistas refer to second class verbs as _stative verbs_ or _descriptive verbs_. That is, they are verbs which describe the state of someone/something rather than an action. As a result of this, when we translate them into Portuguese or English, we often end up using adjectives in their place. Therefore, when you use an adjective in Tupi, you are really just using a second class verb. Let me show you some examples:

## Roots ending in -a

::: warning
Do not confuse the dictionary entries that are nouns `(s.)` with the dictionary entries which indicate a pluriform transitive verb `(s)`. The only difference is a period unfortunately.
:::

If a dictionary entry ends with a non-tonic `a` _(meaning the stress is __not__ on the last vowel)_ then it can be used as a second class verb by removing the `-a` noun suffix:

Let's see what that looks like with <root root=rana /> _(rude thing/rustic thing)_:

| English | Person | Example |
|------|-----------------|--------|
| I _(am)_ rude | 1ps            |<py>n.conjugate("1ps")</py>   |
| You _(are)_ rude | 2ps           |<py>n.conjugate("2ps")</py>    |
| We _(are)_ rude  _(excl.)_ | 1ppe   |<py>n.conjugate("1ppe")</py>   |
| We _(are)_ rude  _(incl.)_ | 1ppi  |<py>n.conjugate("1ppi")</py>    |
| Y'all _(are)_ rude | 2pp           |<py>n.conjugate("2pp")</py>      |
| They _(are)_ rude | 3p            |<py>n.conjugate("3p")</py>       |

Now if we put the `-a` suffix which turns roots into nouns back, this statement becomes possesive:

| English | Person | Example |
|------|-----------------|--------|
| My rudeness | 1ps            |<py>n.possessive(person="1ps").substantivo()</py>   |
| Your rudeness | 2ps           |<py>n.possessive(person="2ps").substantivo()</py>    |
| Our rudeness  _(excl.)_ | 1ppe   |<py>n.possessive(person="1ppe").substantivo()</py>   |
| Our rudeness  _(incl.)_ | 1ppi  |<py>n.possessive(person="1ppi").substantivo()</py>    |
| Y'all's rudeness | 2pp           |<py>n.possessive(person="2pp").substantivo()</py>      |
| Their rudeness | 3p            |<py>n.possessive(person="3p").substantivo()</py>       |



## Vowel ending nouns (s.)

If a root ends with a <tVowels/> _(excluding a non-tonic `a`)_ then it can be used directly as a second class verb without changing it at all from the noun form. Likewise when you see a second class verb or adjective in the dictionary, you do not need to change it to make it a noun if it follows this phonetic pattern.

::: warning
This means that the following phrases are ambiguous without more context. We rely on context heavily for disambiguity, especially in languages which were not traditionally written.
:::

Let's see what that looks like with <root root=aruru /> _(sadness)_:

| English | Person | Example |
|------|-----------------|--------|
| I _(am)_ sad / My sadness   | 1ps            |<py>n.conjugate("1ps")</py>   |
| You _(are)_ sad / Your sadness  | 2ps           |<py>n.conjugate("2ps")</py>    |
| We _(are)_ sad / Our sadness _(excl.)_ | 1ppe   |<py>n.conjugate("1ppe")</py>   |
| We _(are)_ sad / Our sadness _(incl.)_| 1ppi  |<py>n.conjugate("1ppi")</py>    |
| Y'all _(are)_ sad / Y'all's sadness | 2pp           |<py>n.conjugate("2pp")</py>      |
| They _(are)_ sad / Their sadness | 3p            |<py>n.conjugate("3p")</py>       |

## Composition

Sometimes instead of saying something like _That woman is **beautiful**_ we will say _She is a **beautiful woman**_.

| Tupi | English | Explanation |
|------|-----------------|--------|
| <root root="kunhã" /> <root root=i entryNumber=4 /> <root root='poranga' /> | (that) woman is beautiful | using the _"adjective"_ as a second class verb |
| <root root=i entryNumber=4 /> <root root="kunhã" /><root type=noun root='poranga' /> | She is a beautiful woman | using the _"adjective"_ in composition with the base noun to create a *new root* |


