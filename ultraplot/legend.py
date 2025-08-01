from typing_extensions import override
from matplotlib import legend as mlegend

try:
    from typing import override
except ImportError:
    from typing_extensions import override


class Legend(mlegend.Legend):
    # Soft wrapper of matplotlib legend's class.
    # Currently we only override the syncing of the location.
    # The user may change the location and the legend_dict should
    # be updated accordingly. This caused an issue where
    # a legend format was not behvaving according to the docs
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @override
    def set_loc(self, loc=None):
        # Sync location setting with the move
        old_loc = None
        if self.axes is not None:
            # Get old location which is a tuple of location and
            # legend type
            for k, v in self.axes._legend_dict.items():
                old_loc = k
            value = self.axes._legend_dict.pop(old_loc, None)
        super().set_loc(loc)
        if old_loc:
            where, type = old_loc
            self.axes._legend_dict[(loc, type)] = value
