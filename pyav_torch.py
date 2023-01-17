
import glob
import multiprocessing
import os
import time
import timeit

import av
import torch
import torchvision.transforms as transforms
from PIL import Image
from torchvision.utils import save_image as s_image


def pyav_decode(filepath):
    container = av.open(filepath)
    # print(filepath)
    decoded_result = container.decode(video=0)

    indices = [6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36]
    frames = []
    for k, frame in enumerate(decoded_result):
        if k in indices:
            frames.append(frame.to_image())

    # print(cnt, end="  ")
    # pil_image = frame.to_image()
    # frame.to_image().save('frame-%04d.jpg' % frame.index)
    return frames


def image_transform():
    s = 1
    color_jitter = transforms.ColorJitter(0.8 * s, 0.8 * s, 0.8 * s, 0.2 * s)
    data_transforms = transforms.Compose(
        [   

            # transforms.RandomResizedCrop((96, 96)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomApply([color_jitter], p=0.8),
            transforms.RandomGrayscale(p=0.2),
            # GaussianBlur(kernel_size=int(0.1 * eval(input_shape)[0])),
            transforms.ToTensor(),
            # transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
    )
    return data_transforms
    # data_transforms(pil_img)
    # image_crop = data_transforms(pil_img)


def worker(filepath_list):

    wfd = open("out.log", "w")
    for k, filepath in enumerate(filepath_list):

        # t1 = timeit.timeit(lambda: pyav_decode(filepath), number=1)
        # print(t1)
        data_transform = image_transform()
        resize_trans = transforms.RandomCrop((96, 96))

        start_time = time.time()
        eightframes = pyav_decode(filepath)
        decoded_time = time.time()

        if len(eightframes)!=16:
            print("not 16 frames")
            return

        # print(decoded_time-start_time)
        resized_images = []
        for img in eightframes:
            h, w = img.size
            if h<96:
                continue
            if w<96:
                continue

            resized_img = resize_trans(img)
            resized_images.append(resized_img)
        
        tr_start_time = time.time()
        aaa_list = []
        for l, output in enumerate(resized_images):
            aaa_list.append(data_transform(output))
        s_image(aaa_list, f"saved_pngs/{k}_.png")
        end_time = time.time()

        wfd.write(f"{decoded_time-start_time} {end_time-tr_start_time}\n")

        if k == 100:
            break
    wfd.close()

def main():
    # dir = "/dev/shm/small-k400-test"
    dir = "/ssd/hong/small-k400-test"

    video_dir = os.path.join(dir, "*.mp4")
    fname_videos = sorted(glob.glob(video_dir))
    images = []
    worker(fname_videos)
    # for fname in fname_videos:
    #     # Opens a image in RGB mode
    #     im = Image.open(fname)

    #     transform = transforms.Resize((761, 500))
    #     # transform = transforms.Resize((1280, 720))
    #     img_resize = transform(im)
    #     images.append(img_resize)
    #     # images.append(im)

    exit()
    # num_split = 15
    # img_len = len(images)
    # batch_size = img_len // num_split
    # # image_pool = [images[:img_len//2], images[img_len//2:]]
    # image_pool = []
    # for i in range(num_split):
    #     if i == num_split - 1:
    #         image_pool.append(images[batch_size * i :])
    #     else:
    #         image_pool.append(images[batch_size * i : batch_size * (i + 1)])

    # start = time.perf_counter()
    # processes = []

    # for inputs in image_pool:
    #     p = multiprocessing.Process(target=worker, args=(inputs,))  ## 각 프로세스에 작업을 등록
    #     p.start()
    #     processes.append(p)

    # for process in processes:
    #     process.join()

    # finish = time.perf_counter()

    # print(f"{round(finish-start,3)}초 만에 작업이 완료되었습니다.")


if __name__ == "__main__":
    # run main program
    main()
