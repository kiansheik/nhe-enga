import random
from pydicate.lang.tupilang import *
from pydicate.lang.tupilang.pos import *
from pydicate import Predicate
from tqdm import tqdm


# one line random hash function
rhash = lambda x: sum([ord(c) for c in str(x)])
from graphviz import Digraph


def build_graphviz(predicate, graph=None, parent_name=None, edge_label=None):
    """
    Recursively builds a Graphviz graph from a Predicate structure.
    :param predicate: The root Predicate or LinguisticElement object.
    :param graph: The Graphviz Digraph object being constructed.
    :param parent_name: The name of the parent node.
    :return: A Graphviz Digraph object representing the predicate tree.
    """
    if graph is None:
        graph = Digraph(format="png")
        graph.attr(rankdir="TB")  # Set tree to vertical (Top-to-Bottom) by default
        graph.attr(
            label=predicate.eval(),
            labelloc="t",
            fontsize="24",
            fontname="Helvetica-Bold",
        )

    if parent_name is None:
        parent_name = "Root"
        graph.node(parent_name, label=f"IP")
    # Generate a unique name for the current node
    node_name = (
        f"{predicate.category}_{predicate.verbete}_{rhash(predicate)}"
        if isinstance(predicate, Predicate)
        else predicate.verbete
    )

    # Add the current node to the graph
    label = (
        f"{predicate.category}\n{predicate.verbete}"
        if isinstance(predicate, Predicate)
        else predicate.verbete
    )
    label += "\n(NEG)" if predicate.negated else ""
    graph.node(node_name, label=label, parent_name="Root")

    # Connect the current node to its parent
    if parent_name is not None:
        graph.edge(parent_name, node_name, label=edge_label)

    # Add adjuncts as children
    if isinstance(predicate, Predicate):
        with graph.subgraph() as s:
            s.attr(rank="same")  # Adjuncts on the same rank as Predicate
            for adjunct in predicate.pre_adjuncts:
                adj_name = f"Pre_Adjunct_{adjunct.eval()}_{rhash(adjunct)}"
                label = f"{adjunct.category}\n{adjunct.eval()}"
                label += "\n(NEG)" if adjunct.negated else ""
                graph.node(adj_name, label=label)
                # graph.edge(parent_name, adj_name)  # Connect adjunct to the parent node
                s.edge(
                    adj_name,
                    node_name,
                    label="+",
                    # decorate="true",
                    arrowhead="none",
                    # style="invis"  # Removes the line under the "+" sign
                )
        # Recursively add arguments
        for i, arg in enumerate(predicate.arguments):
            build_graphviz(arg, graph, parent_name=node_name, edge_label=f"Arg {i+1}")

        with graph.subgraph() as s:
            s.attr(rank="same")  # Adjuncts on the same rank as Predicate
            for adjunct in predicate.post_adjuncts:
                adj_name = f"Post_Adjunct_{adjunct.eval()}_{rhash(adjunct)}"
                label = f"{adjunct.category}\n{adjunct.eval()}"
                label += "\n(NEG)" if adjunct.negated else ""
                graph.node(adj_name, label=label)
                # graph.edge(parent_name, adj_name)  # Connect adjunct to the parent node
                s.edge(
                    node_name,
                    adj_name,
                    label="+",
                    # decorate="true",
                    arrowhead="none",
                    constraint="false",
                    # style="invis"  # Removes the line under the "+" sign
                )

    return graph


prompt = """
The following has a passage which is in tupi, but annotated grammatically,
then you see the same structure of the sentence below in a hierarchical way, 
recursively representing a syntax tree of the sentence before it, with english glosses 
for each part as the node values, with both arguments and adjuncts represented with +. 
There are multiple sentences pertaining to the same narrative. 
Interpret each of these into an english story, choosing the best word to represent the meaning and structures. 
Do not get creative and pay attention to context, try to make the most adequate English interpretation possible.
"""
# # Example usage
# and_predicate = Conjunction("abé",) * abá * ixé + Adverb("nhõ")


# and_predicate_1 = Conjunction("abé",) * Noun("Pedro") * Noun("Pindobasu")

# and_and_predicate = Conjunction("abé") * and_predicate * and_predicate_1
# # print(and_predicate)
# print()
# print(and_and_predicate.eval())

