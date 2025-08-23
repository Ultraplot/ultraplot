#!/usr/bin/env python3
"""Test script to reproduce the edgecolor issue with scatter plots."""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ultraplot as pplt


def test_edgecolor_issue():
    """Test to reproduce the edgecolor issue described in the GitHub issue."""
    # Create test data
    d = pd.DataFrame(dict(x=[1, 2], y=[1, 2], sizes=[300, 300]))
    
    # Create subplots
    fig, ax = pplt.subplots(ncols=3, figsize=(12, 4))
    
    # Test case 1: Multiple rows with alpha - should work correctly
    ax[0].scatter("x", "y", s="sizes", data=d, fc="red8", ec="none", alpha=1)
    
    # Test case 2: Single row with alpha - BUG: edgecolor ignored
    ax[1].scatter("x", "y", s="sizes", data=d.loc[[1]], fc="red8", ec="none", alpha=1)
    
    # Test case 3: Single row without alpha - should work correctly
    ax[2].scatter("x", "y", s="sizes", data=d.loc[[1]], fc="red8", ec="none")
    
    # Format axes
    ax.format(
        xlim=(0.8, 2.2),
        ylim=(0.9, 2.1),
        suptitle="ax[0]: Right ec with len(d)>1 and alpha"
        + "\nax[1]: Wrong ec with len(d)=1 and alpha"
        + "\nax[2]: Right ec with len(d)=1 and no alpha",
        suptitle_kw={"ha": "left"},
    )
    
    plt.show()
    return fig, ax


if __name__ == "__main__":
    fig, ax = test_edgecolor_issue()