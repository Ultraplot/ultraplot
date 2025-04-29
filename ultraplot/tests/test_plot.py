from cycler import V
from pandas.core.arrays.arrow.accessors import pa
import ultraplot as uplt, pytest, numpy as np
from unittest import mock

from ultraplot.internals.warnings import UltraPlotWarning

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


def test_violin_labels():
    """
    Test the labels functionality of violinplot and violinploth.
    """
    labels = "hello world !".split()
    fig, ax = uplt.subplots()
    bodies = ax.violinplot(y=[1, 2, 3], labels=labels)
    for label, body in zip(labels, bodies):
        assert body.get_label() == label

    # # Also test the horizontal ticks
    bodies = ax.violinploth(x=[1, 2, 3], labels=labels)
    ytick_labels = ax.get_yticklabels()
    for label, body in zip(labels, bodies):
        assert body.get_label() == label

    # Labels are padded if they are shorter than the data
    shorter_labels = [labels[0]]
    with pytest.warns(UltraPlotWarning):
        bodies = ax.violinplot(y=[[1, 2, 3], [2, 3, 4]], labels=shorter_labels)
        assert len(bodies) == 3
        assert bodies[0].get_label() == shorter_labels[0]


@pytest.mark.parametrize(
    "mpl_version, expected_key, expected_value",
    [
        ("3.10.0", "orientation", "vertical"),
        ("3.9.0", "vert", True),
    ],
)
def test_violinplot_mpl_versions(
    mpl_version: str,
    expected_key: str,
    expected_value: bool | str,
):
    """
    Test specific logic for violinplot to ensure that past and current versions work as expected.
    """
    fig, ax = uplt.subplots()
    with mock.patch("ultraplot.axes.plot._version_mpl", new=mpl_version):
        with mock.patch.object(ax.axes, "_call_native") as mock_call:
            # Note: implicit testing of labels passing. It should work
            ax.violinplot(y=[1, 2, 3], vert=True)

            mock_call.assert_called_once()
            _, kwargs = mock_call.call_args
            assert kwargs[expected_key] == expected_value
            if expected_key == "orientation":
                assert "vert" not in kwargs
            else:
                assert "orientation" not in kwargs


def test_violinplot_hatches():
    """
    Test the input on the hatches parameter. Either a singular or a list of strings. When a list is provided, it must be of the same length as the number of violins.
    """
    # should be ok
    fig, ax = uplt.subplots()
    ax.violinplot(y=[1, 2, 3], vert=True, hatch="x")

    with pytest.raises(ValueError):
        ax.violinplot(y=[1, 2, 3], vert=True, hatches=["x", "o"])


@pytest.mark.parametrize(
    "mpl_version, expected_key, expected_value",
    [
        ("3.10.0", "orientation", "vertical"),
        ("3.9.0", "vert", True),
    ],
)
def test_boxplot_mpl_versions(
    mpl_version: str,
    expected_key: str,
    expected_value: bool | str,
):
    """
    Test specific logic for violinplot to ensure that past and current versions work as expected.
    """
    fig, ax = uplt.subplots()
    with mock.patch("ultraplot.axes.plot._version_mpl", new=mpl_version):
        with mock.patch.object(ax.axes, "_call_native") as mock_call:
            # Note: implicit testing of labels passing. It should work
            ax.boxplot(y=[1, 2, 3], vert=True)

            mock_call.assert_called_once()
            _, kwargs = mock_call.call_args
            assert kwargs[expected_key] == expected_value
            if expected_key == "orientation":
                assert "vert" not in kwargs
            else:
                assert "orientation" not in kwargs
