from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.utils import read_fmt, decompositor
from clip_tools.clip.ClipData import Layer, Mipmap, MipmapInfo, Offscreen
from clip_tools.constants import BlendMode, LayerType, LayerVisibility, LayerFolder, LayerLock, LayerMasking, VectorNormalType, DrawToMaskMipmapType, DrawToMaskOffscreenType, DrawToRenderMipmapType, DrawToRenderOffscreenType, OffsetAndExpandType, EffectRenderType, SpecialRenderType, MaterialContentType, RenderThumbnailType, ColorMode, OffsetAndExpandType
from clip_tools.parsers import *
from clip_tools.api.Gradient import Gradient
from clip_tools.api.Effect import LayerEffects
from clip_tools.api.Correction import parse_correction_attributes
from clip_tools.data_classes import Color, OffscreenAttribute
from clip_tools.api.Ruler import Rulers
from clip_tools.api.Mask import Mask
from clip_tools.api.Vector import Vector, VectorPoint, VectorList
from clip_tools.api.Text import Text
from clip_tools.api import Correction
import binascii
import uuid
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
            mask_offscreen = self._get_render_offscreen(self._get_mask_render_mipmap())
            self.mask = Mask(self, self.mask_type, mask_offscreen)

        if self.has_ruler:
            self.rulers = Rulers.init_rulers(self)

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

        if layer_data.VectorNormalType == VectorNormalType.STROKE:
            return VectorLayer(clip_file, layer_data)

        if layer_data.VectorNormalType == VectorNormalType.BALLOON:
            return BalloonLayer(clip_file, layer_data)

        if layer_data.VectorNormalType == VectorNormalType.SPEEDLINLES:
            return StreamLineLayer(clip_file, layer_data)

        if layer_data.VectorNormalType == VectorNormalType.FRAMEBORDER:
            return FrameLayer(clip_file, layer_data)

        if layer_data.TextLayerType is not None:
            return TextLayer(clip_file, layer_data)

        if layer_data.AnimationFolder:
            return AnimationFolder(clip_file, layer_data)

        if layer_data.LayerFolder & LayerFolder.FOLDER:
            return Folder(clip_file, layer_data)

        if layer_data.GradationFillInfo is not None:
            return GradientLayer(clip_file, layer_data)

        if layer_data.ResizableOriginalMipmap is not None:
            return ImageLayer(clip_file, layer_data)

        logger.warning("Couldn't find proper layer type for %s. LayerType is %d" % (layer_data.LayerName, layer_data.LayerType))
        return BaseLayer(clip_file, layer_data)

    @classmethod
    def _new(cls, clip_file, layer_name = "Layer"):

        canvas = clip_file.sql_database.get_table("Canvas")[1]

        uuid_str = str(uuid.uuid4())

        uuid_str = uuid_str[-2:] + uuid_str[:-2]

        # Big default init
        layer = Layer.new(
            clip_file.sql_database,
            CanvasId = 1,
            LayerName = layer_name,
            LayerType = 0,
            LayerLock = 0,
            LayerClip = 0,
            LayerMasking = 0,
            LayerOffsetX = 0,
            LayerOffsetY = 0,
            LayerRenderOffscrOffsetX = 0,
            LayerRenderOffscrOffsetY = 0,
            LayerMaskOffsetX = 0,
            LayerMaskOffsetY = 0,
            LayerMaskOffscrOffsetX = 0,
            LayerMaskOffscrOffsetY = 0,
            LayerOpacity = 256,
            LayerComposite = BlendMode.NORMAL,
            LayerUsePaletteColor = 0,
            LayerNoticeablePaletteColor = 0,
            LayerPaletteRed = 0,
            LayerPaletteGreen = 0,
            LayerPaletteBlue = 0,
            LayerFolder = 0,
            LayerVisibility = 1,
            LayerSelect = 0,
            LayerNextIndex = 0,
            LayerFirstChildIndex = 0,
            LayerUuid = uuid_str,
            LayerRenderMipmap = 0,
            LayerLayerMaskMipmap = 0,
            LayerRenderThumbnail = 0,
            LayerLayerMaskThumbnail = 0
        )

        scales = [100.0, 50.0, 25.0, 12.5, 6.25]

        offscreens = []
        mipmap_infos = []

        for scale in scales:

            offscreen = Offscreen.new(
                clip_file.sql_database,
                CanvasId = 1,
                LayerId = layer.MainId,
                Attribute = OffscreenAttribute.new(
                    int((canvas.CanvasWidth * scale) // 100),
                    int((canvas.CanvasHeight * scale) // 100),
                    ColorMode(canvas.CanvasDefaultColorTypeIndex)
                ).tobytes(),
                BlockData = DataChunk.new_id()
            )

            offscreens.append(offscreen)

            mipinfo = MipmapInfo.new(
                clip_file.sql_database,
                CanvasId = 1,
                LayerId = layer.MainId,
                ThisScale = scale,
                Offscreen = offscreen.MainId,
                NextIndex = 0
            )

            mipmap_infos.append(mipinfo)

        mipmap = Mipmap.new(
            clip_file.sql_database,
            CanvasId = 1,
            LayerId = layer.MainId,
            MipmapCount = 5,
            BaseMipmapInfo = mipmap_infos[0].MainId
        )

        for i in range(len(mipmap_infos) - 1):
            mipmap_infos[i].NextIndex = mipmap_infos[i + 1].MainId
            mipmap_infos[i].save()

        layer.LayerRenderMipmap = mipmap.MainId
        layer.save()

        return layer

    def save(self):
        self._data.save()

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
    def layer_name(self):
        return self._data.LayerName

    @layer_name.setter
    def layer_name(self, layer_name):
        self._data.layer_name = layer_name

    @property
    def opacity(self):
        return int(self._data.LayerOpacity / 256 * 100)

    @opacity.setter
    def opacity(self, new_opacity):
        self._data.LayerOpacity = int((new_opacity / 100) * 256)

    @property
    def blend_mode(self):
        return BlendMode(self._data.LayerComposite) # See constants.BlendMode

    @blend_mode.setter
    def blend_mode(self, new_mode):
        self._data.LayerComposite = new_mode # From constants.BlendMode

    @property
    def clipping(self):
        return bool(self._data.LayerClip)

    @clipping.setter
    def clipping(self, clip):
        self._data.LayerClip = int(bool(clip))

    @property
    def reference(self):
        return bool(self._data.ReferLayer)

    @reference.setter
    def reference(self, refer):
        self._data.ReferLayer = int(bool(refer))

    @property
    def draft(self):
        return bool(self._data.OutputAttribute)

    @draft.setter
    def draft(self, new_val):
        self._data.OutputAttribute = int(bool(new_val))

    @property
    def lock(self):
        return LayerLock(self._data.LayerLock)

    @lock.setter
    def lock(self, lock_flag):
        self._data.LayerLock = lock_flag

    def unlock(self):
        self._data.LayerLock = 0

    @property
    def palette(self):
        if self._data.LayerUsePaletteColor != 1:
            return None

        return Color(self._data.LayerPaletteRed >> 24,
                self._data.LayerPaletteGreen >> 24,
                self._data.LayerPaletteBlue >> 24)

    @palette.setter
    def palette(self, new_palette: Color):

        self._data.LayerUsePaletteColor = 1

        self._data.LayerPaletteRed = new_palette.r << 24
        self._data.LayerPaletteGreen = new_palette.g << 24
        self._data.LayerPaletteBlue = new_palette.b << 24

    def toggle_palette(self):
        self._data.LayerUsePaletteColor = self._data.LayerUsePaletteColor ^ 1

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
            self._parent._update_metadata()
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
        return "%s(%r)" % (self.__class__.__name__, self.layer_name)

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

        if len(self) != 0:
            self._data.LayerFirstChildIndex = self[0]._data.MainId

        for i in range(len(self) - 1):
            self[i]._data.LayerNextIndex = self[i + 1]._data.MainId

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
            if name in layer.layer_name:
                yield layer

class Folder(FolderMixin, BaseLayer):

    # Is a folder if LayerFolder column is 1

    def __init__(self, clip_file, layer_data):

        self._layers = []
        BaseLayer.__init__(self, clip_file, layer_data)

    @property
    def is_open(self):
        return not self._data.LayerFolder & LayerFolder.CLOSED

    @classmethod
    def new(cls, clip_file, layer_name = "Folder"):

        layer_data = BaseLayer._new(clip_file, layer_name)

        layer_data.LayerMasking = LayerMasking.FOLDER
        layer_data.LayerFolder = 1

        layer_data.save()

        return cls(clip_file, layer_data)

# Do no use that class for anything else than the first folder of a canvas
class RootFolder(Folder):

    @classmethod
    def new(cls, clip_file, layer_name = "Folder"):

        layer_data = BaseLayer._new(clip_file, layer_name)

        layer_data.LayerType = LayerType.ROOT_FOLDER
        layer_data.LayerMasking = LayerMasking.BLOCK_APPLY_MASK
        layer_data.LayerFolder = 1

        layer_data.save()

        return cls(clip_file, layer_data)

class PixelLayer(BaseLayer):

    @classmethod
    def new(cls, clip_file, name = "Layer"):

        canvas = clip_file.sql_database.get_table("Canvas")[1]

        pil_im = Image.new(
            ColorMode.pil_mode(canvas.CanvasDefaultColorTypeIndex),
            (int(canvas.CanvasWidth), int(canvas.CanvasHeight)),
        )

        return PixelLayer.frompil(clip_file, pil_im, name)

    def topil(self):

        if self._get_render_offscreen(self._get_render_mipmap()).BlockData not in self.clip_file.data_chunks.keys():
            return None

        offscreen = self._get_render_offscreen(self._get_render_mipmap())
        parsed_attribute = OffscreenAttribute.read(io.BytesIO(offscreen.Attribute))

        return decode_chunk_to_pil(
            self.clip_file.data_chunks[offscreen.BlockData],
            parsed_attribute
        )

    @classmethod
    def frompil(cls, clip_file, pil_im, name = "Pixel"):

        layer_data = BaseLayer._new(clip_file, name)
        layer_data.LayerType = LayerType.PIXEL
        layer_data.LayerColorTypeIndex = ColorMode.from_pil(pil_im.mode)
        layer_data.LayerColorTypeBlackChecked = 1
        layer_data.LayerColorTypeWhiteChecked = 1

        chunk, offscreen_attribute = encode_pil_to_chunk(pil_im)

        mipmap = clip_file.sql_database.get_referenced_items("Mipmap", "LayerId", layer_data.MainId)
        mipinfos = clip_file.sql_database.get_referenced_items("MipmapInfo", "LayerId", layer_data.MainId)
        offscreens = clip_file.sql_database.get_referenced_items("Offscreen", "LayerId", layer_data.MainId)

        main_offscreen = offscreens[mipinfos[mipmap[layer_data.LayerRenderMipmap].BaseMipmapInfo].Offscreen]

        main_offscreen.Attribute = offscreen_attribute.tobytes()
        main_offscreen.BlockData = chunk.external_chunk_id

        main_offscreen.save()

        clip_file.data_chunks[chunk.external_chunk_id] = chunk

        return cls(clip_file, layer_data)


class ImageLayer(BaseLayer):

    def topil(self):

        if self._get_render_offscreen(self.mipmaps[self._data.ResizableOriginalMipmap]).BlockData not in self.clip_file.data_chunks.keys():
            return None

        offscreen = self._get_render_offscreen(self.mipmaps[self._data.ResizableOriginalMipmap])

        parsed_attribute = parse_offscreen_attribute(offscreen.Attribute)

        #print(parsed_attribute)
        return decode_chunk_to_pil(
            self.clip_file.data_chunks[offscreen.BlockData],
            parsed_attribute
        )

class PaperLayer(BaseLayer):

    @property
    def color(self):
        return Color(self._data.DrawColorMainRed >> 24,
                self._data.DrawColorMainGreen >> 24,
                self._data.DrawColorMainBlue >> 24)

    @color.setter
    def color(self, new_color: Color):
        self._data.DrawColorMainRed = new_color.r << 24
        self._data.DrawColorMainGreen = new_color.g << 24
        self._data.DrawColorMainBlue = new_color.b << 24

    @classmethod
    def new(cls, clip_file, layer_name = "Paper", color = Color(0, 0, 0)):

        layer_data = BaseLayer._new(clip_file, layer_name)

        layer_data.LayerType = LayerType.PAPER

        layer_data.DrawToRenderOffscreenType = DrawToRenderOffscreenType.PAPER
        layer_data.SpecialRenderType = SpecialRenderType.PAPER
        layer_data.DrawToRenderMipmapType = DrawToRenderMipmapType.PAPER
        layer_data.MoveOffsetAndExpandType = OffsetAndExpandType.PAPER
        layer_data.FixOffsetAndExpandType = OffsetAndExpandType.PAPER
        layer_data.RenderBoundForLayerMoveType = OffsetAndExpandType.PAPER
        layer_data.SetRenderThumbnailInfoType = OffsetAndExpandType.PAPER

        layer_data.DrawColorEnable = 1

        # No idea of what the actual data format is
        layer_data.MonochromeFillInfo = binascii.unhexlify("0000003e0000000100000011004d006f006e006f006300680072006f006d006500530065007400740069006e006700000000000000000000000000000001")

        layer_data.save()

        layer = cls(clip_file, layer_data)

        layer.color = color

        return layer

class TextLayer(BaseLayer):

    # A text layer has a LayerType of 0
    # The text layer info is in the TextLayer* columns
    # TextLayerType not None
    # TextLayerString - The text
    # TextLayerAttributes - This is the paragraph data information
    # Etc

    # Text layers have no External chunk

    def __init__(self, clip_file, layer_data):

        self.text_objects = []

        BaseLayer.__init__(self, clip_file, layer_data)

        attr_array = self._get_text_attributes_array()
        text_array = self._get_strings_array()

        #print(self.layer_name)
        for attr, stri in zip(attr_array, text_array):
            #print(f"String length : {len(stri)}")
            #parse_text_attribute(attr)
            self.text_objects.append(Text.read(stri.decode("UTF-8"), attr))

        #print()

    @property
    def texts(self):
        for text in self.text_objects:
            print(text)

    @property
    def text(self):
        return self._data.TextLayerString

    def _get_strings_array(self):

        array = [self._data.TextLayerString]

        if self._data.TextLayerStringArray is not None:
            array.extend(self._split_array(self._data.TextLayerStringArray))

        return array

    def _get_text_attributes_array(self):
        array = [self._data.TextLayerAttributes]

        if self._data.TextLayerAttributesArray is not None:
            array.extend(self._split_array(self._data.TextLayerAttributesArray))

        return array

    def _split_array(self, array):

        data = io.BytesIO(array)
        arr = []
        while data.tell() < len(array):

            length = read_fmt("<i", data)
            arr.append(data.read(length))

        return arr

class CorrectionLayer(BaseLayer):

    def __init__(self, clip_file, layer_data):

        BaseLayer.__init__(self, clip_file, layer_data)

        if self._data.FilterLayerInfo is not None:
            self._correction = parse_correction_attributes(self._data.FilterLayerInfo)

    @property
    def correction(self):
        return self._correction

    @correction.setter
    def correction(self, new_correction):
        self._correction = new_correction
        self._data.FilterLayerInfo = self._correction.to_bytes()

    def save(self):

        self._data.FilterLayerInfo = self._correction.to_bytes()

        if isinstance(self._correction, Correction.GradientMap):
            self._data.FilterLayerV132 = 1
        else:
            self._data.FilterLayerV132 = None

        super().save()

    @classmethod
    def new(cls, clip_file, correction, layer_name = "Correction"):

        layer_data = BaseLayer._new(clip_file, layer_name)

        layer_data.LayerType = LayerType.CORRECTION

        layer_data.SpecialRenderType = SpecialRenderType.CORRECTION
        layer_data.SetRenderThumbnailInfoType = RenderThumbnailType.CORRECTION
        layer_data.DrawRenderThumbnailType = RenderThumbnailType.CORRECTION

        layer_data.LayerSelect = layer_data.LayerSelect | 256
        layer_data.LayerMasking = layer_data.LayerMasking | LayerMasking.BLOCK_APPLY_MASK | LayerMasking.MASK_ENABLED

        layer_data.save()

        layer = cls(clip_file, layer_data)

        layer.correction = correction

        return layer

class GradientLayer(BaseLayer):

    # Layer type : 2 (No pixel, only mask)
    # Gradient info in GradationFillInfo column
    # Gradients don't seem to have external data
    # Screentones have special values in LayerRenderInfo column and following along LayerEffectInfo column

    def __init__(self, clip_file, layer_data):

        BaseLayer.__init__(self, clip_file, layer_data)
        self.gradient = Gradient.from_bytes(self._data.GradationFillInfo)

    @classmethod
    def new(cls, clip_file, gradient, layer_name = "Gradient"):

        layer_data = BaseLayer._new(clip_file, layer_name)

        layer_data.DrawToRenderOffscreenType = DrawToRenderOffscreenType.GRADIENT
        layer_data.DrawToRenderMipmapType = DrawToRenderMipmapType.GRADIENT
        layer_data.MoveOffsetAndExpandType = OffsetAndExpandType.GRADIENT
        layer_data.FixOffsetAndExpandType = OffsetAndExpandType.GRADIENT
        layer_data.RenderBoundForLayerMoveType = OffsetAndExpandType.GRADIENT
        layer_data.SetRenderThumbnailInfoType = RenderThumbnailType.GRADIENT
        layer_data.DrawRenderThumbnailType = RenderThumbnailType.GRADIENT
        layer_data.GradationFillInfo = gradient.to_bytes()

        layer_data.save()

        return cls(
            clip_file,
            layer_data
        )

    def save(self):

        self._data.GradationFillInfo = self.gradient.to_bytes()
        super().save()

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

    def __init__(self, clip_file, layer_data):

        BaseLayer.__init__(self, clip_file, layer_data)

        vector_chunks = self.clip_file.sql_database.get_referenced_items("VectorObjectList", "LayerId", self._data.MainId)

        self.lines = []

        for vector_chunk in vector_chunks.values():
            self.lines.append(
                VectorList.read(
                    self.clip_file.data_chunks[vector_chunk.VectorData].block_data.data
                )
            )

            #self.lines = parse_vector(self.clip_file.data_chunks[vector_chunk.VectorData].block_data)

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

class BalloonLayer(VectorLayer):
    pass

class AnimationFolder(Folder):
    pass

class Layer3D(BaseLayer):

    # Three dimmension layer has a LayerType of 0
    # Specific data starts at Manager3DOd
    # LayerObject table holds the additional light/camera data for the 3D layers
    # 3D Scene data in Manager3DOd table
    # Has external data, Data starts by the signature "_STUDIO_3D_DATA2"

    # Additional metadata in SpecialRulerManager, RulerVanishPoint, RulerPerspective, 

    pass