# go = Verb("só")
# print(go.eval())  # só

# igo = go * ixé
# print(igo.eval())  # ixé asó

# yougo = go * endé
# print(yougo.eval())  # endé eresó

# yougo = go * endé + Adverb("koritei")
# print(yougo.eval())  # endé eresó koritei

# yougo_circ = Adverb("koritei") + go * endé
# print(yougo_circ.eval())  # koritei endé eresó

# hego = go * ~ae + Adverb("koritei")
# print(hego.eval())  # a'e osó koritei

# hego_circ = Adverb("koritei") + go * ~ae
# print(hego_circ.eval())  # koritei i sóû

# want = Verb("potar", "v.tr.", definition="to want")

# ver = Verb("epîak", "v.tr. (s)", definition="to see")

# tl = ver * ixé * endé << go * ixé
# print(tl.eval())  # ixé endé epîak só

# ver_circ = ~-go / want * ixé >> -ver * +ixé * endé
# print(ver_circ.eval())  # ixé endé epîak só


# ver_circ = endé * koty + ixé * -go + sosé * ixé
# print(ver_circ.eval())  # ixé endé epîak só


# euepedro = (abé * Noun("Pedro") * ixé)
# me_n_pedro = -ver * (endé * euepedro)
# print(me_n_pedro.eval()) # Mateus sees Pedro
# vergo =  Noun("Mateus") == Noun("Pedro")
# vergo_neg =  Noun("Mateus") != Noun("Pedro")
# print("ble: ", (vergo).eval())

# build_graphviz(hego).render("and_predicate1", view=True)
# build_graphviz(hego_circ).render("and_predicate_circ1", view=True)

# print("Let's write a story in Tupi!\n\n")

arakae = Adverb(
    "araka'e", definition="a long time ago, distant past", tag="[ADVERB:DISTANT_PAST]"
)
rakae = Adverb(
    "raka'e", definition="a long time ago, distant past", tag="[ADVERB:DISTANT_PAST]"
)
kunumim = Noun("kunum˜i", definition="young boy")
ikó = Verb("ikó", definition="to live")
taba = Noun("taba", definition="village")
irun = Noun("ir˜u", definition="friend")
era = Noun("er", definition="(t); name")

