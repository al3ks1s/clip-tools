from collections import namedtuple
from attrs import define, Factory, field
import io
from clip_tools.constants import GradientRepeatMode, GradientShape, TextAlign, TextStyle, TextOutline, VectorFlag, VectorPointFlag, CanvasChannelOrder, ColorMode
from clip_tools.utils import read_fmt, read_csp_unicode_str, read_csp_str, read_csp_unicode_le_str, attrs_range_builder, write_fmt, write_bytes, write_csp_str, shifter_calculator, pil_to_channel, get_pil_depth, write_csp_unicode_str
# TODO Write Methods that return bytes format

@define
class Position():
    x: float
    y: float

    def write(self, io_stream, fmt = ">d"):
        write_fmt(io_stream, fmt, self.x)
        write_fmt(io_stream, fmt, self.y)

    @classmethod
    def read(cls, io_stream, fmt = ">d"):
        return cls(
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream)
        )

@define
class BBox():
    x1: int
    y1: int
    x2: int
    y2: int

    def write(self, io_stream, fmt = ">i"):
        write_fmt(io_stream, fmt, self.x1)
        write_fmt(io_stream, fmt, self.y1)
        write_fmt(io_stream, fmt, self.x2)
        write_fmt(io_stream, fmt, self.y2)

    @classmethod
    def read(cls, io_stream, fmt = ">i"):
        return cls(
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream)
        )

@define
class Color():
    r: int = attrs_range_builder(int, 0, [0, 255])
    g: int = attrs_range_builder(int, 0, [0, 255])
    b: int = attrs_range_builder(int, 0, [0, 255])

    def write(self, io_stream, fmt = ">I"):
        write_fmt(io_stream, fmt, self.r << shifter_calculator(fmt))
        write_fmt(io_stream, fmt, self.g << shifter_calculator(fmt))
        write_fmt(io_stream, fmt, self.b << shifter_calculator(fmt))

    @classmethod
    def read(cls, io_stream, fmt = ">I"):
        return cls(
            read_fmt(fmt, io_stream) >> shifter_calculator(fmt),
            read_fmt(fmt, io_stream) >> shifter_calculator(fmt),
            read_fmt(fmt, io_stream) >> shifter_calculator(fmt)
        )

    @classmethod
    def WHITE(cls):
        return cls(255, 255, 255)

    @classmethod
    def RED(cls):
        return cls(255, 0, 0)

    @classmethod
    def GREEN(cls):
        return cls(0, 255, 0)

    @classmethod
    def BLUE(cls):
        return cls(0, 0, 255)


@define
class CurvePoint:
    # Temporary due to unusual value in gradient color stops
    input_point: float#attrs_range_builder(int, 127, [0, 255])
    output_point: float#attrs_range_builder(int, 127, [0, 255])

    def write(self, io_stream, fmt = ">i"):
        write_fmt(io_stream, fmt, self.input_point)
        write_fmt(io_stream, fmt, self.output_point)

    @classmethod
    def read(cls, io_stream, fmt = ">i"):
        return cls(
            read_fmt(fmt, io_stream),
            read_fmt(fmt, io_stream)
        )

    def write_short(self, io_stream):
        write_fmt(io_stream, ">H", self.input_point << 8)
        write_fmt(io_stream, ">H", self.output_point << 8)

    @classmethod
    def read_short(cls, io_stream):
        return cls(
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8
        )

@define
class CurveList():

    points = field(default=Factory(list))

    @property
    def point_count(self):
        return len(self.points)

    def add_point(self, point: CurvePoint):

        if self.point_count >= 32:
            print("Too much points in curve list")
            return

        self.points.append(point)

    def write_short(self, io_stream, padding = True):

        points_count = len(self.points)

        write_fmt(io_stream, ">h", points_count)

        for point in self.points:
            point.write_short(io_stream)

        if padding:
            write_bytes(io_stream, b'\x00' * (0x80 - (4 * points_count)))


    @classmethod
    def read_short(cls, io_stream, padding = True):
        points_count = read_fmt(">h", io_stream)

        points = cls()
        for _ in range(points_count):
            point = CurvePoint.read_short(io_stream)
            points.add_point(point)

        if padding:
            io_stream.read(0x80 - (4 * points_count)) # Point count is limited to 32

        return points


    @classmethod
    def new(cls):

        cl = cls()
        cl.add_point(CurvePoint(0, 0))
        cl.add_point(CurvePoint(255,255))
        return cl

    @classmethod
    def dummy(cls):
        return cls.new()

