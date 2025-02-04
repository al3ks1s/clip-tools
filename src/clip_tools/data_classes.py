from collections import namedtuple
from attrs import define

from clip_tools.constants import GradientRepeatMode, GradientShape, TextJustify, TextStyle, TextOutline, VectorFlag, VectorPointFlag

# TODO Write Methods that return bytes format

@define
class Position():
    x: float
    y: float

@define
class BBox():
    x1: int
    y1: int
    x2: int
    y2: int

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
class CurvePoint:
    input_point: int # TODO Default fields + validators
    output_point: int

@define
class Posterization():
    posterize_input: int
    posterize_output: int

@define
class EffectApplyOpacity():
    apply_opacity: bool

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

@define
class Balance():

    Cyan: int # TODO Validators
    Magenta: int
    Yellow: int



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
