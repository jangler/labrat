"""
This module contains functions for converting colors between integers,
RGB tuples, XYZ tuples, and LAB tuples.
"""

# reference white determined experimentally
_XN, _YN, _ZN = 0.96, 1.01, 1.10


# helper function for XYZ conversion
def _f(t):
    if t > 0.008856:
        return pow(t, 1/3)
    return 7.787 * t + 16/116


# limit a value between a minimum and maximum
def _lim(minimum, val, maximum):
    return max(minimum, min(val, maximum))


def rgb_from_int(val):
    """Return an RGB tuple converted from an int in the range [0, 0xffffff]."""
    return tuple([
        ((val >> 16) & 0xff) / 0xff,
        ((val >> 8) & 0xff) / 0xff,
        (val & 0xff) / 0xff])


def int_from_rgb(rgb):
    """Return an int in the range [0, 0xffffff] converted from an RGB tuple."""
    return (round(rgb[0] * 0xff) << 16) + \
        (round(rgb[1] * 0xff) << 8) + \
        round(rgb[2] * 0xff)


def xyz_from_rgb(rgb):
    """Return an XYZ tuple converted from an RGB tuple."""
    return tuple([
        0.412453 * rgb[0] + 0.357580 * rgb[1] + 0.180423 * rgb[2],
        0.212671 * rgb[0] + 0.715160 * rgb[1] + 0.072169 * rgb[2],
        0.019334 * rgb[0] + 0.119193 * rgb[1] + 0.950227 * rgb[2]])


def rgb_from_xyz(xyz):
    """Return an RGB tuple converted from an XYZ tuple."""
    return tuple([
        _lim(0, 3.240479 * xyz[0] - 1.537150 * xyz[1] - 0.498535 * xyz[2], 1),
        _lim(0, -0.969256 * xyz[0] + 1.875992 * xyz[1] + 0.041556 * xyz[2], 1),
        _lim(0, 0.055648 * xyz[0] - 0.204043 * xyz[1] + 1.057311 * xyz[2], 1)])


def lab_from_xyz(xyz):
    """Return an LAB tuple converted from an XYZ tuple."""
    if xyz[1] / _YN > 0.008856:
        l = 116 * pow(xyz[1] / _YN, 1/3) - 16
    else:
        l = 903.3 * xyz[1] / _YN
    return tuple([
        l,
        500 * (_f(xyz[0] / _XN) - _f(xyz[1] / _YN)),
        200 * (_f(xyz[1] / _YN) - _f(xyz[2] / _ZN))])


def xyz_from_lab(lab):
    """Return an XYZ tuple converted from an LAB tuple."""
    base = (lab[0] + 16) / 116
    return tuple([
        _XN * pow(base + lab[1] / 500, 3),
        _YN * pow(base, 3),
        _ZN * pow(base - lab[2] / 200, 3)])
