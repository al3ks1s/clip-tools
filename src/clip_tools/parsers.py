import io
import zlib

from PIL import Image
from clip_tools.utils import read_fmt, read_csp_unicode_str, read_csp_str, read_csp_unicode_le_str, decompositor

from clip_tools.constants import GradientRepeatMode, GradientShape, ScreenToneShape, ExtractLinesDirection, TextAttribute, TextAlign, TextStyle, TextOutline, TextWrapDirection, VectorFlag, VectorPointFlag
from clip_tools.data_classes import Position, Color, ColorStop, CurvePoint, VectorPoint, VectorLine, TextRun, TextParam, BBox, RulerCurvePoint, ReadingSetting, TextBackground, TextEdge

from collections import namedtuple

import logging
import binascii

logger = logging.getLogger(__name__)

def parse_offscreen_attribute(offscreen_attribute):

    columns = ["header_size", "info_section_size", "extra_info_section_size", "u1", "bitmap_width", "bitmap_height", "block_grid_width", "block_grid_height", "pixel_packing_attributes", "u2", "default_fill_color", "u3", "other_init_color_count", "u5", "u6", "block_count", "u7", "block_sizes"]

    parameter_str = "Parameter".encode('UTF-16-BE')
    initcolor_str = "InitColor".encode('UTF-16-BE')
    blocksize_str = "BlockSize".encode('UTF-16-BE')

    offscreen_io = io.BytesIO(offscreen_attribute)

    header_size = read_fmt(">i", offscreen_io)
    info_section_size = read_fmt(">i", offscreen_io)

    extra_info_section_size = read_fmt(">i", offscreen_io)

    u1 = read_fmt(">i", offscreen_io)

    parameter_size = read_fmt(">i", offscreen_io)
    assert offscreen_io.read(parameter_size * 2) == parameter_str

    bitmap_width = read_fmt(">i", offscreen_io)
    bitmap_height = read_fmt(">i", offscreen_io)
    block_grid_width = read_fmt(">i", offscreen_io)
    block_grid_height = read_fmt(">i", offscreen_io)

    pixel_packing_attributes = [read_fmt(">i", offscreen_io) for _i in range(16)]

    initcolor_size = read_fmt(">i", offscreen_io)
    assert offscreen_io.read(initcolor_size * 2) == initcolor_str

    u2 = read_fmt(">i", offscreen_io)
    default_fill_color = read_fmt(">i", offscreen_io)
    u3 = read_fmt(">i", offscreen_io)
    other_init_colors_count = read_fmt(">i", offscreen_io) # ?
    u5 = read_fmt(">i", offscreen_io)

    other_init_colors = []
    for _ in range(other_init_colors_count):
        other_init_colors.append(read_fmt(">i", offscreen_io))
    
    blocksize_size = read_fmt(">i", offscreen_io)
    assert offscreen_io.read(blocksize_size * 2) == blocksize_str

    u6 = read_fmt(">i", offscreen_io)
    block_count = read_fmt(">i", offscreen_io)
    u7 = read_fmt(">i", offscreen_io)

    blocks_sizes = [read_fmt(">i", offscreen_io) for _i in range(block_count)]
    
    values = [header_size, info_section_size, extra_info_section_size, u1, bitmap_width, bitmap_height, block_grid_width, block_grid_height, pixel_packing_attributes, u2, default_fill_color, u3, other_init_colors_count, u5, u6, block_count, u7, blocks_sizes]
    
    return namedtuple("mipAttributes", columns)(*values)

