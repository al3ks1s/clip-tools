from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.utils import read_fmt
from clip_tools.clip.ClipData import Layer

import io
import zlib

from PIL import Image
from collections import namedtuple

# Abstract
class BaseLayer():

    def __init__(self, clip_file, layer_data):
        self.clip_file = clip_file
        self._data = layer_data

        self.mipmaps = []
        self.mask_mipmap = []

    @classmethod
    def new(cls, clip_file, layer_data):
        

        if layer_data.LayerType == 0:

            if layer_data.TextLayerType is not None:
                return TextLayer(clip_file, layer_data)
            if layer_data.VectorNormalType == 0:
                return VectorLayer(clip_file, layer_data)
            elif layer_data.VectorNormalType == 2:
                return StreamLineLayer(clip_file, layer_data)
            elif layer_data.VectorNormalType == 3:
                return FrameLayer(clip_file, layer_data)

            return Folder(clip_file, layer_data)
        elif layer_data.LayerType == 1:
            return PixelLayer(clip_file, layer_data)
        elif layer_data.LayerType == 2:
            return GradientLayer(clip_file, layer_data)
        elif layer_data.LayerType == 256:
            return RootFolder(clip_file, layer_data)
        elif layer_data.LayerType == 4098:
            return CorrectionLayer(clip_file, layer_data)
        else: 
            return BaseLayer(clip_file, layer_data)


    @property
    def LayerName(self):

        return self._data.LayerName

    @LayerName.setter
    def layer_name(self, layer_name):

        self._data.layer_name = layer_name


    def _get_render_mipmap(self):

        if self._data.LayerRenderMipmap == 0:
            return None

        render_mipmap = self.clip_file.sql_database.fetch_values("Mipmap")[self._data.LayerRenderMipmap]

        return render_mipmap

    def _get_mask_render_mipmap(self):

        if self._data.LayerLayerMaskMipmap == 0:
            return None

        mask_render_mipmap = self.clip_file.sql_database.fetch_values("Mipmap")[self._data.LayerLayerMaskMipmap]
    
        return mask_render_mipmap

    def _get_render_offscreen(self, mipmap):
        
        mipmapsinfo = self.clip_file.sql_database.fetch_values("MipmapInfo")[mipmap.BaseMipmapInfo]

        offscreen = self.clip_file.sql_database.fetch_values("Offscreen")[mipmapsinfo.Offscreen]

        return offscreen

    def _get_offscreen_attributes(self):
        
        return self._get_render_offscreen(self._get_render_mipmap()).Attribute

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

    def _decode_chunk_to_pil(self, chunk, offscreen_attributes):

        def channel_to_pil(c_num):

            c_d = {
                3: "RGB",
                4: "RGBA",
                1: "L",
                2: "LA"
            }

            return c_d.get(c_num)

        c_count1 = offscreen_attributes.pixel_packing_attributes[1]
        c_count2 = offscreen_attributes.pixel_packing_attributes[2]
        c_count3 = offscreen_attributes.pixel_packing_attributes[3]

        block_area = offscreen_attributes.pixel_packing_attributes[4]

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

    def topil(self):

        if self._get_render_offscreen(self._get_render_mipmap()).BlockData not in self.clip_file.data_chunks.keys():
            return None

        offscreen = self._get_render_offscreen(self._get_render_mipmap())

        parsed_attribute = self._parse_offscreen_attribute(offscreen.Attribute)

        return self._decode_chunk_to_pil(self.clip_file.data_chunks[offscreen.BlockData], parsed_attribute)

    def save_to_db(self):

        # Need to write a function to write to the db and alter the db without writing all the null junk

        pass

class FolderMixin:
    pass


class Folder(BaseLayer, FolderMixin):

    # Is a folder if LayerFolder column is 1

    pass

class RootFolder(Folder):
    pass

class PixelLayer(BaseLayer):

    @property
    def text(self):
        return self._data.TextLayerString

    @property
    def font(self):
        pass

    @property
    def pix_size(self):
        pass

    @property
    def style(self):
        pass

    @property
    def justify(self):
        pass

    @property
    def direction(self):
        pass

    @property
    def color(self):
        pass


class TextLayer(BaseLayer):

    # A text layer has a LayerType of 0
    # The text layer info is in the TextLayer* columns
    # TextLayerType not None
    # TextLayerString - The text
    # TextLayerAttributes - This is the paragraph data information
    # Etc

    # Text layers have no External chunk

    pass

class CorrectionLayer(BaseLayer):

    # LayerType of 4098
    # Correction metadata in FilterLayerInfo in the DB
    # First int is the layer type, second the length, then all the correction data 

    # Correction BaseLayer has no external data

    pass


class GradientLayer(BaseLayer):

    # Layer type : 2
    # Gradient info in GradationFillInfo column
    # Gradients don't seem to have external data
    # Screentones have special values in LayerRenderInfo column and following along LayerEffectInfo column

    pass


class VectorLayer(BaseLayer):

    # A vector layer has a LayerType of 0
    # 

    # Vector layer has External chunk but not in a bitmap block list format, referenced in the VectorObjectList
    # Seems to be an Adobe Photoshop Color swatch data, probably has other data following
    # Vector Normal Type : 0

    pass


class FrameLayer(VectorLayer):
    
    # Frame Border BaseLayer, Typelayer : 0
    # Special vector folder

    # VectorNormalType: 3

    
    pass

class StreamLineLayer(VectorLayer):
    
    # Defines speedlines layers, LayerType : 0
    # Definition data in StreamLine table, index in the StreamLineIndex column
    # Has vectorized external data, seems to be an Adobe Photoshop Color swatch data
    
    # VectorNormalType: 2

    pass

class Layer_3D(BaseLayer):
    
    # Three dimmension layer has a LayerType of 0
    # Specific data starts at Manager3DOd
    # LayerObject table holds the additional light/camera data for the 3D layers
    # 3D Scene data in Manager3DOd table
    # Has external data, Data starts by the signature "_STUDIO_3D_DATA2"
    
    # Additional metadata in SpecialRulerManager, RulerVanishPoint, RulerPerspective, 

    pass