@define
class ColorStop():
    color: Color
    opacity: int
    is_current_color: bool
    position: int
    num_curve_points: int
    curve_points: CurveList

    @classmethod
    def new(cls):
        pass

@define
class LevelCorrection:

    input_left: int = attrs_range_builder(int, 0, [0, 255])
    intput_mid: int = attrs_range_builder(int, 127, [0, 255])
    input_right: int = attrs_range_builder(int, 255, [0, 255])

    output_left: int = attrs_range_builder(int, 0, [0, 255])
    output_right: int = attrs_range_builder(int, 255, [0, 255])

    def write(self, io_stream):
        write_fmt(io_stream, ">H", self.input_left << 8)
        write_fmt(io_stream, ">H", self.intput_mid << 8)
        write_fmt(io_stream, ">H", self.input_right << 8)

        write_fmt(io_stream, ">H", self.output_left << 8)
        write_fmt(io_stream, ">H", self.output_right << 8)

    @classmethod
    def read(cls, io_stream):
        return cls(
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8,
            read_fmt(">H", io_stream) >> 8
        )

    @classmethod
    def dummy(cls):
        return LevelCorrection()

@define
class Balance():

    cyan: int = attrs_range_builder(int, 0, [-100, 100])
    magenta: int = attrs_range_builder(int, 0, [-100, 100])
    yellow: int = attrs_range_builder(int, 0, [-100, 100])

    def write(self, io_stream):
        write_fmt(io_stream, ">i", self.cyan)
        write_fmt(io_stream, ">i", self.magenta)
        write_fmt(io_stream, ">i", self.yellow)

    @classmethod
    def read(cls, io_stream):
        return cls(
            read_fmt(">i", io_stream),
            read_fmt(">i", io_stream),
            read_fmt(">i", io_stream)
        )

@define
class RulerCurvePoint():

    pos: Position
    thickness: int


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

@define
class TextBackground():

    enabled: bool
    color: Color
    opacity: int

    @classmethod
    def read(cls, io_stream):
        enabled = read_fmt("<i", io_stream)
        color = Color.read(io_stream)
        opacity = ((read_fmt("<I", io_stream) >> 24) * 100) // 255

        return cls(enabled, color, opacity)

@define
class TextEdge():
    enabled: bool
    size: int
    color:Color

    @classmethod
    def read(cls, io_stream):
        edge_enabled = read_fmt("<i", io_stream)
        edge_size = read_fmt("<i", io_stream) // 1000

        unk = read_fmt("<i", io_stream)

        edge_color = Color.read(io_stream)

        return cls(edge_enabled, edge_size, edge_color)


@define
class ReadingSetting():

    reading_type: int
    reading_ratio: int
    adjust_reading: float
    space_between: float
    reading_space_free: float

    reading_font: str

    def write(self, io_stream):
        write_fmt(io_stream, "<h", self.reading_type)
        write_fmt(io_stream, "<h", self.reading_ratio)
        write_fmt(io_stream, "<h", self.adjust_reading * 100)
        write_fmt(io_stream, "<h", self.space_between * 100)
        write_fmt(io_stream, "<h", self.reading_space_free * 100)

        write_csp_str(io_stream, "<h",  self.reading_font)

    @classmethod
    def read(cls, io_stream):

        reading_type = read_fmt("<h", io_stream)
        reading_ratio = read_fmt("<h", io_stream)
        adjust_reading = read_fmt("<h", io_stream) / 100
        space_between = read_fmt("<h", io_stream) / 100
        reading_space_free = read_fmt("<h", io_stream) / 100

        reading_font = read_csp_str("<h", io_stream)

        return cls(
            reading_type,
            reading_ratio,
            adjust_reading,
            space_between,
            reading_space_free,
            reading_font
        )

