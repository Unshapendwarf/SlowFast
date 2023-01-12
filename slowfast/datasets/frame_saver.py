import sys
import torch
import torch.utils.data
import torchvision.transforms as transforms

from queue import Queue
from torchvision.utils import save_image, make_grid
from PIL import Image

'''
    2022-01-09 implementing
    dictionary-> png로 할껀데 이제 한 iteration에 16장이 필요라고 설정(8*2 for one video)
    ordered picture cropping 이 필요할듯
    augmentation except crop -> 이거는 나중에 load하고 해보는걸로

    정할 거:
        group policy -> preview_epoch 수 많큼 저장하는걸로 하고 (8*2*previewnum)
    data:
        saved_path: epoch-videopath-
        saved_order
        frame infos: start-end time, tdiff
    ---
    Where data is stored
    - frames: ssd
    - start-end time: RAM
    - tdiff: RAM

    no problem with the RAM size?
    
'''
# 아래 frameMan 을 가지고 정리하는 dictionary가 필요하다 -> kinetics_custom에서 만들어서 사용하면 될듯
# 아래 frameMan 을 queue에 넣고 그 queue를 dictionary의 value가 되게 해야함
# Qcontainer는 queue object안에 한 iteration 에 필요한 데이터를 push한다

class Qcontainer:
    # __slots__ = ["videopath", "frames", "times", "diff_augs"]
    # queue with thread safe queue which uses lock for thread-safe
    __slots__ = ["video_name", "data_queue", "num_preview", "q_length"]

    def __init__(self, video_name: str, num_preview: int = 1):
        self.video_name = video_name
        self.data_queue = Queue(maxsize=num_preview*2)
        self.q_length = 0

    def q_pop(self):
        # pop data from dataQueue, get the image or run the decoding procedure
        # read png file from Storage
        if self.data_queue.empty():
            print(f"the Queue is empty")
            return
        else:
            frame_paths, start_end_times, tdiff = self.data_queue.get() # expected outputs are in 3 ways

        # if queue is empty
        # load PNG images as PIL images
        frames = []
        for path in frame_paths:
            img = Image.open(path)
            # images are already cropped here
            frames.append(img)
            # no channel processing for this? 
        
        # ?? new thread를 만들어서 그때 data가 삭제가 안되서 돌아가는건가? 이거는 확인해봐야지
        # -> 그런데 이거는 문제가 안되는게 동시에 push 해서 order가 꼬이는 상황을 막기 위한 lock일건데 
        #    나 같은 경우는 각 queue마다 한개의 decoding process가 실행되는거라서 의미 없다
        frame = None
        return frame

    def q_push(self, input1, input2, input3):
        # frame handling procedure: 
        # crop frames
        # save stitched images

        images = []
        save_name = f"some saving name"
        # consideration: you need to think about the none frames
        stitched_img = make_grid(images, padding=0)
        save_image(stitched_img, save_name)
        
        # we will put list of list as a queue element 
        # save cropped frames as png in SSD
        # push save-path, start-end time, tdiff in dataQueue
        self.data_queue.put(None)  # put above data, what is the format? listed data?

        # self.glen update
        self.q_length = self.data_queue.qsize()  # or self.qlen += 1

    def get_len(self):
        return self.q_length
