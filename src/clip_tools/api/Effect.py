import io
import logging

import attrs

from attrs import define, field
from attrs.validators import instance_of

from clip_tools.constants import ScreenToneShape, ExtractLinesDirection
from clip_tools.utils import read_fmt, read_csp_unicode_str, attrs_range_builder
from clip_tools.data_classes import Position, Color

logger = logging.getLogger(__name__)

# Abstract, Do not use
@define
class Effect():
    enabled = field(validator=instance_of(bool), default=False)

@define
class EffectApplyOpacity(Effect):

    @classmethod
    def read(cls, io_stream):
        section_size = read_fmt(">i", io_stream)
        apply_opacity_enabled = bool(read_fmt(">i", io_stream)) # Enable layer reflect opacity

        return cls(apply_opacity_enabled)

@define
class EffectEdge(Effect):

    thickness = attrs_range_builder(float, 1.0, [1.0, 250.0])
    color = field(validator=instance_of(Color), default=Color(0, 0, 0))

    @classmethod
    def read(cls, io_stream):

        edge_enabled = bool(read_fmt(">i", io_stream))
        thickness = read_fmt(">d", io_stream)
        color = Color.read(io_stream)

        return cls(edge_enabled, thickness, color)

@define
class EffectTone(Effect):

    resolution = attrs_range_builder(float, 1.0, [1.0, 250.0])

    shape = field(validator=instance_of(ScreenToneShape), default=ScreenToneShape.CIRCLE)
    use_image_brightness = field(validator=instance_of(bool), default=False)

    frequency = attrs_range_builder(float, 60.0, [5.0, 85.0])
    angle = attrs_range_builder(int, 0, [0, 359])
    noise_size = attrs_range_builder(int, 100, [10, 1000])
    noise_factor = attrs_range_builder(int, 0, [0, 1000])

    dot_position = field(validator=instance_of(Position), default=Position(0.0, 0.0))

    @classmethod
    def read(cls, io_stream):

        screentone_enabled = bool(read_fmt(">i", io_stream))

        resolution = read_fmt(">d", io_stream)

        screentone_shape = ScreenToneShape(read_fmt(">i", io_stream))
        use_image_brightness = bool(read_fmt(">i", io_stream)) # Default is "use image color"

        to_investigate = read_fmt(">i", io_stream) # Not 20 for some gradients
        #assert read_fmt(">i", io_stream) == 0x14, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        frequency = read_fmt(">d", io_stream) # Between 5.0 and 85.0
        
        assert read_fmt(">i", io_stream) == 1, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        assert read_fmt(">i", io_stream) == 0, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        angle = read_fmt(">i", io_stream) # Between 0 and 359

        noise_size = read_fmt(">i", io_stream)
        noise_factor = read_fmt(">i", io_stream)

        assert read_fmt(">i", io_stream) == 0, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        assert read_fmt(">i", io_stream) == 0, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        dot_position = Position(read_fmt(">d", io_stream), read_fmt(">d", io_stream))

        return cls(screentone_enabled, resolution, screentone_shape, use_image_brightness, frequency, angle, noise_size, noise_factor, dot_position)

@define
class Posterization():
    posterize_input = attrs_range_builder(int, 127, [1, 255])
    posterize_output = attrs_range_builder(int, 50, [0, 99])

@define
class EffectTonePosterize(Effect):

    posterizations = field(factory=list)

    @property
    def posterization_count(self):
        return len(self.posterizations)

    def add_posterization(self, posterization_point):
        if self.posterization_count >= 10:
            return

        for i in range(self.posterization_count):
            if self.posterizations[i].posterize_input > posterization_point.posterize_input:
                self.posterizations.insert(i, posterization_point)
                # Add a step to normalize output against neighboring points. They're supposed to be strictly ordered
                return

        self.posterizations.append(posterization_point)

    def clear_posterizations(self):
        self.posterizations = []

    @classmethod
    def read(cls, io_stream):

        posterize_enabled = bool(read_fmt(">i", io_stream))
        posterize_count = read_fmt(">i", io_stream)
        posterizations = []

        for _ in range(posterize_count):
            posterize_input = read_fmt(">i", io_stream) # Posterization input over 0..255
            posterize_output = read_fmt(">i", io_stream) # Postrize output over 1..99

            posterizations.append(Posterization(posterize_input, posterize_output))

        return cls(posterize_enabled, posterizations)


@define
class EffectWaterEdge(Effect):

    edge_range = attrs_range_builder(float, 1.0, [1.0, 20.0])
    edge_opacity = attrs_range_builder(float, 1.0, [1.0, 100.0])
    edge_darkness = attrs_range_builder(float, 1.0, [0.0, 100.0])
    edge_blurring = attrs_range_builder(float, 1.0, [0.0, 10.0])

    @classmethod
    def read(cls, io_stream):
        water_edge_enabled = bool(read_fmt(">i", io_stream))

        edge_range = read_fmt(">d", io_stream)
        edge_opacity = read_fmt(">d", io_stream)
        edge_darkness = read_fmt(">d", io_stream)
        edge_blurring = read_fmt(">d", io_stream)

        return cls(water_edge_enabled, edge_range, edge_opacity, edge_darkness, edge_blurring)

