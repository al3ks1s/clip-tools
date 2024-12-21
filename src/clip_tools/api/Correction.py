# FilterLayerInfo
from attrs import define
from clip_tools.constants import CorrectionType

import io

from clip_tools.utils import read_fmt

@define
class BrightnessContrast():
    Brightness: int = 0
    Contrast: int = 0

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class Level():
    

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class ToneCurve():
    
    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class HSL():
    Hue: int = 0
    Saturation: int = 0
    Luminance: int = 0

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class ColorBalance():
    
    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

class ReverseGradient():
    
    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class Posterization():
    PosterizationLevel: int = 0

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class Threshold():
    ThresholdLevel: int = 128

    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

@define
class GradientMap():
    
    def to_bytes(self):
        pass

    @classmethod
    def from_bytes(self, correction_data):
        pass

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