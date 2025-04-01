# FilterLayerInfo
from attrs import define, validators, field, Factory
from clip_tools.constants import CorrectionType
import binascii
import io
import logging

import math

from clip_tools.utils import read_fmt, write_fmt, write_bytes, attrs_range_builder
from clip_tools.data_classes import ColorStop, Color, Position, CurveList, CurvePoint, LevelCorrection, Balance

from collections import namedtuple

logger = logging.getLogger(__name__)

@define
class BrightnessContrast():

    brightness: int = attrs_range_builder(int, 0, [-100, 100])
    contrast: int = attrs_range_builder(int, 0, [-100, 100])

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.BRIGHTNESS_CONTRAST)
        write_fmt(io_stream, ">i", 0x08)

        write_fmt(io_stream, ">i", int(self.brightness))
        write_fmt(io_stream, ">i", int(self.contrast))

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        return cls(
            read_fmt(">i", correction_data),
            read_fmt(">i", correction_data)
        )

@define
class Level():

    rgb: LevelCorrection = field(factory=LevelCorrection)
    red: LevelCorrection = field(factory=LevelCorrection)
    green: LevelCorrection = field(factory=LevelCorrection)
    blue: LevelCorrection = field(factory=LevelCorrection)

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.LEVEL)

        offset = io_stream.tell()
        write_fmt(io_stream, ">i", 0)

        self.rgb.write(io_stream)
        self.red.write(io_stream)
        self.green.write(io_stream)
        self.blue.write(io_stream)

        size = io_stream.tell() - 8
        io_stream.seek(offset)
        write_fmt(io_stream, ">i", size)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):
        section_size = read_fmt(">i", correction_data)

        levels = []

        while correction_data.tell() < section_size + 8:
            levels.append(LevelCorrection.read(correction_data))

        # There is only 4 meaningful level tables, no idea why there are more
        return cls(levels[0],levels[1],levels[2],levels[3])

@define
class ToneCurve():

    rgb: CurveList = field(default=CurveList.new())
    red: CurveList = field(default=CurveList.new())
    green: CurveList = field(default=CurveList.new())
    blue: CurveList = field(default=CurveList.new())

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.TONE_CURVE)

        offset = io_stream.tell()
        write_fmt(io_stream, ">i", 0)

        self.rgb.write_short(io_stream)
        self.red.write_short(io_stream)
        self.green.write_short(io_stream)
        self.blue.write_short(io_stream)

        size = io_stream.tell() - 8
        io_stream.seek(offset)
        write_fmt(io_stream, ">i", size)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):
        section_size = read_fmt(">i", correction_data)

        curves = []

        while correction_data.tell() < section_size + 8:
            curves.append(CurveList.read_short(correction_data))

        # There is only 4 meaningful point tables, no idea why there are more
        return cls(curves[0], curves[1], curves[2], curves[3])

@define
class HSL():
    hue: int = attrs_range_builder(int, 0, [-180, 180])
    saturation: int = attrs_range_builder(int, 0, [-100, 100])
    luminance: int = attrs_range_builder(int, 0, [-100, 100])

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.HSL)
        write_fmt(io_stream, ">i", 0x0c)

        write_fmt(io_stream, ">i", int(self.hue))
        write_fmt(io_stream, ">i", int(self.saturation))
        write_fmt(io_stream, ">i", int(self.luminance))

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        return cls(
            read_fmt(">i", correction_data),
            read_fmt(">i", correction_data),
            read_fmt(">i", correction_data)
        )

@define
class ColorBalance():

    keep_brightness: bool = True

    shadows: Balance = field(factory=Balance)
    midtones: Balance = field(factory=Balance)
    highlight: Balance = field(factory=Balance)

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.COLOR_BALANCE)
        write_fmt(io_stream, ">i", 0x28)
        write_fmt(io_stream, ">i", int(self.keep_brightness))

        self.shadows.write(io_stream)
        self.midtones.write(io_stream)
        self.highlight.write(io_stream)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)

        keep_brightness = bool(read_fmt(">i", correction_data))

        balance_shadow = Balance.read(correction_data)
        balance_midtones = Balance.read(correction_data)
        balance_highlight = Balance.read(correction_data)

        return cls(keep_brightness, balance_shadow, balance_midtones, balance_highlight)

@define
class ReverseGradient():

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.REVERSE_GRADIENT)
        write_fmt(io_stream, ">i", 0)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):
        # There's no meaningful data in this glob
        return cls()

