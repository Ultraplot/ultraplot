.. _ug_rcmpl: https://matplotlib.org/stable/tutorials/introductory/customizing.html

.. _ug_mplrc: https://matplotlib.org/stable/tutorials/introductory/customizing.html#customizing-with-matplotlibrc-files

.. _ug_config:

Configuring UltraPlot
===================

Overview
--------

A dictionary-like object named `~ultraplot.config.rc`, belonging to the
`~ultraplot.config.Configurator` class, is created when you import UltraPlot.
This is your one-stop shop for working with
`matplotlib settings <ug_rcmpl_>`_
stored in `~ultraplot.config.rc_matplotlib`
(our name for the `~matplotlib.rcParams` dictionary)
and :ref:`ultraplot settings <ug_rcUltraPlot>`
stored in `~ultraplot.config.rc_UltraPlot`.

To change global settings on-the-fly, simply update `~ultraplot.config.rc`
using either dot notation or as you would any other dictionary:

.. code-block:: python

  import ultraplot as uplt
  uplt.rc.name = value
  uplt.rc['name'] = value
  uplt.rc.update(name1=value1, name2=value2)
  uplt.rc.update({'name1': value1, 'name2': value2})

To apply settings to a particular axes or figure, pass the setting
to `ultraplot.axes.Axes.format` or `ultraplot.figure.Figure.format`:

.. code-block:: python

  import ultraplot as uplt
  fig, ax = uplt.subplots()
  ax.format(name1=value1, name2=value2)
  ax.format(rc_kw={'name1': value1, 'name2': value2})

To temporarily modify settings for particular figure(s), pass the setting
to the `~ultraplot.config.Configurator.context` command:

.. code-block:: python

   import ultraplot as uplt
   with uplt.rc.context(name1=value1, name2=value2):
       fig, ax = uplt.subplots()
   with uplt.rc.context({'name1': value1, 'name2': value2}):
       fig, ax = uplt.subplots()


In all of these examples, if the setting name contains dots,
you can simply omit the dots. For example, to change the
:rcraw:`title.loc` property, the following approaches are valid:

.. code-block:: python

  import ultraplot as uplt
  # Apply globally
  uplt.rc.titleloc = value
  uplt.rc.update(titleloc=value)
  # Apply locally
  fig, ax = uplt.subplots()
  ax.format(titleloc=value)

.. _ug_rcmatplotlib:

Matplotlib settings
-------------------

Matplotlib settings are natively stored in the `~matplotlib.rcParams`
dictionary. UltraPlot makes this dictionary available in the top-level namespace as
`~ultraplot.config.rc_matplotlib`. All matplotlib settings can also be changed with
`~ultraplot.config.rc`. Details on the matplotlib settings can be found on
`this page <ug_rcmpl_>`_.

.. _ug_rcUltraPlot:

UltraPlot settings
----------------

UltraPlot settings are natively stored in the `~ultraplot.config.rc_UltraPlot` dictionary.
They should almost always be changed with `~ultraplot.config.rc` rather than
`~ultraplot.config.rc_UltraPlot` to ensure that :ref:`meta-settings <ug_rcmeta>` are
synced. These settings are not found in `~matplotlib.rcParams` -- they either
control UltraPlot-managed features (e.g., a-b-c labels and geographic gridlines)
or they represent existing matplotlib settings with more clear or succinct names.
Here's a broad overview of the new settings:

* The ``subplots`` category includes settings that control the default
  subplot layout and padding.
* The ``geo`` category contains settings related to geographic plotting, including the
  geographic backend, gridline label settings, and map bound settings.
* The ``abc``, ``title``, and ``label`` categories control a-b-c labels, axes
  titles, and axis labels. The latter two replace ``axes.title`` and ``axes.label``.
* The ``suptitle``, ``leftlabel``, ``toplabel``, ``rightlabel``, and ``bottomlabel``
  categories control the figure titles and subplot row and column labels.
* The ``formatter`` category supersedes matplotlib's ``axes.formatter``
  and includes settings that control the `~ultraplot.ticker.AutoFormatter` behavior.
* The ``cmap`` category supersedes matplotlib's ``image`` and includes
  settings relevant to colormaps and the `~ultraplot.colors.DiscreteNorm` normalizer.
* The ``tick`` category supersedes matplotlib's ``xtick`` and ``ytick``
  to simultaneously control *x* and *y* axis tick and tick label settings.
* The matplotlib ``grid`` category includes new settings that control the meridian
  and parallel gridlines and gridline labels managed by `~ultraplot.axes.GeoAxes`.
* The ``gridminor`` category optionally controls minor gridlines separately
  from major gridlines.
