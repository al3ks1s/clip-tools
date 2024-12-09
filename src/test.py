from clip_tools.clip.ClipStudioFile import ClipStudioFile
from clip_tools.api.Layer import *
from clip_tools.utils import read_fmt
import os
import io
from collections import namedtuple
from PIL import Image
import zlib

workdir = '../tests'

#filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]
filelist = ["Illustration.clip"]

for f in filelist:
    with open(os.path.join(workdir, f), "rb") as fp:
        
        clipFile = ClipStudioFile.read(fp)

        layers = clipFile.sql_database.fetch_values("Layer")

        for layer in layers:
            l = Layer.new(clipFile, layers[layer])

            if isinstance(l, GradientLayer):
                
                chunk, attr = l._get_mip_attributes()
                
                im = l._decode_chunk_to_pil(chunk, attr)

                im.show()



