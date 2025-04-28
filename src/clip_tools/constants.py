from enum import Enum, IntEnum, IntFlag, auto

# DefaultPageColorType
# LayerColorTypeIndex
class ColorMode(IntEnum):
    RGB = 0
    GRAYSCALE = 1
    MONOCHROME = 2

    @classmethod
    def pil_mode(cls, color_mode):
        return {
            ColorMode.RGB: "RGBA",
            ColorMode.GRAYSCALE: "LA",
            ColorMode.MONOCHROME: "LA" # Due to csp encoding and lack of transparency support in monochrome image from pil
        }.get(color_mode)

    @classmethod
    def from_pil(cls, pil_mode):
        return {
            "RGB": ColorMode.RGB,
            "RGBA": ColorMode.RGB,
            "L": ColorMode.GRAYSCALE,
            "LA": ColorMode.GRAYSCALE,
            "1": ColorMode.MONOCHROME
        }.get(pil_mode)

class CanvasChannelOrder(IntFlag):

    ALPHA = 1
    BW = 16
    RGB = 32

    @classmethod
    def from_color_mode(cls, color_mode):

        return {
            ColorMode.RGB: CanvasChannelOrder.ALPHA | CanvasChannelOrder.RGB,
            ColorMode.GRAYSCALE: CanvasChannelOrder.ALPHA | CanvasChannelOrder.BW,
            ColorMode.MONOCHROME: CanvasChannelOrder.ALPHA | CanvasChannelOrder.BW,
        }.get(color_mode)

    @classmethod
    def from_pil_mode(cls, pil_mode):
        return CanvasChannelOrder.ALPHA | {
            "RGB": CanvasChannelOrder.RGB,
            "RGBA": CanvasChannelOrder.RGB,
            "L": CanvasChannelOrder.BW,
            "LA": CanvasChannelOrder.BW,
            "1": CanvasChannelOrder.ALPHA
        }.get(pil_mode)


class CanvasUnit(IntEnum):
    PIXEL = 0


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
    # 114, For Frame folders (MASK_AREA + UNK + Folder + Frame)
    MASK_ENABLED = 1
    MASK_AREA = 2
    UNK = 16 # Use Vector line as mask delimitation?
    BLOCK_APPLY_MASK = 32
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
    STROKE = 0
    BALLOON = 1 # Probably part of the VectorNormalFillIndex
    SPEEDLINLES = 2
    FRAMEBORDER = 3 # Will take its values in VectorNormalBalloonIndex

class DrawToMaskOffscreenType(IntEnum):
    FRAME = 21

class DrawToMaskMipmapType(IntEnum):
    FRAME = 10

class DrawToRenderOffscreenType(IntEnum):
    VECTOR = 10
    BALLOON = 11
    EXT_IMAGE = 20
    TEXT = 40
    GRADIENT = 60
    PAPER = 61

class DrawToRenderMipmapType(IntEnum):
    EXT_IMAGE = 20
    PAPER = 31
    GRADIENT = 32
    TEXT = 40

# Same for:
# MoveOffsetAndExpandType
# FixOffsetAndExpandType (No TEXT)
# RenderBoundForLayerMoveType (No TEXT, FRAME)
# Different types of layers don't have all of them
class OffsetAndExpandType(IntEnum):
    EXT_IMAGE = 10
    GRADIENT = 30
    PAPER = 31
    FRAME = 40
    TEXT = 50

# Same for :
# EffectRenderType
# EffectLayerRenderType
# EffectReferAreaType
# EffectSetUpdateRectType
# EffectOffscreenFixType
# EffectOffscreenMoveType
class EffectRenderType(IntEnum):
    GRADIENT = 10 # Very useful

# Same for:
# SetRenderThumbnailInfoType
# DrawRenderThumbnailType
class RenderThumbnailType(IntEnum):
    CORRECTION = 20
    GRADIENT = 30
    PAPER = 31

class SpecialRenderType(IntEnum):
    CORRECTION = 13
    FRAME = 14
    PAPER = 20

class MaterialContentType(IntEnum):
    FRAME = 100
    TEXT = 110
    FRAME_BACKGROUND = 160 # Frame backgrounds are gradients layers with extra steps

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

class RulerRange(IntEnum):
    ALL_LAYERS = 0
    ONLY_FOLDER = 1
    ONLY_TARGET = 2

class TextAttribute(IntEnum):

    RUNS = 11
    ALIGN = 12
    LINE_SPACING = 13
    CHARACTER_SPACING = 14
    UNDERLINE = 16
    OUTLINE = 18
    STRIKE = 20

    ASPECT_RATIO = 26
    CONDENSE_TEXT = 27

    FONT = 31
    FONT_SIZE = 32
    GLOBAL_STYLE = 33
    GLOBAL_COLOR = 34
    GLOBAL_JUSTIFY = 35

    ABSOLUTE_SPACING = 37
    HORZ_IN_VERT = 38

    BBOX = 42

    READING_SETTING = 47
    ANTI_ALIASING = 48

    TEXT_ID = 50

    HALF_WIDTH_PUNCT = 52

    WRAP_FRAME = 53
    WRAP_DIRECTION = 55

    BACKGROUND = 54
    EDGE = 56

    FONTS = 57

    ROTATION_ANGLE = 58

    SKEW_ANGLE_1 = 59
    SKEW_ANGLE_2 = 60

    BOX_SIZE = 63
    QUAD_VERTS = 64

class TextAlign(IntEnum):
    LEFT = 0
    RIGHT = 1
    CENTER = 2

class TextStyle(IntFlag):
    NONE = 0
    BOLD = 1
    ITALIC = 2
    UNDERLINE = 4
    STRIKEOUT = 8
    VERTICAL = 16

class TextOutline(IntEnum):
    NONE = 0
    LIGHT = 1
    BOLD = 2

class TextWrapDirection(IntEnum):
    TOP = 0
    CENTER = 1
    BOTTOM = 2

# These are most likely flags but they make no sense
class VectorFlag(IntFlag):

    NORMAL= 1
    RULER = 4
    FRAME = 8

    # Defines the curve type
    CURVE_STRAIGHT = 16
    CURVE_QUADRATIC_BEZIER = 32
    CURVE_CUBIC_BEZIER = 64
    CURVE_SPLINE = 128

    CLOSED_LOOP = 256 # First control point is also the last

    UNK1 = 4096 # Only seen with frames
    UNK2 = 8192 # Only seen with free pen vectors

class VectorPointFlag(IntFlag):

    NORMAL = 0

    CORNER = 1
    FRAME = 2 # for a frame or to define mask?

    SPEEDLINE = 512

    unk_THICKNESS_CHANGED = 4096

class AntiAliasing(IntEnum):
    NONE = 0
    WEAK = 1
    MEDIUM = 2
    STRONG = 3
