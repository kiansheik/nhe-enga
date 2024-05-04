# Introduction

Nouns in Tupi Antigo, much like verbs and adjectives, are just different inflections and uses of the same roots.

## Phonetic Considerations

In Tupi Antigo, there are two possible root endings:

### Root Forms

| <Tooltip content="vowel (not -a)"><py>' '.join([x for x in Noun.vogais if x != 'a'])</py></Tooltip> | <tConsonants/> |
|-----------------|------------|
| <root type=root root="îuká" /> | <root type=root root="ker" /> |

:::warning
Nouns in tupi must ___always___ end in a <tVowels/>. If the root ends in a consonant, we add `-a`.
:::

### Noun Forms

| <Tooltip content="vowel (not -a)"><py>' '.join([x for x in Noun.vogais if x != 'a'])</py></Tooltip> | <tConsonants/> |
|-----------------|------------|
| <root type=noun root="îuká" /> | <root type=noun root="ker" /> |

You can see that between the __root form__ and the __noun form__, <root type=noun root="îuká" /> is identical but <root type=root root="ker" /> becomes <root type=noun root="ker" />.

## Transitive Considerations

A big difference between these two roots other than their phonetic qualities is the fact that <root type=root root="îuká" /> is ___transitive___ whilst <root type=root root="ker" /> is not.

So if we say `xe kera` then that means something like _my sleep_, it can be thought of as a _possessive_ or a _subject-marking_ relationship because there is no object space to the left of an intransitive root like <root type=root root="ker" />.

This means that <root type=absolute root="ker"  /> is a valid _absolute noun_, but <root type=noun root="îuká" /> alone is not, because it is missing an _object_. It leaves us wondering, _"murder ___of what?"____

On the other hand, if I say `xe îuká` then it is not indicating possession or marking a subject, but rather an __object__. _I am_ what is _being murdered_. This is because transitive roots ___necessarily___ will have their object _directly to the left_ of them at __all times__. 

:::tip
It can even be helpful to write it fixed like `xeîuká` if that helps to conceptualize how stuck together the object and the transitive root are.
:::

Now, if I want to use possession or agency with a __transitive__ root, as long as we know what the object is, we can still do it the same way. You can tell the difference between the verb forms and the noun forms here: 

| Noun | English | Verb | English |
|------|-------|----------|--------|
| `nde xeîuká` | _your murder of me_ | `xeîuká îepé` | _you murdered me_ |
| `xe ndeîuká` | _my murder of you_ | `xe oroîuká` | _I murdered you_ |

<!-- # Basic Nominalizing Suffix (-a)

The most basic form of a noun will be referred to as the _Basic Nominalizing Suffix_. This will take the form as either `-a` or `-ø`, as shown above -->
