from attrs import define
from clip_tools.parsers import parse_gradient_info
from clip_tools.constants import GradientRepeatMode, GradientShape

from collections import namedtuple

Position = namedtuple("Position", ["x", "y"])
Color = namedtuple("Color", ["r", "g", "b"])

@define
class Gradient():

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

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, gradation_fill_info):

        gradient_info = parse_gradient_info(gradation_fill_info)
        return cls(**gradient_info)

    @classmethod
    def new(cls):
        pass