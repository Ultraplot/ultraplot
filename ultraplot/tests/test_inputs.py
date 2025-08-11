import ultraplot as uplt, pytest, numpy as np


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
