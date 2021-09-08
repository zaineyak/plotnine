from warnings import warn

from mizani.bounds import rescale_mid
from mizani.palettes import (hue_pal, brewer_pal, grey_pal,
                             gradient_n_pal, cmap_pal, cmap_d_pal,
                             desaturate_pal)

import collections
import math
from ..utils import alias
from ..doctools import document
from ..exceptions import PlotnineWarning
from .scale import scale_discrete, scale_continuous, scale_datetime


# Discrete color scales #

# Note: plotnine operates in the hcl space
@document
class scale_color_hue(scale_discrete):
    """
    Qualitative color scale with evenly spaced hues

    Parameters
    ----------
    h : float
        first hue. Must be in the range [0, 1]
        Default is ``0.01``
    l : float
        lightness. Must be in the range [0, 1]
        Default is ``0.6``
    s : float
        saturation. Must be in the range [0, 1]
        Default is ``0.65``
    colorspace : str in ``['hls', 'husl']``
        Color space to use.
        `hls <https://en.wikipedia.org/wiki/HSL_and_HSV>`_
        `husl <http://www.husl-colors.org/>`_
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'#7F7F7F'``
    """
    _aesthetics = ['color']
    na_value = '#7F7F7F'

    def __init__(self, h=.01, l=.6, s=.65, color_space='hls', **kwargs):
        self.palette = hue_pal(h, l, s, color_space=color_space)
        scale_discrete.__init__(self, **kwargs)


@document
class scale_fill_hue(scale_color_hue):
    """
    Qualitative color scale with evenly spaced hues

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']

    
@document
class scale_color_rcmap(scale_discrete):
    """
    R ggplot-style colormap

    Parameters
    ----------
    hue : tuple or float
        range of hue or single value. Values must be in the range [0, 1]
        Default is ``(0.004, 1.00399)``
    luma : tuple or float
        range of lightness or single value. Must be in the range [0, 1]
        Default is ``0.6``
    chroma : float
        range of chroma (colorfullness) or single value. Must be in the range [0, 1]
        Default is ``0.8``
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'#7F7F7F'``
    """
    _aesthetics = ['color']
    na_value = '#7F7F7F'

    def __init__(self, hue=(0.004,1.00399), chroma=0.8, luma=0.6, **kwargs):
        self.palette = lambda n: scale_color_rcmap.ggcolors(n, hue = hue, chroma=chroma, luma=luma)
        scale_discrete.__init__(self, **kwargs)

    @staticmethod
    def ggcolors(n, hue=(0.004,1.00399), chroma=0.8, luma=0.6, skipHue=True) :
        # Assume:
        #   n: integer >= 1
        #   hue[from, to]: all floats - red = 0; green = 0.33333 (or -0.66667) ; blue = 0.66667 (or -0.33333)
        #   chroma[from, to]: floats all in range 0 .. 1
        #   luma[from, to]: floats all in range 0 .. 1
        # Returns a list of #rgb colour strings:

        # convert stand alone values to ranges
        if not isinstance(hue, collections.Iterable):
            hue = (hue, hue)
        if not isinstance(chroma, collections.Iterable):
            chroma = (chroma, chroma)
        if not isinstance(luma, collections.Iterable):
            luma = (luma, luma)

        # convert ints to floats
        hue = [float(hue[y]) for y in (0, 1)]
        chroma = [float(chroma[y]) for y in (0, 1)]
        luma = [float(luma[y]) for y in (0, 1)]

        # some sanity checks
        n = int(n)
        if n < 1:
            raise ValueError('n is a value between 1 and 360')
        if any([chroma[y] < 0.0 or chroma[y] > 1.0 for y in (0, 1)]) :
            raise ValueError('chroma is a value between 0 and 1')
        if any([luma[y] < 0.0 or luma[y] > 1.0 for y in (0, 1)]) :
            raise ValueError('luma is a value between 0 and 1')
                
        # generate a list of hex colour strings
        x = n + 1 if n % 2 else n
        if n > 1 :
            lDiff = (luma[1] - luma[0]) / float(n - 1.0)
            cDiff = (chroma[1] - chroma[0]) / float(n - 1.0)
            if skipHue :
                hDiff = (hue[1] - hue[0]) / float(x)
            else :
                hDiff = (hue[1] - hue[0]) / float(x - 1.0)
        else:
            hDiff = 0.0
            lDiff = 0.0
            cDiff = 0.0

        colors = []
        for i in range(n) :
            c = chroma[0] + i * cDiff
            l = luma[0] + i * lDiff
            h = math.modf(hue[0] + i * hDiff)[0]
            h = h + 1 if h < 0.0 else h
            (h, c, l) = (min(h, 0.99999999999), min(c, 1.0), min(l, 1.0))
            (h, c, l) = (max(h, 0.0), max(c, 0.0), max(l, 0.0))
            (r, g, b) = scale_color_rcmap.hcl_to_rgb(h, c, l)
            colors.append( '#%02x%02x%02x' % (int(r*255), int(g*255), int(b*255)) )
        return colors

    @staticmethod
    def hcl_to_rgb(hue=0, chroma=0, luma=0):
        # sanity checks
        hue = math.modf(float(hue))[0]
        if hue < 0 or hue >= 1 :
            raise ValueError('hue is a value greater than or equal to 0 and less than 1')
        chroma = float(chroma)
        if chroma < 0 or chroma > 1 :
            raise ValueError('chroma is a value between 0 and 1')
        luma = float(luma)
        if luma < 0 or luma > 1 :
            raise ValueError('luma is a value between 0 and 1')

        # do the conversion
        _h = hue * 6.0
        x = chroma * ( 1 - abs((_h % 2) - 1) )

        c = chroma
        if   0 <= _h and _h < 1 :
            r, g, b = (c, x, 0.0)
        elif 1 <= _h and _h < 2 :
            r, g, b = (x, c, 0.0)
        elif 2 <= _h and _h < 3 :
            r, g, b = (0.0, c, x)
        elif 3 <= _h and _h < 4 :
            r, g, b = (0.0, x, c)
        elif 4 <= _h and _h < 5 :
            r, g, b = (x, 0.0, c)
        elif 5 <= _h and _h <= 6 :
            r, g, b = (c, 0.0, x)
        else :
            r, g, b = (0.0, 0.0, 0.0)

        m = luma - (0.298839*r + 0.586811*g + 0.114350*b)
        z = 1.0
        if m < 0.0 :
            z = luma/(luma-m)
            m = 0.0
        elif m + c > 1.0 :
            z = (1.0-luma)/(m+c-luma)
            m = 1.0 - z * c
            (r, g, b) = (z*r+m, z*g+m, z*b+m)

        # clipping ...
        (r, g, b) = (min(r, 1.0), min(g, 1.0), min(b, 1.0))
        (r, g, b) = (max(r, 0.0), max(g, 0.0), max(b, 0.0))
        return (r, g, b)
        

@document
class scale_fill_rcmap(scale_color_rcmap):
    """
    R ggplot-style colormap

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']
    


