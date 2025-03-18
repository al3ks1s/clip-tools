from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.api.Canvas import Canvas

class Project():
    
    def __init__(self, clip_file, data):
        self.clip_file = clip_file
        self._data = data

        canvas_data = self.clip_file.sql_database.get_table("Canvas")[self._data.ProjectCanvas]

        self.canvas = Canvas(clip_file, canvas_data)

    def save(self, fp):
        self.clip_file.write(fp)

    @classmethod
    def open(cls, fp):
        
        clip_file = ClipStudioFile.read(fp)
        data = clip_file.sql_database.fetch_project_data()

        return cls(clip_file, data)


    @classmethod
    def new(cls, fp):
        pass


class MultifileProject():
    pass
    # Temp name for the class using the .cmc files
