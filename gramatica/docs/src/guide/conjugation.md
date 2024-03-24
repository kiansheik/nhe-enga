# Conjugation

In English, we generally follow a **SVO _(subject-verb-object)_**:
``` python
I stab you
S V    O
```

In Tupi Antigo, we will always follow **OV _(object-verb)_** at a minumum. The language is pro-drop, meaning the subject may be ommitted when the context is clear enough to allow it. 

``` python
%Noun('kutuk', '(v.tr.)').conjugate(subject_tense='1ps', object_tense='2ps', pro_drop=True)%
O  V
```

Here, `oro-` is a <Tooltip content="2nd Person Singular (you/endé/nde/oro-)">_2ps_</Tooltip> object prefix _(nde)_. Given this prefix, the subject pronoun will always be <Tooltip content="1st Person (I/we/xe/oré)">_1p_</Tooltip>.

Depending on the context, this can mean `I stab you (%Noun('kutuk', '(v.tr.)').conjugate(subject_tense='1ps', object_tense='2ps', pro_drop=False)%)` or `We stab you (%Noun('kutuk', '(v.tr.)').conjugate(subject_tense='1ppe', object_tense='2ps', pro_drop=False)%)`

::: warning
It cannot be _îandé_ becuase it would be strange to include the object of the oration as a subject as well. Perhaps this semi-reflexivity is possible in poetry, but we will ignore such forms in this text. 
:::

### Moving onto the next section... 
There are **2 classes** when it comes to using roots as verbs in Tupi Antigo. The first class can be thought of as "action verbs" while the second class can be thought of as "stative verbs". These are just general concepts to help guide your understanding, we will elaborate more on those later. 

## First Class Verbs

Verbs in the first class are conjugated with the following _(optional)_ **Subject Pronouns** and **Subject prefixes**:

| Lema | Subject Pronoun | Prefix |
|------|-----------------|--------|
| I    | Ixé             | a-     |
| You  | Endé            | ere-   |
| He   | A'e             | o-     |
| We _(Exclusive)_ | Oré    | oro- |
| We _(Inclusive)_ | Îandé  | îa-  |
| Ya'll | Pe'ẽ           | pe-    |
| They  | A'e            | o-     |

### Transitive Verbs

::: tip
**All transitive verbs are of the first class** which means that **they will recieve the subject prefixes when the object is in the 3rd person**. This includes the reflexive and mutual object markers, _-îe- (-nhe-)_ and _-îo- (-nho-)_, respectively.
:::

The subject prefix is always required for first class verbs.

One quirk of Tupi Antigo is the 3rd person object pronoun _-î- (–s-)_. When the object is 3rd person, we must always _(there are exceptions)_ include the referential object pronoun _(unless we incorporate it between the prefix and the root)_. In this case, the pattern of **SVO _(subject-verb-object)_** is possible, because the object pronoun _-î- (–s-)_ is fulfilling the space to the left of the verb **S-î-V**, allowing the raw direct object to come either before the verb (**SOV**) or after (**SVO**).



In these cases, the following orders are permitted: _(object in the 3rd person)_
| Verb Format | Type | Example |
|-------|-------|------|
| **[Object]** [Subject Prefix]-**[î]**-[Root] |Preverbal Object| %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='anteposto')% |
| [Subject Prefix]-**[Object]**-[Root] |Incorporated Object| %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='incorporado')% |
| [Subject Prefix]-**[î]**-[Root] **[Object]** |Postverbal Object| %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="1ps", object_tense="3p", dir_obj_raw='pirá', pos='posposto')% |

In all other cases (often called _nominal cases_ by others), the object must always precede the verb. The following orders are permitted for the given subjects: _(object **not** in the 3rd person)_

<!-- Subject: Order
3p: OV/OVS/SOV
2p: OVS
1p: OV/SOV -->
| Subject | Order | Example |
|---------|-------|---|
| 3p      | OV / OVS / SOV | %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="3p", object_tense="1ps", pro_drop=True)% / %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="3p", object_tense="1ps", pro_drop=False)% / %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="3p", object_tense="1ps", pro_drop=False, pos='posposto')% |
| 2p      | OVS | %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="2ps", object_tense="1ps", pro_drop=False)% |
| 1p      | OV / SOV |  %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="1ps", object_tense="2ps", pro_drop=True)% / %Noun('kutuk', '(v.tr.)').conjugate(subject_tense="1ps", object_tense="2ps", pro_drop=False)%  |

A transitive root will always recieve an object upon conjugation or noun-creation. Nouns and verbs of transitives roots may be pro-drop in regards to the subject of the root, but the object is always necessary. 

## Second Class Verbs

::: tip
Second class verbs are always intransitive
:::