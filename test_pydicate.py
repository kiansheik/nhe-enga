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
# opá (part.) - 1) todo (s, a, as); tudo: Xe tekokuaba opá amokanhem. - Meu entendimento todo fiz desaparecer. (Anch., Poemas, 106); Opá og ugûy me'engi, omanomõ... - Todo seu sangue deu, morrendo. (Anch., Poemas, 108); Oîké îugûasu, i akanga kutuka, opá i mombuka. - Entram grandes espinhos, espetando sua cabeça, furando-a toda. (Anch., Poemas, 122); ...Opá o boîá nde pópe i mongûapa... - Todos os seus discípulos para tuas mãos fazendo passar. (Anch., Poemas, 124); Opá taba moangaîpabi! - Tudo faz a aldeia pecar! (Anch., Teatro, 38); Opá emonã tekoara îandé ratá îaîarõ. - A todos os que assim vivem nosso fogo convém. (Anch., Teatro, 154); Opá i îeakypûereroîebyri. - Todos eles voltaram-se para trás. (Ar., Cat., 54v); Opá abá sóû. - Todos os homens foram. (Anch., Arte, 54v); Opá abá îukáû. - Matou todos os homens. (Anch., Arte, 54v); Opápe turi? - Todos vieram? (Anch., Arte, 54v); 2) ambos (as): Opá xe uba îesyî. - Ambas as minhas coxas adormeceram. (Anch., Teatro, 26)
opá = Adverb("opá", definition="everything, all, whole, entire, complete", tag="[ADVERB:ALL]")
# basem2 (ou mbasem ou basẽ) (v. intr. compl. posp.) - achar, encontrar (complemento com supé ou pé): Our benhẽ i kera pé nhẽ obasemano. - Veio de novo, achando-os novamente no sono. (Ar., Cat., 53v); Mbype erebasẽ i xupé? - Achaste-os por perto? (Anch., Teatro, 46); N'abasẽ-mirĩ-angáî marãbirĩ ikó abá rekopûera amõ supé... - Não encontro nem um pouco, absolutamente, algum ato passado deste homem no mal. (Ar., Cat., 58v) ● basemaba - tempo, lugar, modo, etc. de achar; achado, o que alguém acha: Ereîme'engype mba'e-kanhema nde basemagûera i îara supé? - Deste as coisas sumidas que tu achaste para seu dono? (Ar., Cat., 107)
basem = Verb("basem", definition="to find, to discover, to encounter")
# mboryb1 (ou moryb ou mbory) (v.tr.) - 1) alegrar, satisfazer: Maria t'îambory... - Que alegremos a Maria. (Anch., Poemas, 188); 2) alegrar-se de, ter gozo em, deleitar-se com, comprazer-se de: ...O kera pupé o pupukûera morypa... - Deleitando-se com sua polução em seu sono. (Ar., Cat., 72); Arakaîá-te ombory... - Mas os aracajás deleitam-se com eles. (Anch., Teatro, 36); Ereîmborype nde angaîpagûera resé nde ma'enduasaba? - Tiveste gozo com tuas lembranças de teus pecados antigos? (Ar., Cat., 233) ● omboryba'e - o que alegra; o que se compraz em: ...O ké-poxy omboryba'e... - O que se compraz em seu sonho mau. (Anch., Diál. da Fé, 211); mborypara (ou morypara) - o que alegra, o que se deleita com: -Abá abépe oîaby? -Kunhã me'engara... koîpó i mborypara. -Quem mais o transgride? -O que entrega mulheres e o que se deleita com elas. (Ar., Cat., 71); morypaba - tempo, lugar, modo, etc. de alegrar, de deleitar-se com; regozijo, gozo, deleite: ...O morybagûera poepyka... - Retribuindo seu regozijo com ele. (Ar., Cat., 89)
mboryb = Verb("mboryb", definition="to please, to delight, to satisfy")
# eté1 (t) (s.) - 1) verdade, legitimidade; 2) excelência; 3) normalidade; [adj.: eté (r, s)] - 1) verdadeiro, legítimo, autêntico, genuíno: Tupã rendabeté, Tupã raîyra. - Verdadeira estância de Deus, filha de Deus. (Anch., Poemas, 88); T'orosaûsu îandé ruba, îandé monhangareté. - Que amemos nosso pai, nosso verdadeiro criador. (Anch., Teatro, 120); 2) muito bom; excelente, ótimo; fino; enorme, fora do comum, a valer: Mba'e-eté ka'ugûasu... - Coisa muito boa é uma grande bebedeira. (Anch., Teatro, 6); ka'aeté - mata ótima, de boa madeira (Anch., Cartas, 460); ybyrá-eté - madeira fina, ótima (Anch., Cartas, 460); 3) normal: kunhãeté - mulher normal (isto é, que nunca foi escrava) (VLB, I, 142); karaibeté - cristão normal (isto é, o que não é missionário; leigo) (VLB, II, 20); 4) mais, maior, melhor: Turusueté - Ele é maior. I porangeté - Ele é mais bonito. (VLB, II, 35); Ixé xe katueté. - Eu sou melhor. (VLB, II, 35); (adv.) - muito, bastante; verdadeiramente, de fato: Sekó-te i poxyeté... - Mas sua vida é muito má. (Anch., Teatro, 28); Aûîé; xe rorybeté. - Basta; eu estou muito contente. (Anch., Teatro, 128); 'Arangaturameté... - Dia muito bom. (Anch., Poemas, 94); Adão, oré rubypy, oré mokanhemeté... - Adão, nosso primeiro pai, fez-nos perder verdadeiramente. (Anch., Poemas, 130); Té oureté kybõ Reriûasu mã! - Ah, veio de fato para cá o Ostra Grande! (Léry, Histoire, 341) ● eté-eté (r, s) (adj.) - imenso, grandioso: Tupã myatã-eté-eté... - a imensa força de Deus (Bettendorff, Compêndio, 62); (adv.) - demais, muitíssimo: O'u-eté-eté ahẽ mba'e. - Ele comeu demais aquela coisa. (VLB, II, 118); etekatu - muitíssimo, demais: Xe moaîu-marangatu, xe moŷrõ-etekatûabo, aîpó tekó-pysasu. - Importuna-me bem, irritando-me muitíssimo, aquela lei nova. (Anch., Teatro, 4); Asé ra'angetekatu... Anhanga...? - Tenta-nos demais o diabo? (Ar., Cat., 92v); eté nhẽ - muito; muito bem (VLB, II, 44); eté'ĩ - muito, verdadeiramente: Xe angaîpabeté'ĩ ra'u mã! - Ah, eu fui muito pecador! (Anch., Doutr. Cristã, I, 195); eté'ĩ ...mã! - ó, como me alegro! graças a Deus!: Our-eté'ĩ xe ruba mã! - Graças a Deus meu pai veio! (VLB, II, 54)
eté = Adverb("eté", definition="true, real, genuine, authentic, very good, more, better", tag="[ADVERB:TRUE]")
# apé (r, s) (s.) - caminho (em relação a quem passa por ele): Pé ku'ape, kunumĩ pu'ama'ubi xe ri... - No meio do caminho, meninos assaltaram-me. (Anch., Poemas, 150); T'îasó sapépe... - Vamos ao seu caminho. (Ar., Cat., 53v); Asó xe ruba rapépe. - Vou ao caminho de meu pai. (VLB, II, 111); sapé - o caminho dele (Fig., Arte, 78); Asapé-monhang amana. - Faço caminho para a água da chuva. (Fig., Arte, 88) ● 'y rapé - rego d'água (VLB, I, 65); pé-îoasapaba (ou pé-îoasasaba) - encruzilhada do caminho (VLB, I, 115); pé-mirĩ - carreirão, caminho pequeno para quem vai a pé (VLB, I, 68); pé kugûapaba - baliza do caminho (VLB, I, 51); pé pukuî - ao longo do caminho; todo o caminho (VLB, II, 130)
apé = Noun("apé", definition="(s, r, s) path, way, road, route")
# epenhan1 (ou epenhã ou epenhang) (s) (v.tr.) - 1) atacar: ...T'oporepenhã oîkóbo... - Que estejam atacando gente. (Anch., Teatro, 16); ...Apŷaba eresepenhãne. - Os índios atacarás. (Anch., Teatro, 20); ...A'epe kunhãmuku repenhana... - Ali atacando as moças. (Anch., Teatro, 34); Îasepenhan, îaîpysyk, i apysyk' e'ymebé... - Atacamo-los, prendemo-los, antes que se consolem. (Anch., Teatro, 66); Esepenhan, Saraûaî! - Ataca-o, Sarauaia! (Anch., Teatro, 76); 2) brigar com, pelejar com (com espada, etc.) (VLB, II, 71) ● epenhandara (t) - o que ataca: Aîpysy-potá-katu morepenhandara ri. - Quero muito apanhá-las com os que atacam as pessoas. (Anch., Teatro, 154, 2006)
epenhan = Verb("epenhan", definition="to attack, to assault, to fight with")
# îagûara1 (ou îaûara) (s.) - 1) JAGUAR, onça, onça-pintada, carnívoro americano da família dos felídeos (Panthera onca), de cor amarelo-avermelhada, com manchas pretas simétricas, arredondadas ou irregulares, pelo corpo. É a fera mais terrível do continente americano, tomando grandes presas. É também conhecida no Brasil como JAGUARAPINIMA, JAGUARETÊ, canguçu, acanguçu: Îaûara ixé. - Eu sou uma onça. (Staden, Viagem, 109); Aîuká-ukar îagûara Pedro supé. - Fiz Pedro matar uma onça. (Fig. Arte, 146); 2) nome dado pelos índios ao cão (VLB, I, 65) [Nesta acepção pode ser acompanhado pelo termo eîmbaba (t) - criação, animal de criação, à diferença de quando o termo significa onça, que nunca se cria domesticamente.]: o apixara reîmbaba îagûara remimomosẽgûera - o que perseguiu o cão de seu próximo (Ar., Cat., 73); I mba'e-potar îagûara. - O cão é ávido (isto é, bom de caça, que quer tudo apanhar). (VLB, I, 62); Îagûara-p'ipó? - É este o cão? (Knivet, The Adm. Adv., 1208) ● îagûara'yra - filhote de cão (VLB, I, 62) (V. tb. îagûareté)
îagûara = Noun("îagûara", definition="jaguar, onça, onça-pintada, large wild cat of the Americas, also means dog in some contexts")
# îebyr (v. intr.) - voltar, tornar: Oú-îebype erimba'e o boîá reîasagûerype? - Voltou a vir aonde tinha deixado seus discípulos? (Ar., Cat., 53); Aîur gûiîeby. - Vim, voltando. (VLB, II, 133); Omanõba'epûera suí sekobé-îebyri. - Voltou a viver dos que morreram. (Anch., Doutr. Cristã, I, 141) ● îebyraba - tempo, lugar, modo, causa, etc., do voltar; volta, retorno: ...Ebapó ta peîkó pe îebyragûama resé ixé nde momorandube'yma pukuî. - Ali ficai enquanto eu não vos informar acerca de vossa futura volta. (Ar., Cat., 10v); îeby benhẽ - voltar atrás: Aîeby benhẽ, gûixóbo. - Indo, voltei atrás. (VLB, I, 43)
îebyr = Verb("îebyr", definition="to return, to come back, to go back")
# epîak (s) (v.tr.) - ver: Sory-katu xe repîaka... - Estavam felizes ao ver-me. (Anch., Teatro, 10); I abaeté sepîaka ixébo... - É terrível para mim vê-los... (Anch., Teatro, 26); ...Seté anhõ osepîakyne. - Seu corpo somente verão. (Ar., Cat., 46v); ...Îandé repîaka our! - Veio para nos ver!... Eîori nde retamûama repîaka. - Vem para ver tua futura terra. (Léry, Histoire, 341) ● epîakara (t) - o que vê: Marangatuba'e santos ybakype, Tupã repîakaretá, osasá 'ara ro'y remierekó papasaba. - Os bem-aventurados e os santos no céu, que vêem a Deus, ultrapassam o número dos dias que o ano tem. (Ar., Cat., 135); epîakaba (t) - lugar, tempo, modo, etc. de ver; a visão: -Mamõpe Pilatos senosemi a'ereme? -Okarype morepîakápe... -Para onde Pilatos o retirou, então? -Para a praça, para o lugar de ver gente... (Ar., Cat., 60v); emiepîaka (t) - o visto, o que alguém vê: Oîepó-eî te'yîa remiepîakamo. - Lavou-se as mãos à vista da multidão (isto é, como o que a multidão vê). (Ar., Cat., 61); Ereîmombe'upe abá rekopoxŷagûera oîepebẽ nde remiepîakûera abá supé? - Contaste o mau procedimento de alguém, que somente tu viste, para as pessoas? (Ar., Cat., 108); sepîakypyra - o que é (ou deve ser) visto: ...Mo'yrobyeté sepîakypyre'yma. - Colares azuis não vistos (ainda). (Léry, Histoire, 346); sepîakypypabẽ - coisa notória por ser vista totalmente; notório, patente (VLB, II, 51) (Com o verbo 'i / 'é, como auxiliar, significa crer, vendo): Eré sepîakane. - Crerás, vendo. (Fig., Arte, 159)
epîak = Verb("epîak", definition="to see, to look at, to watch, to observe")
# atã2 (t) (s.) - o forte, o bravo na guerra e em outras ocasiões; força; coisa tesa (VLB, II, 127): Nd'a'é te'e nde ratãngatu resé gûiîekoka... - Por isso mesmo em tua grande força apóio-me. (Anch., Teatro, 12); tatã - o forte, o bravo (Léry, Histoire, 368); [adj.: atã (r, s) ou (r, t)] - forte, firme, duro, rígido, rijo, teso; (fig.) árduo: Xe posaká, xe ratã... - Eu sou moçacara, eu sou forte. (Anch., Teatro, 162); T'îasó maranatãûãme...? - Havemos de ir à árdua guerra? (Anch., Poemas, 112); kunumĩûasu-atã-atã - rapazes muito fortes (Léry, Histoire, 338, 1994); (adv.) firmemente, duramente, rijamente: Oîar-atã serã i aoba i nupãsagûera i moperé-perebagûera resé? - Pegou-se firmemente sua roupa com que ele foi castigado às suas chagas? (Ar., Cat., 62); Anhe'eng-atã. - Falei duramente. (VLB, I, 40); Esekyî-atã! - Puxa-o rijamente! (VLB, II, 106); Îapopûar-atã, i moangaîpapa. - Amarram suas mãos firmemente, fazendo-lhe mal. (Anch., Poemas, 120)
atã = Noun("atã", definition="(t) strong, brave, firm, hard, tough, rigid, arduous")
# gûarinĩ1 (s.) - 1) guerra (VLB, I, 152); 2) guerreiro, soldado: Marãpe gûarinĩetá i pysykara serekóû a'ereme? - Como os soldados que o agarravam trataram-no, então? (Anch., Dial. da Fé, 175) ● gûarinĩ-(ramo) só [ou gûarinĩ-(namo) só] - ir à guerra, ir como guerreiro, guerrear: -Mba'e-mba'e-piã te'õ suí nheangûaba? -Gûarinĩ-namo só, paranãgûasu rasabano. -Quais são, por acaso, as ocasiões de se ter medo da morte? -Ir à guerra, atravessar o oceano também. (Ar., Cat., 91); Onhemombe'upe abá gûarinĩ-namo o só îanondé? - Confessa-se alguém antes de ir à guerra? (Anch., Doutr. Cristã, I, 212); Nd'eresóî xópe irã gûarinĩ? - Não irás futuramente à guerra? (Léry, Histoire, 353); Asó gûarinĩramo. - Vou à guerra, vou como guerreiro. (VLB, I, 152)
gûarinin = Noun("gûarinin", definition="war, warfare, battle, warrior, soldier")

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
    ((pindo *abé * pedro) * (mboryb) * îo) << ((pindo *abé * pedro) * epîak * îo ),
    (((ae * apé) * pe + te) + (îebyr * ae)) >> ((amõ * îagûara) * epenhan * +ae),
    (amo * (gûarinin)) + (pedro * îuká * (aîpó * îagûara)),
    (sara) * (pedro * îuká * (îagûara)) == pedro,
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