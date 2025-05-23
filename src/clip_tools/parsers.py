import io
import zlib
from isal import isal_zlib
import concurrent.futures
from PIL import Image, ImageChops
from clip_tools.utils import read_fmt, read_csp_unicode_str, read_csp_str, read_csp_unicode_le_str, decompositor, channel_to_pil
from clip_tools.clip.DataChunk import DataChunk, BlockData, Block
from clip_tools.constants import TextAttribute, TextAlign, TextStyle, TextOutline, TextWrapDirection, VectorFlag, VectorPointFlag
from clip_tools.data_classes import Position, Color, TextRun, TextParam, BBox, ReadingSetting, TextBackground, TextEdge, OffscreenAttribute, PixelPackingAttribute, ColorMode
from Cryptodome.Hash import MD5
from collections import namedtuple

import logging

logger = logging.getLogger(__name__)

def decode_chunk_to_pil(chunk, offscreen_attribute):

    pix_packing = offscreen_attribute.packing_attributes

    total_channel_count = pix_packing.buffer_channel_count + pix_packing.alpha_channel_count

    im = Image.new(
        channel_to_pil(total_channel_count),
        (offscreen_attribute.bitmap_width, offscreen_attribute.bitmap_height),
        255*offscreen_attribute.default_fill_color
    )

    block_area = pix_packing.block_width * pix_packing.block_height

    for h in range(offscreen_attribute.block_grid_height):
        for w in range(offscreen_attribute.block_grid_width):
            block = chunk.block_data[h * offscreen_attribute.block_grid_width + w]
            block_res = b''

            if block.data_present:

                pix_bytes = zlib.decompress(block.data)

                final_channels = []

                if pix_packing.buffer_channel_count != 0:

                    buffer_block_byte_count = block_area // (8 // (pix_packing.buffer_bit_depth // pix_packing.buffer_channel_count))

                    if pix_packing.monochrome:
                        block_buffer = Image.frombuffer(
                            "1", 
                            (pix_packing.block_width, pix_packing.block_height),
                            pix_bytes[
                                buffer_block_byte_count * pix_packing.alpha_channel_count:
                                buffer_block_byte_count *(pix_packing.buffer_channel_count + pix_packing.alpha_channel_count)
                            ]
                        )

                        block_buffer = block_buffer.convert(channel_to_pil(pix_packing.buffer_channel_count))

                    else:
                        block_buffer = Image.frombuffer(
                            channel_to_pil(pix_packing.buffer_channel_count),
                            (pix_packing.block_width, pix_packing.block_height),
                            pix_bytes[
                                buffer_block_byte_count * pix_packing.alpha_channel_count:
                                buffer_block_byte_count*(pix_packing.buffer_channel_count + pix_packing.alpha_channel_count)
                            ]
                        )

                    buffer_channels = block_buffer.split()
                    block_buffer = buffer_channels[:3][::-1]

                    final_channels.extend(block_buffer)

                if pix_packing.alpha_channel_count != 0:

                    alpha_byte_count = block_area // (8 // pix_packing.alpha_bit_depth)

                    if pix_packing.monochrome:
                        block_alpha = Image.frombuffer(
                            "1", 
                            (pix_packing.block_width, pix_packing.block_height),
                            pix_bytes[:alpha_byte_count * pix_packing.alpha_channel_count]
                        )

                        block_alpha = block_alpha.convert(channel_to_pil(pix_packing.alpha_channel_count))
                    else:

                        block_alpha = Image.frombuffer(
                            channel_to_pil(pix_packing.alpha_channel_count),
                            (pix_packing.block_width, pix_packing.block_height),
                            pix_bytes[:alpha_byte_count * pix_packing.alpha_channel_count]
                        )

                    final_channels.extend(block_alpha.split())

                if len(final_channels) == 0:
                    raise ValueError("No channels to merge in chunk decoding")

                block_res = Image.merge(channel_to_pil(total_channel_count), final_channels)

                im.paste(block_res, (256*w,256*h))

    return im

