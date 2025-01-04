from attrs import define

from clip_tools.constants import TextStyle, TextJustify, TextOutline
from clip_tools.data_classes import Color

@define
class Text():
    pass

@define
class TextToken(str):

    style: TextStyle
    alignement: TextJustify
    aspect_ratio: (float, float)
    outline: TextOutline

    font: str
    font_size: float
    font_scale: float

    color: Color
