from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.utils import read_fmt

import io
import zlib

from PIL import Image
from collections import namedtuple

# Abstract
class Layer:

    def __init__(self, clip_file, layer_info):
        self.clip_file = clip_file
        self.layer_info = layer_info

    @classmethod
    def new(cls, clip_file, layer_info):
        
        if layer_info.LayerType == 0:

            if layer_info.TextLayerType is not None:
                return TextLayer(clip_file, layer_info)
            if layer_info.VectorNormalType == 0:
                return VectorLayer(clip_file, layer_info)
            elif layer_info.VectorNormalType == 2:
                return StreamLineLayer(clip_file, layer_info)
            elif layer_info.VectorNormalType == 3:
                return FrameLayer(clip_file, layer_info)

            return Folder(clip_file, layer_info)
        elif layer_info.LayerType == 1:
            return PixelLayer(clip_file, layer_info)
        elif layer_info.LayerType == 2:
            return GradientLayer(clip_file, layer_info)
        elif layer_info.LayerType == 256:
            return Layer(clip_file, layer_info)
        elif layer_info.LayerType == 4098:
            return CorrectionLayer(clip_file, layer_info)
        else: 
            return Layer(clip_file, layer_info)


    @property
    def layer_name(self):

        return self.layer_info.layer_name

    @layer_name.setter
    def layer_name(self, layer_name):

        self.layer_info.layer_name = layer_name


    def get_render_mipmap(self):

        if self.layer_info.LayerRenderMipmap == 0:
            return None

        render_mipmap = self.clip_file.sql_database.fetch_values("Mipmap")[self.layer_info.LayerRenderMipmap]

        return render_mipmap

    def get_mask_render_mipmap(self):

        if self.layer_info.LayerLayerMaskMipmap == 0:
            return None

        mask_render_mipmap = self.clip_file.sql_database.fetch_values("Mipmap")[self.layer_info.LayerLayerMaskMipmap]
    
        return mask_render_mipmap

    def get_render_offscreen(self, mipmap):
        
        mipmapsinfo = self.clip_file.sql_database.fetch_values("MipmapInfo")[mipmap.BaseMipmapInfo]

        offscreen = self.clip_file.sql_database.fetch_values("Offscreen")[mipmapsinfo.Offscreen]

        return offscreen

    def _get_mip_attributes(self):
        
        mipmaps = self.clip_file.sql_database.fetch_values("Mipmap")
        mipmapsinfos = self.clip_file.sql_database.fetch_values("MipmapInfo")
        offscreen = self.clip_file.sql_database.fetch_values("Offscreen")

        mipmap = self.layer_info.LayerRenderMipmap
        mipbase = mipmaps[mipmap].BaseMipmapInfo
        relevant_offscreen = offscreen[mipmapsinfos[mipbase].Offscreen]

        chunk = self.clip_file.data_chunks[relevant_offscreen.BlockData]
        mip_attr = self._parse_offscreen_attribute(relevant_offscreen.Attribute)
        return chunk, mip_attr

    def _parse_offscreen_attribute(self, offscreen_attribute):

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

    def _decode_chunk_to_pil(self, chunk, mip_attributes):

        def channel_to_pil(c_num):

            c_d = {
                3: "RGB",
                4: "RGBA",
                1: "L",
                2: "LA"
            }

            return c_d.get(c_num)

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

class FolderMixin:
    pass


class Folder(Layer, FolderMixin):

    # Is a folder if LayerFolder column is 1

    pass



class PixelLayer(Layer):

    def topil(self):
        pass

    def frompil(self):
        pass


class TextLayer(Layer):

    # A text layer has a LayerType of 0
    # The text layer info is in the TextLayer* columns
    # TextLayerType not None
    # TextLayerString - The text
    # TextLayerAttributes - This is the paragraph data information
    # Etc

    # Text layers have no External chunk

    pass

class VectorLayer(Layer):

    # A vector layer has a LayerType of 0
    # 

    # Vector layer has External chunk but not in a bitmap block list format, referenced in the VectorObjectList
    # Seems to be an Adobe Photoshop Color swatch data, probably has other data following
    # Vector Normal Type : 0

    pass

class CorrectionLayer(Layer):

    # LayerType of 4098
    # Correction metadata in FilterLayerInfo in the DB
    # First int is the layer type, second the length, then all the correction data 

    # Correction Layer has no external data

    pass

class GradientLayer(Layer):

    # Layer type : 2
    # Gradient info in GradationFillInfo column
    # Gradients don't seem to have external data
    # Screentones have special values in LayerRenderInfo column and following along LayerEffectInfo column

    pass

class FrameLayer(VectorLayer):
    
    # Frame Border Layer, Typelayer : 0
    # Special vector folder

    # VectorNormalType: 3

    
    pass

class StreamLineLayer(VectorLayer):
    
    # Defines speedlines layers, LayerType : 0
    # Definition data in StreamLine table, index in the StreamLineIndex column
    # Has vectorized external data, seems to be an Adobe Photoshop Color swatch data
    
    # VectorNormalType: 2

    pass

class TDLayer(Layer):
    
    # Three dimmension layer has a LayerType of 0
    # Specific data starts at Manager3DOd
    # LayerObject table holds the additional light/camera data for the 3D layers
    # 3D Scene data in Manager3DOd table
    # Has external data, Data starts by the signature "_STUDIO_3D_DATA2"
    
    # Additional metadata in SpecialRulerManager, RulerVanishPoint, RulerPerspective, 

    pass