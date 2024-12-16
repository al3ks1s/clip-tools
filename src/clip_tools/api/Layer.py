from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.utils import read_fmt
from clip_tools.clip.ClipData import Layer

import io
import zlib

from typing import (
    Any,
    Callable,
    Iterable,
    Iterator,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from PIL import Image
from collections import namedtuple



# Abstract
class BaseLayer():

    def __init__(self, clip_file, layer_data):
        self.clip_file = clip_file
        self._data = layer_data

        self._parent = None

        self.mipmaps = []
        self.mask_mipmap = []

    @classmethod
    def from_db(cls, clip_file, layer_data):
        # Need to make a better one
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
        elif layer_data.LayerType == 1584:
            return PaperLayer(clip_file, layer_data)
        else:
            return BaseLayer(clip_file, layer_data)

    @property
    def LayerName(self):
        return self._data.LayerName

    @LayerName.setter
    def layer_name(self, layer_name):
        self._data.layer_name = layer_name

    @property
    def lock(self):
        return self._data.LayerLock

    @lock.setter
    def lock(self, lock_mask):
        self._data.LayerLock = lock_mask

    @property
    def opacity(self):
        return int(self._data.LayerOpacity / 256) * 100

    @opacity.setter
    def opacity(self, new_opacity):
        self._data.LayerOpacity = int(new_opacity / 100) * 256

    @property
    def blend_mode(self):
        return self._data.LayerComposite # See constants.LayerComposite

    @blend_mode.setter
    def blend_mode(self, new_mode):
        self._data.LayerComposite = new_mode # From constants.LayerComposite

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

    @property
    def firstChildIndex(self):
        return self._data.LayerFirstChildIndex

    @property
    def nextLayerIndex(self):
        return self._data.LayerNextIndex    

    def delete_layer(self):
        """
        Deletes the layer and all its child layers if the layer is a group from its parent (group or psdimage).
        """

        if self._parent is not None and isinstance(self._parent, FolderMixin):
            if self in self._parent:
                self._parent.remove(self)
            self._parent._update_psd_record()
        else:
            pass

        return self

    def move_to_group(self, group: "GroupMixin"):
        """
        Moves the layer to the given group, updates the tree metadata as needed.

        :param group: The group the current layer will be moved into.
        """

        assert isinstance(group, FolderMixin)
        assert group is not self

        if isinstance(self, FolderMixin):
            assert (
                group not in self.descendants()
            ), "Cannot move group {} into its descendant {}".format(self, group)

        if self._parent is not None and isinstance(self._parent, FolderMixin):
            if self in self._parent:
                self._parent.remove(self)

        group.append(self)

        return self


class FolderMixin():
    _layers: list[BaseLayer]

    def __len__(self) -> int:
        return self._layers.__len__()

    def __iter__(self):
        return self._layers.__iter__()

    def __getitem__(self, key) -> BaseLayer:
        return self._layers.__getitem__(key)

    def __setitem__(self, key, value) -> None:
        self._check_valid_layers(value)
        self._layers.__setitem__(key, value)
        self._update_metadata()        

    def __delitem__(self, key) -> None:
        self._layers.__delitem__(key)
        self._update_metadata()

    def append(self, layer: BaseLayer) -> None:
        """
        Add a layer to the end (top) of the group

        :param layer: The layer to add
        """
        self._check_valid_layers(layer)
        self.extend([layer])

    def extend(self, layers) -> None:
        """
        Add a list of layers to the end (top) of the group

        :param layers: The layers to add
        """

        self._check_valid_layers(layers)
        self._layers.extend(layers)
        self._update_metadata()

    def insert(self, index: int, layer: BaseLayer) -> None:
        """
        Insert the given layer at the specified index.

        :param index:
        :param layer:
        """

        self._check_valid_layers(layer)
        self._layers.insert(index, layer)
        self._update_metadata()
        
    def remove(self, layer: BaseLayer):
        """
        Removes the specified layer from the group

        :param layer:
        """

        self._layers.remove(layer)
        self._update_metadata()
        return self

    def pop(self, index: int = -1) -> BaseLayer:
        """
        Removes the specified layer from the list and returns it.

        :param index:
        """

        popLayer = self._layers.pop(index)
        self._update_metadata()
        return popLayer

    def clear(self) -> None:
        """
        Clears the group.
        """

        self._layers.clear()
        self._update_metadata()

    def index(self, layer: BaseLayer) -> int:
        """
        Returns the index of the specified layer in the group.

        :param layer:
        """

        return self._layers.index(layer)

    def count(self, layer: BaseLayer) -> int:
        """
        Counts the number of occurences of a layer in the group.

        :param layer:
        """

        return self._layers.count(layer)
    
    def _check_valid_layers(self, layers: BaseLayer | Iterable[BaseLayer]) -> None:

        return

        assert layers is not self, "Cannot add the group {} to itself.".format(self)

        if isinstance(layers, BaseLayer):
            layers = [layers]

        for layer in layers:
            assert isinstance(layer, BaseLayer)
            if isinstance(layer, FolderMixin):
                assert (
                    self not in list(layer.descendants())
                ), "This operation would create a reference loop within the group between {} and {}.".format(
                    self, layer
                )

    def _update_metadata(self):
        
        for layer in self._layers:
            layer._parent = self

    def descendants(self) -> Iterator[BaseLayer]:
        """
        Return a generator to iterate over all descendant layers.

        Example::

            # Iterate over all layers
            for layer in psd.descendants():
                print(layer)

            # Iterate over all layers in reverse order
            for layer in reversed(list(psd.descendants())):
                print(layer)

        """
        for layer in self:
            yield layer
            if isinstance(layer, FolderMixin):
                for child in layer.descendants():
                    yield child

    def find(self, name: str) -> BaseLayer | None:
        """
        Returns the first layer found for the given layer name

        :param name:
        """

        for layer in self.findall(name):
            return layer
        return None

    def findall(self, name: str) -> Iterator[BaseLayer]:
        """
        Return a generator to iterate over all layers with the given name.

        :param name:
        """

        for layer in self.descendants():
            if layer.name == name:
                yield layer

class Folder(FolderMixin, BaseLayer):

    # Is a folder if LayerFolder column is 1

    def __init__(self, clip_file, layer_data):

        self._layers = []

        BaseLayer.__init__(self, clip_file, layer_data)


class RootFolder(Folder):
    pass

class PixelLayer(BaseLayer):

    def topil(self):

        if self._get_render_offscreen(self._get_render_mipmap()).BlockData not in self.clip_file.data_chunks.keys():
            return None

        offscreen = self._get_render_offscreen(self._get_render_mipmap())

        parsed_attribute = self._parse_offscreen_attribute(offscreen.Attribute)

        return self._decode_chunk_to_pil(self.clip_file.data_chunks[offscreen.BlockData], parsed_attribute)


class PaperLayer(BaseLayer):
    pass

class TextLayer(BaseLayer):

    # A text layer has a LayerType of 0
    # The text layer info is in the TextLayer* columns
    # TextLayerType not None
    # TextLayerString - The text
    # TextLayerAttributes - This is the paragraph data information
    # Etc

    # Text layers have no External chunk

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

    def _parse_text_attribute(self):
        
        return None

class CorrectionLayer(BaseLayer):

    # LayerType of 4098
    # Correction metadata in FilterLayerInfo in the DB
    # First int is the layer type, second the length, then all the correction data 

    # Correction Layer has no external data

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


class FrameLayer(Folder, VectorLayer):
    
    # Frame Border BaseLayer, Typelayer : 0
    # Special vector folder

    # VectorNormalType: 3

    def __init__(self, clip_file, layer_data):

        self._layers = []

        VectorLayer.__init__(self, clip_file, layer_data)
    

class StreamLineLayer(Folder, VectorLayer):
    
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