@define
class EffectLine(Effect):

    black_fill_enabled = field(validator=instance_of(bool), default=False)
    black_fill_level = attrs_range_builder(int, 0, [0, 255])

    posterize_enabled = field(validator=instance_of(bool), default=False)

    line_width = attrs_range_builder(int, 1, [0, 5]) 
    effect_threshold = attrs_range_builder(int, 0, [0, 255]) 

    directions = field(validator=instance_of(ExtractLinesDirection),
                        default=ExtractLinesDirection.BOTTOM |
                                ExtractLinesDirection.TOP |
                                ExtractLinesDirection.LEFT |
                                ExtractLinesDirection.RIGHT
                    )

    posterizations = field(factory=list)

    anti_aliasing = field(validator=instance_of(bool), default=False)

    @property
    def posterization_count(self):
        return len(self.posterizations)

    @classmethod
    def read(cls, io_stream):
        
        extract_line_enabled = bool(read_fmt(">i", io_stream))

        black_fill_enabled = bool(read_fmt(">i", io_stream))
        black_fill_level = 255 - (read_fmt(">I", io_stream) >> 24)

        posterize_enabled = bool(read_fmt(">i", io_stream))

        assert read_fmt(">i", io_stream) == 0, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        line_width = read_fmt(">i", io_stream)

        assert read_fmt(">i", io_stream) == 0, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        effect_threshold = read_fmt(">i", io_stream)

        assert read_fmt(">d", io_stream) == 5.0, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        assert read_fmt(">d", io_stream) == 5.0, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        assert read_fmt(">i", io_stream) == 0x04, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        directions_map = {0:ExtractLinesDirection.LEFT,
                            1:ExtractLinesDirection.TOP,
                            2:ExtractLinesDirection.RIGHT,
                            3:ExtractLinesDirection.BOTTOM}

        directions = ExtractLinesDirection(0)
        
        for _ in range(4):
            direction = read_fmt(">i", io_stream)
            direction_enabled = bool(read_fmt(">i", io_stream))

            if direction_enabled:
                directions = directions | directions_map[direction]

        posterize_count = read_fmt(">i", io_stream)
        posterizations = []

        for _ in range(posterize_count):
            posterize_input = read_fmt(">i", io_stream) # Posterization input over 0..255
            posterize_output = read_fmt(">i", io_stream) # Postrize output over 1..99

            posterizations.append((posterize_input, posterize_output))
        
        to_investigate = read_fmt(">i", io_stream) # 1 or 0 for gradients
        #assert read_fmt(">i", io_stream) == 0x1, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        anti_aliasing = bool(read_fmt(">i", io_stream)) # Edge anti aliasing ?  Why is it here
        assert read_fmt(">i", io_stream) == 0xc8, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        

        return cls(extract_line_enabled, black_fill_enabled, black_fill_level, posterize_enabled, line_width, effect_threshold, directions, posterizations, anti_aliasing)


@define
class LayerEffects():

    edge: EffectEdge
    tone: EffectTone
    apply_opacity: EffectApplyOpacity
    posterize: EffectTonePosterize
    water_edge: EffectWaterEdge
    line_extract: EffectLine

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, layer_effect_info):

        io_stream = io.BytesIO(layer_effect_info)

        effect_data_size = read_fmt(">i", io_stream)
        assert read_fmt(">i", io_stream) == 0x02, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        effects = {}

        while io_stream.tell() < effect_data_size:

            param_name = read_csp_unicode_str(">i", io_stream)

            if param_name == "EffectEdge":
                effects[param_name] = EffectEdge.read(io_stream)

            elif param_name == "EffectTone":
                effects[param_name] = EffectTone.read(io_stream)

            elif param_name == "EffectTextureMap":
                section_size = read_fmt(">i", io_stream)
                io_stream.read(section_size - 4)

                # Bypass
            elif param_name == "EffectApplyOpacity":
                effects[param_name] = EffectApplyOpacity.read(io_stream)

            elif param_name == "EffectToneAreaColor":
                section_size = read_fmt(">i", io_stream)
                io_stream.read(section_size - 4)

                # Bypass

            elif param_name == "EffectTonePosterize":
                section_size = read_fmt(">i", io_stream)
                effects[param_name] = EffectTonePosterize.read(io_stream)

            elif param_name == "EffectWaterEdge":
                section_size = read_fmt(">i", io_stream)
                effects[param_name] = EffectWaterEdge.read(io_stream)

            elif param_name == "EffectLine":
                section_size = read_fmt(">i", io_stream)
                effects[param_name] = EffectLine.read(io_stream)

            else:
                logger.warning(f"Unknown param name {param_name} effect parsing, might be due to incorrect parsing")


        return cls(effects["EffectEdge"],
                    effects["EffectTone"],
                    effects["EffectApplyOpacity"],
                    effects["EffectTonePosterize"],
                    effects["EffectWaterEdge"],
                    effects["EffectLine"])

    @classmethod
    def new(cls, effects):
        pass