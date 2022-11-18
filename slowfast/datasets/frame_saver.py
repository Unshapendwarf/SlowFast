import sys
import torch
import numpy as np
import torch.utils.data
from pympler.asizeof import asizeof


class frameInfo:
    __slots__ = ["path", "frames", "times", "diff_augs"]

    def __init__(self, path, frames: list, times: list, diff_augs: list):
        self.path = path
        self.frames: list = frames
        self.times: list = times
        self.diff_augs: list = diff_augs

    def putInfo(self, frame, time_idx, diff_aug):
        self.frames.append(frame)
        self.times.append(time_idx)
        self.diff_augs.append(diff_aug)

    def popInfo(self):
        # print(f"popInfo() {asizeof(self.frames)}")
        return self.frames.pop(0), self.times.pop(0), self.diff_augs.pop(0)

    def getLen(self):
        if len(self.frames) == len(self.times) and len(self.times) == len(self.diff_augs):
            return len(self.frames)
        else:
            return -1