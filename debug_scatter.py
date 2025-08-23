#!/usr/bin/env python3
"""Debug script to understand the edgecolor issue."""

import pandas as pd
import numpy as np
import ultraplot as pplt
import matplotlib.pyplot as plt


def debug_scatter_call():
    """Debug what happens during scatter calls with different data sizes."""
    
    # Test data
    d = pd.DataFrame(dict(x=[1, 2], y=[1, 2], sizes=[300, 300]))
    
    # Create figure
    fig, axes = pplt.subplots(ncols=1, figsize=(4, 4))
    ax = axes[0]  # Get the actual axis object
    
    # Try to inspect the arguments being passed to matplotlib's scatter
    print("=== Testing single row with alpha ===")
    
    # Monkey patch to see what's happening
    original_call_native = ax._call_native
    
    def debug_call_native(method_name, *args, **kwargs):
        if method_name == 'scatter':
            print(f"scatter called with args: {args}")
            print(f"scatter called with kwargs keys: {list(kwargs.keys())}")
            if 'edgecolors' in kwargs:
                print(f"edgecolors: {kwargs['edgecolors']}")
            if 'alpha' in kwargs:
                print(f"alpha: {kwargs['alpha']}")
            if 'c' in kwargs:
                print(f"c (color): {kwargs['c']}")
            if 's' in kwargs:
                print(f"s (size): {kwargs['s']}")
        result = original_call_native(method_name, *args, **kwargs)
        return result
    
    ax._call_native = debug_call_native
    
    # Test single row with alpha
    try:
        result = ax.scatter("x", "y", s="sizes", data=d.loc[[1]], fc="red8", ec="none", alpha=1)
        print("Single row with alpha: SUCCESS")
        print(f"Result type: {type(result)}")
        
        # Check if the scatter plot has the right edge color
        if hasattr(result, 'get_edgecolors'):
            edge_colors = result.get_edgecolors()
            print(f"Actual edge colors: {edge_colors}")
        
        # Let's also test the opposite case
        print("\n=== Testing multiple rows with alpha ===")
        ax.clear()
        result2 = ax.scatter("x", "y", s="sizes", data=d, fc="red8", ec="none", alpha=1)
        print("Multiple rows with alpha: SUCCESS")
        
        if hasattr(result2, 'get_edgecolors'):
            edge_colors2 = result2.get_edgecolors()
            print(f"Actual edge colors: {edge_colors2}")
            
    except Exception as e:
        print(f"ERROR - {e}")
        import traceback
        traceback.print_exc()
    
    plt.close()


if __name__ == "__main__":
    debug_scatter_call()