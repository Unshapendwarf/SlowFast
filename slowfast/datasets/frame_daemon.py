import os
import asyncio
from queue import Queue
from .transform import random_crop


class DataDaemon:
    def __init__(self, num_video):
        self.num_video = num_video
        self.queue = Queue(maxsize = 64)
        # set process pool in here
        # start the daemon with run
        self.run()
        
    def run():
        print("start DataDaemon")
        
    # async def corun():
    #     await a =
    
    # async def receive():
    #     await a
        
        


class BaseContainer:
    # queue with thread safe queue which uses lock for thread-safe
    __slots__ = ["video_name", "data_queue", "q_length", "crop_size", "index"]

    def __init__(self, video_name: str, num_preview: int = 1):
        self.video_name = video_name
        self.data_queue = Queue(maxsize=num_preview*2)
        self.index = 0
        self.crop_size = (96, 96)  # (height, weight)
        self.q_length = 0

    def cropper(self, frame):
        frame = frame.permute(3, 0, 1, 2)  # T H W C -> C T H W.
        frame, _ = random_crop(frame, self.crop_size[0])
        frame = frame.permute(1, 0, 2, 3)  # C T H W -> T C H W.
        return frame
        # randomly crop the frames and return it

    def get_len(self):
        return self.q_length


class ContainerRAM(BaseContainer):
    """
    store the cropped data at the memory

    """
    __slots__ = ()

    def __init__(self, video_name: str, num_preview: int = 1):
        super().__init__(video_name, num_preview)

    def q_pop(self):
        # pop data from dataQueue, get the image or run the decoding procedure
        if self.data_queue.empty():
            print(f"the Queue is empty, nothing to Pop()")
            return
        else:
            frames, start_end_times, tdiff = self.data_queue.get()  # expected outputs are in 3 ways
            return frames, start_end_times, tdiff

    def q_push(self, input1, input2, input3):
        # frame handling procedure:

        # we will put list of list as a queue element
        # save cropped frames as png in SSD
        # push save-path, start-end time, tdiff in dataQueue
        self.data_queue.put(None)  # put above data, what is the format? listed data?

        # self.glen update
        self.q_length = self.data_queue.qsize()  # or self.qlen += 1
        self.index += 1

