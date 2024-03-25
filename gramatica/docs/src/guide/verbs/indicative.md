# Indicative Mood

The indicative mood is the most common. We are describing the happenings of reality.

The following chapter will lay out the steps to take in order to conjugate any root in the indicative mood.

<!-- ``` python
subj = (
    self.personal_inflections[subject_tense][1] + f"[SUBJECT:{subject_tense}]"
    if dir_subj_raw is None 
    else dir_subj_raw + f"[SUBJECT:{subject_tense}:DIRECT]"
)
pluriforme = ""
if self.pluriforme:
    if "3p" in subject_tense:
        pluriforme = f"s[PLURIFORM_PREFIX:S]-"
        subj = ""
    else:
        pluriforme = f"r[PLURIFORM_PREFIX:R]-"
vb =  f"{pluriforme}{self.verbete}[ROOT]"
result = f"{perm_suf[1]}{subj} {vb}"
if negative:
    result = self.negate_verb(result, mode)
``` -->
%n = Noun("ma\'enduar", 'remember - adj.');''%

## Second Class Verbs

Second class verbs recieve the following _subject prefixes_:

| Lema | Person | Prefix _(Pluriform)_ |
|------|-----------------|--------|
| I    | 1ps             |   %n.personal_inflections["1ps"][1]%(r)   |
| You  | 2ps            | %n.personal_inflections["2ps"][1]%(r)    |
| We _(Exclusive)_ | 1ppe    | %n.personal_inflections["1ppe"][1]%(r)  |
| We _(Inclusive)_ | 1ppi  | %n.personal_inflections["1ppi"][1]%(r)   |
| Ya'll | 2pp           | %n.personal_inflections["2pp"][1]%(r)     |
| They  | 3p            | %n.personal_inflections["3p"][1]%/(s)      |

::: warning
There is no **pro drop** form of second class verbs, these prefixes are _necessary_.

We will write these __"prefixes"__ as though they were **pronouns** due to orthographic convention, but it's important to note that they are inseperable from the root. This is why they are included in the [Negation](#negation) process, whereas the _subject pronouns_ of [first class roots](#first-class-verbs) are not. More on this later.
:::

### Uniform Roots

Given a uniform, second class root like **%n.verbete()%** _(to remember)_, we will conjugate it as follows:

| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps")%    |
| You  | 2ps           | %n.conjugate("2ps")%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe")%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi")%     |
| Ya'll | 2pp           | %n.conjugate("2pp")%       |
| They  | 3p            | %n.conjugate("3p")%        |

Nice Job! Super easy! 

### Pluriform Roots

Now let's look at a pluriform root, like **%n = Noun('akûaur', '(r, s) (xe) (v. da 2ª classe) - pubescer, passar a ter pêlos pubianos (VLB, II, 89)'); n.verbete()%** _(to go through puberty)_:

| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps")%    |
| You  | 2ps           | %n.conjugate("2ps")%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe")%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi")%     |
| Ya'll | 2pp           | %n.conjugate("2pp")%       |
| They  | 3p            | %n.conjugate("3p")%        |

::: tip
When a second class root is pluriform, add an **r-** prefix.
:::

::: warning
Notice how in the <Tooltip content="3rd Person (they/a'e/i/-î-/-îo-/s-/-s-/-îos-)">_3p_</Tooltip>, rather than a `personal pronoun + r-` we are getting a single `s-` which takes the place of the `i` pronoun used in the above uniform case. 
:::

It really is that easy! 

### Negation

Let's take a look at the _negated form_ real quick before we move onto first class verbs.

| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps", negative=True)%    |
| You  | 2ps           | %n.conjugate("2ps", negative=True)%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe", negative=True)%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi", negative=True)%     |
| Ya'll | 2pp           | %n.conjugate("2pp", negative=True)%       |
| They  | 3p            | %n.conjugate("3p", negative=True)%        |

#### Step 1 - First letter check

