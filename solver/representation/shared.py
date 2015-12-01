import numpy as np

from numpy.polynomial import Chebyshev, Legendre, Laguerre, Hermite
from solver.constants import LEGENDRE, LEGENDRE_SYMBOL, LAGUERRE, LAGUERRE_SYMBOL, HERMITE, HERMITE_SYMBOL, \
    CHEBYSHEV_SYMBOL

DOM = np.array([0, 1])
POLYNOM_MASK = '{:e}*{:s}[{:d},{:d}]^{:d}'
SPECIAL_POLYNOM_MASK = '{:e}*{:s}{:d}[x{:d},{:d}]'

__all__ = ['convert_polynom_to_string', 'convert_special_polynom_to_string', 'polynom_picker', 'DOM']


def convert_polynom_to_string(polynom, first, second, symbol='x'):
    coef = polynom.coef
    return ' + '.join([POLYNOM_MASK.format(coef[i], symbol, first, second, i) for i in reversed(range(len(coef)))])


def convert_special_polynom_to_string(polynom, first, second, symbol='C'):
    coef = polynom.coef
    return ' + '.join(
        [SPECIAL_POLYNOM_MASK.format(coef[i], symbol, i, first, second) for i in reversed(range(len(coef)))])


def polynom_picker(polynom_type):
    if polynom_type is LEGENDRE:
        return Legendre, LEGENDRE_SYMBOL
    elif polynom_type is LAGUERRE:
        return Laguerre, LAGUERRE_SYMBOL
    elif polynom_type is HERMITE:
        return Hermite, HERMITE_SYMBOL
    else:
        return Chebyshev, CHEBYSHEV_SYMBOL
