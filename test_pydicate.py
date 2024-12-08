import sys

sys.path.append("pydicate")

from pydicate.lang.tupi import *
from pydicate.lang.tupi.pos import *
from pydicate import Predicate

# # Example usage
# and_predicate = Conjunction("abé",) * abá * ixé + Adverb("nhõ")


# and_predicate_1 = Conjunction("abé",) * Noun("Pedro") * Noun("Pindobasu")

# and_and_predicate = Conjunction("abé") * and_predicate * and_predicate_1
# # print(and_predicate)
# print()
# print(and_and_predicate.eval())

go = Verb("só")
print(go.eval())

igo = go * Noun("ixé")
print(igo.eval())

yougo = go * Noun("Endé")
print(yougo.eval())


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
    node_name = f"{predicate.category}_{predicate.verbete}_{hash(predicate)}" if isinstance(predicate, Predicate) else predicate.verbete

    # Add the current node to the graph
    label = f"{predicate.category}\n{predicate.verbete}" if isinstance(predicate, Predicate) else predicate.verbete
    graph.node(node_name, label=label, parent_name="Root")

    # Connect the current node to its parent
    if parent_name is not None:
        graph.edge(parent_name, node_name, label=edge_label)

    # Add adjuncts as children
    if isinstance(predicate, Predicate):
        # Recursively add arguments
        for i, arg in enumerate(predicate.arguments):
            build_graphviz(arg, graph, parent_name=node_name, edge_label=f"Arg {i+1}")

        with graph.subgraph() as s:
            s.attr(rank="same")  # Adjuncts on the same rank as Predicate
            for adjunct in predicate.adjuncts:
                adj_name = f"Adjunct_{adjunct.eval()}_{hash(adjunct)}"
                graph.node(adj_name, label=f"PP\n{adjunct.eval()}")
                # graph.edge(parent_name, adj_name)  # Connect adjunct to the parent node
                s.edge(
                    node_name,
                    adj_name,
                    label="+",
                    # decorate="true",
                    arrowhead="none",
                    # style="invis"  # Removes the line under the "+" sign
                )

    return graph

# build_graphviz(and_and_predicate).render("and_predicate", view=True)