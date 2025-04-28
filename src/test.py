from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.api.Layer import *
from clip_tools.api.Project import *
from clip_tools.clip.ClipData import ModelData3D
from clip_tools.clip.DataChunk import DataChunk
from clip_tools.parsers import encode_pil_to_chunk, encode_pil_to_chunk_parallels
from clip_tools.utils import read_fmt, decompositor
from clip_tools.api import Correction
from clip_tools import data_classes
import os
import io
from collections import namedtuple
from PIL import Image
import zlib
import sys
from clip_tools.constants import *
from clip_tools.api.Text import *
import cProfile

from Cryptodome.Hash import MD5
#"""
workdir = '../tests/Samples'

filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
#filelist = ["Illustration-Base.clip", "Illustration-Base-BW.clip", "Illustration-Base-Monochrome.clip", "Illustration-Mask.clip"]
filelist = ["Illustration-Small.clip"]

"""
with open("test.clip", "wb") as f:
    proj = Project.new()

    proj.save(f)

with open("test.clip", "rb") as f:
    proj = Project.open(f)

    print(proj.canvas)

#"""

"""
workdir = '../../ClipDissect/Page'

#filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["page0001.clip"]
"""

for f in filelist:

    print()
    print(f)

    with open(os.path.join(workdir, f), "rb") as fp:

        proj = Project.open(fp)
        

        """
        layer = proj.canvas.root_folder.find("Premier plan au transparent")
        print(layer.layer_name)
        print(layer.gradient)

        """

        layer = proj.canvas.root_folder[0]

        new_layer = PixelLayer.frompil(
                proj.clip_file,
                layer.topil()
        )

        new_layer.topil()

        for x in [GradientShape.LINEAR, GradientShape.CIRCLE, GradientShape.ELLIPSE]:
            proj.canvas.root_folder.extend([
                GradientLayer.new(
                    proj.clip_file,
                    Gradient.new(
                        shape=x
                    )
                )
            ])

        print(proj.canvas.root_folder[-1].gradient)

        with open(os.path.join("network","Illustration-copy.clip"), "wb") as f:
            proj.save(f)#"""
