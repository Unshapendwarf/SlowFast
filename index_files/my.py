import os
from shutil import copyfile

idx_file = "test1.csv"
split = "test"
# src_dir = os.path.join("/data/hong/k400/reduced/", split)
dest_dir = os.path.join("/data/hong/k400/reduced/", "other", split)

with open(idx_file, "rt") as ff:
    for line in ff.readlines():
        mine = line.split(" ")[0].strip()
        if os.path.exists(mine):
            pass
        else:
            print(mine, os.path.exists(mine))
        mp4name = os.path.basename(mine)
        dst_file = os.path.join(dest_dir, mp4name)
        if os.path.isfile(dst_file):
            pass
        else:
            print(dst_file)
            copyfile(mine, dst_file)
        
# copyfile()

