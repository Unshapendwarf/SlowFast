import os
from queue import Queue
from .transform import random_crop
from PIL import Image
from torchvision.utils import make_grid, save_image

class DataDaemon:
    def __init__(self, ):
        print("hello")


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


class ContainerSSD(BaseContainer):
    """
    frame Container for SSD design implementation
    """

    __slots__ = ["storage_path"]

    def __init__(self, video_name: str, num_preview: int = 1):
        super().__init__(video_name, num_preview)
        self.storage_path = "/ssd/hong/slow_png_storage"  # storage path for goguma6

    def q_pop(self):
        # pop data from dataQueue, get the image or run the decoding procedure
        # read png file from Storage
        if self.data_queue.empty():
            print(f"the Queue is empty, nothing to Pop()")
            return
        else:
            save_path1, save_path2, start_end_times, tdiff = self.data_queue.get()  # expected outputs are in 3 ways

        # load PNG images as PIL images
        frames = []

        stitched1 = Image.open(save_path1)
        stitched2 = Image.open(save_path2)

        ######## you should start from here. this is cropping for temporal frames
        ######## 2023-01-16

        # cropped1 = stitched1.crop(self.index+)
        # images are already cropped here
        frames.append()
        # no channel processing for this?

        frame = None
        return frame

    def q_push(self, raw_frames, st_end_time, tdiff):
        """
        raw_frames: raw_frames from pyav decoder
        st_end_time: frame start-end time
        tdiff: time difference
        """

        # randomly crop the frames
        cropped_1 = self.cropper(raw_frames[0])
        cropped_2 = self.cropper(raw_frames[1])

        save_name = self.video_name + f"_{self.index}"
        save_path1 = os.path.join(self.storage_path, "aa", save_name)
        save_path2 = os.path.join(self.storage_path, "bb", save_name)

        # cropped_1 & cropped_2 are in form of "T C H W"
        stitched_img1 = make_grid(cropped_1, padding=0)
        stitched_img2 = make_grid(cropped_2, padding=0)
        save_image(stitched_img1, save_path1)
        save_image(stitched_img2, save_path2)

        # push save-path, start-end time, tdiff in dataQueue
        self.data_queue.put((save_path1, save_path2, st_end_time, tdiff))  # put above data, what is the format?

        # self.qlen update
        self.q_length = self.data_queue.qsize()  # or self.qlen += 1
        self.index += 1