def decode_chunk_to_pil(chunk, offscreen_attributes):

    def channel_to_pil(c_num):

        c_d = {
            3: "RGB",
            4: "RGBA",
            5: "RGBA",

            1: "L",
            2: "LA"
        }

        return c_d.get(c_num)

    bit_depth = offscreen_attributes.pixel_packing_attributes[0] # See CanvasChannelBytes

    alpha_channel_count = offscreen_attributes.pixel_packing_attributes[1] # Alpha channel count
    buffer_channel_count = offscreen_attributes.pixel_packing_attributes[2] # Image buffer channel count
    total_channel_count = offscreen_attributes.pixel_packing_attributes[3] # Total channel count

    buffer_block_byte_count = offscreen_attributes.pixel_packing_attributes[4]# Buffer block byte count dependant on bit depth (eg : 1-bit will be 8192)

    buffer_channel_count2 = offscreen_attributes.pixel_packing_attributes[5]
    buffer_bit_depth = offscreen_attributes.pixel_packing_attributes[6] // 32 # Buffer bit depth (Per buffer block, need to divide by the number of channel) 

    alpha_channel_count2 = offscreen_attributes.pixel_packing_attributes[7]
    alpha_bit_depth = offscreen_attributes.pixel_packing_attributes[8] // 32

    buffer_block_area = offscreen_attributes.pixel_packing_attributes[9]

    block_width = offscreen_attributes.pixel_packing_attributes[10]
    block_height = offscreen_attributes.pixel_packing_attributes[11]

    unk1 = offscreen_attributes.pixel_packing_attributes[12] # Always 8
    unk1 = offscreen_attributes.pixel_packing_attributes[13] # Always 8

    monochrome = bool(offscreen_attributes.pixel_packing_attributes[14]) # Only changed to 1 when the layer was mono
    
    unk1 = offscreen_attributes.pixel_packing_attributes[15] # Always 0

    total_channel_count = buffer_channel_count + alpha_channel_count

    im = Image.new(channel_to_pil(total_channel_count), (offscreen_attributes.bitmap_width, offscreen_attributes.bitmap_height), 255*offscreen_attributes.default_fill_color)

    block_area = block_width * block_height

    for h in range(offscreen_attributes.block_grid_height):
        for w in range(offscreen_attributes.block_grid_width):
            block = chunk.block_datas[h * offscreen_attributes.block_grid_width + w]

            block_res = b''

            if block.data_present:

                pix_bytes = zlib.decompress(block.data)

                final_channels = []

                if buffer_channel_count != 0:

                    buffer_block_byte_count = block_area // (8 // (buffer_bit_depth // buffer_channel_count))

                    if monochrome:
                        block_buffer = Image.frombuffer("1", (block_width, block_height), pix_bytes[buffer_block_byte_count * alpha_channel_count:buffer_block_byte_count*(buffer_channel_count + alpha_channel_count)])
                        block_buffer = block_buffer.convert(channel_to_pil(buffer_channel_count))

                    else:
                        block_buffer = Image.frombuffer(channel_to_pil(buffer_channel_count), (block_width, block_height), pix_bytes[buffer_block_byte_count * alpha_channel_count:buffer_block_byte_count*(buffer_channel_count + alpha_channel_count)])

                    buffer_channels = block_buffer.split()
                    block_buffer = buffer_channels[:3][::-1]

                    final_channels.extend(block_buffer)

                if alpha_channel_count != 0:

                    alpha_byte_count = block_area // (8 // alpha_bit_depth)

                    if monochrome:
                        block_alpha = Image.frombuffer("1", (block_width, block_height), pix_bytes[:alpha_byte_count * alpha_channel_count])
                        block_alpha = block_alpha.convert(channel_to_pil(alpha_channel_count))
                    else:

                        block_alpha = Image.frombuffer(channel_to_pil(alpha_channel_count), (block_width, block_height), pix_bytes[:alpha_byte_count * alpha_channel_count])

                    final_channels.extend(block_alpha.split())

                if len(final_channels) == 0:
                    raise ValueError("No channels to merge in chunk decoding")

                block_res = Image.merge(channel_to_pil(total_channel_count), final_channels)

                im.paste(block_res, (256*w,256*h))

    return im

