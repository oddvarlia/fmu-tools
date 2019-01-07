# -*- coding: utf-8 -*-

"""Top-level package for fmu_tools"""

from ._theversion import theversion
__version__ = theversion()

del theversion

from .rms import volumetrics # noqa

from .sensitivities import DesignMatrix # noqa
from .sensitivities import summarize_design # noqa
from .sensitivities import calc_tornadoinput # noqa
from .sensitivities import find_combinations # noqa
from .sensitivities import add_webviz_tornadoplots # noqa
from .sensitivities import excel2dict_design # noqa
