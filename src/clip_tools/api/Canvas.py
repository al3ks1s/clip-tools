from clip_tools.api.Layer import BaseLayer, FolderMixin


class Canvas():

    def __init__(self, clip_file, canvas_data):
        self.clip_file = clip_file
        self.canvas_data = canvas_data
        self.root_folder = None

        self._init_structure()

    @property
    def height(self):
        return self.canvas_data.CanvasHeight

    @height.setter
    def height(self, new_height):
        self.canvas_data.CanvasHeight = new_height

    @property
    def width(self):
        return self.canvas_data.CanvasWidth

    @width.setter
    def width(self, new_width):
        self.canvas_data.CanvasWidth = new_width

    @property
    def resolution(self):
        return self.canvas_data.CanvasResolution

    @resolution.setter
    def resolution(self, new_resolution):
        self.canvas_data.CanvasResolution = new_resolution


    def _init_structure(self):
        
        layers = self.clip_file.sql_database.get_table("Layer")

        root_data = layers[self.canvas_data.CanvasRootFolder]
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
        return "Canvas(size=%dx%d, dpi=%s)" % (int(self.width),
            int(self.height),
            int(self.resolution))