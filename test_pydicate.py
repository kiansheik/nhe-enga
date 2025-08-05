from pydicate.lang.tupilang import *
from pydicate.lang.tupilang.pos import *
from pydicate import Predicate

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

print("Let's write a story in Tupi!\n\n")

arakae = Adverb("araka'e", definition="a long time ago, distant past", tag="[ADVERB:DISTANT_PAST]")
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
monhang = Verb("monhang", definition="to do, to make, to create, to cause, to perform, to commit")
mongetá = Verb("mongetá", definition="to talk, to converse, to speak with")
kanhem = Verb("kanhem", definition="to disappear, to vanish, to lose oneself")
oka = Noun("oka", definition="(t); house, home, dwelling, abode, residence")
lost = (bae * kanhem)
potar = Verb("potar", definition="to want, to desire, to wish for")
kaa = Noun("ka'a", definition="(t); forest, jungle, woods, bush, thicket")
opá = Adverb("opá", definition="everything, all, whole, entire, complete", tag="[ADVERB:ALL]")
basem = Verb("basem", definition="to find, to discover, to encounter")
mboryb = Verb("mboryb", definition="to please, to delight, to satisfy")
eté = Adverb("eté", definition="true, real, genuine, authentic, very good, more, better", tag="[ADVERB:TRUE]")
apé = Noun("apé", definition="(s, r, s) path, way, road, route")
epenhan = Verb("epenhan", definition="to attack, to assault, to fight with")
îagûara = Noun("îagûara", definition="jaguar, onça, onça-pintada, large wild cat of the Americas, also means dog in some contexts")
îebyr = Verb("îebyr", definition="to return, to come back, to go back")
epîak = Verb("epîak", definition="to see, to look at, to watch, to observe")
atã = Noun("atã", definition="(t) strong, brave, firm, hard, tough, rigid, arduous")
gûarinin = Noun("gûarinin", definition="war, warfare, battle, warrior, soldier")
ur = Verb("îur", definition="to come")
poî = Verb("poî", definition="to feed, to nourish, to sustain")
# 'i / 'é1 (v. intr. irreg.) 1) dizer: Marã e'ipe asé, karaibebé o arõana mongetábo? - Que a gente diz, conversando com o anjo seu guardião? (Ar., Cat., 23v); Aîpó eré supikatu... - Isso dizes com razão... (Anch., Teatro, 32); 2) rezar, enunciar-se, prescrever: Aîpó tekoangaîpaba robaîara nã e'i. - Os opostos daqueles pecados assim se enunciam. (Ar., Cat., 18); 3) querer dizer, querer significar, pensar, supor, presumir, cogitar, julgar: Marã e'ipe asé o py'ape aîpó o'îabo i xupé? - Que quer dizer a gente em seu coração, dizendo isso para ela? (Ar., Cat., 31v); "Osó ipó re'a" a'é. - Presumo que ele deve ter ido. (VLB, II, 86); 4) concluir, julgar por indícios: Emonã ûĩ re'a a'é. - Concluo que talvez isso seja assim. (VLB, II, 16); Amõ îuká-potá ûĩ sekóû a'é. - Concluí que ele está querendo matar alguém. (VLB, II, 16) ● e'iba'e - o que diz: Mendara... "xe mena koîpó xe remirekó re'õ ré t'îamendar îandé îoesé" e'iba'e, se'õ nhẽ roîré nd'e'ikatuî sesé omendá. - O cônjuge que diz: "-Após a morte de meu marido ou de minha esposa havemos de nos casar", após sua morte não pode casar-se com ele (ou ela). (Ar., Cat., 1686, 279-280); 'îara (ou e'îara) - o que diz; o indicador: Îaîuká memẽ aîpó 'îara... - Matemos juntos o que diz isso. (Ar., Cat., 79); ...Îasytatá serekoarama resé... pé 'îaramo i xupé... - Por causa da estrela sua guardiã,... como indicadora do caminho para eles. (Ar., Cat., 3); ...Marã e'îara... - As que dizem coisas más. (Anch., Teatro, 36); "...-Our temõ anhanga xe rerasóbo mã" e'îara. - O que diz: -Oxalá venha o diabo para me levar... (Ar., Cat., 67); 'îaba (ou 'eaba ou 'esaba) - 1) tempo, lugar, modo, etc. de dizer; o dizer: Okaî oupa aûîeramanhẽ... o îurupe nhote aîpó o 'eagûera repyramo. - Estão queimando para sempre como pena de dizerem isso somente em suas bocas. (Ar., Cat., 1686, 248); 2) o que alguém diz, o chamado por alguém, o dito: Ybytyra Monte Calvário 'îápe... - Para o monte chamado Calvário (Ar., Cat., 89); Erimba'epe aîpó nde 'îaba ereîmopóne? - Quando cumprirás isso que tu dizes? (Ar., Cat., 111v); O'u nhẽpe a'e 'ybá, tegûama, Tupã 'îaba? - Comeu aquele fruto, causa da morte, que Deus dissera? (Ar., Cat., 40v); Aîpó i 'eagûera rerekóbo, semimbo'e-etá... miapé rari o pópe... - Tendo isso que ele disse, seus discípulos tomaram o pão em suas mãos. (Ar., Cat., 84v)
ei = Verb("'i", definition="to say, to tell, to speak, to indicate, to mean, to conclude, to judge", )

pdb = +(pindo * abé * pedro)

frases = [
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
    (iré * (mosapyr + ara)) + ((pedro * ekar * pindo) >> +pedro * basem + (ae*supé)),
    ((pindo * abé * pedro) * (mboryb) * îo) << ((pindo * abé * pedro) * epîak * îo),
    (((ae * apé) * pe + te) + (îebyr * pdb)) >> ((amõ * îagûara) * epenhan * +pdb),
    (amo * (gûarinin)) + (pedro * îuká * (aîpó * îagûara)),
    (sara) * (pedro * îuká * (îagûara)) == pedro,
    # Aîur ta xe poî na ûi'îabo ruã. - Venho não tendo a intenção de que me alimentem. (Anch., Arte, 55v)
    (ur * +ixé) << ((poî * ixé).imp() >> ~(ei * ixé)),

]

print(prompt)
print()
for frase in frases:
    print(f"{frase.eval(annotated=False)}.")
print()
for frase in frases:
    print(f"{frase.eval(annotated=True)}.")
print()
for frase in frases:
    print(f"{frase.semantic()}")