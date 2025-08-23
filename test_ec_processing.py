#!/usr/bin/env python3
"""Test to see what happens to ec parameter during preprocessing."""

import pandas as pd
import numpy as np
import ultraplot as pplt


def test_ec_processing():
    """Test what happens to the ec parameter."""
    
    # Test data
    d1 = pd.DataFrame(dict(x=[1, 2], y=[1, 2], sizes=[300, 300]))  # 2 rows
    d2 = pd.DataFrame(dict(x=[2], y=[2], sizes=[300]))  # 1 row
    
    # Create figure
    fig, axes = pplt.subplots(ncols=2, figsize=(8, 4))
    
    # Patch the _from_data function to see what it does
    from ultraplot.internals import inputs
    original_from_data = inputs._from_data
    
    def debug_from_data(data, *args):
        print(f"_from_data called with data: {type(data)}, len: {len(data) if hasattr(data, '__len__') else 'N/A'}")
        print(f"_from_data args: {args}")
        result = original_from_data(data, *args)
        if result is not None:
            print(f"_from_data result: {result}")
        return result
    
    inputs._from_data = debug_from_data
    
    # Test with multiple rows
    print("=== Multiple rows case ===")
    try:
        axes[0].scatter("x", "y", s="sizes", data=d1, fc="red8", ec="none", alpha=1)
        print("Multiple rows: SUCCESS")
    except Exception as e:
        print(f"Multiple rows: ERROR - {e}")
    
    # Test with single row
    print("\n=== Single row case ===")
    try:
        axes[1].scatter("x", "y", s="sizes", data=d2, fc="red8", ec="none", alpha=1)
        print("Single row: SUCCESS")
    except Exception as e:
        print(f"Single row: ERROR - {e}")
    
    # Restore original function
    inputs._from_data = original_from_data
    
    import matplotlib.pyplot as plt
    plt.close()


if __name__ == "__main__":
    test_ec_processing()