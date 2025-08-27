import ultraplot as uplt, pytest, numpy as np
from unittest.mock import Mock, patch


@pytest.mark.parametrize(
    "data, dtype",
    [
        ([1, 2, 3], int),
        ([[1, 2], [1, 2, 3]], object),
        (["hello", 1], np.dtype("<U21")),  # will convert 1 to string
        ([["hello"], 1], object),  # non-homogeneous  # mixed types
    ],
)
def test_to_numpy_array(data, dtype):
    """
    Test that to_numpy_array works with various data types.
    """
    arr = uplt.internals.inputs._to_numpy_array(data)
    assert arr.dtype == dtype, f"Expected dtype {dtype}, got {arr.dtype}"


def test_name_preserved_and_args_processed():
    """
    Check if the name is preserved across nested decoration
    for tri-related functions
    """
    parser_mock = Mock(return_value=("triang", "zval", None, None))

    def tripcolor(self, tri, z, extra=None, kw=None):
        return "ok"

    decorated = uplt.internals.inputs._parse_triangulation_with_preprocess()(tripcolor)

    # Test that the decorator preserves the function name
    assert decorated.__name__ == "tripcolor"


@pytest.mark.parametrize("transform", [None, uplt.constructor.Proj("merc")])
def test_projection_set_correctly(rng, transform):

    fig, ax = uplt.subplots(proj="merc")
    fig.canvas.draw()
    data = rng.random((10, 10))

    with patch.object(ax, "imshow", wraps=ax.imshow) as mock_imshow:
        # Call imshow with some dummy data
        settings = dict(transform=transform)
        ax.imshow(data, **settings)

        # Assert that the transform keyword argument was set correctly
        mock_imshow.assert_called_once()
        _, kwargs = mock_imshow.call_args
        assert "transform" in kwargs, "The 'transform' keyword argument is missing."
        assert (
            kwargs["transform"] is transform
        ), f"Expected transform to be {transform}, got {kwargs['transform']}"
    uplt.close(fig)