@document
class scale_color_brewer(scale_discrete):
    """
    Sequential, diverging and qualitative discrete color scales

    See `colorbrewer.org <http://colorbrewer2.org/>`_

    Parameters
    ----------
    type : str in ``['seq', 'div', 'qual']``
        Type of data. Sequential, diverging or qualitative
    palette : int | str
         If a string, will use that named palette.
         If a number, will index into the list of palettes
         of appropriate type. Default is 1
    direction: int in ``[-1, 1]``
         Sets the order of colors in the scale. If 1,
         the default, colors are as output by
         mizani.palettes.brewer_pal(). If -1,
         the order of colors is reversed.
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``
    """
    _aesthetics = ['color']
    na_value = '#7F7F7F'

    def __init__(self, type='seq', palette=1, direction=1, **kwargs):
        self.palette = brewer_pal(type, palette, direction=direction)
        scale_discrete.__init__(self, **kwargs)


@document
class scale_fill_brewer(scale_color_brewer):
    """
    Sequential, diverging and qualitative color scales

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_grey(scale_discrete):
    """
    Sequential grey color scale.

    Parameters
    ----------
    start : float
        grey value at low end of palette.
        Default is 0.2
    end : float
        grey value at high end of palette
        Default is 0.8
    {superclass_parameters}
    """
    _aesthetics = ['color']

    def __init__(self, start=0.2, end=0.8, **kwargs):
        self.palette = grey_pal(start, end)
        scale_discrete.__init__(self, **kwargs)


@document
class scale_fill_grey(scale_color_grey):
    """
    Sequential grey color scale.

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


# Continuous color scales #

