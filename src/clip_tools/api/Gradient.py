from attrs import define
from clip_tools.constants import GradientRepeatMode, GradientShape
from clip_tools.data_classes import Position, Color, ColorStop, CurvePoint, CurveList
from clip_tools.utils import read_fmt, write_fmt, read_csp_unicode_str, write_csp_unicode_str
import io

from collections import namedtuple

@define
class Gradient():

    #TODO Replace by GradientMap from corrections
    color_stops: list

    repeat_mode: GradientRepeatMode
    shape: GradientShape

    anti_aliasing: bool

    diameter: float
    ellipse_diameter: float

    rotation_angle: float

    start: Position
    end: Position

    is_flat: bool
    fill_color: Color

    def add_stop(self, color_stop):
        # TODO Add data validation on stop position [0, 100] & strictly increasing order
        self.color_stops.append(color_stop)

    def clear_stops(self):
        self.color_stops.clear()

    def to_bytes(self):

        gradient_data = io.BytesIO()

        write_fmt(gradient_data, ">i", 0)
        write_fmt(gradient_data, ">i", 2)

        # Gradation Data
        write_csp_unicode_str(">i", gradient_data, "GradationData")

        gradation_size_offset = gradient_data.tell()
        write_fmt(gradient_data, ">i", 0)

        write_fmt(gradient_data, ">i", 16)
        write_fmt(gradient_data, ">i", 28)
        write_fmt(gradient_data, ">i", len(self.color_stops))

        write_fmt(gradient_data, ">i", 16)

        for color_stop in self.color_stops:
            color_stop.color.write(gradient_data)

            write_fmt(gradient_data, ">I", color_stop.opacity << 24)
            write_fmt(gradient_data, ">i", int(color_stop.is_current_color))
            write_fmt(gradient_data, ">i", ((color_stop.position * 32768) // 100) + 100) # +100 is offset for rounding for a scale over 100 instead of 256
            write_fmt(gradient_data, ">i", color_stop.curve_points.point_count)

        for color_stop in self.color_stops:
            if color_stop.curve_points.point_count != 0:
                for point in color_stop.curve_points.points:
                    point.write(gradient_data, ">d")

        gradation_size = gradient_data.tell() - gradation_size_offset - 4

        # Gradient setting
        write_csp_unicode_str(">i", gradient_data, "GradationSetting")

        write_fmt(gradient_data, ">i", self.repeat_mode)
        write_fmt(gradient_data, ">i", self.shape)
        write_fmt(gradient_data, ">i", int(self.anti_aliasing))
        write_fmt(gradient_data, ">d", self.diameter)
        write_fmt(gradient_data, ">d", self.ellipse_diameter)
        write_fmt(gradient_data, ">d", self.rotation_angle)
        self.start.write(gradient_data)
        self.end.write(gradient_data)

        # Flat gradient
        write_csp_unicode_str(">i", gradient_data, "GradationSettingAdd0001")
        write_fmt(gradient_data, ">i", 0x14)

        write_fmt(gradient_data, ">i", int(self.is_flat))
        self.fill_color.write(gradient_data)
        write_fmt(gradient_data, ">i", 1)

        # Sizes
        total_size = gradient_data.tell()
        gradient_data.seek(0)
        write_fmt(gradient_data, ">i", total_size)

        gradient_data.seek(gradation_size_offset)
        write_fmt(gradient_data, ">i", gradation_size)

        return gradient_data.getbuffer().tobytes()

    @classmethod
    def from_bytes(cls, gradation_fill_info):

        gradient_data = io.BytesIO(gradation_fill_info)

        gradient_data_size = read_fmt(">i", gradient_data)
        unk1 = read_fmt(">i", gradient_data) # Always '0x02'
        assert unk1 == 2

        gradient_info = {}

        while gradient_data.tell() < gradient_data_size:

            param_name = read_csp_unicode_str(">i", gradient_data)

            if param_name == "GradationData":

                section_size = read_fmt(">i", gradient_data)
                unk2 = read_fmt(">i", gradient_data)
                assert unk2 == 16

                unk3 = read_fmt(">i", gradient_data)
                assert unk3 == 28

                num_color_stop = read_fmt(">i", gradient_data)
                unk4 = read_fmt(">i", gradient_data)
                assert unk4 == 16, unk4

                color_stops = []

                for _ in range(num_color_stop):

                    rgb = Color.read(gradient_data)

                    opacity = read_fmt(">I", gradient_data) >> 24
                    is_current_color = read_fmt(">i", gradient_data)
                    position = read_fmt(">i", gradient_data) * 100 // 32768
                    num_curve_points = read_fmt(">i", gradient_data)

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
                            point = CurvePoint.read(gradient_data, ">d")

                            # To look into, these ones are floats while curve points are usually ints
                            color_stop.curve_points.add_point(point)

                gradient_info["color_stops"] = color_stops

            if param_name == "GradationSettingAdd0001":
                section_size = read_fmt(">i", gradient_data)

                gradient_info["is_flat"] = bool(read_fmt(">i", gradient_data))
                gradient_info["fill_color"] = Color.read(gradient_data)

                read_fmt(">i", gradient_data)

            if param_name == "GradationSetting":

                gradient_info["repeat_mode"] = GradientRepeatMode(read_fmt(">i", gradient_data))
                gradient_info["shape"] = GradientShape(read_fmt(">i", gradient_data))

                gradient_info["anti_aliasing"] = bool(read_fmt(">i", gradient_data))

                gradient_info["diameter"] = read_fmt(">d", gradient_data)
                gradient_info["ellipse_diameter"] = read_fmt(">d", gradient_data)

                gradient_info["rotation_angle"] = read_fmt(">d", gradient_data)

                gradient_info["start"] = Position.read(gradient_data)
                gradient_info["end"] = Position.read(gradient_data)

        return cls(**gradient_info)

    @classmethod
    def new(cls,
     repeat_mode = GradientRepeatMode.CLIP,
     shape = GradientShape.LINEAR,
     anti_aliasing = False,
     diameter = 100.0,
     ellipse_diameter = 100.0,
     rotation_angle = 45.0,
     start = Position(0.0, 0.0),
     end = Position(100.0, 100.0),
     is_flat = False,
     fill_color = Color()
    ):

        # Change by class.new()
        stops = [
            ColorStop(Color(0,0,0), 255, 0, 0, 0, CurveList.new()),
            ColorStop(Color(255, 255, 255), 255, 0, 100, 0, CurveList.new())
        ]

        return cls(
            stops,
            repeat_mode,
            shape,
            anti_aliasing,
            diameter,
            ellipse_diameter,
            rotation_angle,
            start,
            end,
            is_flat,
            fill_color
        )
