from collections import namedtuple
from attrs import define

from clip_tools.constants import GradientRepeatMode, GradientShape

@define
class Position():
    x: float
    y: float

@define
class Color():
    r: int
    g: int
    b: int

@define
class ColorStop():
    color: Color
    opacity: int
    is_current_color: bool
    position: Position
    num_curve_points: int
    curve_points: []

@define
class CurvePoint:
    input_point: int # TODO Default fields + validators
    output_point: int

@define
class LevelCorrection:
    input_left: int # TODO Default fields + validators
    intput_mid: int
    input_right: int
    output_left: int
    output_right: int

@define
class CurveList(list):
    pass # TODO Add verifications when adding new points (32 max, insert in order, no same input value)

@define
class Posterization():
    posterize_input: int
    posterize_output: int

@define
class EffectEdge():
    enabled: bool
    thickness: float
    color: Color

@define 
class EffectTone():
    enabled: bool
    resolution: float
    shape: GradientShape
    use_image_brightness: bool
    frequency: float
    angle: int
    noise_size: int
    noise_factor: int
    position: Position

@define
class EffectTonePosterize():
    enabled: bool
    posterization_count: int
    posterizations: []

@define
class EffectWaterEdge():
    enabled: bool
    edge_range: float
    edge_opacity: float
    edge_darkness: float
    edge_blurring: float

@define
class EffectLine():
    enabled: bool

    black_fill_enabled: bool
    black_fill_level: int

    posterize_enabled: bool

    line_width: int
    effect_threshold: int

    directions: {}

    posterization_count: int
    posterizations: {}

    anti_aliasing: bool

"""

            nmt = namedtuple("EffectEdge", ["enabled", "thickness", "rgb"])
            nmt = namedtuple("EffectTone", ["enabled", "resolution", "shape", "use_image_brightness", "frequency", "angle", "noise_size", "noise_factor", "position"])

nmt = namedtuple("EffectTonePosterize", ["enabled", "posterization_counts", "posterizations"])
nmt = namedtuple("EffectWaterEdge", ["enabled", "range", "opacity", "darkness", "blurring"])
nmt = namedtuple("EffectLine", ["enabled", "black_fill_enabled", "black_fill_level", "posterize_enabled", "line_width", "effect_threshold", "directions", "posterize_count", "posterizations", "anti_aliasing"])
"""