pindo = ProperNoun("Pindoba Mirĩ")
pedro = ProperNoun("Pedro")
love = Verb("aûsub", definition="to love")
kunhatai = Noun("kunhataĩ", definition="young girl")
abét = Adverb("abé", definition="also, as well")
ara = Noun("'ara", definition="day, light, sunlight, time, period, era")
ekar = Verb("ekar", definition="to search, to seek, to look for")
só = Verb("só", definition="to go, to leave, to travel")
îuká = Verb("îuká", definition="to murder, to kill, to slay")
monhang = Verb(
    "monhang", definition="to do, to make, to create, to cause, to perform, to commit"
)
mongetá = Verb("mongetá", definition="to talk, to converse, to speak with")
kanhem = Verb("kanhem", definition="to disappear, to vanish, to lose oneself")
oka = Noun("oka", definition="(t); house, home, dwelling, abode, residence")
lost = bae * kanhem
potar = Verb("potar", definition="to want, to desire, to wish for")
kaa = Noun("ka'a", definition="(t); forest, jungle, woods, bush, thicket")
opá = Adverb(
    "opá", definition="everything, all, whole, entire, complete", tag="[ADVERB:ALL]"
)
basem = Verb("basem", definition="to find, to discover, to encounter")
mboryb = Verb("mboryb", definition="to please, to delight, to satisfy")
eté = Adverb(
    "eté",
    definition="true, real, genuine, authentic, very good, more, better",
    tag="[ADVERB:TRUE]",
)
apé = Noun("apé", definition="(s, r, s) path, way, road, route")
epenhan = Verb("epenhan", definition="to attack, to assault, to fight with")
îagûara = Noun(
    "îagûara",
    definition="jaguar, onça, onça-pintada, large wild cat of the Americas, also means dog in some contexts",
)
îebyr = Verb("îebyr", definition="to return, to come back, to go back")
epîak = Verb("epîak", definition="to see, to look at, to watch, to observe")
atã = Noun("atã", definition="(t) strong, brave, firm, hard, tough, rigid, arduous")
gûarinin = Noun("gûarinin", definition="war, warfare, battle, warrior, soldier")
ur = Verb("îur", definition="to come")
poî = Verb("poî", definition="to feed, to nourish, to sustain")
# 'i / 'é1 (v. intr. irreg.) 1) dizer: Marã e'ipe asé, karaibebé o arõana mongetábo? - Que a gente diz, conversando com o anjo seu guardião? (Ar., Cat., 23v); Aîpó eré supikatu... - Isso dizes com razão... (Anch., Teatro, 32); 2) rezar, enunciar-se, prescrever: Aîpó tekoangaîpaba robaîara nã e'i. - Os opostos daqueles pecados assim se enunciam. (Ar., Cat., 18); 3) querer dizer, querer significar, pensar, supor, presumir, cogitar, julgar: Marã e'ipe asé o py'ape aîpó o'îabo i xupé? - Que quer dizer a gente em seu coração, dizendo isso para ela? (Ar., Cat., 31v); "Osó ipó re'a" a'é. - Presumo que ele deve ter ido. (VLB, II, 86); 4) concluir, julgar por indícios: Emonã ûĩ re'a a'é. - Concluo que talvez isso seja assim. (VLB, II, 16); Amõ îuká-potá ûĩ sekóû a'é. - Concluí que ele está querendo matar alguém. (VLB, II, 16) ● e'iba'e - o que diz: Mendara... "xe mena koîpó xe remirekó re'õ ré t'îamendar îandé îoesé" e'iba'e, se'õ nhẽ roîré nd'e'ikatuî sesé omendá. - O cônjuge que diz: "-Após a morte de meu marido ou de minha esposa havemos de nos casar", após sua morte não pode casar-se com ele (ou ela). (Ar., Cat., 1686, 279-280); 'îara (ou e'îara) - o que diz; o indicador: Îaîuká memẽ aîpó 'îara... - Matemos juntos o que diz isso. (Ar., Cat., 79); ...Îasytatá serekoarama resé... pé 'îaramo i xupé... - Por causa da estrela sua guardiã,... como indicadora do caminho para eles. (Ar., Cat., 3); ...Marã e'îara... - As que dizem coisas más. (Anch., Teatro, 36); "...-Our temõ anhanga xe rerasóbo mã" e'îara. - O que diz: -Oxalá venha o diabo para me levar... (Ar., Cat., 67); 'îaba (ou 'eaba ou 'esaba) - 1) tempo, lugar, modo, etc. de dizer; o dizer: Okaî oupa aûîeramanhẽ... o îurupe nhote aîpó o 'eagûera repyramo. - Estão queimando para sempre como pena de dizerem isso somente em suas bocas. (Ar., Cat., 1686, 248); 2) o que alguém diz, o chamado por alguém, o dito: Ybytyra Monte Calvário 'îápe... - Para o monte chamado Calvário (Ar., Cat., 89); Erimba'epe aîpó nde 'îaba ereîmopóne? - Quando cumprirás isso que tu dizes? (Ar., Cat., 111v); O'u nhẽpe a'e 'ybá, tegûama, Tupã 'îaba? - Comeu aquele fruto, causa da morte, que Deus dissera? (Ar., Cat., 40v); Aîpó i 'eagûera rerekóbo, semimbo'e-etá... miapé rari o pópe... - Tendo isso que ele disse, seus discípulos tomaram o pão em suas mãos. (Ar., Cat., 84v)
ei = Verb(
    "'i",
    definition="to say, to tell, to speak, to indicate, to mean, to conclude, to judge",
)
er = Verb("er", verb_class="(s) (adj.)", definition="to have a name")
pdb = +(pindo * abé * pedro)