def encode_pil_to_chunk(pil_im):

    chunk_data = DataChunk.new()

    width = pil_im.width
    height = pil_im.height
    color_mode = ColorMode.from_pil(pil_im.mode)

    offscreen_attribute = OffscreenAttribute.new(width, height, color_mode)
    packing_attributes = offscreen_attribute.packing_attributes

    for h in range(offscreen_attribute.block_grid_height):
        for w in range(offscreen_attribute.block_grid_width):

            image_data = io.BytesIO()

            block_image = pil_im.crop((
                w * packing_attributes.block_width,
                h * packing_attributes.block_height,
                (w+1) * packing_attributes.block_width,
                (h+1) * packing_attributes.block_height
            ))

            if block_image.getbbox(alpha_only=False) is None and "A" in block_image.getbands():
                chunk_data.block_data.append(
                    Block.new(h * offscreen_attribute.block_grid_width + w, None)
                )
                continue

            if "A" in block_image.getbands():
                alpha_channel = block_image.getchannel("A")
                image_data.write(alpha_channel.tobytes('raw'))
            else:
                mock_alpha = Image.new(
                    "L",
                    (packing_attributes.block_width, packing_attributes.block_height),
                    255
                )
                image_data.write(mock_alpha.tobytes('raw'))

            color_bands = tuple(band for band in block_image.getbands() if band != 'A')

            color_channels = Image.merge(
                block_image.mode.rstrip("A"),
                [block_image.getchannel(band) for band in color_bands][::-1]
            )

            if color_channels.mode == "RGB":
                color_channels.putalpha(0) # Padding

            image_data.write(color_channels.tobytes('raw'))

            compressed_blk = zlib.compress(image_data.getbuffer().tobytes(), level=1)

            chunk_data.block_data.append(Block.new(
                h * offscreen_attribute.block_grid_width + w,
                compressed_blk
            ))

            offscreen_attribute.block_sizes[h * offscreen_attribute.block_grid_width + w] = (112 + len(compressed_blk))

    return chunk_data, offscreen_attribute



# Not sure these two are relevant to keep
def encoder_worker(img_part_tuple):

    img_part = img_part_tuple[0]
    offscreen_attribute = img_part_tuple[1]
    w = img_part_tuple[2]
    h = img_part_tuple[3]

    packing_attributes = offscreen_attribute.packing_attributes

    image_data = io.BytesIO()

    if img_part.getbbox(alpha_only=False) is None and "A" in img_part.getbands():
        return Block.new(h * offscreen_attribute.block_grid_width + w, None)

    if "A" in img_part.getbands():
        alpha_channel = img_part.getchannel("A")
        image_data.write(alpha_channel.tobytes('raw'))
    else:
        mock_alpha = Image.new(
            "L",
            (packing_attributes.block_width, packing_attributes.block_height),
            255
        )
        image_data.write(mock_alpha.tobytes('raw'))

    color_bands = tuple(band for band in img_part.getbands() if band != 'A')

    color_channels = Image.merge(
        img_part.mode.rstrip("A"),
        [img_part.getchannel(band) for band in color_bands][::-1]
    )

    if color_channels.mode == "RGB":
        color_channels.putalpha(0) # Padding

    image_data.write(color_channels.tobytes('raw'))

    return Block.new(
        h * offscreen_attribute.block_grid_width + w,
        zlib.compress(image_data.getbuffer(), level=1)
    )

def encode_pil_to_chunk_parallels(pil_im):

    chunk_data = DataChunk.new()

    offscreen_attribute = OffscreenAttribute.new(pil_im)
    packing_attributes = offscreen_attribute.packing_attributes

    img_parts = []

    for h in range(offscreen_attribute.block_grid_height):
        for w in range(offscreen_attribute.block_grid_width):

            block_image = pil_im.crop((
                w * packing_attributes.block_width,
                h * packing_attributes.block_height,
                (w+1) * packing_attributes.block_width,
                (h+1) * packing_attributes.block_height
            ))

            img_parts.append((block_image, offscreen_attribute, w, h))

            #chunk_data.block_data.append(encoder_worker(block_image, offscreen_attribute, w, h))

    with concurrent.futures.ProcessPoolExecutor() as executor:
        for block in executor.map(encoder_worker, img_parts):
            chunk_data.block_data.append(block)

    return chunk_data, offscreen_attribute


