from clip_tools.api.Layer import BaseLayer, FolderMixin, PaperLayer
from clip_tools.constants import ColorMode
from clip_tools.data_classes import Color

class Canvas():

    def __init__(self, clip_file, canvas_data):
        self.clip_file = clip_file
        self._data = canvas_data
        self.root_folder = None

        self._init_structure()

    def add_paper(self, color = Color(255,255,255)):

        if len(self.root_folder) == 0:
            self.root_folder.append(PaperLayer.new(
                clip_file=self.clip_file,
                color=color
            ))
            return

        if not isinstance(self.root_folder[0], PaperLayer):
            self.root_folder.insert(0, PaperLayer.new(
                clip_file=self.clip_file,
                color=color
            ))
            return

        print("A paper layer already exists")

    @property
    def height(self):
        return self._data.CanvasHeight

    @height.setter
    def height(self, new_height):
        self._data.CanvasHeight = new_height

    @property
    def width(self):
        return self._data.CanvasWidth

    @width.setter
    def width(self, new_width):
        self._data.CanvasWidth = new_width

    @property
    def resolution(self):
        return self._data.CanvasResolution

    @resolution.setter
    def resolution(self, new_resolution):
        self._data.CanvasResolution = new_resolution

    @property
    def color_mode(self):
        return ColorMode(self._data.CanvasDefaultColorTypeIndex)

    def save(self):
        self._data.save()

        self.root_folder.save()

        for layer in self.root_folder:
            layer.save()

    def _init_structure(self):
        
        layers = self.clip_file.sql_database.get_table("Layer")

        root_data = layers[self._data.CanvasRootFolder]
        self.root_folder = BaseLayer.from_db(self.clip_file, root_data)

        self._recurse_structure(self.clip_file, layers, self.root_folder)

    def _recurse_structure(self, clip_file, layers, current_layer):

        if current_layer._data.LayerFirstChildIndex != 0:
            first_child_layer_data = layers[current_layer._data.LayerFirstChildIndex]
            first_child_layer = BaseLayer.from_db(clip_file, first_child_layer_data)

            current_layer.append(first_child_layer)
            self._recurse_structure(clip_file, layers, first_child_layer)

        if current_layer._data.LayerNextIndex != 0:
            next_layer_data = layers[current_layer._data.LayerNextIndex]
            next_layer = BaseLayer.from_db(clip_file, next_layer_data)

            current_layer._parent.append(next_layer)
            self._recurse_structure(clip_file, layers, next_layer)

    def __repr__(self):
        return "Canvas(size=%dx%d, dpi=%s, color_mode=%s)" % (int(self.width),
            int(self.height),
            int(self.resolution),
            self.color_mode.name
            )
