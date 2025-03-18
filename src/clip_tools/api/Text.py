from attrs import define

from clip_tools.constants import TextStyle, TextAlign, TextOutline, TextWrapDirection
from clip_tools.data_classes import Color, BBox, TextBackground, TextEdge

"""{<TextAttribute.RUNS: 11>: [
        TextRun(start=0, length=19, style_flag=0, default_style_flag=0, color=Color(r=0, g=0, b=0), font_scale=0.0, font=''), 
        TextRun(start=19, length=6, style_flag=1, default_style_flag=0, color=Color(r=0, g=0, b=0), font_scale=0.0, font=''), 
        TextRun(start=25, length=13, style_flag=3, default_style_flag=0, color=Color(r=0, g=0, b=0), font_scale=0.0, font=''), 
        TextRun(start=38, length=13, style_flag=2, default_style_flag=0, color=Color(r=0, g=0, b=0), font_scale=0.0, font=''), 
        TextRun(start=51, length=20, style_flag=0, default_style_flag=0, color=Color(r=0, g=0, b=0), font_scale=0.0, font=''), 
        TextRun(start=71, length=7, style_flag=0, default_style_flag=2, color=Color(r=0, g=0, b=0), font_scale=200.0, font=''), 
        TextRun(start=78, length=2, style_flag=0, default_style_flag=2, color=Color(r=0, g=0, b=0), font_scale=100.0, font=''), 
        TextRun(start=80, length=13, style_flag=0, default_style_flag=1, color=Color(r=1, g=1, b=1), font_scale=0.0, font='')
    ], 
    <TextAttribute.ASPECT_RATIO: 26>: [
        (0, 93, (100.0, 100.0))
    ], 
    <TextAttribute.ALIGN: 12>: [
        TextParam(attribute=<TextAttribute.ALIGN: 12>, start=0, length=93, value=<TextJustify.CENTER: 2>)
    ], 
    <TextAttribute.LINE_SPACING: 13>: [
        (0, 93, 1, 0.0, 120.0)
    ], 
    <TextAttribute.UNDERLINE: 16>: [
        TextParam(attribute=<TextAttribute.UNDERLINE: 16>, start=51, length=11, value=True), 
        TextParam(attribute=<TextAttribute.UNDERLINE: 16>, start=62, length=31, value=False)
    ], 
    <TextAttribute.STRIKE: 20>: [
        TextParam(attribute=<TextAttribute.STRIKE: 20>, start=62, length=9, value=True), 
        TextParam(attribute=<TextAttribute.STRIKE: 20>, start=71, length=22, value=False)
    ], 
    <TextAttribute.OUTLINE: 18>: [
        (0, 93, <TextOutline.NONE: 0>)
    ], 
    <TextAttribute.FONT: 31>: b'CCComicrazy', 
    <TextAttribute.FONT_SIZE: 32>: 10.0, 
    <TextAttribute.GLOBAL_STYLE: 33>: <TextStyle: 0>, 
    <TextAttribute.GLOBAL_COLOR: 34>: Color(r=0, g=0, b=0), 
    <TextAttribute.GLOBAL_JUSTIFY: 35>: <TextJustify.CENTER: 2>, 
    <TextAttribute.HORZ_IN_VERT: 38>: 2, 
    <TextAttribute.BBOX: 42>: BBox(x1=167, y1=141, x2=889, y2=1013), 
    <TextAttribute.READING_SETTING: 47>: ReadingSetting(reading_type=4, reading_ratio=50, adjust_reading=0.0, space_between=0.0, reading_space_free=0.0, reading_font='Tahoma'),
    <TextAttribute.WRAP_FRAME: 53>: False, 
    <TextAttribute.WRAP_DIRECTION: 55>: <TextWrapDirection.TOP: 0>, 
    <TextAttribute.HALF_WIDTH_PUNCT: 52>: True, 
    <TextAttribute.BACKGROUND: 54>: TextBackground(enabled=0, color=Color(r=0, g=0, b=0), opacity=100), 
    <TextAttribute.EDGE: 56>: TextEdge(enabled=0, size=1, color=Color(r=255, g=255, b=255)), 
    <TextAttribute.TEXT_ID: 50>: 175, 
    <TextAttribute.FONTS: 57>: [['CCComicrazy', 'CCComicrazy-Roman']], 
    <TextAttribute.ROTATION_ANGLE: 58>: 180.0, 
    <TextAttribute.SKEW_ANGLE_1: 59>: 90.0, 
    <TextAttribute.SKEW_ANGLE_2: 60>: 90.0, 
    <TextAttribute.BOX_SIZE: 63>: [722, 886], 
    <TextAttribute.QUAD_VERTS: 64>: [0.0, 14.0, 722.0, 14.0, 722.0, 886.0, 0.0, 886.0]}"""

# TODO : Make a tokenizer that dynamically cuts a string depending on the style
@define
class TextToken():

    start: int
    length: int

    color: Color

    style: TextStyle
    scale: float
    align: TextAlign

    outline: TextOutline

    aspect_ratio: (float, float)

    use_relative_spacing: bool
    absolute_spacing: float
    relative_spacing: float

    def split_token(self, index):
        pass

    @classmethod
    def merge_tokens(cls, token_1, token_2):
        pass

@define
class Text():

    tokens: [TextToken]

    font: str
    font_size: float
    style: TextStyle
    color: Color

    align: TextAlign

    horizontal_in_vertical: int

    bbox: BBox

    wrap_frame: bool
    wrap_direction: TextWrapDirection

    half_width_punctuation: bool

    background: TextBackground
    edge: TextEdge

    identifier: int
    additional_fonts: []

    angle: float

    skew_angles: (float, float)

    box_size: []
    quad_verts: []

    def __repr__(self):
        pass

    @classmethod
    def read(cls, text_attributes):
        pass