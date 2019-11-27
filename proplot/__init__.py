#!/usr/bin/env python3
#------------------------------------------------------------------------------#
# Import everything into the top-level module namespace
# Have sepearate files for various categories, so we don't end up with a
# single enormous 12,000-line file
#------------------------------------------------------------------------------#
# Monkey patch warnings format for warnings issued by ProPlot, make sure to
# detect if this is just a matplotlib warning traced back to ProPlot code
# See: https://stackoverflow.com/a/2187390/4970632
# For internal warning call signature: https://docs.python.org/3/library/warnings.html#warnings.showwarning
# For default warning source code see: https://github.com/python/cpython/blob/master/Lib/warnings.py
import warnings as _warnings
def _warning_proplot(message, category, filename, lineno, line=None):
    if line is None:
        try:
            import linecache
            line = linecache.getline(filename, lineno)
        except ModuleNotFoundError:
            pass
    if 'proplot' in filename and line is not None and 'warnings' in line:
        string = f'{filename}:{lineno}: ProPlotWarning: {message}'
    else:
        string = f'{filename}:{lineno}: {category.__name__}: {message}'
        if line is not None:
            string += ('\n' + line) # default behavior
    return (string + '\n') # must end in newline or not shown in IPython
if _warnings.formatwarning is not _warning_proplot:
    _warnings.formatwarning = _warning_proplot

# Initialize customization folders
import os as _os
_rc_folder = _os.path.join(_os.path.expanduser('~'), '.proplot')
if not _os.path.isdir(_rc_folder):
    _os.mkdir(_rc_folder)
for _rc_sub in ('cmaps', 'cycles', 'colors', 'fonts'):
    _rc_sub = _os.path.join(_rc_folder, _rc_sub)
    if not _os.path.isdir(_rc_sub):
        _os.mkdir(_rc_sub)

# Initialize customization file
_rc_file = _os.path.join(_os.path.expanduser('~'), '.proplotrc')
_rc_file_default = _os.path.join(_os.path.dirname(__file__), '.proplotrc')
if not _os.path.isfile(_rc_file):
    with open(_rc_file_default) as f:
        lines = ''.join(
            '#   ' + line if line.strip() and line[0] != '#' else line
            for line in f.readlines()
            )
    with open(_rc_file, 'x') as f:
        f.write('# User default settings\n'
            + '# See https://proplot.readthedocs.io/en/latest/rctools.html\n'
            + lines)

# Import stuff in reverse dependency order
# Make sure to load styletools early so we can try to update TTFPATH before
# the fontManager is loaded by other modules (requiring a rebuild)
from .utils import _benchmark
with _benchmark('total time'):
    from .utils import *
    with _benchmark('styletools'):
        from .styletools import *
    with _benchmark('rctools'):
        from .rctools import *
    with _benchmark('axistools'):
        from .axistools import *
    with _benchmark('wrappers'):
        from .wrappers import *
    with _benchmark('projs'):
        from .projs import *
    with _benchmark('axes'):
        from .axes import *
    with _benchmark('subplots'):
        from .subplots import *

# SCM versioning
import pkg_resources as _pkg
name = 'ProPlot'
try:
    version = __version__ = _pkg.get_distribution(__name__).version
except _pkg.DistributionNotFound:
    version = __version__ = 'unknown'