@define
class PixelPackingAttribute():

    bit_order: CanvasChannelOrder

    alpha_channel_count: int
    buffer_channel_count: int
    total_channel_count: int

    buffer_block_byte_count: int
    buffer_channel_count2: int
    buffer_bit_depth: int

    alpha_channel_count2: int
    alpha_bit_depth: int

    buffer_block_area: int

    block_width: int
    block_height: int

    unk1: int
    unk2: int

    monochrome: bool

    unk3: int

    def write(self, io_stream):
        write_fmt(io_stream, ">i", self.bit_order)

        write_fmt(io_stream, ">i", self.alpha_channel_count)
        write_fmt(io_stream, ">i", self.buffer_channel_count)
        write_fmt(io_stream, ">i", self.total_channel_count)

        write_fmt(io_stream, ">i", self.buffer_block_byte_count)
        write_fmt(io_stream, ">i", self.buffer_channel_count2)
        write_fmt(io_stream, ">i", self.buffer_bit_depth << 5)

        write_fmt(io_stream, ">i", self.alpha_channel_count2)
        write_fmt(io_stream, ">i", self.alpha_bit_depth << 5)

        write_fmt(io_stream, ">i", self.buffer_block_area)

        write_fmt(io_stream, ">i", self.block_width)
        write_fmt(io_stream, ">i", self.block_height)


        write_fmt(io_stream, ">i", self.unk1)
        write_fmt(io_stream, ">i", self.unk2)
        
        write_fmt(io_stream, ">i", int(self.monochrome))

        write_fmt(io_stream, ">i", self.unk3)

    @classmethod
    def read(cls, io_stream):
        
        bit_order = CanvasChannelOrder(read_fmt(">i", io_stream))

        alpha_channel_count = read_fmt(">i", io_stream)
        buffer_channel_count = read_fmt(">i", io_stream)
        total_channel_count = read_fmt(">i", io_stream)

        buffer_block_byte_count = read_fmt(">i", io_stream)
        buffer_channel_count2 = read_fmt(">i", io_stream)
        buffer_bit_depth = read_fmt(">i", io_stream) >> 5

        alpha_channel_count2 = read_fmt(">i", io_stream)
        alpha_bit_depth = read_fmt(">i", io_stream) >> 5

        buffer_block_area = read_fmt(">i", io_stream)

        block_width = read_fmt(">i", io_stream)
        block_height = read_fmt(">i", io_stream)

        unk1 = read_fmt(">i", io_stream)
        unk2 = read_fmt(">i", io_stream)

        monochrome = bool(read_fmt(">i", io_stream))

        unk3 = read_fmt(">i", io_stream)

        return cls(
            bit_order,
            alpha_channel_count,
            buffer_channel_count,
            total_channel_count,
            buffer_block_byte_count,
            buffer_channel_count2,
            buffer_bit_depth,
            alpha_channel_count2,
            alpha_bit_depth,
            buffer_block_area,
            block_width,
            block_height,
            unk1,
            unk2,
            monochrome,
            unk3
        )

    @classmethod
    def new(cls, color_mode):

        pil_mode = ColorMode.pil_mode(color_mode)

        return cls(
            bit_order = CanvasChannelOrder.from_pil_mode(pil_mode),
            alpha_channel_count = 1,
            buffer_channel_count = pil_to_channel(pil_mode),
            total_channel_count = pil_to_channel(pil_mode) + 1,
            buffer_block_byte_count = (256*256) // (8 // (get_pil_depth(pil_mode) // pil_to_channel(pil_mode))),
            buffer_channel_count2 = pil_to_channel(pil_mode),
            buffer_bit_depth = get_pil_depth(pil_mode),
            alpha_channel_count2 = 1,
            alpha_bit_depth = min(get_pil_depth(pil_mode), 8),
            buffer_block_area = 256 * 256,
            block_width = 256,
            block_height = 256,
            unk1 = 8,
            unk2 = 8,
            monochrome = color_mode == ColorMode.MONOCHROME,
            unk3 = 0
        )