pedro_and_pindoba = [
    arakae + ((pe * taba) + (ikó * (amõ * kunumim))),
    (kunumim * era) == pedro,
    pe * (pedro * taba) + ikó * (amõ * kunhatai) + abét,
    pindo == (kunhatai * era),
    love * pedro * pindo,
    love * pindo * pedro + abét,
    amõ * ara * pupé + (pedro * só) << (pedro * ekar * pindo),
    (lost == pindo) + é,
    amo * lost + (pindo * ikó),
    pupé * (opá + kaa) + (pedro * ekar * pindo),
    (iré * (mosapyr + ara)) + ((pedro * ekar * pindo) >> +pedro * basem + (ae * supé)),
    ((pindo * abé * pedro) * (mboryb) * îo) << ((pindo * abé * pedro) * epîak * îo),
    (((ae * apé) * pe + te) + (îebyr * pdb)) >> ((amõ * îagûara) * epenhan * +pdb),
    (amo * (gûarinin)) + (pedro * îuká * (aîpó * îagûara)),
    (sara) * (pedro * îuká * (îagûara)) == pedro,
    # Aîur ta xe poî na ûi'îabo ruã. - Venho não tendo a intenção de que me alimentem. (Anch., Arte, 55v)
]

# COMPENDIO DA DOUTRINA
# CHRISTÄA Na lingua Portugueza, e Brasilica.
# PRIMEIRA PARTE
# . Dos primeiros elementos da Fé Christãa.
# Oração dofinal da Santa Cruz.

santa_cruz = ProperNoun("Santa Cruz")
tupan = ProperNoun("Tupã")
aang = Verb("a'ang")
pysyro = Verb("pysyrõ")
îara = Noun("îara")
amotar = Verb("amotar")
tb = Conjunction("", tag="[CONJUNCTION:AND]")
tuba = Noun("uba", "pai")
tayra = Noun("a'yra", "filho")
espirito_santo = ProperNoun("Espírito Santo")
amen = Interjection(
    "amém", definition="so be it, truly, let it be", tag="[INTERJECTION:AMEN]"
)
jesus = ProperNoun("Jesus")
ybaka = Noun("ybaka")
moeté = Verb("moeté")
reino = Noun(
    "Reino", definition="kingdom, realm, dominion", tag="[NOUN:LOAN_WORD:PORTUGUESE]"
)
yby = Noun("yby", definition="earth, land, ground, soil, country, world")
u = Verb("'u")
iabiõ = Postposition("îabi'õ", "each, every", tag="[POSTPOSITION:EVERY]")
meeng = Verb("me'eng")
nheeng = Verb("nhe'eng")
kori = Adverb("kori")
nhyron = Verb("nhyrõ", "adj.")
angaipaba = Noun("angaîpaba")
erekomemûã = Verb("erekomemûã")
ar = Verb("'ar")
ukar = Verb("ukar")
tentação = Noun("tentação")
mbae = Noun("mba'e")
aiba = Noun("aíba")
obaîtin = Verb("obaît˜i")
ykyyra = Noun("yky'yra")
eõ = Verb("manõ")
poreaûsub = Verb(
    "poreaûsub", definition="sad, forlorn, mourn", verb_class="(2ª classe)"
)
tyb = Verb("tyb")
bebé = Verb("bebé")
okendabok = Verb("okendabok")
gûyrá = Noun("gûyrá")
pab = Verb("pab", verb_class="(v.tr)", definition="to rear, animal husbandry")
Enza = ProperNoun("Enza")
iké = Verb("iké")

tom_story = [
    ((tyb + rakae) * gûyrá),
    (emi * (xe * pab)) == ae,
    (Enza) == (bae * er),
    (ae * (okendabok * Enza)) << (+Enza * bebé),
]

avemaria = ProperNoun("Ave Maria")
santamaria = ProperNoun("Santa Maria")
graça = Noun(
    "graça", definition="grace, favor, blessing", tag="[NOUN:LOAN_WORD:PORTUGUESE]"
)
ynysema = Noun("ynysema")
mombeu = Verb("mombe'u")
kunhã = Noun("kunhã")
katu = Noun("katu")
membyra = Noun("membyra")
sy = Noun("sy")
tupãmongetá = Verb("tupãmongetá")
koyr = Adverb("ko'yr")
irã = Adverb("irã")
îekyî = Verb("îekyî")
îub = Verb("îub")
béno = Adverb("béno")
erobîar = Verb("erobîar")

salve_rainha = ProperNoun("Salva Rainha")
poraûsubara = Noun("poraûsubara")
ikobé = Verb("ikobé")
een = Noun("e'ẽ")
salve = Interjection("salve", definition="hail", tag="[INTERJECTION:HAIL]")
sapukai = Verb("sapukaî")
pea = Verb("pe'a")
eva = ProperNoun("Eva")
nheangerur = Verb("nhe'angerur")
poasema = Noun("poasema")
îaseo = Verb("îase'o")

