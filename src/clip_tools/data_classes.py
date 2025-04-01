from collections import namedtuple
from attrs import define, Factory, field

from clip_tools.constants import GradientRepeatMode, GradientShape, TextAlign, TextStyle, TextOutline, VectorFlag, VectorPointFlag
from clip_tools.utils import read_fmt, read_csp_unicode_str, read_csp_str, read_csp_unicode_le_str, attrs_range_builder, write_fmt, write_bytes, write_csp_str
# TODO Write Methods that return bytes format

@define
class Position():
    x: float
    y: float

    def write(self, io_stream, fmt = ">d"):
        write_fmt(io_stream, fmt, self.x)
        write_fmt(io_stream, fmt, self.y)

    @classmethod
    def read(cls, io_stream, fmt = ">d"):
        return cls(
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream)
        )

@define
class BBox():
    x1: int
    y1: int
    x2: int
    y2: int

    def write(self, io_stream, fmt = ">i"):
        write_fmt(io_stream, fmt, self.x1)
        write_fmt(io_stream, fmt, self.y1)
        write_fmt(io_stream, fmt, self.x2)
        write_fmt(io_stream, fmt, self.y2)

    @classmethod
    def read(cls, io_stream, fmt = ">i"):
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

    def write(self, io_stream):
        write_fmt(io_stream, ">I", self.r << 24)
        write_fmt(io_stream, ">I", self.g << 24)
        write_fmt(io_stream, ">I", self.b << 24)

    @classmethod
    def read(cls, io_stream):
        return cls(
            read_fmt(">I", io_stream) >> 24,
            read_fmt(">I", io_stream) >> 24,
            read_fmt(">I", io_stream) >> 24
        )

@define
class CurvePoint:
    # Temporary due to unusual value in gradient color stops
    input_point: float#attrs_range_builder(int, 127, [0, 255])
    output_point: float#attrs_range_builder(int, 127, [0, 255])

    def write(self, io_stream, fmt = ">i"):
        write_fmt(io_stream, fmt, self.input_point)
        write_fmt(io_stream, fmt, self.output_point)

    @classmethod
    def read(cls, io_stream, fmt = ">i"):
        return cls(
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream)
        )

    def write_short(self, io_stream):
        write_fmt(io_stream, ">H", self.input_point << 8)
        write_fmt(io_stream, ">H", self.output_point << 8)

    @classmethod
    def read_short(cls, io_stream):
        return cls(
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8
        )

@define
class CurveList():

    points = field(default=Factory(list))

    @property
    def point_count(self):
        return len(self.points)

    def add_point(self, point: CurvePoint):

        if self.point_count >= 32:
            print("Too much points in curve list")
            return

        self.points.append(point)

    def write_short(self, io_stream, padding = True):

        points_count = len(self.points)

        write_fmt(io_stream, ">h", points_count)

        for point in self.points:
            point.write_short(io_stream)

        if padding:
            write_bytes(io_stream, b'\x00' * (0x80 - (4 * points_count)))


    @classmethod
    def read_short(cls, io_stream, padding = True):
        points_count = read_fmt(">h", io_stream)

        points = cls()
        for _ in range(points_count):
            point = CurvePoint.read_short(io_stream)
            points.add_point(point)

        if padding:
            io_stream.read(0x80 - (4 * points_count)) # Point count is limited to 32

        return points


    @classmethod
    def new(cls):

        cl = cls()
        cl.add_point(CurvePoint(0, 0))
        cl.add_point(CurvePoint(255,255))
        return cl


@define
class ColorStop():
    color: Color
    opacity: int
    is_current_color: bool
    position: int
    num_curve_points: int
    curve_points: CurveList

@define
class LevelCorrection:

    input_left: int = attrs_range_builder(int, 0, [0, 255])
    intput_mid: int = attrs_range_builder(int, 127, [0, 255])
    input_right: int = attrs_range_builder(int, 255, [0, 255])

    output_left: int = attrs_range_builder(int, 0, [0, 255])
    output_right: int = attrs_range_builder(int, 255, [0, 255])

    def write(self, io_stream):
        write_fmt(io_stream, ">H", self.input_left << 8)
        write_fmt(io_stream, ">H", self.intput_mid << 8)
        write_fmt(io_stream, ">H", self.input_right << 8)

        write_fmt(io_stream, ">H", self.output_left << 8)
        write_fmt(io_stream, ">H", self.output_right << 8)

    @classmethod
    def read(cls, io_stream):
        return cls(
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8
        )


@define
class Balance():

    cyan: int = attrs_range_builder(int, 0, [-100, 100])
    magenta: int = attrs_range_builder(int, 0, [-100, 100])
    yellow: int = attrs_range_builder(int, 0, [-100, 100])

    def write(self, io_stream):
        write_fmt(io_stream, ">i", self.cyan)
        write_fmt(io_stream, ">i", self.magenta)
        write_fmt(io_stream, ">i", self.yellow)

    @classmethod
    def read(cls, io_stream):
        return cls(
            read_fmt(">i", io_stream),
            read_fmt(">i", io_stream),
            read_fmt(">i", io_stream)
        )

@define
class RulerCurvePoint():

    pos: Position
    thickness: int


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


@define
class ReadingSetting():

    reading_type: int
    reading_ratio: int
    adjust_reading: float
    space_between: float
    reading_space_free: float

    reading_font: str

    def write(self, io_stream):
        write_fmt(io_stream, "<h", self.reading_type)
        write_fmt(io_stream, "<h", self.reading_ratio)
        write_fmt(io_stream, "<h", self.adjust_reading * 100)
        write_fmt(io_stream, "<h", self.space_between * 100)
        write_fmt(io_stream, "<h", self.reading_space_free * 100)

        write_csp_str(io_stream, "<h",  self.reading_font)

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