@define
class OffscreenAttribute():

    bitmap_width: int
    bitmap_height: int

    block_grid_width: int
    block_grid_height: int

    packing_attributes: PixelPackingAttribute

    default_fill_color: int
    other_init_colors: []

    block_sizes: []

    def write(self, io_stream):

        write_fmt(io_stream, ">i", 0)
        write_fmt(io_stream, ">i", 0)
        write_fmt(io_stream, ">i", 0)
        write_fmt(io_stream, ">i", 0)

        param_offset = io_stream.tell()

        write_csp_unicode_str(">i", io_stream, "Parameter")
        write_fmt(io_stream, ">i", self.bitmap_width)
        write_fmt(io_stream, ">i", self.bitmap_height)
        write_fmt(io_stream, ">i", self.block_grid_width)
        write_fmt(io_stream, ">i", self.block_grid_height)

        self.packing_attributes.write(io_stream)
        param_section_size = io_stream.tell() - param_offset

        init_color_offset = io_stream.tell()
        write_csp_unicode_str(">i", io_stream, "InitColor")
        write_fmt(io_stream, ">i", 20)
        write_fmt(io_stream, ">i", self.default_fill_color)
        write_fmt(io_stream, ">i", 0)
        write_fmt(io_stream, ">i", len(self.other_init_colors))
        write_fmt(io_stream, ">i", 4)

        for col in self.other_init_colors:
            write_fmt(io_stream, ">i", col)

        init_color_size = io_stream.tell() - init_color_offset

        block_size_offset = io_stream.tell()
        write_csp_unicode_str(">i", io_stream, "BlockSize")
        write_fmt(io_stream, ">i", 12)
        write_fmt(io_stream, ">i", len(self.block_sizes))
        write_fmt(io_stream, ">i", 4)

        for size in self.block_sizes:
            write_fmt(io_stream, ">i", size)

        total_size = io_stream.tell()
        block_size = total_size - block_size_offset

        io_stream.seek(0)

        write_fmt(io_stream, ">i", 0x10)
        write_fmt(io_stream, ">i", param_section_size)
        write_fmt(io_stream, ">i", init_color_size)
        write_fmt(io_stream, ">i", block_size)

    def tobytes(self):
        byte_arr = io.BytesIO()
        self.write(byte_arr)
        return byte_arr.getbuffer().tobytes()

    @classmethod
    def read(cls, io_stream):

        if not isinstance(io_stream, io.BytesIO):
            io_stream = io.BytesIO(io_stream)

        header_size = read_fmt(">i", io_stream)
        parameter_section_size = read_fmt(">i", io_stream)
        init_color_section_size = read_fmt(">i", io_stream)
        block_size_section_size = read_fmt(">i", io_stream)

        assert read_csp_unicode_str(">i", io_stream) == "Parameter"

        bitmap_width = read_fmt(">i", io_stream)
        bitmap_height = read_fmt(">i", io_stream)
        block_grid_width = read_fmt(">i", io_stream)
        block_grid_height = read_fmt(">i", io_stream)

        packing_attributes = PixelPackingAttribute.read(io_stream)

        assert read_csp_unicode_str(">i", io_stream) == "InitColor"

        u2 = read_fmt(">i", io_stream)
        assert u2 == 20, u2

        default_fill_color = read_fmt(">i", io_stream)
        u3 = read_fmt(">i", io_stream)
        #assert u3 == -1, u3

        other_init_colors_count = read_fmt(">i", io_stream) # ?

        u5 = read_fmt(">i", io_stream)
        assert u5 == 4, u5

        other_init_colors = []
        for _ in range(other_init_colors_count):
            other_init_colors.append(read_fmt(">i", io_stream))

        assert read_csp_unicode_str(">i", io_stream) == "BlockSize"

        u6 = read_fmt(">i", io_stream)
        assert u6 == 12, u6

        block_count = read_fmt(">i", io_stream)

        u7 = read_fmt(">i", io_stream)
        assert u7 == 4, u7

        blocks_sizes = [read_fmt(">i", io_stream) for _i in range(block_count)]

        return cls(
            bitmap_width,
            bitmap_height,
            block_grid_width,
            block_grid_height,
            packing_attributes,
            default_fill_color,
            other_init_colors,
            blocks_sizes
        )

    @classmethod
    def new(cls, width, height, color_mode):

        block_number = ((width // 256) + 1) * ((height // 256) + 1)

        return cls(
            bitmap_width = width,
            bitmap_height = height,
            block_grid_width = (width // 256) + 1,
            block_grid_height = (height // 256) + 1,
            packing_attributes = PixelPackingAttribute.new(color_mode),
            default_fill_color = 0,
            other_init_colors = [],
            block_sizes = [104 for _ in range(block_number)]
        )
