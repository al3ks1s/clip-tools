from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.api.Canvas import Canvas
from clip_tools.clip import ClipData
from clip_tools.constants import ColorMode, CanvasChannelOrder
from clip_tools.api.Layer import RootFolder, PixelLayer

class Project():

    def __init__(self, clip_file, data):
        self.clip_file = clip_file
        self._data = data

        canvas_data = self.clip_file.sql_database.get_table("Canvas")[self._data.ProjectCanvas]

        self.canvas = Canvas(clip_file, canvas_data)

    def save(self, fp):

        self._data.save()
        self.canvas.save()
        self.clip_file.write(fp)

    @classmethod
    def open(cls, fp):

        clip_file = ClipStudioFile.read(fp)
        data = clip_file.sql_database.fetch_project_data()

        return cls(clip_file, data)

    @classmethod
    def new(
        cls,
        name = "Project",
        width = 1000.0,
        height = 1000.0,
        resolution = 600.0,
        color_mode = ColorMode.RGB
    ):

        clip_file = ClipStudioFile.new()

        project_data = ClipData.Project.new(
            clip_file.sql_database,
            ProjectInternalVersion = '1.1.0',
            ProjectName = name,
            ProjectCanvas = 1,
            ProjectItemBank = 1,
            ProjectCutBank = 1,
            ProjectRootCanvasNode = 0,

            DefaultPageUnit = 0,
            DefaultPageWidth = width,
            DefaultPageHeight = height,
            DefaultPageResolution = resolution,
            DefaultPageChannelBytes = 1,
            DefaultPageChannelOrder = CanvasChannelOrder.from_color_mode(color_mode),
            DefaultPageColorType = color_mode,
            DefaultPageBlackChecked = 1,
            DefaultPageWhiteChecked = 1,
            DefaultPageToneLine = 60.0,
            DefaultPageUsePaper = 0,
            DefaultPagePaperRed = 4294967295,
            DefaultPagePaperBlue = 4294967295,
            DefaultPagePaperGreen = 4294967295,
            DefaultPageUseTemplate = 0,
            DefaultPageDoublePage = 0,
            DefaultPageCheckBookBinding = 0,
            # This herculean task is killing me i'll just add values if needed
            DefaultPageSettingType = "Illust",
            DefaultPageRecordTimeLapse = 0,
        )

        root_folder = RootFolder.new(clip_file)

        canvas_data = ClipData.Canvas.new(
            clip_file.sql_database,
            CanvasUnit = 0, # see constants.CanvasUnit
            CanvasWidth = width,
            CanvasHeight = height,
            CanvasResolution = resolution,
            CanvasChannelBytes = 1,
            CanvasDefaultChannelOrder = CanvasChannelOrder.from_color_mode(color_mode),
            CanvasRootFolder = root_folder._data.MainId,
            CanvasCurrentLayer = root_folder._data.MainId,

            CanvasDoSimulateColor = 0,
            CanvasDefaultColorTypeIndex = color_mode,
            CanvasDefaultColorBlackChecked = project_data.DefaultPageBlackChecked,
            CanvasDefaultColorWhiteChecked = project_data.DefaultPageWhiteChecked,
            CanvasDefaultToneLine = project_data.DefaultPageToneLine,
            CanvasDoublePage = project_data.DefaultPageDoublePage
        )

        base_layer = PixelLayer.new(clip_file, "Test")
        root_folder.append(base_layer)

        canvas_data.CanvasCurrentLayer = base_layer._data.MainId

        canvas_data.save()
        base_layer.save()
        root_folder.save()

        return cls(clip_file, project_data)


class MultifileProject():
    pass
    # Temp name for the class using the .cmc files
