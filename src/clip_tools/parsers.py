import io
import zlib

from PIL import Image
from clip_tools.utils import read_fmt, read_csp_unicode_str

from clip_tools.constants import GradientRepeatMode, GradientShape

from collections import namedtuple

Position = namedtuple("Position", ["x", "y"])
Color = namedtuple("Color", ["r", "g", "b"])


def parse_offscreen_attribute(offscreen_attribute):

    columns = ["header_size", "info_section_size", "extra_info_section_size", "u1", "bitmap_width", "bitmap_height", "block_grid_width", "block_grid_height", "pixel_packing_attributes", "u2", "default_fill_color", "u3", "u4", "u5", "u6", "block_count", "u7", "block_sizes"]

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

    #pixel_packing_names = ["ChannelBytes", "AlphaChannelCount", "BufferChannelCount", "TotalChannelCount", "BlockArea"]
    pixel_packing_attributes = [read_fmt(">i", offscreen_io) for _i in range(16)]

    initcolor_size = read_fmt(">i", offscreen_io)
    assert offscreen_io.read(initcolor_size * 2) == initcolor_str

    u2 = read_fmt(">i", offscreen_io)
    default_fill_color = read_fmt(">i", offscreen_io)
    u3 = read_fmt(">i", offscreen_io)
    u4 = read_fmt(">i", offscreen_io)
    u5 = read_fmt(">i", offscreen_io)
    
    blocksize_size = read_fmt(">i", offscreen_io)
    assert offscreen_io.read(blocksize_size * 2) == blocksize_str

    u6 = read_fmt(">i", offscreen_io)
    block_count = read_fmt(">i", offscreen_io)
    u7 = read_fmt(">i", offscreen_io)

    blocks_sizes = [read_fmt(">i", offscreen_io) for _i in range(block_count)]
    
    values = [header_size, info_section_size, extra_info_section_size, u1, bitmap_width, bitmap_height, block_grid_width, block_grid_height, pixel_packing_attributes, u2, default_fill_color, u3, u4, u5, u6, block_count, u7, blocks_sizes]
    
    return namedtuple("mipAttributes", columns)(*values)

def decode_chunk_to_pil(chunk, offscreen_attributes):

    def channel_to_pil(c_num):

        c_d = {
            3: "RGB",
            4: "RGBA",
            1: "L",
            2: "LA"
        }

        return c_d.get(c_num)

    alpha_channel_count = offscreen_attributes.pixel_packing_attributes[1] # Alpha channel count
    buffer_channel_count = offscreen_attributes.pixel_packing_attributes[2] # Image buffer channel count
    c_count3 = offscreen_attributes.pixel_packing_attributes[3] # Total channel count

    block_area = offscreen_attributes.pixel_packing_attributes[4] # Block Area

    if buffer_channel_count == 0:
        return None

    im = Image.new(channel_to_pil(buffer_channel_count), (offscreen_attributes.bitmap_width, offscreen_attributes.bitmap_height), 255*offscreen_attributes.default_fill_color)

    for h in range(offscreen_attributes.block_grid_height):
        for w in range(offscreen_attributes.block_grid_width):
            block = chunk.block_datas[h * offscreen_attributes.block_grid_width + w]
            block_res = b''
            if block.data_present:
                
                pix_bytes = zlib.decompress(block.data)

                if buffer_channel_count == 4:

                    b_alpha = Image.frombuffer(channel_to_pil(1), (256,256), pix_bytes[:block_area])
                    b_im = Image.frombuffer(channel_to_pil(4), (256,256), pix_bytes[block_area:])

                    # Who thought it would be a good idea? why is a RGBA image over 5 chans, but in that order? with the alpha first then a buffer????
                    b,g,r,_ = b_im.split()
                    a, = b_alpha.split()

                    b_bands = (r,g,b,a)

                    #a = [Image.frombuffer("L", (256, 256), pix_bytes[i * block_area:block_area*(i+1)]) for i in range(c_count3)][::-1]

                    block_res = Image.merge("RGBA", b_bands)

                elif buffer_channel_count == 1:
                    
                    b_a = Image.frombuffer(channel_to_pil(1), (256, 256), pix_bytes[:block_area])
                    block_res = Image.frombuffer(channel_to_pil(buffer_channel_count), (256, 256), pix_bytes[block_area:])

                im.paste(block_res, (256*w,256*h))

    return im

def parse_gradient_info(gradation_fill_info):

    gradient_data = io.BytesIO(gradation_fill_info)

    gradient_data_size = read_fmt(">i", gradient_data)
    unk1 = read_fmt(">i", gradient_data)

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

                nmt = namedtuple("ColorStop", ["color", "opacity", "is_current_color", "position", "curve_points"])

                r,g,b = (read_fmt(">I", gradient_data) >> 24 for _ in range(3))
                rgb = Color(r,g,b)

                opacity = read_fmt(">I", gradient_data) >> 24
                is_current_color = read_fmt(">i", gradient_data)
                position = read_fmt(">i", gradient_data) * 100 // 32768
                num_curve_points = read_fmt(">i", gradient_data)

                curve_points = []

                color_stops.append(nmt(rgb, opacity, is_current_color, position, curve_points))

            gradient_info["color_stops"] = color_stops

        if param_name == "GradationSettingAdd0001":
            
            section_size = read_fmt(">i", gradient_data)
    
            nmt = namedtuple("FillInfo", ["is_flat", "color"])

            gradient_info["is_flat"] = bool(read_fmt(">i", gradient_data))

            r,g,b = (read_fmt(">I", gradient_data) >> 24 for _ in range(3))
            gradient_info["fill_color"] = Color(r,g,b)

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

def parse_effect_info(layer_effect_info):
    pass

def parse_text_attribute(text_layer_attribute_array):
        
    text_attributes = io.BytesIO(text_layer_attribute_array)

    return None