def parse_gradient_info(gradation_fill_info):

    gradient_data = io.BytesIO(gradation_fill_info)

    gradient_data_size = read_fmt(">i", gradient_data)
    unk1 = read_fmt(">i", gradient_data) # Always '0x02'

    gradient_info = {}

    while gradient_data.tell() < gradient_data_size:

        param_name = read_csp_unicode_str(">i", gradient_data)

        if param_name == "GradationData":

            section_size = read_fmt(">i", gradient_data)
            unk2 = read_fmt(">i", gradient_data)
            unk3 = read_fmt(">i", gradient_data)
            num_color_stop = read_fmt(">i", gradient_data)
            unk4 = read_fmt(">i", gradient_data)

            color_stops = []

            for _ in range(num_color_stop):

                r,g,b = (read_fmt(">I", gradient_data) >> 24 for _ in range(3))
                rgb = Color(r,g,b)

                opacity = read_fmt(">I", gradient_data) >> 24
                is_current_color = read_fmt(">i", gradient_data)
                position = read_fmt(">i", gradient_data) * 100 // 32768
                num_curve_points = read_fmt(">i", gradient_data)

                curve_points = []

                color_stops.append(ColorStop(rgb, opacity, is_current_color, position, num_curve_points, curve_points))

            for color_stop in color_stops:
                if color_stop.num_curve_points != 0:
                    for _ in range(color_stop.num_curve_points):
                        point = CurvePoint(read_fmt(">d", gradient_data), read_fmt(">d", gradient_data))
                        
                        # To look into

                        color_stop.curve_points.append(point)

            gradient_info["color_stops"] = color_stops

        if param_name == "GradationSettingAdd0001":

            section_size = read_fmt(">i", gradient_data)

            gradient_info["is_flat"] = bool(read_fmt(">i", gradient_data))

            r,g,b = (read_fmt(">I", gradient_data) >> 24 for _ in range(3))
            gradient_info["fill_color"] = Color(r,g,b)

            read_fmt(">i", gradient_data)

        if param_name == "GradationSetting":

            gradient_info["repeat_mode"] = GradientRepeatMode(read_fmt(">i", gradient_data))
            gradient_info["shape"] = GradientShape(read_fmt(">i", gradient_data))

            gradient_info["anti_aliasing"] = bool(read_fmt(">i", gradient_data))

            gradient_info["diameter"] = read_fmt(">d", gradient_data)
            gradient_info["ellipse_diameter"] = read_fmt(">d", gradient_data)

            gradient_info["rotation_angle"] = read_fmt(">d", gradient_data)

            gradient_info["start"] = Position(read_fmt(">d", gradient_data), read_fmt(">d", gradient_data))
            gradient_info["end"] = Position(read_fmt(">d", gradient_data), read_fmt(">d", gradient_data))

    return gradient_info

