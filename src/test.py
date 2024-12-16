from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.api.Layer import *
from clip_tools.api.Project import *
from clip_tools.utils import read_fmt
import os
import io
from collections import namedtuple
from PIL import Image
import zlib

#"""
workdir = '../tests/clip-tools-samples'

#filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["Illustration.clip"]

"""

workdir = '../../ClipDissect/Page'

#filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["page0001.clip"]

#"""

for f in filelist:
    with open(os.path.join(workdir, f), "rb") as fp:
        
        proj = Project.open(fp)

        print(proj.canvas.root_folder[0])

        keys = proj.clip_file.sql_database.table_scheme.copy()
        del keys["ElemScheme"]
        del keys["ParamScheme"]
        del keys["ExternalTableAndColumnName"]
        del keys["ExternalChunk"]
        del keys["RemovedExternal"]
        del keys["Project"]
        del keys["sqlite_sequence"]

        for k in keys:
            proj.clip_file.sql_database.fetch_values(k)

        """
        clipFile = ClipStudioFile.read(fp)

        #clipFile.sql_database._scheme_to_classes()
        
        layers = clipFile.sql_database.fetch_values("Layer")
                      
        for layer in layers:
            
            l = BaseLayer.new(clipFile, layers[layer])

            if isinstance(l, PixelLayer) and l.LayerName == "Pix Layer":
                
                im = l.topil()
                im.show()
        """