* The ``land``, ``ocean``, ``rivers``, ``lakes``, ``borders``, and ``innerborders``
  categories control geographic content managed by `~ultraplot.axes.GeoAxes`.

.. _ug_rcmeta:

Meta-settings
-------------

Some UltraPlot settings may be more accurately described as "meta-settings",
as they change several matplotlib and UltraPlot settings at once (note that settings
are only synced when they are changed on the `~ultraplot.config.rc` object rather than
the `~ultraplot.config.rc_UltraPlot` and `~ultraplot.config.rc_matplotlib` dictionaries).
Here's a broad overview of the "meta-settings":

* Setting :rcraw:`font.small` (or, equivalently, :rcraw:`fontsmall`) changes
  the :rcraw:`tick.labelsize`, :rcraw:`grid.labelsize`,
  :rcraw:`legend.fontsize`, and :rcraw:`axes.labelsize`.
* Setting :rcraw:`font.large` (or, equivalently, :rcraw:`fontlarge`) changes
  the :rcraw:`abc.size`, :rcraw:`title.size`, :rcraw:`suptitle.size`,
  :rcraw:`leftlabel.size`, :rcraw:`toplabel.size`, :rcraw:`rightlabel.size`
  :rcraw:`bottomlabel.size`.
* Setting :rcraw:`meta.color` changes the :rcraw:`axes.edgecolor`,
  :rcraw:`axes.labelcolor` :rcraw:`tick.labelcolor`, :rcraw:`hatch.color`,
  :rcraw:`xtick.color`, and :rcraw:`ytick.color` .
* Setting :rcraw:`meta.width` changes the :rcraw:`axes.linewidth` and the major
  and minor tickline widths :rcraw:`xtick.major.width`, :rcraw:`ytick.major.width`,
  :rcraw:`xtick.minor.width`, and :rcraw:`ytick.minor.width`. The minor tickline widths
  are scaled by :rcraw:`tick.widthratio` (or, equivalently, :rcraw:`tickwidthratio`).
* Setting :rcraw:`tick.len` (or, equivalently, :rcraw:`ticklen`) changes the major and
  minor tickline lengths :rcraw:`xtick.major.size`, :rcraw:`ytick.major.size`,
  :rcraw:`xtick.minor.size`, and :rcraw:`ytick.minor.size`. The minor tickline lengths
  are scaled by :rcraw:`tick.lenratio` (or, equivalently, :rcraw:`ticklenratio`).
* Setting :rcraw:`grid.color`, :rcraw:`grid.linewidth`, :rcraw:`grid.linestyle`,
  or :rcraw:`grid.alpha` also changes the corresponding ``gridminor`` settings. Any
  distinct ``gridminor`` settings must be applied after ``grid`` settings.
* Setting :rcraw:`grid.linewidth` changes the major and minor gridline widths.
  The minor gridline widths are scaled by :rcraw:`grid.widthratio`
  (or, equivalently, :rcraw:`gridwidthratio`).
* Setting :rcraw:`title.border` or :rcraw:`abc.border` to ``True`` automatically
  sets :rcraw:`title.bbox` or :rcraw:`abc.bbox` to ``False``, and vice versa.

.. _ug_rctable:

Table of settings
-----------------

A comprehensive table of the new UltraPlot settings is shown below.

.. include:: _static/rctable.rst

.. _ug_ultraplotrc:

The ultraplotrc file
------------------

When you import UltraPlot for the first time, a ``ultraplotrc`` file is generated with
all lines commented out. This file is just like `matplotlibrc <ug_mplrc_>`_,
except it controls both matplotlib *and* UltraPlot settings. The syntax is essentially
the same as matplotlibrc, and the file path is very similar to matplotlibrc. On most
platforms it is found in ``~/.UltraPlot/ultraplotrc``, but a loose hidden file in the
home directory named ``~/.ultraplotrc`` is also allowed (use
`~ultraplot.config.Configurator.user_file` to print the path). To update this file
after a version change, simply remove it and restart your python session.

To change the global `~ultraplot.config.rc` settings, edit and uncomment the lines
in the ``ultraplotrc`` file. To change the settings for a specific project, place a file
named either ``.ultraplotrc`` or ``ultraplotrc`` in the same directory as your python
session, or in an arbitrary parent directory. To generate a ``ultraplotrc`` file
containing the settings you have changed during a python session, use
`~ultraplot.config.Configurator.save` (use `~ultraplot.config.Configurator.changed`
to preview a dictionary of the changed settings). To explicitly load a ``ultraplotrc``
file, use `~ultraplot.config.Configurator.load`.

As an example, a ``ultraplotrc`` file containing the default settings
is shown below.

.. include:: _static/ultraplotrc
   :literal:
