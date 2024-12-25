from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.utils import read_fmt
from clip_tools.clip.ClipData import Layer
from clip_tools.constants import BlendMode, LayerType, LayerVisibility, LayerFolder, LayerLock, LayerMasking
from clip_tools.parsers import *
from clip_tools.api.Gradient import Gradient
from clip_tools.api.Effect import LayerEffects
from clip_tools.api.Correction import parse_correction_attributes
from clip_tools.data_classes import Color

import io
import zlib
import logging 

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

logger = logging.getLogger(__name__)

class BaseLayer():

    def __init__(self, clip_file, layer_data):
        self.clip_file = clip_file
        self._data = layer_data

        self._parent = None

        self.mipmaps = self.clip_file.sql_database.get_referenced_items("Mipmap", "LayerId", self._data.MainId)
        self.mipmap_infos = self.clip_file.sql_database.get_referenced_items("MipmapInfo", "LayerId", self._data.MainId)
        self.offscreens = self.clip_file.sql_database.get_referenced_items("Offscreen", "LayerId", self._data.MainId)

        self.effects = None
        self.mask = None
        self.rulers = None

        if self.has_effect or self._data.LayerEffectInfo is not None:
            self.effects = LayerEffects.from_bytes(self._data.LayerEffectInfo)

        if self.has_mask:

            mask_offscreen_attribute = parse_offscreen_attribute(self._get_mask_offscreen_attributes())
            mask_offscreen = self._get_render_offscreen(self._get_mask_render_mipmap())

            self.mask = decode_chunk_to_pil(self.clip_file.data_chunks[mask_offscreen.BlockData], mask_offscreen_attribute)

        if self.has_ruler:
            pass

    @classmethod
    def from_db(cls, clip_file, layer_data):

        if layer_data.LayerType & LayerType.ROOT_FOLDER:
            return RootFolder(clip_file, layer_data)

        if layer_data.LayerType == LayerType.PAPER: # Paper is a combination of flags but can't determine yet what specifically defines a paper layer
            return PaperLayer(clip_file, layer_data)

        if layer_data.LayerType & LayerType.PIXEL:
            return PixelLayer(clip_file, layer_data)

        if layer_data.LayerType & LayerType.CORRECTION:
            return CorrectionLayer(clip_file, layer_data)

        if layer_data.VectorNormalType == 0:
            return VectorLayer(clip_file, layer_data)

        if layer_data.VectorNormalType == 2:
            return StreamLineLayer(clip_file, layer_data)

        if layer_data.VectorNormalType == 3:
            return FrameLayer(clip_file, layer_data)

        if layer_data.TextLayerType is not None:
            return TextLayer(clip_file, layer_data)

        if layer_data.LayerFolder & LayerFolder.FOLDER:
            return Folder(clip_file, layer_data)

        if layer_data.GradationFillInfo is not None:
            return GradientLayer(clip_file, layer_data)

        logger.warning("Couldn't find proper layer type for %s. LayerType is %d" % (layer_data.LayerName, layer_data.LayerType))
        return BaseLayer(clip_file, layer_data)


    @property
    def has_ruler(self):
        return self._data.RulerRange is not None

    @property
    def has_pixels(self):
        return self._data.LayerType & LayerType.PIXEL

    @property
    def has_mask(self): # Masks for FramesBorders work differently, the vector line defines the mask and the ruler
        return self._data.LayerType & LayerType.MASKED # TODO: Modify this to include FRAMES, need to modify the mask initialization for frames, probably in subclass

    @property
    def has_effect(self):
        return self._data.LayerEffectAttached == 1

    @property
    def mask_type(self):
        return LayerMasking(self._data.LayerMasking)

    @property
    def visible(self):
        return self._data.LayerVisibility & LayerVisibility.VISIBLE

    @property
    def LayerName(self):
        return self._data.LayerName

    @LayerName.setter
    def LayerName(self, layer_name):
        self._data.layer_name = layer_name

    @property
    def opacity(self):
        return int(self._data.LayerOpacity / 256 * 100)

    @opacity.setter
    def opacity(self, new_opacity):
        self._data.LayerOpacity = int((new_opacity / 100) * 256)

    @property
    def blend_mode(self):
        return self._data.LayerComposite # See constants.BlendMode

    @blend_mode.setter
    def blend_mode(self, new_mode):
        self._data.LayerComposite = new_mode # From constants.BlendMode

    @property
    def clipping(self):
        return bool(self._data.LayerClip)

    @clipping.setter
    def clipping(self, clip):
        self._data.LayerClip = bool(clip)

    @property
    def reference(self):
        return bool(self._data.ReferLayer)

    @reference.setter
    def reference(self, refer):
        self._data.ReferLayer = bool(refer)


    @property
    def lock(self):
        return LayerLock(self._data.LayerLock)

    @lock.setter
    def lock(self, lock_flag):
        self._data.LayerLock = lock_flag

    def unlock(self):
        self._data.LayerLock = 0

    def render_mask(self):
        
        print()
        print(self.LayerName)

        if not self.has_mask:
            return None

        offscreen = self._get_render_offscreen(self._get_mask_render_mipmap())

        parsed_attribute = parse_offscreen_attribute(offscreen.Attribute)

        print(self.clip_file.data_chunks[offscreen.BlockData].block_datas)

        return decode_chunk_to_pil(self.clip_file.data_chunks[offscreen.BlockData], parsed_attribute)

    # Metadata functions
    def _get_render_mipmap(self):

        if self._data.LayerRenderMipmap == 0:
            return None

        render_mipmap = self.mipmaps[self._data.LayerRenderMipmap]

        return render_mipmap

    def _get_mask_render_mipmap(self):

        if self._data.LayerLayerMaskMipmap == 0:
            return None

        mask_render_mipmap = self.mipmaps[self._data.LayerLayerMaskMipmap]
    
        return mask_render_mipmap

    def _get_render_offscreen(self, mipmap):
      
        mipmapsinfo = self.mipmap_infos[mipmap.BaseMipmapInfo]
        offscreen = self.offscreens[mipmapsinfo.Offscreen]

        return offscreen

    def _get_offscreen_attributes(self):
        return self._get_render_offscreen(self._get_render_mipmap()).Attribute

    def _get_mask_offscreen_attributes(self):
        return self._get_render_offscreen(self._get_mask_render_mipmap()).Attribute

    # Structure edition
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

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.LayerName)

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
            if name in layer.LayerName:
                yield layer

