from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.utils import read_fmt
import os
import io
from collections import namedtuple
from PIL import Image
import zlib

workdir = '../../ClipDissect/Page'

#filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["page0001.clip"]

for f in filelist:
    with open(os.path.join(workdir, f), "rb") as fp:
        clipFile = ClipStudioFile.read(fp)

        layers = clipFile.sql_database.fetch_values("Layer")
        mipmaps = clipFile.sql_database.fetch_values("Mipmap")
        mipmapsinfos = clipFile.sql_database.fetch_values("MipmapInfo")
        offscreen = clipFile.sql_database.fetch_values("Offscreen")

        def parse_mipmap_attribute(offscreen_attribute):

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

        def decode_chunk_to_pil(chunk, mip_attributes):

            def channel_to_pil(c_num):

                c_d = {
                    3: "RGB",
                    4: "RGBA",
                    1: "L",
                    2: "LA"
                }

                return c_d.get(c_num)

            print(mip_attributes.pixel_packing_attributes)

            c_count1 = mip_attributes.pixel_packing_attributes[1]
            c_count2 = mip_attributes.pixel_packing_attributes[2]
            c_count3 = mip_attributes.pixel_packing_attributes[3]

            block_area = mip_attributes.pixel_packing_attributes[4]

            im = Image.new(channel_to_pil(c_count2), (mip_attributes.bitmap_width, mip_attributes.bitmap_height), 255*mip_attributes.default_fill_color)

            for h in range(mip_attributes.block_grid_height):
                for w in range(mip_attributes.block_grid_width):
                    block = chunk.block_datas[h * mip_attributes.block_grid_width + w]
                    block_res = b''
                    if block.data_present:

                        if c_count2 == 4:
                            pix_bytes = zlib.decompress(block.data)

                            b_alpha = Image.frombuffer(channel_to_pil(1), (256,256), pix_bytes[:block_area])
                            b_im = Image.frombuffer(channel_to_pil(4), (256,256), pix_bytes[block_area:])

                            # I have no idea whats the point in all that
                            b,g,r,_ = b_im.split()
                            a, = b_alpha.split()

                            b_bands = (r,g,b,a)

                            #a = [Image.frombuffer("L", (256, 256), pix_bytes[i * block_area:block_area*(i+1)]) for i in range(c_count3)][::-1]

                            block_res = Image.merge("RGBA", b_bands)

                        elif c_count2 == 1:

                            pix_bytes = zlib.decompress(block.data)
                            block_res = Image.frombuffer(channel_to_pil(c_count2), (256, 256), pix_bytes[block_area:])

                        im.paste(block_res, (256*w,256*h))


            return im

        print(clipFile.data_chunks)

        for layer in layers:

            if layers[layer].LayerType==1:

                mipmap = layers[layer].LayerRenderMipmap
                mipbase = mipmaps[mipmap].BaseMipmapInfo
                relevant_offscreen = offscreen[mipmapsinfos[mipbase].Offscreen]

                chunk = clipFile.data_chunks[relevant_offscreen.BlockData]
                mip_attr = parse_mipmap_attribute(relevant_offscreen.Attribute)
                decode_chunk_to_pil(chunk, mip_attr)
