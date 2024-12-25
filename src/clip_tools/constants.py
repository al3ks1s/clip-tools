from enum import Enum, IntEnum, IntFlag, auto

# -----------------
# Param Scheme data

class DataType(IntEnum):
    INT = 1
    FLOAT = 2
    STR = 3
    BYTES = 4

"""

class Flag(Enum):
    pass

class OwnerType(Enum):
    pass

class LockType(Enum):
    pass

class LockSpecified(Enum):
    pass

"""

# ----------------
# Data definitions

class CanvasChannelBytes(IntFlag):
    
    ALPHA = 1
    BW = 16
    RGB = 32

class LayerType(IntFlag):

    # Defines the flags for the layer type, can be a combination of several of them

    VECTOR = 0 # Defines either Vector, Folder, 3D Layer, Speedlines, pretty much general purpose
    PIXEL = 1
    MASKED = 2

    UNK_1 = 16
    UNK_2 = 32

    ROOT_FOLDER = 256
    
    UNK_3 = 512
    UNK_4 = 1024

    PAPER = 1584 # Paper Layers is the combination of (1024 + 512 + 32 + 16) which actually specifies the Paper layer is unknown
    CORRECTION = 4096 # Usually correction layers have the value 4098 (Correction + Masked)


class CorrectionType(IntEnum):
    BRIGHTNESS_CONTRAST = 1
    LEVEL = 2
    TONE_CURVE = 3
    HSL = 4
    COLOR_BALANCE = 5
    REVERSE_GRADIENT = 6
    POSTERIZATION = 7
    THRESHOLD = 8 # Also called Binarization in CSP GUI
    GRADIENT_MAP = 9

class BlendMode(IntEnum):
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

class LayerMasking(IntFlag):
    # 0 No mask
    # 1 Mask enabled
    # 3 Mask + Show mask area
    # 32 For folders without masks
    # 33 For folders with mask (Folder + Mask)
    # 114, For Frame folders (MASK_AREA + UNK + Folder + Frame)
    MASK_ENABLED = 1
    MASK_AREA = 2
    UNK = 16 # Use Vector line as mask delimitation?
    FOLDER = 32
    FRAME = 64
    

class LayerVisibility(IntFlag):
    VISIBLE = 1
    MASK_VISIBLE = 2
    RULER_VISIBLE = 4
    
class LayerFolder(IntFlag):
    FOLDER = 1
    CLOSED = 16

class LayerLock(IntFlag):
    FULL = 1
    ALPHA = 16

class LayerSelect(IntFlag):
    # Flag system too
    # 0
    # 2 
    # 256
    # 512
    pass

class VectorNormalType(IntEnum):
    NORMAL = 0
    UNKN = 1 # Probably part of the VectorNormalFillIndex
    SPEEDLINLES = 2
    FRAMEBORDER = 3

class EffectRenderType(IntEnum):
    pass

class TextAttribute(IntEnum):
    pass

class GradientRepeatMode(IntEnum):
    CLIP = 0
    REPEAT = 1
    MIRROR = 2
    EMPTY = 3


class GradientShape(IntEnum):
    LINEAR = 0
    CIRCLE = 1
    ELLIPSE = 2

class ExtractLinesDirection(IntFlag):
    LEFT = auto()
    RIGHT = auto()
    BOTTOM = auto()
    TOP = auto()

class ScreenToneShape(IntEnum):

    CIRCLE = 1
    SQUARE = 2
    LOZENGE = 3
    LINE = 4
    CROSS = 5
    ELLIPSE = 6
    NOISE = 7
    SUGAR_PLUM = 8
    ASTERISK = 9
    STAR = 10
    CARROT = 11
    CHERRY_ROUND = 12
    CHERRY_MID = 13
    CHERRY_THIN = 14
    FLOWER_ROUND = 15
    FLOWER_MID = 16
    FLOWER_THIN = 17
    CLOVER_ROUND = 18
    CLOVER_THIN = 19
    NINJA_STAR = 20
    DIAMOND = 21
    HEART = 22
    CLUBS = 23
    SPADES = 24