def parse_text_attribute(text_layer_attribute_array):

    text_attributes = io.BytesIO(text_layer_attribute_array)
    text_params = {}

    while text_attributes.tell() < len(text_layer_attribute_array):
        param_id = read_fmt("<i", text_attributes)
        param_size = read_fmt("<i", text_attributes)

        if param_size == 0:
            continue

        if param_id == TextAttribute.RUNS:
            num_runs = read_fmt("<i", text_attributes)
            runs = []

            for _ in range(num_runs):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                entry_size = read_fmt("<i", text_attributes)

                style_flag = read_fmt("<b", text_attributes)
                default_style_flag = read_fmt("<b", text_attributes)

                color = Color(
                    read_fmt("<H", text_attributes) // 65535,
                    read_fmt("<H", text_attributes) // 65535,
                    read_fmt("<H", text_attributes) // 65535
                )

                font_scale = read_fmt("<d", text_attributes)

                font = read_csp_unicode_le_str("<h", text_attributes)

                runs.append(
                    TextRun(
                        start,
                        length,
                        style_flag,
                        default_style_flag,
                        color,
                        font_scale,
                        font
                    )
                )

            text_params[TextAttribute(param_id)] = runs
            #print(runs)

        elif param_id == TextAttribute.ALIGN:

            num_aligns = read_fmt("<i", text_attributes)

            aligns = []

            for _ in range(num_aligns):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)
                align = read_fmt("h", text_attributes)
                #unk = read_fmt("b", text_attributes)

                aligns.append(TextParam(TextAttribute(param_id),
                                start,
                                length,
                                TextAlign(align)))

            text_params[TextAttribute(param_id)] = aligns

            #print(aligns)

        elif param_id == TextAttribute.UNDERLINE:
            num_underlines = read_fmt("<i", text_attributes)

            underlines = []

            for _ in range(num_underlines):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)
                underline = read_fmt("<h", text_attributes)

                #unk = read_fmt("<b", text_attributes)
                #print(unk)
                underlines.append(TextParam(TextAttribute(param_id),
                                    start,
                                    length,
                                    bool(underline)))

            text_params[TextAttribute(param_id)] = underlines

        elif param_id == TextAttribute.STRIKE:

            num_strikes = read_fmt("<i", text_attributes)

            strikes = []

            for _ in range(num_strikes):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)
                strike = read_fmt("h", text_attributes)

                strikes.append(TextParam(TextAttribute(param_id),
                                start,
                                length,
                                bool(strike)))

            text_params[TextAttribute(param_id)] = strikes
            
            #print(strikes)

        elif param_id == TextAttribute.ASPECT_RATIO:

            num_ratio = read_fmt("<i", text_attributes)

            ratios = []

            for _ in range(num_ratio):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)

                ratios.append((start, length, (read_fmt("<d", text_attributes), read_fmt("<d", text_attributes))))

            text_params[TextAttribute(param_id)] = ratios

            #print(ratios)

        elif param_id == TextAttribute.CONDENSE_TEXT:
            # Condense Text
            num_param = read_fmt("<i", text_attributes)

            params = []

            for _ in range(num_param):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)

                params.append(read_fmt("<d", text_attributes))

            text_params[TextAttribute(param_id)] = params

            #print(params)

        elif param_id == TextAttribute.CHARACTER_SPACING:
            # Spacing
            num_param = read_fmt("<i", text_attributes)

            params = []

            for _ in range(num_param):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)

                params.append(read_fmt("<d", text_attributes))

            text_params[TextAttribute(param_id)] = params
            #print(params)

        elif param_id == TextAttribute.FONT:
            font = text_attributes.read(param_size)
            #print(font)

            text_params[TextAttribute(param_id)] = font

        elif param_id == TextAttribute.FONT_SIZE:
            font_size = read_fmt("<i", text_attributes) / 100
            #print(font_size)

            text_params[TextAttribute(param_id)] = font_size


        elif param_id == TextAttribute.GLOBAL_COLOR:

            color = Color(read_fmt("<I", text_attributes) >> 24,
                            read_fmt("<I", text_attributes) >> 24,
                            read_fmt("<I", text_attributes) >> 24)

            #print(color)
            text_params[TextAttribute(param_id)] = color

        elif param_id == TextAttribute.BBOX:
            bbox = BBox.read("<I", text_attributes)
            #print(bbox)
            text_params[TextAttribute(param_id)] = bbox

        elif param_id == TextAttribute.FONTS:
            num_fonts = read_fmt("<h", text_attributes)

            font_list = []

            for _ in range(num_fonts):

                disp_name = read_csp_str("<h", text_attributes)
                font_name = read_csp_str("<h", text_attributes)

            angle = read_fmt("<i", text_attributes)
            font_list.append([disp_name, font_name])

            #print(font_list)
            text_params[TextAttribute(param_id)] = font_list

        elif param_id == TextAttribute.BOX_SIZE:
            box_size = [read_fmt("<i", text_attributes), read_fmt("<i", text_attributes)]
            #print(box_size)
            text_params[TextAttribute(param_id)] = box_size

        elif param_id == TextAttribute.QUAD_VERTS:
            quad_verts = [read_fmt("<i", text_attributes) / 100 for _ in range(8)]
            #print(quad_verts)
            text_params[TextAttribute(param_id)] = quad_verts

        elif param_id == TextAttribute.OUTLINE:

            num_outlines = read_fmt("<i", text_attributes)

            outlines = []

            for _ in range(num_outlines):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)

                outline = TextOutline(read_fmt("<h", text_attributes))

                outlines.append((start, length, outline))

            #print(outlines)
            text_params[TextAttribute(param_id)] = outlines

        elif param_id == TextAttribute.GLOBAL_STYLE:
            style_flag = TextStyle(read_fmt("<i", text_attributes))
            #print([style_flag])
            text_params[TextAttribute(param_id)] = style_flag

        elif param_id in [TextAttribute.SKEW_ANGLE_1, TextAttribute.SKEW_ANGLE_2]:
            skew_angle = read_fmt("<i", text_attributes) / 10
            #print(skew_angle)
            text_params[TextAttribute(param_id)] = skew_angle

        elif param_id == TextAttribute.GLOBAL_JUSTIFY:
            value = TextAlign(read_fmt("<i", text_attributes))
            #print([value])
            text_params[TextAttribute(param_id)] = value

        elif param_id == TextAttribute.ABSOLUTE_SPACING:
            # This is not spacing, something else but its also correlated to spacing?
            spacing = read_fmt("<i", text_attributes)
            #print(spacing)

        elif param_id == TextAttribute.READING_SETTING:
            # Part of reading settings : First short is a flag for Reading even/align, second is reading size ratio
            text_params[TextAttribute(param_id)] = ReadingSetting.read(text_attributes)

        elif param_id == TextAttribute.BACKGROUND:
            # Background param

            text_params[TextAttribute(param_id)] = TextBackground.read(text_attributes)
            #print(bg_enabled, bg_color, bg_opacity)

        elif param_id == TextAttribute.EDGE:
            # Edge data

            text_params[TextAttribute(param_id)] = TextEdge.read(text_attributes)

            #print(edge_enabled, edge_size, unk, edge_color)

        elif param_id == TextAttribute.ANTI_ALIASING:
            # Anti aliasing on/off ? Has 1 for on, 2 for off
            value = read_fmt("<i", text_attributes)

        elif param_id == TextAttribute.WRAP_FRAME:
            text_params[TextAttribute(param_id)] = bool(read_fmt("<i", text_attributes))

        elif param_id == TextAttribute.WRAP_DIRECTION:
            text_params[TextAttribute(param_id)] = TextWrapDirection(read_fmt("<i", text_attributes))

        elif param_id == TextAttribute.HALF_WIDTH_PUNCT:
            text_params[TextAttribute(param_id)] = bool(read_fmt("<i", text_attributes))

        elif param_id == TextAttribute.ROTATION_ANGLE:
            text_params[TextAttribute(param_id)] = read_fmt("<i", text_attributes) / 10

        elif param_id == TextAttribute.HORZ_IN_VERT:
            # TateChuYoko (Horizontal In Vertical) Never managed to make it work on my csp so idk what it does
            text_params[TextAttribute(param_id)] = read_fmt("<i", text_attributes)

        elif param_id == TextAttribute.TEXT_ID:
            text_params[TextAttribute(param_id)] = read_fmt("<i", text_attributes)

        elif param_id == TextAttribute.LINE_SPACING:

            params = []
            num_spacings = read_fmt("<i", text_attributes)

            for _ in range(num_spacings):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)
                absolute_spacing_enabled = read_fmt("<h", text_attributes)
                # 1 is absolute, 0 is relative

                relative_spacing = read_fmt("<d", text_attributes)
                absolute_spacing = read_fmt("<d", text_attributes)

                params.append((
                    start,
                    length,
                    absolute_spacing_enabled,
                    relative_spacing,
                    absolute_spacing
                ))

            text_params[TextAttribute(param_id)] = params

        elif param_id == 39:
            # Tuple usually defining the text length, either on the first or second index
            unk_pair = (read_fmt("<i", text_attributes), read_fmt("<i", text_attributes))
            #print(unk_pair)
        elif param_id == 44:
            # No idea, consistently 8333
            value = read_fmt("<i", text_attributes)
            assert value == 8333
            #print(decompositor(value))
        elif param_id == 43:
            # Consistently 50
            value = read_fmt("<i", text_attributes)
            assert value == 50
            #print(value)
        elif param_id == 45:
            # Consistently 0
            value = read_fmt("<i", text_attributes)
            assert value == 0
        elif param_id == 46:
            # 0
            value = read_fmt("<i", text_attributes)
            #print(param_id, value)
        elif param_id == 49:
            # 100
            value = read_fmt("<i", text_attributes)
            #print(param_id, value)
        elif param_id == 51:
            # 0
            value = read_fmt("<i", text_attributes)
            #print(param_id, value)
        elif param_id == 61:
            # 0
            value = read_fmt("<i", text_attributes)
            #print(param_id, value)
        elif param_id == 62:
            # 0
            value = read_fmt("<i", text_attributes)
            #print(param_id, value)
        elif param_id == 17:
            # Mixed font data?
            
            params = []
            num_params = read_fmt("<i", text_attributes)

            for _ in range(num_params):

                start = read_fmt("<I", text_attributes)
                length = read_fmt("<i", text_attributes)

                data_size = read_fmt("<i", text_attributes)

                # 4 ints? 2 floats? anything else?
                unk1 = read_fmt("<i", text_attributes)
                unk2 = read_fmt("<i", text_attributes)
                unk3 = read_fmt("<i", text_attributes)
                unk4 = read_fmt("<i", text_attributes)

                stri = read_csp_unicode_le_str("<h", text_attributes)

                params.append((start, length, unk1, unk2, unk3, unk4, stri))

            #print(params)

        else:

            value = text_attributes.read(param_size)
            logger.warning(f"Unknown text param: {param_id} {param_size} {value}")

    return text_params

