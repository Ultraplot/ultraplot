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
    Graph function should show labels when asked
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
    Graph function should show labels when asked
    """
    import networkx as nx

    g = nx.path_graph(5)
    circular = nx.circular_layout(g)
    layouts = [None, nx.spring_layout, circular, "forceatlas2", "spring_layout"]
    fig, ax = uplt.subplots(ncols=len(layouts))
    for axi, layout in zip(ax[1:], layouts):
        axi.graph(g, layout=layout)


def test_graph_rescale():
    """ """
    import networkx as nx

    g = nx.path_graph(5)
    layout = nx.spring_layout(g)

    fig, ax = uplt.subplots()
    nodes_rescaled = ax.graph(g, layout=layout, rescale=True)[0]

    xlim_scaled = ax.get_xlim()
    ylim_scaled = ax.get_ylim()

    fig, ax = uplt.subplots()
    nodes_not_rescaled = ax.graph(g, layout=layout, rescale=False)[0]

    xlim_not_scaled = ax.get_xlim()
    ylim_not_scaled = ax.get_ylim()

    assert xlim_not_scaled[0] != xlim_scaled[0]
    assert xlim_not_scaled[1] != xlim_scaled[1]
    assert ylim_not_scaled[0] != ylim_scaled[0]
    assert ylim_not_scaled[1] != ylim_scaled[1]
