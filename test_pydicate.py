import sys

sys.path.append("pydicate")

from pydicate.lang.tupi import *
from pydicate.lang.tupi.pos import *
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
        graph.attr(label=predicate.eval(), labelloc="t", fontsize="24", fontname="Helvetica-Bold")
    
    if parent_name is None:
        parent_name = "Root"
        graph.node(parent_name, label=f"IP")
    # Generate a unique name for the current node
    node_name = f"{predicate.category}_{predicate.verbete}_{rhash(predicate)}" if isinstance(predicate, Predicate) else predicate.verbete

    # Add the current node to the graph
    label = f"{predicate.category}\n{predicate.verbete}" if isinstance(predicate, Predicate) else predicate.verbete
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

# # Example usage
# and_predicate = Conjunction("abé",) * abá * ixé + Adverb("nhõ")


# and_predicate_1 = Conjunction("abé",) * Noun("Pedro") * Noun("Pindobasu")

# and_and_predicate = Conjunction("abé") * and_predicate * and_predicate_1
# # print(and_predicate)
# print()
# print(and_and_predicate.eval())

go = Verb("só")
print(go.eval()) # só

igo = go * ixé
print(igo.eval()) # ixé asó

yougo = go * endé
print(yougo.eval()) # endé eresó

yougo = go * endé + Adverb("koritei")
print(yougo.eval()) # endé eresó koritei

yougo_circ =  Adverb("koritei") + go * endé
print(yougo_circ.eval()) # koritei endé eresó

hego = go * ~ae + Adverb("koritei")
print(hego.eval()) # a'e osó koritei

hego_circ = Adverb("koritei") + go * ~ae
print(hego_circ.eval()) # koritei i sóû

want = Verb("potar", "v.tr.", definition="to want")

ver = Verb("epîak", "v.tr. (s)", definition="to see")

tl = ver * ixé * endé << go * ixé
print(tl.eval()) # ixé endé epîak só

ver_circ = ~-go/want * ixé >> -ver * +ixé * endé
print(ver_circ.eval()) # ixé endé epîak só


ver_circ =  endé * koty + ixé * -go + sosé * ixé
print(ver_circ.eval()) # ixé endé epîak só



# euepedro = (abé * Noun("Pedro") * ixé)
# me_n_pedro = -ver * (mateus * euepedro)
# print(me_n_pedro.eval()) # Mateus sees Pedro
# vergo =  Noun("Mateus") == Noun("Pedro")
# vergo_neg =  Noun("Mateus") != Noun("Pedro")
# print("ble: ", (vergo).eval()) 

# build_graphviz(hego).render("and_predicate1", view=True)
# build_graphviz(hego_circ).render("and_predicate_circ1", view=True)