class Folder(FolderMixin, BaseLayer):

    # Is a folder if LayerFolder column is 1

    def __init__(self, clip_file, layer_data):

        self._layers = []
        BaseLayer.__init__(self, clip_file, layer_data)

    @property
    def is_open(self):
        return not self._data.LayerFolder & LayerFolder.CLOSED

class RootFolder(Folder):
    pass

class PixelLayer(BaseLayer):

    def topil(self):

        if self._get_render_offscreen(self._get_render_mipmap()).BlockData not in self.clip_file.data_chunks.keys():
            return None

        offscreen = self._get_render_offscreen(self._get_render_mipmap())

        parsed_attribute = parse_offscreen_attribute(offscreen.Attribute)

        #print(parsed_attribute)
        return decode_chunk_to_pil(self.clip_file.data_chunks[offscreen.BlockData], parsed_attribute)

class PaperLayer(BaseLayer):

    # Paper color stored in the three following columns : DrawColorMainRed, DrawColorMainGreen, DrawColorMainBlue over the full scale of an uint
    # eg: 13369925889263, 1456559825, 3407858463 defines : (79, 86, 202) bitshift of 24 left or right

    # Special RenderType: 20

    # TODO To move to Base Layer
    @property
    def color(self):
        return Color(self._data.DrawColorMainRed >> 24,
                self._data.DrawColorMainGreen >> 24,
                self._data.DrawColorMainBlue >> 24)

    @color.setter
    def color(self, new_color: Color):
        pass

    @classmethod
    def new(self, color):
        
        # Create new Layer() Object, set the colors, add it to the begining of the root folder
        
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


class CorrectionLayer(BaseLayer):

    # LayerType of 4096 + Mask by Default
    # Correction metadata in FilterLayerInfo column in the DB
    # First int is the layer type, second the length, then all the correction data, see CorrectionType constant for list
    # SpecialRenderType: 13

    # Correction Layer has no external data

    def __init__(self, clip_file, layer_data):

        BaseLayer.__init__(self, clip_file, layer_data)
        self.correction = parse_correction_attributes(self._data.FilterLayerInfo)


class GradientLayer(BaseLayer):

    # Layer type : 2 (No pixel, only mask)
    # Gradient info in GradationFillInfo column
    # Gradients don't seem to have external data
    # Screentones have special values in LayerRenderInfo column and following along LayerEffectInfo column

    def __init__(self, clip_file, layer_data):

        BaseLayer.__init__(self, clip_file, layer_data)
        #print(self.LayerName)
        self.gradient = Gradient.from_bytes(self._data.GradationFillInfo)
        #print(self.gradient)
        #print("----------------------")
        #print()


    @property
    def shape(self):
        return self.gradient.shape

    @property
    def repeat_mode(self):
        return self.gradient.repeat_mode
    
    @property
    def anti_aliasing(self):
        return self.gradient.anti_aliasing

    @property
    def start(self):
        return self.gradient.start
    
    @property
    def end(self):
        return self.gradient.end
            

class VectorLayer(BaseLayer):

    # A vector layer has a LayerType of 0

    # Vector layer has External chunk but not in a bitmap block list format, referenced in the VectorObjectList
    # Seems to be an Adobe Photoshop Color swatch data, probably has other data following
    # Vector Normal Type : 0
    # External data index in VectorNormalStrokeIndex

    pass


class FrameLayer(Folder, VectorLayer):
    
    # Frame Border BaseLayer, Typelayer : 0
    # Special vector folder

    # VectorNormalType: 3
    # ExternalData Referenced in VectorNormalBalloonIndex

    # Special RenderType: 14

    def __init__(self, clip_file, layer_data):

        self._layers = []
        VectorLayer.__init__(self, clip_file, layer_data)

class StreamLineLayer(VectorLayer):
    
    # Defines speedlines layers, LayerType : 0
    # Definition data in StreamLine table, index in the StreamLineIndex column
    # Has vectorized external data, seems to be an Adobe Photoshop Color swatch data
    
    # VectorNormalType: 2
    # External data index in VectorNormalStrokeIndex

    pass

class Layer_3D(BaseLayer):
    
    # Three dimmension layer has a LayerType of 0
    # Specific data starts at Manager3DOd
    # LayerObject table holds the additional light/camera data for the 3D layers
    # 3D Scene data in Manager3DOd table
    # Has external data, Data starts by the signature "_STUDIO_3D_DATA2"
    
    # Additional metadata in SpecialRulerManager, RulerVanishPoint, RulerPerspective, 

    pass