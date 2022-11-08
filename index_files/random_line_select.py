import os
import random

root_path = "/home/hong/"
file_path = os.path.join(root_path, "slowfast/index_files/train4999.csv")

count = 0
with open(file_path, "r") as rfd:
    lines = rfd.readlines()
    random_lines = random.sample(lines, 20)
    for k, line in enumerate(random_lines):
        # if k % 13 == 0:
        count += 1
        print(line, end="")
