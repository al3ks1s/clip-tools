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
import sys

#"""
workdir = '../tests/Samples'

filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["Illustration-Corrections.clip"]

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

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

        #with open(os.path.join(workdir,"Illustration-copy.clip"), "wb") as f:
        #    proj.save(f)

roo = Folder.new(proj.clip_file, "Test")
roo.append(PaperLayer.new(proj.clip_file, "Test2", Color(255, 127, 0)))
