from cycler import V
from pandas.core.arrays.arrow.accessors import pa
import ultraplot as uplt, pytest, numpy as np

"""
This file is used to test base properties of ultraplot.axes.plot. For higher order plotting related functions, please use 1d and 2plots
"""


def test_graph_nodes_kw():
    """Test the graph method by setting keywords for nodes"""
    import networkx as nx

    g = nx.path_graph(5)
    labels_in = {node: node for node in range(2)}

    fig, ax = uplt.subplots()
    nodes, edges, labels = ax.graph(g, nodes=[0, 1], labels=labels_in)

    # Expecting 2 nodes 1 edge
    assert len(edges.get_offsets()) == 1
    assert len(nodes.get_offsets()) == 2
    assert len(labels) == len(labels_in)


def test_graph_edges_kw():
    """Test the graph method by setting keywords for nodes"""
    import networkx as nx

    g = nx.path_graph(5)
    edges_in = [(0, 1)]

    fig, ax = uplt.subplots()
    nodes, edges, labels = ax.graph(g, edges=edges_in)

    # Expecting 2 nodes 1 edge
    assert len(edges.get_offsets()) == 1
    assert len(nodes.get_offsets()) == 2
    assert labels == False


def test_graph_input():
    """
    Test graph input methods. We allow for graphs, adjacency matrices, and edgelists.
    """
    import networkx as nx

    g = nx.path_graph(5)
    A = nx.to_numpy_array(g)
    el = np.array(g.edges())
    fig, ax = uplt.subplots()
    # Test input methods
    ax.graph(g)  # Graphs
    ax.graph(A)  # Adjcency matrices
    ax.graph(el)  # edgelists
    with pytest.raises(TypeError):
        ax.graph("invalid_input")


def test_graph_layout_input():
    """
    Test if layout is in a [0, 1] x [0, 1] box
    """
    import networkx as nx

    g = nx.path_graph(5)
    circular = nx.circular_layout(g)
    layouts = [None, nx.spring_layout, circular, "forceatlas2", "spring_layout"]
    fig, ax = uplt.subplots(ncols=len(layouts))
    for axi, layout in zip(ax[1:], layouts):
        axi.graph(g, layout=layout)


def test_graph_rescale():
    """
    Graphs can be normalized such that the node size is the same independnt of the fig size
    """
    import networkx as nx

    g = nx.path_graph(5)
    layout = nx.spring_layout(g)
    # shift layout outside the box
    layout = {node: np.array(pos) + np.array([10, 10]) for node, pos in layout.items()}

    fig, ax = uplt.subplots()
    nodes1 = ax.graph(g, layout=layout, rescale=True)[0]

    xlim_scaled = np.array(ax.get_xlim())
    ylim_scaled = np.array(ax.get_ylim())

    fig, ax = uplt.subplots()
    nodes2 = ax.graph(g, layout=layout, rescale=False)[0]

    for x, y in nodes1.get_offsets():
        assert x >= 0 and x <= 1
        assert y >= 0 and y <= 1
    for x, y in nodes2.get_offsets():
        assert x > 1
        assert y > 1
