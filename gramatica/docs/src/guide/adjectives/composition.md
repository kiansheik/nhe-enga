# Composition

Sometimes instead of saying something like _That woman is **beautiful**_ we will say _She is a **beautiful woman**_.

| Tupi | English | Explanation |
|------|-----------------|--------|
| <root root="kunhã" /> <root root=i entryNumber=4 /> <root root='poranga' /> | (that) woman is beautiful | using the _"adjective"_ as a second class verb |
| <root root=i entryNumber=4 /> <root root="kunhã" /><root type=noun root='poranga' /> | She is a beautiful woman | using the _"adjective"_ in composition with the base noun to create a *new root* |

## Step-by-step Process

There are some rules to compositions which we need to take into account.

Let's define some terms for this process:

### Terminology

| Sounds Types     | Letters                 |
|------------------|-------------------------|
| Oral Consonants  | p b t s x k r gû û î ŷ  |
| Nasal Consonants | m n ng nh mb nd         |
| Tonic Oral Vowels      | á é í ý ó ú |
| Non-Tonic Oral Vowels      | a e i y o u |
| Nasal Vowels     | ã ẽ ĩ ỹ õ ũ             |
| Base root | Noun |
| Modifier root | Adjective |
| Base+Modifier | Composition |

### Steps

1.  If the base root ends in a <Tooltip content="tonic vowel">á é í ý ó ú</Tooltip>:    <root root=îuká /> __+__ <root root=katu />
    -  replace it with its <Tooltip content="non-tonic counterpart">a e i y o u</Tooltip>:    <root root=îuká type=compose adjective=katu />
1.  If there is an encounter of <Tooltip content="Oral Consonants">p b t s x k r gû û î ŷ</Tooltip>:    <root root=kutuk /> __+__ <root root=poxy />
    -  remove the base root's ending consonant:    <root root=kutuk type=compose adjective=poxy />
1.  If the base root ends in <Tooltip content="Any Consonant">p b t s x k r gû û î ŷ m n ng nh mb nd</Tooltip> and the modifier starts with a `'`_(glottal stop)_:  <root root=kutuk /> __+__ <root root="'anga" />
    -  remove the `'`_(glottal stop)_ from the modifier:    <root root=kutuk type=compose adjective="'anga" />
1.  If the base root ends with <Tooltip content="Any Nasal">m n ng nh mb nd ã ẽ ĩ ỹ õ ũ<</Tooltip> and the modifier starts with <Tooltip content="Any Consonant">p b t s x k r gû û î ŷ m n ng nh mb nd</Tooltip>
    1.  If the final vowel of the base root is not already marked with a `~`:   <root root=nhan /> __+__ <root root=mixyr />
        -   nasalize it:    <root root=nhan type=compose adjective="mixyr" />
    1.  If the `base root` ends in `nh`:  <root type=noun root="ky'ynha" /> __+__ <root root=mirĩ />  
        -   it becomes a `î`:    <root root="ky'ynha" type=compose adjective="mirĩ" />
    1.  If the `base root` ends in <Tooltip content="any other nasal consonant">m n ng mb nd</Tooltip>:   <root root="nhe'eng" /> __+__ <root root=mirĩ />
        -   delete it:    <root root="nhe'eng" type=compose adjective="mirĩ" />
    1.  If the modifier root does not already contain <Tooltip content="any nasals">m n ng nh mb nd ã ẽ ĩ ỹ õ ũ<</Tooltip>
        -  nasalize the first letter based on the following table, if needed:
    
        | Oral | Nasal | Base + Modifier | Composition |
        |------|-------|-----------------|-------------|
        | p    | mb    | <root root="nhe'eng" /> __+__ <root root="poxy" /> | <root root="nhe'eng" type=compose adjective="poxy" /> |
        | k    | ng    | <root root="nhe'eng" /> __+__ <root root="katu" /> | <root root="nhe'eng" type=compose adjective="katu" /> |
        | t    | nd    | <root root="nhe'eng" /> __+__ <root root="tinga" /> | <root root="nhe'eng" type=compose adjective="tinga" /> |
        | s    | nd    | <root root="nhe'eng" /> __+__ <root root="supi" /> | <root root="nhe'eng" type=compose adjective="supi" /> |

::: warning
`ting` does not become `nding` in composition because the nasal letter `ng` is already present in the root, so it will remain unchanged by the nasalization process.
:::

1.  Any other case is as simple as just sticking them together with no phonetic changes

That's composition!