@define
class Posterization():

    level: int = attrs_range_builder(int, 8, [2, 20])

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.POSTERIZATION)
        write_fmt(io_stream, ">i", 4)
        write_fmt(io_stream, ">i", self.level)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        return cls(read_fmt(">i", correction_data))

@define
class Threshold():
    level: int = attrs_range_builder(int, 127, [1, 255])

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.THRESHOLD)
        write_fmt(io_stream, ">i", 4)
        write_fmt(io_stream, ">i", self.level)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        return cls(read_fmt(">i", correction_data))

@define
class GradientMap():

    color_stops: list

    def to_bytes(self):

        io_stream = io.BytesIO()

        write_fmt(io_stream, ">i", CorrectionType.GRADIENT_MAP)
        size_offset = io_stream.tell()
        write_fmt(io_stream, ">i", 0)
        write_fmt(io_stream, ">i", 0)

        write_fmt(io_stream, ">i", 16)
        write_fmt(io_stream, ">i", 28)

        write_fmt(io_stream, ">i", len(self.color_stops))

        write_fmt(io_stream, ">i", 16)

        for stop in self.color_stops:
            stop.color.write(io_stream)

            write_fmt(io_stream, ">I", stop.opacity << 24)
            write_fmt(io_stream, ">i", stop.is_current_color)
            write_fmt(io_stream, ">i", (stop.position * 32768 // 100) + 100) # +100 is offset for rounding
            write_fmt(io_stream, ">i", stop.curve_points.point_count)

        for stop in self.color_stops:
            for point in stop.curve_points.points:
                point.write(io_stream, ">d")

        g_size = io_stream.tell() - 8
        io_stream.seek(size_offset)
        write_fmt(io_stream, ">i", g_size)
        write_fmt(io_stream, ">i", g_size - 4)

        io_stream.seek(0)
        return io_stream.read()

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)

        gradient_section_size = read_fmt(">i", correction_data)
        unk2 = read_fmt(">i", correction_data)
        assert unk2 == 16

        unk3 = read_fmt(">i", correction_data)
        assert unk3 == 28

        num_color_stop = read_fmt(">i", correction_data)

        unk4 = read_fmt(">i", correction_data)
        assert unk4 == 16

        color_stops = []

        for _ in range(num_color_stop):

            rgb = Color.read(correction_data)

            opacity = read_fmt(">I", correction_data) >> 24
            is_current_color = read_fmt(">i", correction_data)
            position = math.ceil(read_fmt(">i", correction_data) * 100 // 32768)
            num_curve_points = read_fmt(">i", correction_data)

            curve_points = CurveList()

            color_stops.append(
                ColorStop(
                    rgb,
                    opacity,
                    is_current_color,
                    position,
                    num_curve_points,
                    curve_points
                )
            )

        for color_stop in color_stops:
            if color_stop.num_curve_points != 0:
                for _ in range(color_stop.num_curve_points):
                    point = CurvePoint.read(correction_data, ">d")

                    # To look into, these ones are floats while curve points are usually ints
                    color_stop.curve_points.add_point(point)

        return cls(color_stops)

    @classmethod
    def new(cls):
        return cls([
            ColorStop(Color(0, 0, 0), 100, 0, 0, 0, CurveList.new()),
            ColorStop(Color(255, 255, 255), 100, 0, 100, 0, CurveList.new())
        ])


def parse_correction_attributes(correction_attributes):

    correction_data = io.BytesIO(correction_attributes)

    correction_type = read_fmt(">i", correction_data)

    if correction_type == CorrectionType.BRIGHTNESS_CONTRAST:
        return BrightnessContrast.from_bytes(correction_data)

    if correction_type == CorrectionType.LEVEL:
        return Level.from_bytes(correction_data)

    if correction_type == CorrectionType.TONE_CURVE:
        return ToneCurve.from_bytes(correction_data)

    if correction_type == CorrectionType.HSL:
        return HSL.from_bytes(correction_data)

    if correction_type == CorrectionType.COLOR_BALANCE:
        return ColorBalance.from_bytes(correction_data)

    if correction_type == CorrectionType.REVERSE_GRADIENT:
        return ReverseGradient.from_bytes(correction_data)

    if correction_type == CorrectionType.POSTERIZATION:
        return Posterization.from_bytes(correction_data)

    if correction_type == CorrectionType.THRESHOLD:
        return Threshold.from_bytes(correction_data)

    if correction_type == CorrectionType.GRADIENT_MAP:
        return GradientMap.from_bytes(correction_data)
