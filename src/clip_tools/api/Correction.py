# FilterLayerInfo
from attrs import define, validators, field
from clip_tools.constants import CorrectionType
import binascii
import io
import logging
from clip_tools.utils import read_fmt

from collections import namedtuple

logger = logging.getLogger(__name__)

@define
class BrightnessContrast():
    
    brightness: int = 0 # TODO Validators
    contrast: int = 0

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):
        
        section_size = read_fmt(">i", correction_data)
        return cls(read_fmt(">i", correction_data), read_fmt(">i", correction_data))

@define
class Level():

    @define
    class LevelCorrection:
        input_left: int # TODO Default fields + validators
        intput_mid: int
        input_right: int
        output_left: int
        output_right: int

    RGB: LevelCorrection
    Red: LevelCorrection
    Green: LevelCorrection
    Blue: LevelCorrection

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):
        section_size = read_fmt(">i", correction_data)

        levels = []

        while correction_data.tell() < section_size + 8:
            
            levels.append(Level.LevelCorrection(read_fmt(">H", correction_data) >> 8,
                                                read_fmt(">H", correction_data) >> 8,
                                                read_fmt(">H", correction_data) >> 8,
                                                read_fmt(">H", correction_data) >> 8,
                                                read_fmt(">H", correction_data) >> 8))

        # There is only 4 meaningful level tables, no idea why there are more
        return cls(levels[0],levels[1],levels[2],levels[3])

@define
class ToneCurve():
    
    @define
    class CurvePoint:
        input_point: int # TODO Default fields + validators
        output_point: int

    @define
    class CurveList(list):
        pass # TODO Add verifications when adding new points (32 max, insert in order, no same input value)


    RGB: CurveList
    Red: CurveList
    Green: CurveList
    Blue: CurveList

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):
        section_size = read_fmt(">i", correction_data)

        curves = []

        while correction_data.tell() < section_size + 8:

            points_count = read_fmt(">h", correction_data)
           
            points = []  
            for _ in range(points_count):
                point = ToneCurve.CurvePoint(read_fmt(">H", correction_data) >> 8, read_fmt(">H", correction_data) >> 8)
                points.append(point)

            padding = correction_data.read(0x80 - (4 * points_count)) # Point count is limited to 32
            
            curves.append(points)

        # There is only 4 meaningful point tables, no idea why there are more
        return cls(curves[0], curves[1], curves[2], curves[3])

@define
class HSL():
    Hue: int = 0 # TODO Validators
    Saturation: int = 0
    Luminance: int = 0

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        return cls(read_fmt(">i", correction_data), read_fmt(">i", correction_data), read_fmt(">i", correction_data))


@define
class ColorBalance():
    
    @define
    class Balance():

        Cyan: int # TODO Validators
        Magenta: int
        Yellow: int

    keep_brightness: bool

    shadows: Balance
    midtones: Balance
    highlight: Balance

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        
        keep_brightness = bool(read_fmt(">i", correction_data))

        balance_shadow = ColorBalance.Balance(read_fmt(">i", correction_data), read_fmt(">i", correction_data), read_fmt(">i", correction_data))
        balance_midtones = ColorBalance.Balance(read_fmt(">i", correction_data), read_fmt(">i", correction_data), read_fmt(">i", correction_data))
        balance_highlight = ColorBalance.Balance(read_fmt(">i", correction_data), read_fmt(">i", correction_data), read_fmt(">i", correction_data))

        return cls(keep_brightness, balance_shadow, balance_midtones, balance_highlight)

class ReverseGradient():
    
    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):
        # There's no meaningful data in this data glob
        return cls()

@define
class Posterization():
    PosterizationLevel: int = 8 # TODO Validators

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):
        
        section_size = read_fmt(">i", correction_data)

        return cls(read_fmt(">i", correction_data))

@define
class Threshold():
    threshold_level: int = 128 # TODO Validators

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):

        section_size = read_fmt(">i", correction_data)
        return cls(read_fmt(">i", correction_data))

@define
class GradientMap():
    
    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(cls, correction_data):
        logger.warning("Gradient Map correction not implemented")

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