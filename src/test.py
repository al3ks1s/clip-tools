from clip_tools.clip.ClipStudioFile import ClipStudioFile
import os

workdir = '../../ClipDissect/Page'

filelist = [f for f in os.listdir(workdir) if f.endswith(".clip")]

for f in filelist:
    with open(os.path.join(workdir, f), "rb") as fp:
        clipFile = ClipStudioFile.read(fp)
        
