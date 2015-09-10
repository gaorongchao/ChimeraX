# vi: set expandtab shiftwidth=4 softtabstop=4:

import re
from . import cli
from ..colors import Color


class ColorArg(cli.Annotation):
    """Support color names and CSS3 color specifications.

    The CSS3 color specifications supported are: rgb, rgba, hsl, hsla, and
    gray from CSS4.

    The following examples are all ``red``, except for the gray ones::

        red
        #f00
        #0xff0000
        rgb(255, 0, 0)
        rgb(100%, 0, 0)
        rgba(100%, 0, 0, 1)
        rgba(100%, 0, 0, 100%)
        hsl(0, 100%, 50%)
        gray(128)
        gray(50%)
    """
    name = 'a color'

    @staticmethod
    def parse(text, session):
        if text[0] == '#':
            token, text, rest = cli.next_token(text)
            c = Color(token)
            c.explicit_transparency = (len(token) in (5,9,17))
            return c, text, rest
        m = _color_func.match(text)
        if m is None:
            from .colordef import _find_named_color
            color = None
            if session is not None:
                name, color, rest = _find_named_color(session.user_colors, text)
            else:
                from ..colors import _BuiltinColors
                name, color, rest = _find_named_color(_BuiltinColors, text)
            if color is None:
                raise ValueError("Invalid color name or specifier")
            return color, name, rest
        color_space = m.group(1)
        numbers = _parse_numbers(m.group(2))
        rest = text[m.end():]
        if color_space == 'gray' and len(numbers) in (1, 2):
            # gray( number [%], [ number [%] ])
            try:
                x = _convert_number(numbers[0], 'gray scale')
                if len(numbers) == 2:
                    alpha = _convert_number(numbers[1], 'alpha', maximum=1)
                else:
                    alpha = 1
            except cli.AnnotationError as err:
                err.offset += m.end(1)
                raise
            c = Color([x, x, x, alpha])
            c.explicit_transparency = (len(numbers) == 2)
            return c, m.group(), rest
        if color_space == 'rgb' and len(numbers) == 3:
            # rgb( number [%], number [%], number [%])
            try:
                red = _convert_number(numbers[0], 'red')
                green = _convert_number(numbers[1], 'green')
                blue = _convert_number(numbers[2], 'blue')
            except cli.AnnotationError as err:
                err.offset += m.end(1)
                raise
            c = Color([red, green, blue, 1])
            c.explicit_transparency = False
            return c, m.group(), rest
        if color_space == 'rgba' and len(numbers) == 4:
            # rgba( number [%], number [%], number [%], number [%])
            try:
                red = _convert_number(numbers[0], 'red')
                green = _convert_number(numbers[1], 'green')
                blue = _convert_number(numbers[2], 'blue')
                alpha = _convert_number(numbers[3], 'alpha', maximum=1)
            except cli.AnnotationError as err:
                err.offset += m.end(1)
                raise
            c = Color([red, green, blue, alpha])
            c.explicit_transparency = True
            return c, m.group(), rest
        if color_space == 'hsl' and len(numbers) == 3:
            # hsl( number [%], number [%], number [%])
            try:
                hue = _convert_angle(numbers[0], 'hue angle')
                sat = _convert_number(numbers[1], 'saturation',
                                      require_percent=True)
                light = _convert_number(numbers[2], 'lightness',
                                        require_percent=True)
            except cli.AnnotationError as err:
                err.offset += m.end(1)
                raise
            if sat < 0:
                sat = 0
            if light < 0:
                light = 0
            elif light > 1:
                light = 1
            import colorsys
            red, green, blue = colorsys.hls_to_rgb(hue, light, sat)
            c = Color([red, green, blue, 1])
            c.explicit_transparency = False
            return c, m.group(), rest
        if color_space == 'hsla' and len(numbers) == 4:
            # hsla( number [%], number [%], number [%], number [%])
            try:
                hue = _convert_angle(numbers[0], 'hue angle')
                sat = _convert_number(numbers[1], 'saturation',
                                      require_percent=True)
                light = _convert_number(numbers[2], 'lightness',
                                        require_percent=True)
                alpha = _convert_number(numbers[3], 'alpha', maximum=1)
            except cli.AnnotationError as err:
                err.offset += m.end(1)
                raise
            if sat < 0:
                sat = 0
            if light < 0:
                light = 0
            elif light > 1:
                light = 1
            import colorsys
            red, green, blue = colorsys.hls_to_rgb(hue, light, sat)
            c = Color([red, green, blue, alpha])
            c.explicit_transparency = True
            return c, m.group(), rest
        raise ValueError(
            "Wrong number of components for %s specifier" % color_space,
            offset=m.end())


