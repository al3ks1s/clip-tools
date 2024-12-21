import io
import zlib

from PIL import Image
from clip_tools.utils import read_fmt

from collections import namedtuple

def parse_offscreen_attribute(offscreen_attribute):

    columns = ["header_size", "info_section_size", "extra_info_section_size", "u1", "bitmap_width", "bitmap_height", "block_grid_width", "block_grid_height", "pixel_packing_attributes", "u2", "default_fill_color", "u3", "u4", "u5", "u6", "block_count", "u7", "block_sizes"]

    parameter_str = "Parameter".encode('UTF-16-BE')
    initcolor_str = "InitColor".encode('UTF-16-BE')
    blocksize_str = "BlockSize".encode('UTF-16-BE')

    offscreen_io = io.BytesIO(offscreen_attribute)

    header_size = read_fmt(">i", offscreen_io)[0]
    info_section_size = read_fmt(">i", offscreen_io)[0]

    extra_info_section_size = read_fmt(">i", offscreen_io)[0]

    u1 = read_fmt(">i", offscreen_io)[0]

    parameter_size = read_fmt(">i", offscreen_io)[0]
    assert offscreen_io.read(parameter_size * 2) == parameter_str

    bitmap_width = read_fmt(">i", offscreen_io)[0]
    bitmap_height = read_fmt(">i", offscreen_io)[0]
    block_grid_width = read_fmt(">i", offscreen_io)[0]
    block_grid_height = read_fmt(">i", offscreen_io)[0]

    #pixel_packing_names = ["ChannelBytes", "AlphaChannelCount", "BufferChannelCount", "TotalChannelCount", "BlockArea"]
    pixel_packing_attributes = [read_fmt(">i", offscreen_io)[0] for _i in range(16)]

    initcolor_size = read_fmt(">i", offscreen_io)[0]
    assert offscreen_io.read(initcolor_size * 2) == initcolor_str

    u2 = read_fmt(">i", offscreen_io)[0]
    default_fill_color = read_fmt(">i", offscreen_io)[0]
    u3 = read_fmt(">i", offscreen_io)[0]
    u4 = read_fmt(">i", offscreen_io)[0]
    u5 = read_fmt(">i", offscreen_io)[0]
    
    blocksize_size = read_fmt(">i", offscreen_io)[0]
    assert offscreen_io.read(blocksize_size * 2) == blocksize_str

    u6 = read_fmt(">i", offscreen_io)[0]
    block_count = read_fmt(">i", offscreen_io)[0]
    u7 = read_fmt(">i", offscreen_io)[0]

    blocks_sizes = [read_fmt(">i", offscreen_io)[0] for _i in range(block_count)]
    
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

    c_count1 = offscreen_attributes.pixel_packing_attributes[1] # Alpha channel count
    c_count2 = offscreen_attributes.pixel_packing_attributes[2] # Image buffer channel count
    c_count3 = offscreen_attributes.pixel_packing_attributes[3] # Total channel count

    block_area = offscreen_attributes.pixel_packing_attributes[4] # Block Area

    if c_count2 == 0:
        return None

    im = Image.new(channel_to_pil(c_count2), (offscreen_attributes.bitmap_width, offscreen_attributes.bitmap_height), 255*offscreen_attributes.default_fill_color)

    for h in range(offscreen_attributes.block_grid_height):
        for w in range(offscreen_attributes.block_grid_width):
            block = chunk.block_datas[h * offscreen_attributes.block_grid_width + w]
            block_res = b''
            if block.data_present:
                
                pix_bytes = zlib.decompress(block.data)

                if c_count2 == 4:

                    b_alpha = Image.frombuffer(channel_to_pil(1), (256,256), pix_bytes[:block_area])
                    b_im = Image.frombuffer(channel_to_pil(4), (256,256), pix_bytes[block_area:])

                    # Who thought it would be a good idea? why is a RGBA image over 5 chans, but in that order? with the alpha first then a buffer????
                    b,g,r,_ = b_im.split()
                    a, = b_alpha.split()

                    b_bands = (r,g,b,a)

                    #a = [Image.frombuffer("L", (256, 256), pix_bytes[i * block_area:block_area*(i+1)]) for i in range(c_count3)][::-1]

                    block_res = Image.merge("RGBA", b_bands)

                elif c_count2 == 1:
                    
                    b_a = Image.frombuffer(channel_to_pil(1), (256, 256), pix_bytes[:block_area])
                    block_res = Image.frombuffer(channel_to_pil(c_count2), (256, 256), pix_bytes[block_area:])

                im.paste(block_res, (256*w,256*h))

    return im

def parse_text_attribute(text_layer_attribute_array):
        
    text_attributes = io.BytesIO(text_layer_attribute_array)

    return None