# Deprecated
def parse_offscreen_attribute(offscreen_attribute):

    columns = ["header_size", "info_section_size", "extra_info_section_size", "u1", "bitmap_width", "bitmap_height", "block_grid_width", "block_grid_height", "pixel_packing_attributes", "u2", "default_fill_color", "u3", "other_init_color_count", "u5", "u6", "block_count", "u7", "block_sizes"]

    parameter_str = "Parameter".encode('UTF-16-BE')
    initcolor_str = "InitColor".encode('UTF-16-BE')
    blocksize_str = "BlockSize".encode('UTF-16-BE')

    offscreen_io = io.BytesIO(offscreen_attribute)

    header_size = read_fmt(">i", offscreen_io)
    parameter_section_size = read_fmt(">i", offscreen_io)
    init_color_section_size = read_fmt(">i", offscreen_io)
    block_size_section_size = read_fmt(">i", offscreen_io)

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
    assert u2 == 20

    default_fill_color = read_fmt(">i", offscreen_io)
    u3 = read_fmt(">i", offscreen_io)
    assert u3 == -1

    other_init_colors_count = read_fmt(">i", offscreen_io) # ?
    u5 = read_fmt(">i", offscreen_io)
    assert u5 == 4

    other_init_colors = []
    for _ in range(other_init_colors_count):
        other_init_colors.append(read_fmt(">i", offscreen_io))
        print(other_init_colors)

    blocksize_size = read_fmt(">i", offscreen_io)
    assert offscreen_io.read(blocksize_size * 2) == blocksize_str

    u6 = read_fmt(">i", offscreen_io)
    assert u6 == 12

    block_count = read_fmt(">i", offscreen_io)
    u7 = read_fmt(">i", offscreen_io)
    assert u7 == 4

    blocks_sizes = [read_fmt(">i", offscreen_io) for _i in range(block_count)]

    values = [
        header_size,
        parameter_section_size,
        init_color_section_size,
        block_size_section_size,

        bitmap_width,
        bitmap_height,
        block_grid_width,
        block_grid_height,

        pixel_packing_attributes,
        u2,
        default_fill_color,
        u3,
        other_init_colors_count,
        u5,
        u6,
        block_count,
        u7,
        blocks_sizes
        ]

    return namedtuple("mipAttributes", columns)(*values)

# Deprecated
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

                color = Color.read(text_attributes, "<H")

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

            color = Color.read(text_attributes, "<I")

            #print(color)
            text_params[TextAttribute(param_id)] = color

        elif param_id == TextAttribute.BBOX:
            bbox = BBox.read(text_attributes, "<I")
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
            # Info doesn't seem valuable, need to see if it can be safely removed
            # Tuple usually defining the text length, either on the first or second index
            unk_pair = (read_fmt("<i", text_attributes), read_fmt("<i", text_attributes))
            #print(unk_pair)
        elif param_id == 44:
            # No idea, consistently 8333, ignore if no valuable info
            value = read_fmt("<i", text_attributes)
            assert value == 8333
            #print(decompositor(value))
        elif param_id == 43:
            # Consistently 50, Ignore in newly made layers if useless
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
            assert value == 1000
            #print(param_id, value)
        elif param_id == 51:
            # 0
            value = read_fmt("<i", text_attributes)
            assert value == 0
            #print(param_id, value)
        elif param_id == 61:
            # 0
            value = read_fmt("<i", text_attributes)
            assert value == 0
            #print(param_id, value)
        elif param_id == 62:
            # 0
            value = read_fmt("<i", text_attributes)
            assert value == 0
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

            print(params)

        else:

            value = text_attributes.read(param_size)
            logger.debug(f"Unknown text param: {param_id} {param_size} {value}")

    return text_params

# Deprecated
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

        vector_bbox = BBox.read(vector_data, ">i")

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
            point_bbox = BBox.read(vector_data, ">i")

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