@document
class scale_color_gradient(scale_continuous):
    """
    Create a 2 point color gradient

    Parameters
    ----------
    low : str
        low color
    high : str
        high color
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``

    See Also
    --------
    :class:`.scale_color_gradient2`
    :class:`.scale_color_gradientn`
    """
    _aesthetics = ['color']
    guide = 'colorbar'
    na_value = '#7F7F7F'

    def __init__(self, low='#132B43', high='#56B1F7', **kwargs):
        """
        Create colormap that will be used by the palette
        """
        self.palette = gradient_n_pal([low, high],
                                      name='gradient')
        scale_continuous.__init__(self, **kwargs)


@document
class scale_fill_gradient(scale_color_gradient):
    """
    Create a 2 point color gradient

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_desaturate(scale_continuous):
    """
    Create a desaturated color gradient

    Parameters
    ----------
    color : str, optional (Default: 'red')
        Color to desaturate
    prop : float, optional (Default: 0)
        Saturation channel of color will be multiplied by
        this value.
    reverse : bool, optional (Default: False)
        Whether to go from color to desaturated color
        or desaturated color to color.
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``
    """
    _aesthetics = ['color']
    guide = 'colorbar'
    na_value = '#7F7F7F'

    def __init__(self, color='red', prop=0, reverse=False,
                 **kwargs):
        self.palette = desaturate_pal(color, prop, reverse)
        scale_continuous.__init__(self, **kwargs)


@document
class scale_fill_desaturate(scale_color_desaturate):
    """
    Create a desaturated color gradient

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_gradient2(scale_continuous):
    """
    Create a 3 point diverging color gradient

    Parameters
    ----------
    low : str, optional
        low color
    mid : str, optional
        mid point color
    high : str, optional
        high color
    midpoint : float, optional (Default: 0)
        Mid point of the input data range.
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``

    See Also
    --------
    :class:`.scale_color_gradient`
    :class:`.scale_color_gradientn`
    """
    _aesthetics = ['color']
    guide = 'colorbar'
    na_value = '#7F7F7F'

    def __init__(self, low='#832424', mid='#FFFFFF',
                 high='#3A3A98', midpoint=0,
                 **kwargs):
        # All rescale functions should have the same signature
        def _rescale_mid(*args, **kwargs):
            return rescale_mid(*args,  mid=midpoint, **kwargs)

        kwargs['rescaler'] = _rescale_mid
        self.palette = gradient_n_pal([low, mid, high],
                                      name='gradient2')
        scale_continuous.__init__(self, **kwargs)


@document
class scale_fill_gradient2(scale_color_gradient2):
    """
    Create a 3 point diverging color gradient

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_gradientn(scale_continuous):
    """
    Create a n color gradient

    Parameters
    ----------
    colors : list
        list of colors
    values : list, optional
        list of points in the range [0, 1] at which to
        place each color. Must be the same size as
        `colors`. Default to evenly space the colors
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``

    See Also
    --------
    :class:`.scale_color_gradient`
    :class:`.scale_color_gradientn`
    """
    _aesthetics = ['color']
    guide = 'colorbar'
    na_value = '#7F7F7F'

    def __init__(self, colors, values=None, **kwargs):
        self.palette = gradient_n_pal(colors, values, 'gradientn')
        scale_continuous.__init__(self, **kwargs)


@document
class scale_fill_gradientn(scale_color_gradientn):
    """
    Create a n color gradient

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_distiller(scale_color_gradientn):
    """
    Sequential and diverging continuous color scales

    This is a convinience scale around :class:`.scale_color_gradientn`
    with colors from `colorbrewer.org <http://colorbrewer2.org/>`_.
    It smoothly interpolates 7 colors from a brewer palette to create
    a continuous palette.

    Parameters
    ----------
    type : str in ``['seq', 'div']``
        Type of data. Sequential, diverging or qualitative
    palette : int | str
         If a string, will use that named palette.
         If a number, will index into the list of palettes
         of appropriate type. Default is 1
    values : list, optional
        list of points in the range [0, 1] at which to
        place each color. Must be the same size as
        `colors`. Default to evenly space the colors
    direction: int in ``[-1, 1]``
        Sets the order of colors in the scale. If 1
        colors are as output by mizani.palettes.brewer_pal().
        If -1, the default, the order of colors is reversed.
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``
    """
    _aesthetics = ['color']
    guide = 'colorbar'
    na_value = '#7F7F7F'

    def __init__(self, type='seq', palette=1,
                 values=None, direction=-1, **kwargs):
        """
        Create colormap that will be used by the palette
        """
        if type.lower() in ('qual', 'qualitative'):
            warn("Using a discrete color palette in a continuous scale."
                 "Consider using type = 'seq' or type = 'div' instead",
                 PlotnineWarning)

        # Grab 7 colors from brewer and create a gradient palette
        # An odd number matches the midpoint of the palette to that
        # of the data
        colors = brewer_pal(type, palette, direction=direction)(7)
        scale_color_gradientn.__init__(self, colors, values, **kwargs)


