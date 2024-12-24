import io
import zlib

from PIL import Image
from clip_tools.utils import read_fmt, read_csp_unicode_str

from clip_tools.constants import GradientRepeatMode, GradientShape, ScreenToneShape
from clip_tools.data_classes import Position, Color, ColorStop, CurvePoint, EffectTone, EffectEdge, Posterization, EffectTonePosterize, EffectWaterEdge, EffectLine

from collections import namedtuple

import logging


logger = logging.getLogger(__name__)

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

    #print(offscreen_attributes.pixel_packing_attributes)

    bit_depth = offscreen_attributes.pixel_packing_attributes[0] # See CanvasChannelBytes

    alpha_channel_count = offscreen_attributes.pixel_packing_attributes[1] # Alpha channel count
    buffer_channel_count = offscreen_attributes.pixel_packing_attributes[2] # Image buffer channel count
    total_channel_count = offscreen_attributes.pixel_packing_attributes[3] # Total channel count

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
                        
                        color_stop.curve_points.append(point)

            gradient_info["color_stops"] = color_stops

        if param_name == "GradationSettingAdd0001":
            
            section_size = read_fmt(">i", gradient_data)
    
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

    layer_effect_data = io.BytesIO(layer_effect_info)

    effect_data_size = read_fmt(">i", layer_effect_data)
    unk1 = read_fmt(">i", layer_effect_data) # Always '0x02'

    effects = {}

    while layer_effect_data.tell() < effect_data_size:

        param_name = read_csp_unicode_str(">i", layer_effect_data)

        if param_name == "EffectEdge":

            edge_enabled = read_fmt(">i", layer_effect_data)
            thickness = read_fmt(">d", layer_effect_data)

            rgb = [read_fmt(">I", layer_effect_data) >> 24 for _ in range(3)]

            effects[param_name] = EffectEdge(edge_enabled, thickness, rgb)

        if param_name == "EffectTone":

            screentone_enabled = read_fmt(">i", layer_effect_data)

            resolution = read_fmt(">d", layer_effect_data)#?

            screentone_shape = ScreenToneShape(read_fmt(">i", layer_effect_data))# Perhaps the shape of the screentone?
            use_image_brightness = bool(read_fmt(">i", layer_effect_data)) # Use image brightness (default is color)
            unk = read_fmt(">i", layer_effect_data) # Consistently 0x14

            frequency = read_fmt(">d", layer_effect_data) # Between 5.0 and 85.0

            unk = read_fmt(">i", layer_effect_data) # Padding? consistently 0
            unk = read_fmt(">i", layer_effect_data) # Padding? consistently 1

            angle = read_fmt(">i", layer_effect_data) # Between 0 and 359

            noise_size = read_fmt(">i", layer_effect_data)
            noise_factor = read_fmt(">i", layer_effect_data)

            unk = read_fmt(">i", layer_effect_data) # Padding? consistently 0
            unk = read_fmt(">i", layer_effect_data) # Padding? consistently 0

            position = Position(read_fmt(">d", layer_effect_data), read_fmt(">d", layer_effect_data))

            effects[param_name] = EffectTone(screentone_enabled, resolution, screentone_shape, use_image_brightness, frequency, angle, noise_size, noise_factor, position)

        if param_name == "EffectTextureMap":
            
            section_size = read_fmt(">i", layer_effect_data)
            layer_effect_data.read(section_size - 4)

            # Bypass

        if param_name == "EffectApplyOpacity":
            
            section_size = read_fmt(">i", layer_effect_data)
            apply_opacity_enabled = read_fmt(">i", layer_effect_data) # Enable layer reflect opacity
            
            effects[param_name] = apply_opacity_enabled

        if param_name == "EffectToneAreaColor":
            
            section_size = read_fmt(">i", layer_effect_data)
            layer_effect_data.read(section_size - 4)

            # Bypass

        if param_name == "EffectTonePosterize":

            section_size = read_fmt(">i", layer_effect_data)
            posterize_enabled = read_fmt(">i", layer_effect_data)

            posterize_count = read_fmt(">i", layer_effect_data)
            posterizations = []

            for _ in range(posterize_count):
                posterize_input = read_fmt(">i", layer_effect_data) # Posterization input over 0..255
                posterize_output = read_fmt(">i", layer_effect_data) # Postrize output over 1..99

                posterizations.append(Posterization(posterize_input, posterize_output))

            effects[param_name] = EffectTonePosterize(posterize_enabled, posterize_count, posterizations)

        if param_name == "EffectWaterEdge":

            section_size = read_fmt(">i", layer_effect_data)
            water_edge_enabled = read_fmt(">i", layer_effect_data)
            
            edge_range = read_fmt(">d", layer_effect_data) # Between 1.0 and 20.0
            edge_opacity = read_fmt(">d", layer_effect_data) # Between 1 and 100
            edge_darkness = read_fmt(">d", layer_effect_data) # Between 0 and 100
            edge_blurring = read_fmt(">d", layer_effect_data) # Between 0 and 10.0

            effects[param_name] = EffectWaterEdge(water_edge_enabled, edge_range, edge_opacity, edge_darkness, edge_blurring)

        if param_name == "EffectLine":
           
            section_size = read_fmt(">i", layer_effect_data)
            extract_line_enabled = bool(read_fmt(">i", layer_effect_data))

            black_fill_enabled = bool(read_fmt(">i", layer_effect_data))
            black_fill_level = 255 - (read_fmt(">I", layer_effect_data) >> 24)

            posterize_enabled = bool(read_fmt(">i", layer_effect_data))
            unk = read_fmt(">i", layer_effect_data) # Padding? Always 0

            line_width = read_fmt(">i", layer_effect_data)
            unk = read_fmt(">i", layer_effect_data) # Padding? Always 0

            effect_threshold = read_fmt(">i", layer_effect_data)
            unk = read_fmt(">d", layer_effect_data) # Thickness? Something else? Consistently 5.0
            unk = read_fmt(">d", layer_effect_data) # Thickness? Something else? Consistently 5.0
            unk = read_fmt(">i", layer_effect_data) # Consistently 0x04

            directions_map = {0:"Left",1:"Top",2:"Right",3:"Bottom"}
            directions = {}
            
            for _ in range(4):
                direction = read_fmt(">i", layer_effect_data)
                direction_enabled = bool(read_fmt(">i", layer_effect_data))

                directions[directions_map[direction]] = direction_enabled

            posterize_count = read_fmt(">i", layer_effect_data)
            posterizations = []

            for _ in range(posterize_count):
                posterize_input = read_fmt(">i", layer_effect_data) # Posterization input over 0..255
                posterize_output = read_fmt(">i", layer_effect_data) # Postrize output over 1..99

                posterizations.append((posterize_input, posterize_output))
            
            unk = read_fmt(">i", layer_effect_data) # Consistently 0x01
            anti_aliasing = read_fmt(">i", layer_effect_data) # Edge anti aliasing ?  Why is it here
            unk = read_fmt(">i", layer_effect_data) # Consistently 0xc8

            effects[param_name] = EffectLine(extract_line_enabled, black_fill_enabled, black_fill_level, posterize_enabled, line_width, effect_threshold, directions, posterize_count, posterizations, anti_aliasing)

    return effects

def parse_text_attribute(text_layer_attribute_array):
        
    text_attributes = io.BytesIO(text_layer_attribute_array)

    return None