class ColormapArg(cli.Annotation):
    """Support color map names and value-color pairs specifications.
    """
    name = 'a colormap'

    @staticmethod
    def parse(text, session):
        token, text, rest = cli.next_token(text)
        parts = token.split(':')
        if len(parts) > 1:
            values = []
            colors = []
            for p in parts:
                vc = p.split(',')
                if len(vc) == 1:
                    color, t, r = ColorArg.parse(vc[0], session)
                elif len(vc) == 2:
                    values.append(float(vc[0]))
                    color, t, r = ColorArg.parse(vc[1], session)
                else:
                    raise ValueError("Too many fields in colormap")
                if r:
                    raise ValueError("Bad color in colormap")
                colors.append(color)
            if len(values) != len(colors):
                raise ValueError("Number of values and color must match in colormap")
            from .. import colors
            return colors.Colormap(values, colors), text, rest
        else:
            if session is not None:
                i = session.user_colormaps.bisect_left(token)
                if i < len(session.user_colormaps):
                    name = session.user_colormaps.iloc[i]
                    if name.startswith(token):
                        return session.user_colormaps[name], name, rest
            from ..colors import BuiltinColormaps
            i = BuiltinColormaps.bisect_left(token)
            if i >= len(BuiltinColormaps):
                raise ValueError("Invalid colormap name")
            name = BuiltinColormaps.iloc[i]
            if not name.startswith(token):
                raise ValueError("Invalid colormap name")
            return BuiltinColormaps[name], name, rest

_color_func = re.compile(r"^(rgb|rgba|hsl|hsla|gray)\s*\(([^)]*)\)")
_number = re.compile(r"\s*[-+]?([0-9]+(\.[0-9]*)?|\.[0-9]+)")
_units = re.compile(r"\s*(%|deg|grad|rad|turn|)\s*")


def _parse_numbers(text):
    # parse comma separated list of number [units]
    result = []
    start = 0
    while 1:
        m = _number.match(text, start)
        if not m:
            raise cli.AnnotationError("Expected a number", start)
        n = float(m.group())
        n_pos = start
        start = m.end()
        m = _units.match(text, start)
        u = m.group(1)
        if not m:
            raise cli.AnnotationError("Unknown units", start)
        u_pos = start
        start = m.end()
        result.append((n, n_pos, u, u_pos))
        if start == len(text):
            return result
        if text[start] != ',':
            raise cli.AnnotationError("Expected a comma", start)
        start += 1


def _convert_number(number, name, maximum=255, require_percent=False):
    """Return number scaled to 0 <= n <= 1"""
    n, n_pos, u, u_pos = number
    if require_percent and u != '%':
        raise cli.AnnotationError("%s must be a percentage" % name, u_pos)
    if u == '':
        return n / maximum
    if u == '%':
        return n / 100
    raise cli.AnnotationError("Unexpected units for %s" % name, u_pos)


def _convert_angle(number, name):
    n, n_pos, u, u_pos = number
    if u in ('', 'deg'):
        return n / 360
    if u == 'rad':
        from math import pi
        return n / (2 * pi)
    if u == 'grad':
        return n / 400
    if u == 'turn':
        return n
    raise cli.AnnotationError("'%s' doesn't make sense for %s" % (u, name),
                              offset=u_pos)

def test():
    tests = [
        "0x00ff00",
        "#0f0",
        "#00ffff",
        "gray(50)",
        "gray(50%)",
        "rgb(0, 0, 255)",
        "rgb(100%, 0, 0)",
        "red",
        "hsl(0, 100%, 50%)",  # red
        "lime",
        "hsl(120deg, 100%, 50%)",  # lime
        "darkgreen",
        "hsl(120, 100%, 20%)",  # darkgreen
        "lightgreen",
        "hsl(120, 75%, 75%)",  # lightgreen
    ]
    for t in tests:
        print(t)
        try:
            print(ColorArg.parse(t))
        except ValueError as err:
            print(err)
    print('same:', ColorArg.parse('white')[0] == Color('#ffffff'))
