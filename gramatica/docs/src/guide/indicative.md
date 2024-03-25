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

## Second Class Verbs

### Uniform Roots

Given a second class root like **%n = Noun("ma\'enduar", 'remember - adj.'); n.verbete()%**, we will conjugate it as follows:

| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps")%    |
| You  | 2ps           | %n.conjugate("2ps")%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe")%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi")%     |
| Ya'll | 2pp           | %n.conjugate("2pp")%       |
| They  | 3p            | %n.conjugate("3p")%        |

### Pluriform Roots

Super easy! Now let's look at a pluriforme root, like **%n = Noun('akûaur', '(r, s) (xe) (v. da 2ª classe) - pubescer, passar a ter pêlos pubianos (VLB, II, 89)'); n.verbete()%**:


| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps")%    |
| You  | 2ps           | %n.conjugate("2ps")%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe")%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi")%     |
| Ya'll | 2pp           | %n.conjugate("2pp")%       |
| They  | 3p            | %n.conjugate("3p")%        |

::: tip
When a second class root is also pluriform, we will add an **r-** prefix. 
:::

::: warning
Notice how in the <Tooltip content="3rd Person (they/a'e/i/-î-/-îo-/s-/-s-/-îos-)">_3p_</Tooltip>, rather than a `personal pronoun + r-` we are getting a single **s-** which takes the place of the **i** pronoun used in the above uniform. 
:::

### Negation

It really is that easy! Let's take a look at the _negated form_ real quick before we move on to first class verbs.

| English | Person | Example |
|------|-----------------|--------|
| I    | 1ps            | %n.conjugate("1ps", negative=True)%    |
| You  | 2ps           | %n.conjugate("2ps", negative=True)%     |
| We _(Exclusive)_ | 1ppe   | %n.conjugate("1ppe", negative=True)%    |
| We _(Inclusive)_ | 1ppi  | %n.conjugate("1ppi", negative=True)%     |
| Ya'll | 2pp           | %n.conjugate("2pp", negative=True)%       |
| They  | 3p            | %n.conjugate("3p", negative=True)%        |

#### Step 1 - First letter check

From the conjugated form (%n.conjugate("1ps")% ) we will add on the negation prefix `n'` if the first letter is a <Tooltip content="%' '.join(n.vogais)%">vowel</Tooltip> or the semi-vowel `î`. Otherwise, the negation prefix will take the form of `na `, a negation particle. 

::: tip
We write this separately out of convention, but the difference between the negation particle and prefix is purely phonetic, they represent the same exact thing.
:::

#### Step 2 - Last letter check

1. If the last letter is `i` or `î`, it remains unchanged.

| Root | Afirmative | Negative |
|------|------|-----------------|
| %n = Noun("esaraî", "(r, s) (xe) (v. da 2ª classe) - 1) esquecer-se");n.verbete() + (f' ({n.pluriforme})' if n.pluriforme else '')% | %n.conjugate('1ps')% | %n.conjugate('1ps', negative=True)% |

2. If it's a <Tooltip content="%' '.join(n.vogais)%">vowel</Tooltip>, then we add on the suffix `-î`

| Root | Afirmative | Negative |
|------|------|-----------------|
| %n = Noun("emirekoe'õ", "(r, s) (v. da 2ª classe) - enviuvar, ser viúvo");n.verbete() + (f' ({n.pluriforme})' if n.pluriforme else '')% | %n.conjugate('2pp')% | %n.conjugate('2pp', negative=True)% |


3. Otherwise, we add on the suffix `-i`

| Root | Afirmative | Negative |
|------|------|-----------------|
| %n = Noun("'atybak", "(xe) (v. da 2ª classe) - voltar o rosto para trás");n.verbete() + (f' ({n.pluriforme})' if n.pluriforme else '')% | %n.conjugate('3p')% | %n.conjugate('3p', negative=True)% |


And there you have it, that's how you negate a second class verb in the indicative mood. Pat yourself on the back!