bettendorff_compendio_pt_1 = [
    # Santa Cruz
    ((saba * (santa_cruz * aang)) * esé)
    + (endé * (pysyro.imp()) * oré)
    + ((tupan == (oré * îara.voc())))
    + ((sara * (-(oré * amotar))) * suí),
    (((tuba + tayra + espirito_santo) * era) * pupé),
    (amen + jesus),
    # Pai nosso
    (oré * tuba).voc() @ (((pe * ybaka)) + (sara * ikó).voc())
    + (amo * (pyra * moeté))
    + (ikó * (nde * era)).perm(),
    (ur * (nde * reino)).perm(),
    (monhang * (emi * (potar * nde)) * îe).perm()
    + (pe * yby)
    + (pe * ybaka)
    + (îabé * (monhang * ae * îe)),
    (((emi * (u * oré)) @ (nduara * (ara * iabiõ))) * (meeng * +endé)).imp()
    + kori
    + (oré * supé),
    ((nde * nhyron).imp() + (oré * angaipaba * esé) + (oré * supé))
    + (îabé * ((((sara * (erekomemûã * oré))) * supé) + (oré * nhyron))),
    (endé * -(mo * (ar / ukar)).imp() * oré) + (tentação * pupé),
    ((oré * ((pysyro * endé))).imp() << te) + ((mbae / aiba) * suí),
    (amen + jesus),
    # Ave Maria
    Copula() * avemaria * (bae * ((esé * graça) + v(ynysema))),
    (amo * (nde * irun)) + (ikó * (îandé * îara)),
    (amo * (pyra * (mombeu / katu))) + (ikó * +endé) + (kunhã * suí),
    Copula() * ((pyra * (mombeu / katu)) + abé) * (Copula() * (nde * membyra) * jesus),
    (Copula() * santamaria * (tupan * sy))
    + (+endé * tupãmongetá).imp()
    + (esé * (Copula() * oré * (bae * v(angaipaba))))
    + koyr
    << (irã + ((îub * oré) >> (îekyî * oré)) << béno),
    (amen + jesus),
    # salva rainha
    (Copula() * (salve_rainha == (poraûsubara * sy)) + ikobé.base_nominal(True))
    + (bae * v(een))
    + (saba * (oré * erobîar * îe))
    + (salve),
    (nde * supé)
    + (+oré * sapukai.redup()).circ(False)
    + (amo * (pyra * pea))
    + (amo * (eva * membyra)),
    (nde * supé) + ((+oré * nheangerur.circ(False)) << (oré * v(poasema)))
    << (+oré * îaseo),
]


# make sure first lines of bettendorf match this
bettendorf_ground_truth = """Santa Cruzra'angaba resé orépysyrõ îepé Tupã oré îar oréamotare'ymbara suí.

tuba ta'yra Espírito Santo rera pupé.

amém Jesus.

oré rub ybakype tekoar imoetépyramo toîkó nde rera.

tour nde Reino.

toîemonhang nde remimotara ybype ybakype i îemonhanga îabé.

oré rembi'u 'ara îabi'õndûara eîme'eng kori orébo.

ndenhyrõ oré angaîpaba resé orébo orérerekomemûãsara supé orénhyrõ îabé.

orémo'arukar umẽ îepé tentação pupé.

orépysyrõte îepé mba'eaíba suí.

amém Jesus.

Ave Maria graça resé tynysemba'e.

nde irũnamo îandé îara rekóû.

imombe'ukatupyramo ereikó kunhã suí.

imombe'ukatupyra abé nde membyra Jesus.

Santa Maria Tupã sy etupãmongetá oré iangaîpaba'e resé ko'yr irã oré îekyî oré rúmebéno."""

# split into lines

bettendorf_ground_truth_lines = bettendorf_ground_truth.split("\n")
# clean empty lines
bettendorf_ground_truth_lines = [
    x.strip()[:-1] for x in bettendorf_ground_truth_lines if x.strip()
]
for i, line in enumerate(bettendorf_ground_truth_lines):
    if bettendorff_compendio_pt_1[i].eval().strip() != line:
        print(f"Line {i+1} does not match:")
        print(f"Expected: {line}")
        print(f"Got:      {bettendorff_compendio_pt_1[i].eval()}")
        print()


