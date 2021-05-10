#!/usr/bin/env python3
"""
Integrate NsCDE's color theme with kitty.

NOTE: this script currently ignores "4-color mode", as terminals need a full 16 color
palette, and all NsCDE palette files have 8 colors. This script can (and does)
extrapolate 8 to 16, but not 4 to 16.

Copyright (c) 2021 Oliver C. Sandli

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import argparse
from operator import add, mul, sub
import sys

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
MAGENTA = (255, 0, 255)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)


class ColorConfModel:
    """A model of a kitty color conf file."""

    def __init__(self):
        """Define the model."""
        fields = [
            "foreground",
            "background",
            "cursor",
            "selection_foreground",
            "selection_background",
            "color0",
            "color1",
            "color2",
            "color3",
            "color4",
            "color5",
            "color6",
            "color7",
            "color8",
            "color9",
            "color10",
            "color11",
            "color12",
            "color13",
            "color14",
            "color15",
        ]
        self.entries = {f: tuple() for f in fields}


def tw_to_rgb(thxs):
    """
    Convert a 12-digit hex color to RGB.

    Parameters
    ----------
    thxs : str
        A 12-digit hex color string.

    Returns
    -------
    tuple[int]
        An RGB tuple.
    """
    if len(thxs) != 13:
        if len(thxs) == 12:
            raise ValueError("thxs is not correctly formatted (#xxxxxxxxxxxx).")
        else:
            print(thxs)
            raise ValueError("thxs must be 12 digits long with '#' at the beginning.")
    return (int(thxs[1:3], 16), int(thxs[5:7], 16), int(thxs[9:11], 16))


def rgb_to_hex(rgb):
    """
    Convert RGB tuple to hex.

    Parameters
    ----------
    rgb : tuple[int]
        An RGB tuple.

    Returns
    -------
    str
        A hex color string.
    """
    return f"#{rgb[0]:x}{rgb[1]:x}{rgb[2]:x}".upper()


def brighten(rgb, values=(20, 20, 20)):
    """
    Brighten an RGB color.

    If the brightened color is over (255, 255, 255), subtract `values` instead of adding
    `values`, effectively dimming the color. If this results in a negative number,
    return the original color. This is implemented to guarantee a valid (and hopefully
    different) color is returned.

    Parameters
    ----------
    rgb : tuple[int]
        An RGB tuple.
    values : tuple[int], optional
        Amount of brightening to apply to R, G, B respectively.

    Returns
    -------
    tuple[int]
        A brightened RGB color.
    """
    # Apply brightness.
    br_color = tuple(map(add, rgb, values))
    if any(i > 255 for i in br_color):
        br_color = tuple(map(sub, rgb, values))
    if any(i < 0 for i in br_color):
        br_color = rgb

    # Make sure elements are ints.
    br_color = tuple(map(round, br_color))

    return br_color


def text_color(bg):
    """
    Determine text color based off background color.

    Parameters
    ----------
    bg : tuple[int]
        Background RGB color.

    Returns
    -------
    tuple[int]
        Foreground RGB color.
    """
    luminance = sum(map(mul, (0.299, 0.587, 0.114), bg)) / 255
    if luminance > 0.5:
        fg = (0, 0, 0)
    else:
        fg = (255, 255, 255)
    return fg


def closest_color(rgb, colors):
    """
    Determine the closest color in `colors` to `rgb`.

    WARNING: this function is *destructive*. It removes the result from the input
    `colors` list. This is to prevent overlapping colors in the color assignment below
    (starting line 263). It is recommended to pass a copied list to this function if you
    wish to protect the original list.

    Parameters
    ----------
    rgb : tuple[int]
        An RGB color.
    colors : list[tuple[int]]

    Returns
    -------
    tuple[int]
        An RGB color.
    """
    r, g, b = rgb
    color_diffs = []
    for color in colors:
        cr, cg, cb = color
        color_diff = (abs(r - cr) ** 2 + abs(g - cg) ** 2 + abs(b - cb) ** 2) ** (1 / 2)
        color_diffs.append((color_diff, color))
    result = min(color_diffs)[1]
    colors.remove(result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Integrate kitty's color theme with NsCDE."
    )
    parser.add_argument("path", help="Path to NsCDE palette (*.dp) file.")
    parser.add_argument("theme", help="Destination of generated kitty theme.")
    parser.add_argument(
        "ncolors", type=int, help="Size of NsCDE palette (4 color mode is ignored)."
    )
    parser.add_argument(
        "--brightness",
        action="store",
        type=int,
        default=20,
        choices=range(0, 256),
        help=(
            "Specify the overall amount of brightness to add (on a range of 0-255)."
            " This is overwritten by the r, g, b flags, respectively."
        ),
    )
    parser.add_argument(
        "-r",
        action="store",
        type=int,
        default=0,
        choices=range(0, 256),
        help="Specify the amount of brightness to add to red elements (R, x, x).",
    )
    parser.add_argument(
        "-g",
        action="store",
        type=int,
        default=0,
        choices=range(0, 256),
        help="Specify the amount of brightness to add to green elements (x, G, x).",
    )
    parser.add_argument(
        "-b",
        action="store",
        type=int,
        default=0,
        choices=range(0, 256),
        help="Specify the amount of brightness to add to blue elements (x, x, B).",
    )
    parser.add_argument(
        "--vibrant", action="store_true", help="Generate more vibrant colors."
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        help=(
            "Enable silent exiting on any handled exceptions (the program will"
            " simply exit on an error instead of crashing)."
        ),
    )
    args = parser.parse_args()

    # Apply r, g, b flags to brightness.
    brightness = tuple(
        map(
            lambda x, y: x if x > 0 else y,
            [args.r, args.g, args.b],
            [args.brightness] * 3,
        )
    )

    # Read the NsCDE palette file into `colors_12d`.
    try:
        with open(args.path, "r") as f:
            colors_12d = f.readlines()
    except Exception as e:
        if args.silent:
            # Silently exit.
            sys.exit(0)
        else:
            raise e

    # Convert the 12-digit colors to RGB.
    colors = [tw_to_rgb(i.strip()) for i in colors_12d]

    if args.vibrant:
        colors = [brighten(i, brightness) for i in colors]
        bright_colors = [brighten(i, brightness * 2) for i in colors]
    else:
        bright_colors = [brighten(i, brightness) for i in colors]

    # Create and populate a kitty color conf model.
    conf = ColorConfModel()

    if args.ncolors in [8, 4]:
        conf.entries["background"] = closest_color(BLACK, colors)
        fg = text_color(conf.entries["background"])
        conf.entries["foreground"] = fg
        conf.entries["cursor"] = closest_color(YELLOW, colors)
        conf.entries["selection_foreground"] = conf.entries["background"]
        conf.entries["selection_background"] = conf.entries["foreground"]

        # Black
        conf.entries["color0"] = conf.entries["background"]
        conf.entries["color8"] = closest_color(BLACK, bright_colors)

        # Red
        conf.entries["color1"] = closest_color(RED, colors)
        conf.entries["color9"] = closest_color(RED, bright_colors)

        # Green
        conf.entries["color2"] = closest_color(GREEN, colors)
        conf.entries["color10"] = closest_color(GREEN, bright_colors)

        # Yellow
        conf.entries["color3"] = conf.entries["cursor"]
        conf.entries["color11"] = closest_color(YELLOW, bright_colors)

        # Blue
        conf.entries["color4"] = closest_color(BLUE, colors)
        conf.entries["color12"] = closest_color(BLUE, bright_colors)

        # Magenta
        conf.entries["color5"] = closest_color(MAGENTA, colors)
        conf.entries["color13"] = closest_color(MAGENTA, bright_colors)

        # Cyan
        conf.entries["color6"] = closest_color(CYAN, colors)
        conf.entries["color14"] = closest_color(CYAN, bright_colors)

        # White
        conf.entries["color7"] = closest_color(WHITE, colors)
        conf.entries["color15"] = closest_color(WHITE, bright_colors)
        # raise ValueError("4 color mode not currently supported.")
    else:
        raise ValueError("ncolors must be either 8 or 4.")

    try:
        # Write to the kitty color conf location.
        with open(args.theme, "w") as f:
            f.write("### Color theme generated by nscde-kitty-integ.py.\n")
            f.write(f"### NsCDE theme: {args.path}\n")
            for e in conf.entries:
                f.write(f"{e} {rgb_to_hex(conf.entries[e])}\n")
    except Exception as e:
        if args.silent:
            # Silently exit.
            sys.exit(0)
        else:
            raise e