From the conjugated form _(%n.conjugate("1ps")%)_ we will add the negation prefix `n'` if the first letter is a <Tooltip content="%' '.join(n.vogais)%">vowel</Tooltip> or the semi-vowel `î`. Otherwise, the negation prefix will take the form of `na `, a negation particle. 

::: tip
We write `na` separate from the root out of convention, but the difference between the negation particle `na verb` and prefix `n'verb` is purely phonetic, they represent the same exact thing and are inseperable from the verb.
:::

#### Step 2 - Last letter check

1. If the last letter is `i` or `î`, it remains unchanged.

| Root | Afirmative | Negative | Translation |
|------|------|-----------------|----|
| %n = Noun("esaraî", "(r, s) (xe) (v. da 2ª classe) - 1) esquecer-se");n.verbete() + (f' ({n.pluriforme})' if n.pluriforme else '')% | %n.conjugate('1ps')% | %n.conjugate('1ps', negative=True)% | I didn't forgot |

2. If it's a <Tooltip content="%' '.join(n.vogais)%">vowel</Tooltip>, then we add on the suffix `-î`

| Root | Afirmative | Negative | Translation |
|------|------|-----------------|---|
| %n = Noun("emirekoe'õ", "(r, s) (v. da 2ª classe) - enviuvar, ser viúvo");n.verbete() + (f' ({n.pluriforme})' if n.pluriforme else '')% | %n.conjugate('2pp')% | %n.conjugate('2pp', negative=True)% | Ya'll aren't widows |


3. Otherwise, we add on the suffix `-i`

| Root | Afirmative | Negative | Translation |
|------|------|-----------------|---|
| %n = Noun("'atybak", "(xe) (v. da 2ª classe) - voltar o rosto para trás");n.verbete() + (f' ({n.pluriforme})' if n.pluriforme else '')% | %n.conjugate('3p')% | %n.conjugate('3p', negative=True)% | They don't turn their face back |


And there you have it, that's how you negate a second class verb in the indicative mood. Pat yourself on the back!

## First Class Verbs

First class verbs recieve the following __subject pronouns__ *(optional)* and __subject prefixes__ *(required)*:

| Lema | Person | Subject Pronoun | Subject Prefix |
|------|-----------------|--------|---|
| I    | 1ps             |  %n.personal_inflections["1ps"][0]% | %n.personal_inflections["1ps"][2]%-   |
| You  | 2ps            | %n.personal_inflections["2ps"][0]% | %n.personal_inflections["2ps"][2]%-    |
| We _(Exclusive)_ | 1ppe    | %n.personal_inflections["1ppe"][0]% | %n.personal_inflections["1ppe"][2]%-  |
| We _(Inclusive)_ | 1ppi  | %n.personal_inflections["1ppi"][0]% | %n.personal_inflections["1ppi"][2]%-   |
| Ya'll | 2pp           | %n.personal_inflections["2pp"][0]% | %n.personal_inflections["2pp"][2]%-     |
| They  | 3p            | %n.personal_inflections["3p"][0]% | %n.personal_inflections["3p"][2]%-      |


First class verbs are split between [intransitive](#intransitive-roots) and [transtitive](#transitive-roots) verbs. 

Simply put, there are roots which _syntactically_ take no object: ___(intransitive)___ 

```
%n = Noun("nhe'eng", "(v. intr.)"); n.conjugate("1ps")%
I speak
```

::: warning
Atlhough some verbs are _intransitive_, they can often be combined with _postpositions_ to serve the role of indirect objects. For example 
```
%n.conjugate("1ps", pro_drop=True)% i xupé
I spoke to them
```
This will be expanded upon in later chapters.
:::

There are also roots which **must** be accompanied by an object: ___(transitive)___ 

```
%n = Noun("aûsub", "(s) (v.tr.)"); n.conjugate("1ps", "3p", dir_obj_raw="mba'e")%
I love things
```

::: tip
In the above statement, the root **%n.verbete()%** must carry an object. If we want to use a generic object, we will use `mba'e` for things and `poro/moro` for people.
:::

### Intransitive Roots

First class intransitive roots in the indicative mood are even more straightforward than second class verbs, the syntax is just a bit different.

Given a uniform, first class root like **%n = Noun("ker", '(v. intr.)'); n.verbete()%** _(to sleep)_, we will conjugate it as follows:

| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps")%    |
| You  | 2ps           | %n.conjugate("2ps")%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe")%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi")%     |
| Ya'll | 2pp           | %n.conjugate("2pp")%       |
| They  | 3p            | %n.conjugate("3p")%        |


