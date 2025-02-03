import ultraplot as uplt, pytest


def test_cycler():
    """
    Matplotlib uses different keywords to define properties. We must map UltraPlot's keywords to Matplotlib's keywords. We do this by constructing a new cycler object that ensures hat these mapping are done correctly.
    """
    # Check if the cycling is working properly
    # Take an arbitrary cycle object and cycle through all objects check if the cycle returns back to the first object
    cycle = uplt.Cycle(
        ["red", "green", "black"],
        marker=["X", "o"],
        sizes=[20, 100],
        edgecolors=["r", "k"],
    )
    first = cycle.get_next()
    # first color, marker and size
    assert first == {
        "color": "red",
        "marker": "X",
        "markeredgecolor": "r",
        "markersize": 20,
    }
    # We have 3 x 2 x 2 = 6 properties to cycle through
    for idx in range(6):
        last = cycle.get_next()
        if idx < 5:
            assert last != first
        else:
            assert last == first


def test_empty_cycle():
    """Tests default return
    The default cycler always set black as a color
    """
    cycle = uplt.Cycle()
    props = cycle.get_next()
    assert props == dict(color="black")
    assert len(props) == 1


def test_cycler_factory():
    """Test the factory function that creates cycler objects"""
    # Test basic factory creation
    cycler = uplt.Cycle(colors=["red", "blue"])
    assert isinstance(cycler, uplt.Cycle)


def test_matplotlib_keyword_mapping():
    """Test that UltraPlot keywords correctly map to Matplotlib keywords"""
    cycle = uplt.Cycle(["red"], linestyle=["-"])
    props = cycle.get_next()
    # Verify matplotlib-specific keywords
    assert "color" in props
    assert "linestyle" in props


def test_not_allowed_keyword():
    """Should raise error when we set a property that cannot be set"""
    with pytest.raises(TypeError):
        uplt.Cycle([], random_property1=["should not be allowed"])


def test_cycler_edge_cases():
    """Test edge cases and error conditions"""
    # Test with empty lists
    cycle = uplt.Cycle(colors=[])
    assert cycle.get_next() == dict(color="black")  # default fallback

    # Test with mismatched lengths
    cycle = uplt.Cycle(["red", "blue"], marker=["o"])
    # Verify cycling still works with mismatched lengths
    props1 = cycle.get_next()
    props2 = cycle.get_next()
    assert props1["marker"] == props2["marker"]  # marker should stay same
    assert props1["color"] != props2["color"]  # color should cycle


# see https://github.com/matplotlib/matplotlib/pull/29469
@pytest.mark.skip("Manual cyling not implemented yet in mpl")
def test_manual_cycle():
    cycle = uplt.Cycle(
        ["red", "green", "black"],
        marker=["X", "o"],
        sizes=[20, 100],
        edgecolors=["r", "k"],
    )
    fig, ax = uplt.subplots()
    ax.set_prop_cycle(cycle)
    ax.scatter([1], [1])

    ax = ax[0]  # force to get single axis rather than GridSpec
    parser = ax._get_lines
    current_pos = parser._idx
    cycled_pos = (current_pos + 1) % len(parser._cycler_items)
    props = ax._active_cycle.get_next()
    assert cycled_pos == parser._idx
    assert props == parser._cycler_items[parser._idx]


def test_pass_on_cycle():
    colors = ["red", "green", "black"]
    cycle = uplt.Cycle(colors)
    fig, ax = uplt.subplots()
    ax.set_prop_cycle(cycle)
    active_cycle = ax.axes._active_cycle
    for color in colors:
        assert color == active_cycle.get_next()["color"]
        assert color == cycle.get_next()["color"]
