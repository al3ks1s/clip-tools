from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.api.Layer import *
from clip_tools.api.Project import *
from clip_tools.clip.ClipData import ModelData3D
from clip_tools.utils import read_fmt, decompositor
import os
import io
from collections import namedtuple
from PIL import Image
import zlib

#"""
workdir = '../tests/Samples'

filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["Illustration-Rulers.clip"]

"""

workdir = '../../ClipDissect/Page'

#filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["page0001.clip"]

#"""

for f in filelist:

    print()
    print(f)

    with open(os.path.join(workdir, f), "rb") as fp:
        
        proj = Project.open(fp)

        #print(list(proj.canvas.root_folder.descendants()))

        keys = proj.clip_file.sql_database.table_scheme.copy()
        del keys["ElemScheme"]
        del keys["ParamScheme"]
        del keys["ExternalTableAndColumnName"]
        del keys["ExternalChunk"]
        del keys["RemovedExternal"]
        del keys["Project"]
        del keys["sqlite_sequence"]

        for k in keys:
            proj.clip_file.sql_database.get_table(k)

        #proj.canvas.root_folder[0].topil().show()
        #clipFile.sql_database._scheme_to_classes()

        for layer in proj.canvas.root_folder.descendants():
            pass
        
        proj.canvas.canvas_data.ShowGrid = 6
        proj.canvas.canvas_data.GridDitch = 10000.0
        
        proj.canvas.canvas_data.write_to_db(proj.clip_file.sql_database)

        proj.clip_file.sql_database.get_table("Canvas")[1].ShowGrid

        data3D = ModelData3D.new()
        data3D.MainId = 5
        data3D.CanvasId = 8
        data3D.Layer3DModelData = b'AAAAAAAAA'
        
        print(data3D)
        data3D.write_to_db(proj.clip_file.sql_database)
        print(proj.clip_file.sql_database.get_table("ModelData3D"))

        data3D.write_to_db(proj.clip_file.sql_database)