::: tip
There are no pluriform intransitive first class verbs :) there are _some_ irregular intransitive roots which are pluriform in their _nominal form (not verb form!)_ but we will discuss this further later. Don't worry about it for now!
:::


### Transitive Roots

::: tip
All transitive verbs are of the [first class](#first-class-verbs)!
:::
<!-- which means that **they will recieve the subject prefixes when the object is in the 3rd person**. This includes the reflexive and mutual object markers, _-îe- (-nhe-)_ and _-îo- (-nho-)_, respectively. -->

If you thought the [intransitive verbs](#intransitive-roots) were too easy to conjugate, then transitive verbs are about to give you a reality check! But don't worry, let's break down each possible case step-by-step:

#### 3p object, any subject

No matter which person-tense the subject may be in `(1p/2p/3p)`, if the object is in the <Tooltip content="3rd Person (they/a'e/i/-î-/-îo-/s-/-s-/-îos-)">_3p_</Tooltip> then the conjugation pattern will be ***very*** similar to the [intransitive first class verbs](#intransitive-roots). The main difference you'll notice below is that we insert an `-î-` in between the **subject prefix** and the **root**: %n = Noun('kutuk', '(v.tr.)');n.verbete()% _(to spear)_
```
%n.conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='anteposto', pro_drop=True)%
fish I-(it)-spear :literal
I speared a fish :translation
```

In Tupi Antigo, the **object** must always fill the space _directly to the left of the root_ `OV`. The _referential 3p object infix_ `-î- (–s-)` allows us to move the _direct object (pirá)_ more freely around the root without _technically_ breaking this rule. It's like a placeholder! A bit like _it_ in English, but not exactly. It takes some time to get used to, but you'll get the hang of _it_ 😄

##### Uniform roots

The following orders are permitted when the object is in the <Tooltip content="3rd Person (they/a'e/i/-î-/-îo-/s-/-s-/-îos-)">_3p_</Tooltip>:
| Verb Format | Type | Example |
|-------|-------|------|
| **[Object]** [Subject Prefix]-**[î]**-[Root] |Preverbal Object| %n.conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='anteposto')% |
| [Subject Prefix]-**[Object]**-[Root] |Incorporated Object| %n.conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='incorporado')% |
| [Subject Prefix]-**[î]**-[Root] **[Object]** |Postverbal Object| %n.conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='posposto')% |

::: warning
When the object is <Tooltip content="3rd Person (they/a'e/i/-î-/-îo-/s-/-s-/-îos-)">_3p_</Tooltip>, we must include `-î-` _(there are exceptions)_.

Notice in the **incorporated** form, we do not use the _referential 3p object infix_ `-î- (–s-)`. Because the _direct object_ is in it's space directly to the left of the root, the use of `-î-` is unnecessary _(and unpermitted)_

Roots with only one syllable will recieve the infix `-îo-` as a simple phonetic change to `-î-`, it does not change the meaning in this context. (i.e. %Noun('ká', '(-îo-) (v.tr.) - 1) quebrar ').conjugate('1ps', '3p')% - I broke them)

Do not confuse with the _mutual infix_ `–îo–` which will only be used when the subject and object are the same and plural. This concept will be explained further in later chapters. 

_a select few irregular verbs will recieve `-îos–` although this is not common._
:::

##### Pluriform roots

