import ultraplot as uplt, pytest


def test_wrong_keyword_reset():
    """
    The context should reset after a failed attempt.
    """
    # Init context
    uplt.rc.context()
    config = uplt.rc
    # Set a wrong key
    with pytest.raises(KeyError):
        config._get_item_dicts("non_existing_key", "non_existing_value")
    # Set a known good value
    config._get_item_dicts("coastcolor", "black")
    # Confirm we can still plot
    fig, ax = uplt.subplots(proj="cyl")
    ax.format(coastcolor="black")
    fig.canvas.draw()


def test_configurator_update_and_reset():
    """
    Test updating a configuration key and resetting configuration.
    """
    config = uplt.rc
    # Update a configuration key
    config["coastcolor"] = "red"
    assert config["coastcolor"] == "red"
    # Reset configuration; after reset the key should not remain as "red"
    config.reset()
    assert config["coastcolor"] != "red"


def test_context_manager_local_changes():
    """
    Test that changes made in a local context do not persist globally.
    """
    config = uplt.rc
    # Save original value if present, else None
    original = config["coastcolor"] if "coastcolor" in config else None
    with config.context(coastcolor="blue"):
        assert config["coastcolor"] == "blue"
    # After the context, the change should be reverted to original
    assert config["coastcolor"] == original
