from attrs import define
from clip_tools.constants import GradientRepeatMode, GradientShape
from clip_tools.data_classes import Position, Color, ColorStop, CurvePoint, CurveList
from clip_tools.utils import read_fmt, write_fmt, read_csp_unicode_str
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
        pass

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
                assert unk4 == 16

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
            ColorStop(Color(255, 255, 255), 255, 0, 0, 0, CurveList.new())
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