Let's take a look at the same thing with a pluriform root: %n = Noun('epîak', '(s) (v.tr.)');n.verbete()% _(to see)_

| Verb Format | Type | Example |
|-------|-------|------|
| **[Object]** [Subject Prefix]-**[î]**-[Root] |Preverbal Object| %n.conjugate(subject_tense="1ps", object_tense="3p", pro_drop=True, dir_obj_raw='pirá', pos='anteposto')% |
| [Subject Prefix]-**[Object]**-[Root] |Incorporated Object| %n.conjugate(subject_tense="1ps", object_tense="3p", pro_drop=True, dir_obj_raw='pirá', pos='incorporado')% |
| [Subject Prefix]-**[î]**-[Root] **[Object]** |Postverbal Object| %n.conjugate(subject_tense="1ps", object_tense="3p", pro_drop=True, dir_obj_raw='pirá', pos='posposto')% |

As you can see, in this case the only difference is that the `-î-` has a phonetic change to `-s-`. This does not change the meaning at all, they represent the same _referential 3p object infix_.

The following orders are permitted for the rest of the cases: %n = Noun('kutuk', '(v.tr.)');n.verbete()% _(to spear)_ _(object **not** in the 3rd person)_

<!-- Subject: Order
3p: OV/OVS/SOV
2p: OVS
1p: OV/SOV -->
| Subject | Order | Example |
|---------|-------|---|
| 3p      | OV / OVS / SOV | %n.conjugate(subject_tense="3p", object_tense="1ps", pro_drop=True)% / %n.conjugate(subject_tense="3p", object_tense="1ps", pro_drop=False)% / %n.conjugate(subject_tense="3p", object_tense="1ps", pro_drop=False, pos='posposto')% |
| 2p      | OVS | %n.conjugate(subject_tense="2ps", object_tense="1ps", pro_drop=False)% |
| 1p      | OV / SOV |  %n.conjugate(subject_tense="1ps", object_tense="2ps", pro_drop=True)% / %n.conjugate(subject_tense="1ps", object_tense="2ps", pro_drop=False)%  |

Let's go over each of these cases:

#### 3p subject, 1p or 2p object

In this case, it looks very similar to the [second class](#second-class-verbs) _subject prefixes_, although these same _personal pronouns_ will serve as _object prefixes_ in this transitive case.

The _subject_ can either go _before_ **(SOV)** or _after_ **(OVS)**.

Let's see **(OVS)** with a uniform root like: %n.verbete()% _(to spear)_

| English | Object Person | Example |
|------|-----------------|--------|
| Me    | 1ps            | %n.conjugate(subject_tense="3p", object_tense="1ps")%    |
| You  | 2ps           | %n.conjugate(subject_tense="3p", object_tense="2ps")%     |
| Us _(Exclusive)_ | 1ppe   | %n.conjugate(subject_tense="3p", object_tense="1ppe")%    |
| Us _(Inclusive)_ | 1ppi  | %n.conjugate(subject_tense="3p", object_tense="1ppi")%     |
| Ya'll | 2pp           | %n.conjugate(subject_tense="3p", object_tense="2pp")%       |

Now **(SOV)** with a pluriforme root like: %n = Noun('epîak', '(s) (v.tr.)');n.verbete()% _(to see)_

| English | Object Person | Example |
|------|-----------------|--------|
| Me    | 1ps            | %n.conjugate(subject_tense="3p", object_tense="1ps", pos="posposto")%    |
| You  | 2ps           | %n.conjugate(subject_tense="3p", object_tense="2ps", pos="posposto")%     |
| Us _(Exclusive)_ | 1ppe   | %n.conjugate(subject_tense="3p", object_tense="1ppe", pos="posposto")%    |
| Us _(Inclusive)_ | 1ppi  | %n.conjugate(subject_tense="3p", object_tense="1ppi", pos="posposto")%     |
| Ya'll | 2pp           | %n.conjugate(subject_tense="3p", object_tense="2pp", pos="posposto")%       |