switch_ref = [
    (ixé * nheeng) << (ixé * só),
    (ixé * nheeng) << (nde * só),
    (ixé * só) >> (+ixé * obaîtin * (endé * ykyyra)),
    ((nde * tuba) * eõ) >> (+xe * poreaûsub.circ(False)),
]


# Marakaîá nda sepyme'engymbyrama ruã, kûépe é asé oîar tenhẽ, pokémon îabé.

epymeeng = Verb("epyme'eng", definition="to pay for, to buy")
marakaîá = Noun("marakaîá", definition="a cat")
tenhen = Adverb(
    "tenh˜e",
    definition="in vain, for nothing, for free",
    tag="[ADVERB:IN_VAIN]",
)
pokémon = ProperNoun("Pokémon")
asé = Noun(
    "asé", definition="We, people in general, all of us", tag="[PRONOUN:UNIVERSAL_WE]"
)
îar = Verb("îar", definition="to capture, to catch")
kûépe = Adverb("kûépe", definition="from far away", tag="[ADVERB:FROM_DISTANCE]")

amb = amõamõ * abá
nã = Adverb("nã", definition="like that", tag="[ADVERB]")
# Amõ abá e'i marakaîá repyme'enga? Nd'aîmo'ãngi nã sekó!
moang = Verb("mo'ang", definition="to imagine")

emerson_saying = [
    ((amb * ei) << peQ) << (amb * epymeeng * marakaîá),
    -(+ixé * moang) * (nã + (ae * ikó)),
    Copula() * marakaîá * ~(rama * (pyra * (epymeeng * ae))),
    (kûépe + é) + (((asé * îar * ae) + tenhen) + (pokémon * îabé)),
]

sistema = Noun(
    "sistema", definition="system, method, scheme", tag="[NOUN:LOAN_WORD:PORTUGUESE]"
)
erekó = Verb("erekó")
ekobîara = Noun("ekobîara")
kuab = Verb("kuab")

nosf = ((amo * (asé * ekobîara))) + ((og * ikó))

mateus_saying = [
    (Copula() * (nde * sistema) * (rama * ((îandé * ekobîara)))) + é,
    # Oîkuab umã asé rekobîáramo o ekorama
    ((+ae * kuab) << umã) * (rama * nosf.base_nominal(True)),
]

frases = bettendorff_compendio_pt_1
output = []
for frase in frases:
    output.append(f"{frase.eval(annotated=False)}.")
output.append("")
# for frase in frases:
#     output.append(f"{frase.eval(annotated=True)}.")
# output.append("")
# for frase in frases:
#     output.append(f"{frase.semantic()}")

result_string = "\n\n".join(output)
print(result_string)

# [print(x.translation_prompt('Portuguese')) for x in frases]

# print(switch_ref[-1].to_forest_tree())

# breakpoint()
# from translate.generate_glosses import get_ai_response

# response = get_ai_response(result_string, prompt)

# print(response)

# from pydicate.dbexplorer import NavarroDB

# db = NavarroDB()
# # aggregate the nouns with '(s.)'
# raw_nouns = db.filter_words_by_definition("s.")
# finished_nouns = []
# for raw_noun in raw_nouns:
#     for prefix in ["mi", "emi", "temi", "tembi", "mbi", "embi", "(e)mi", "(e)mbi"]:
#         if raw_noun.verbete.startswith(prefix):
#             new_vtb = raw_noun.verbete[len(prefix) :]
#             verb = Verb(new_vtb)
#             new_noun = +emi * verb
#             new_noun.definition = raw_noun.definition
#             new_noun.functional_definition = new_noun.definition
#             new_noun.gloss = Noun(
#                 raw_noun.verbete, definition=new_noun.definition
#             ).gloss
#             finished_nouns.append(new_noun)
#             break

# random.shuffle(finished_nouns)
ker = Verb("ker")
pytá = Verb("pytá")
inv = Verb("in")
tu_dorm = (nde * ker) << (nde * îub)
eu_fic = (ixé * pytá) << (ixé * inv)
ele_foi = ae * só
complex = ele_foi << (eu_fic << tu_dorm)
