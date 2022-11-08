import os
import torch
import numpy as np
import torch.utils.data

class frameInfo:
    def __init__(
        self,
        frames=[],
        time=0,
    ):
        self.frames = frames
        self.time = time

    def getframes(self):
        # print("get frames")
        return self.frames

    def gettime(self):
        return self.time


class DecDict:
    def __init__(self):
        self.dictionary = {}

    def put(self, idx, frame):
        print("put")

        # if not exist
        self.dictionary[idx] = frame

        # if exist
        # self.dictionary[idx] = ???

    def get(self, idx):
        print("get")
        return self.dictionary[idx]

    def remove(self, idx):
        print("remove")
        return self.dictionary.pop(idx)

    def remove_all(self):
        print("remove all")
        self.dictionary.clear()

    def len(self):
        return len(self.dictionary)


"""
DecDict
{
    video_idx(int):frameInformation(frameInfo), ....
}

"""
