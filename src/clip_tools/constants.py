from enum import Enum, IntEnum

class LayerType(Enum):
    VECTOR = 0 # Defines either Vector, Folder, 3D Layer, Speedlines, pretty much general purpose
    PIXEL = 1
    GRADIENT = 2

    ROOT_FOLDER = 256
    PAPER = 1584
    CORRECTION = 4098

class DataType(IntEnum):
    INT = 1
    FLOAT = 2
    STR = 3
    BYTES = 4

class Flag(Enum):
    pass

class OwnerType(Enum):
    pass

class LockType(Enum):
    pass

class LockSpecified(Enum):
    pass

class CorrectionType(IntEnum):
    BRIGHTNESS_CONTRAST = 1
    LEVEL = 2
    TONE_CURBE = 3
    HSL = 4
    COLOR_BALANCE = 5
    REVERSE_GRADIENT = 6
    POSTERIZATION = 7
    THRESHOLD = 8 # Called Binarization in CSP GUI
    GRADIENT_MAP = 9

class LayerComposite(IntEnum):
    NORMAL = 0
    DARKEN = 1
    MULTIPLY = 2
    COLOR_BURN = 3
    LINEAR_BURN = 4
    SUBSTRACT = 5
    DARKER_COLOR = 6
    LIGHTEN = 7
    SCREEN = 8
    COLOR_DODGE = 9
    GLOW_DODGE = 10
    ADD = 11
    ADD_GLOW = 12
    LIGHTER_COLOR = 13
    OVERLAY = 14
    SOFT_LIGHT = 15
    HARD_LIGHT = 16
    VIVID_LIGHT = 17
    LINEAR_LIGHT = 18
    PIN_LIGHT = 19
    HARD_MIX = 20
    DIFFERENCE = 21
    EXCLUSION = 22
    HUE = 23
    SATURATION = 24
    COLOR = 25
    BRIGHTNESS = 26
    DIVIDE = 36

class LayerMasking(IntEnum):
    # 0
    # 1
    # 3
    # 32
    # 33
    # 114
    pass

class LayerVisibility(IntEnum):
    # 0
    # 1
    # 3
    # 5
    # 7
    pass

class LayerSelect(IntEnum):
    pass

class VectorNormalType(IntEnum):
    pass

class EffectRenderType(IntEnum):
    pass