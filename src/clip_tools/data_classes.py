from collections import namedtuple
from attrs import define, Factory, field

from clip_tools.constants import GradientRepeatMode, GradientShape, TextAlign, TextStyle, TextOutline, VectorFlag, VectorPointFlag
from clip_tools.utils import read_fmt, read_csp_unicode_str, read_csp_str, read_csp_unicode_le_str, attrs_range_builder
# TODO Write Methods that return bytes format

@define
class Position():
    x: float
    y: float

    @classmethod
    def read(cls, io_stream):
        return cls(read_fmt(">d", io_stream), read_fmt(">d", io_stream))

@define
class BBox():
    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def read(cls, fmt, io_stream):
        return cls(
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream)
        )

@define
class Color():
    r: int = attrs_range_builder(int, 0, [0, 255])
    g: int = attrs_range_builder(int, 0, [0, 255])
    b: int = attrs_range_builder(int, 0, [0, 255])

    @classmethod
    def read(cls, io_stream):
        return cls(
            read_fmt(">I", io_stream) >> 24,
            read_fmt(">I", io_stream) >> 24,
            read_fmt(">I", io_stream) >> 24
        )


@define
class ColorStop():
    color: Color
    opacity: int
    is_current_color: bool
    position: Position
    num_curve_points: int
    curve_points: []


@define
class LevelCorrection:

    input_left: int = attrs_range_builder(int, 0, [0, 255])
    intput_mid: int = attrs_range_builder(int, 127, [0, 255])
    input_right: int = attrs_range_builder(int, 255, [0, 255])

    output_left: int = attrs_range_builder(int, 0, [0, 255])
    output_right: int = attrs_range_builder(int, 255, [0, 255])

    @classmethod
    def read(cls, io_stream):
        return cls(read_fmt(">H", io_stream) >> 8,
                    read_fmt(">H", io_stream) >> 8,
                    read_fmt(">H", io_stream) >> 8,
                    read_fmt(">H", io_stream) >> 8,
                    read_fmt(">H", io_stream) >> 8)

@define
class CurvePoint:
    input_point = attrs_range_builder(int, 127, [0, 255])
    output_point = attrs_range_builder(int, 127, [0, 255])


@define
class CurveList():

    points: Factory(list)

    @property
    def point_count(self):
        return len(self.points)

    def add_point(self, point: CurvePoint):
        
        if self.point_count >= 32:
            return

        self.points.append(point)

    @classmethod
    def new(cls):

        cl = cls()
        cl.add_point(CurvePoint(0, 0))
        cl.add_point(CurvePoint(255,255))
        return cl


@define
class Balance():

    Cyan: int = attrs_range_builder(int, 0, [-100, 100])
    Magenta: int = attrs_range_builder(int, 0, [-100, 100])
    Yellow: int = attrs_range_builder(int, 0, [-100, 100])

    @classmethod
    def read(cls, io_stream):
        return cls(read_fmt(">i", io_stream),
                    read_fmt(">i", io_stream),
                    read_fmt(">i", io_stream))

@define
class RulerCurvePoint():

    pos: Position
    thickness: int

@define
class VectorPoint():

    position: Position
    bbox: BBox

    point_flag: VectorPointFlag

    scale:  float
    scale2: float
    scale3: float

    width: float
    opacity: float

@define
class VectorLine():

    point_count: int
    vector_flag: VectorFlag
    vector_bbox: BBox

    main_color: Color
    sub_color: Color

    opacity: float

    brush_id: int
    brush_radius: float

    points: [VectorPoint]

@define
class TextRun():

    start: int
    length: int

    style_flag: int
    default_style_flag: int
    color: Color
    font_scale: float

    font: str

@define
class TextParam():

    attribute: int

    start: int
    length: int

    value: int

@define
class ReadingSetting():

    reading_type: int
    reading_ratio: int
    adjust_reading: float
    space_between: float
    reading_space_free: float

    reading_font: str

    @classmethod
    def read(cls, io_stream):

        reading_type = read_fmt("<h", io_stream)
        reading_ratio = read_fmt("<h", io_stream)
        adjust_reading = read_fmt("<h", io_stream) / 100
        space_between = read_fmt("<h", io_stream) / 100
        reading_space_free = read_fmt("<h", io_stream) / 100

        reading_font = read_csp_str("<h", io_stream)

        return cls(
            reading_type,
            reading_ratio,
            adjust_reading,
            space_between,
            reading_space_free,
            reading_font
        )

@define
class TextBackground():

    enabled: bool
    color: Color
    opacity: int

    @classmethod
    def read(cls, io_stream):
        enabled = read_fmt("<i", io_stream)
        color = Color.read(io_stream)
        opacity = ((read_fmt("<I", io_stream) >> 24) * 100) // 255

        return cls(enabled, color, opacity)

@define
class TextEdge():
    enabled: bool
    size: int
    color:Color

    @classmethod
    def read(cls, io_stream):
        edge_enabled = read_fmt("<i", io_stream)
        edge_size = read_fmt("<i", io_stream) // 1000

        unk = read_fmt("<i", io_stream)

        edge_color = Color.read(io_stream)

        return cls(edge_enabled, edge_size, edge_color)