@document
class scale_fill_distiller(scale_color_distiller):
    """
    Sequential, diverging continuous color scales

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


# matplotlib colormaps
@document
class scale_color_cmap(scale_continuous):
    """
    Create color scales using Matplotlib colormaps

    Parameters
    ----------
    cmap_name : str
        A standard Matplotlib colormap name. The default is
        `viridis`. For the list of names checkout the output
        of ``matplotlib.cm.cmap_d.keys()`` or see the
        `documentation <http://matplotlib.org/users/colormaps.html>`_.
    lut : None | int
        This is the number of entries desired in the
        lookup table. Default is `None`, leave it up
        Matplotlib.
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``

    See Also
    --------
    :mod:`matplotlib.cm`
    :mod:`matplotlib.colors`
    """
    _aesthetics = ['color']
    guide = 'colorbar'
    na_value = '#7F7F7F'

    def __init__(self, cmap_name='viridis', lut=None, **kwargs):
        self.palette = cmap_pal(cmap_name, lut)
        super(scale_color_cmap, self).__init__(**kwargs)


@document
class scale_fill_cmap(scale_color_cmap):
    """
    Create color scales using Matplotlib colormaps

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_cmap_d(scale_discrete):
    """
    A discrete color scales using Matplotlib colormaps

    Parameters
    ----------
    name : str
        A standard Matplotlib colormap name. It must be of type
        :class:`matplotlib.colors.ListedColormap`.
        . The default is `viridis`. For the list of names checkout
        the output of ``matplotlib.cm.cmap_d.keys()`` or see the
        `documentation <http://matplotlib.org/users/colormaps.html>`_.
    lut : None | int
        This is the number of entries desired in the
        lookup table. Default is `None`, leave it up
        Matplotlib.
    {superclass_parameters}
    na_value : str
        Color of missing values. Default is ``'None'``

    See Also
    --------
    :mod:`matplotlib.cm`
    :mod:`matplotlib.colors`
    """
    _aesthetics = ['color']
    na_value = '#7F7F7F'

    def __init__(self, name='viridis', lut=None, **kwargs):
        self.palette = cmap_d_pal(name, lut)
        super(scale_color_cmap_d, self).__init__(**kwargs)


@document
class scale_fill_cmap_d(scale_color_cmap_d):
    """
    Create color scales using Matplotlib colormaps

    Parameters
    ----------
    {superclass_parameters}
    """
    _aesthetics = ['fill']


@document
class scale_color_datetime(scale_datetime, scale_color_cmap):
    """
    Datetime color scale

    Parameters
    ----------
    {superclass_parameters}
    """


@document
class scale_fill_datetime(scale_datetime, scale_fill_cmap):
    """
    Datetime fill scale

    Parameters
    ----------
    {superclass_parameters}
    """


# Default scales
alias('scale_color_discrete', scale_color_hue)
alias('scale_color_continuous', scale_color_cmap)
alias('scale_color_ordinal', scale_color_cmap_d)
alias('scale_fill_discrete', scale_fill_hue)
alias('scale_fill_continuous', scale_fill_cmap)
alias('scale_fill_ordinal', scale_fill_cmap_d)

# American to British spelling
alias('scale_colour_hue', scale_color_hue)
alias('scale_color_gray', scale_color_grey)
alias('scale_colour_grey', scale_color_grey)
alias('scale_colour_gray', scale_color_grey)
alias('scale_fill_gray', scale_fill_grey)
alias('scale_colour_brewer', scale_color_brewer)
alias('scale_colour_desaturate', scale_color_desaturate)
alias('scale_colour_gradient', scale_color_gradient)
alias('scale_colour_gradient2', scale_color_gradient2)
alias('scale_colour_gradientn', scale_color_gradientn)
alias('scale_colour_discrete', scale_color_hue)
alias('scale_colour_continuous', scale_color_cmap)
alias('scale_colour_distiller', scale_color_distiller)
alias('scale_colour_cmap', scale_color_cmap)
alias('scale_colour_rcmap', scale_color_rcmap)
alias('scale_colour_cmap_d', scale_color_cmap_d)
alias('scale_colour_datetime', scale_color_datetime)
alias('scale_colour_ordinal', scale_color_cmap_d)
