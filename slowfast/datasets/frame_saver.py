import os
import torch
import numpy as np
import torch.utils.data
from torchvision import transforms


class frameInfo:
    def __init__(
        self,
    ):
        self.dictionary = {}

    def get():
        print("get")


class DecDict:
    def __init__(

        self
    ):
        self.dictionary = {}

    def get(idx):
        print("get")

    def put(idx, frame):
        print("put")

    def remove():
        print("remove")

    def remove_all():
        print("remove all")

"""
DecDict
{
    video_idx(int):frameInformation(frameInfo), ....
}

"""