def parse_point_data(point_data):
    points_bytes = io.BytesIO(point_data)

    points = []

    header_size = read_fmt(">i", points_bytes)
    point_count = read_fmt(">i", points_bytes)
    logger.debug("Unknown param for point data : %d" % read_fmt(">i", points_bytes))
    logger.debug("Unknown param for point data : %d" % read_fmt(">i", points_bytes))
    logger.debug("Unknown param for point data : %d" % read_fmt(">i", points_bytes))
    logger.debug("Unknown param for point data : %d" % read_fmt(">i", points_bytes))

    for _ in range(point_count):
        pos = Position.read(points_bytes)
        thickness = read_fmt(">i", points_bytes)

        points.append(RulerCurvePoint(pos, thickness))

    return points

def parse_vector(vector_blob):

    vector_data = io.BytesIO(vector_blob)

    vector_lines = []

    headers_sizes = []
    flags = []

    while vector_data.tell() < len(vector_blob) - 16:

        # Header, holds section size info
        header_size = read_fmt(">i", vector_data) # Full Header section size
        sign2 = read_fmt(">i", vector_data) # Point section size without the point size (16 bytes)
        point_size = read_fmt(">i", vector_data) # Seems to be a single point section size
        sign4 = read_fmt(">i", vector_data) # Default point section size?

        # To identify new values
        assert sign2 == 72, "Please report to https://github.com/al3ks1s/clip-tools/issues"
        assert sign4 == 88, "Please report to https://github.com/al3ks1s/clip-tools/issues"

        #print((header_size, point_size))

        headers_sizes.append((header_size, point_size))

        num_points = read_fmt(">i", vector_data)

        vector_flag = VectorFlag(read_fmt(">i", vector_data))

        flags.append(" ".join(decompositor(vector_flag)))

        vector_bbox = BBox.read(">i", vector_data)

        main_color = Color.read(vector_data)
        sub_color = Color.read(vector_data)

        global_opacity = read_fmt(">d", vector_data)

        brush_id = read_fmt(">i", vector_data)

        brush_radius=0
        if vector_flag & VectorFlag.NORMAL:
            brush_radius = read_fmt(">d", vector_data)
            last_value_unk = read_fmt(">i", vector_data)

        if vector_flag & VectorFlag.FRAME:

            frame_brush_id = read_fmt(">i", vector_data)
            frame_fill_id = read_fmt(">i", vector_data)

            brush_radius = read_fmt(">d", vector_data)
            last_value_unk = read_fmt(">i", vector_data)

            brush_id = frame_brush_id

        points = []

        for _ in range(num_points):

            pos = Position.read(vector_data)
            point_bbox = BBox.read(">i", vector_data)

            point_vector_flag = VectorPointFlag(read_fmt(">i", vector_data))

            # For testing
            remaining_point_size = point_size - (2*8) - (2*8) -4-4-4-4-4-4-4-4-4-4-4-4-4-4

            point_scale = read_fmt(">f", vector_data)
            point_scale_2 = read_fmt(">f", vector_data)
            point_scale_3 = read_fmt(">f", vector_data)
            #print(point_scale, point_scale_2, point_scale_3)

            unk1 = read_fmt(">f", vector_data)
            unk2 = read_fmt(">f", vector_data) # Dispersion? seems to define a statistical looking curve
            #print(unk1, unk2)

            point_width = read_fmt(">f", vector_data)
            point_opacity = read_fmt(">f", vector_data)

            # Some corner values for frames, angles? Doesn't seem to have effect
            unk1 = read_fmt(">f", vector_data)
            unk2 = read_fmt(">f", vector_data)
            unk3 = read_fmt(">f", vector_data)
            #print(unk1, unk2, unk3)

            # Unknown non zero parameter
            unk1 = read_fmt(">f", vector_data)
            unk2 = read_fmt(">f", vector_data)
            #print(unk1, unk2)

            # Only zeros
            unk = read_fmt(">i", vector_data)
            #print(unk)

            if vector_flag & VectorFlag.CURVE_QUADRATIC_BEZIER:
                
                bezier_point = Position.read(vector_data)
                remaining_point_size -= 16

            if vector_flag & VectorFlag.CURVE_CUBIC_BEZIER:
                
                bezier_first_point = Position.read(vector_data)
                bezier_second_point = Position.read(vector_data)
                
                remaining_point_size -= 32

            # For testing
            point_params = []
            for _ in range(remaining_point_size // 4):
                point_params.append(read_fmt(">i", vector_data))
            if len(point_params) != 0:
                logger.warning(f"Found new vector parameters : {point_params}")


            points.append(
                VectorPoint(
                    pos,
                    point_bbox,
                    point_vector_flag,
                    point_scale,
                    point_scale_2,
                    point_scale_3,
                    point_width,
                    point_opacity
                )
            )


        vector_lines.append(
            VectorLine(
                num_points,
                vector_flag,
                vector_bbox,
                main_color,
                sub_color,
                global_opacity,
                brush_id,
                brush_radius,
                points
            )
        )

    #print(set(flags))
    #print(set(headers_sizes))
    #print()

    return vector_lines