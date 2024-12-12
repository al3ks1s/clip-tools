from clip_tools.clip.ClipStudioFile import ClipStudioFile

class Project():
    
    def __init__(self, clip_file, data):
        self.clip_file = clip_file
        self.canvas = []
        self._data = data

    @classmethod
    def open(cls, fp):
        
        clip_file = ClipStudioFile.read(fp)
        data = clip_file.sql_database.fetch_project_data()

        return cls(clip_file, data)

    @classmethod
    def save(cls, fp):
        pass


class MultifileProject():
    pass
    # Temp name for the class using the .cmc files
        

