#!/usr/bin/env python3
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.

import numpy as np
import os
import random
import pandas
import torch
import torch.utils.data
from torchvision import transforms
import copy
import slowfast.utils.logging as logging
from slowfast.utils.env import pathmgr

import nvtx
import time as TTT
from PIL import Image, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True
import pickle

from . import decoder as decoder
from . import transform as transform
from . import utils as utils
from . import video_container as container
from .build import DATASET_REGISTRY
from .random_erasing import RandomErasing
from .transform import (
    MaskingGenerator,
    MaskingGenerator3D,
    create_random_augment,
)

logger = logging.get_logger(__name__)


@DATASET_REGISTRY.register()
class Kinetics(torch.utils.data.Dataset):
    """
    Kinetics video loader. Construct the Kinetics video loader, then sample
    clips from the videos. For training and validation, a single clip is
    randomly sampled from every video with random cropping, scaling, and
    flipping. For testing, multiple clips are uniformaly sampled from every
    video with uniform cropping. For uniform cropping, we take the left, center,
    and right crop if the width is larger than height, or take top, center, and
    bottom crop if the height is larger than the width.
    """

    def __init__(self, cfg, mode, num_retries=3):
        """
        Construct the Kinetics video loader with a given csv file. The format of
        the csv file is:
        ```
        path_to_video_1 label_1
        path_to_video_2 label_2
        ...
        path_to_video_N label_N
        ```
        Args:
            cfg (CfgNode): configs.
            mode (string): Options includes `train`, `val`, or `test` mode.
                For the train and val mode, the data loader will take data
                from the train or val set, and sample one clip per video.
                For the test mode, the data loader will take data from test set,
                and sample multiple clips per video.
            num_retries (int): number of retries.
        """
        # Only support train, val, and test mode.
        assert mode in [
            "train",
            "val",
            "test",
        ], "Split '{}' not supported for Kinetics".format(mode)
        self.mode = mode
        self.cfg = cfg
        self.p_convert_gray = self.cfg.DATA.COLOR_RND_GRAYSCALE
        self.p_convert_dt = self.cfg.DATA.TIME_DIFF_PROB
        self._video_meta = {}
        self._num_retries = num_retries
        self._num_epoch = 0.0
        self._num_yielded = 0
        self.skip_rows = self.cfg.DATA.SKIP_ROWS
        self.use_chunk_loading = True if self.mode in ["train"] and self.cfg.DATA.LOADER_CHUNK_SIZE > 0 else False
        self.dummy_output = None
        
        # Uitaek added at 2023-03-21
        self.dummy_frame = None

        # Uitaek added at 2023-03-21
        self.dummy_frame = None
        self.dummy_time_idx_decode = None

        # For training or validation mode, one single clip is sampled from every
        # video. For testing, NUM_ENSEMBLE_VIEWS clips are sampled from every
        # video. For every clip, NUM_SPATIAL_CROPS is cropped spatially from
        # the frames.
        if self.mode in ["train", "val"]:
            self._num_clips = 1
        elif self.mode in ["test"]:
            self._num_clips = cfg.TEST.NUM_ENSEMBLE_VIEWS * cfg.TEST.NUM_SPATIAL_CROPS

        logger.info("Constructing Kinetics {}...".format(mode))
        self._construct_loader()
        self.aug = False
        self.rand_erase = False
        self.use_temporal_gradient = False
        self.temporal_gradient_rate = 0.0
        self.cur_epoch = 0

        if self.mode == "train" and self.cfg.AUG.ENABLE:
            self.aug = True
            if self.cfg.AUG.RE_PROB > 0:
                self.rand_erase = True

    def _construct_loader(self):
        """
        Construct the video loader.
        """
        path_to_file = os.path.join(self.cfg.DATA.PATH_TO_DATA_DIR, "{}.csv".format(self.mode))
        logger.debug("here is the path: " + path_to_file)
        assert pathmgr.exists(path_to_file), "{} dir not found".format(path_to_file)

        self._path_to_videos = []
        self._labels = []
        self._spatial_temporal_idx = []
        self.cur_iter = 0
        self.chunk_epoch = 0
        self.epoch = 0.0
        self.skip_rows = self.cfg.DATA.SKIP_ROWS

        with pathmgr.open(path_to_file, "r") as f:
            if self.use_chunk_loading:
                rows = self._get_chunk(f, self.cfg.DATA.LOADER_CHUNK_SIZE)
            else:
                rows = f.read().splitlines()
            for clip_idx, path_label in enumerate(rows):
                fetch_info = path_label.split(self.cfg.DATA.PATH_LABEL_SEPARATOR)
                if len(fetch_info) == 2:
                    path, label = fetch_info
                elif len(fetch_info) == 3:
                    path, fn, label = fetch_info
                elif len(fetch_info) == 1:
                    path, label = fetch_info[0], 0
                else:
                    raise RuntimeError(
                        "Failed to parse video fetch {} info {} retries.".format(path_to_file, fetch_info)
                    )
                for idx in range(self._num_clips):
                    self._path_to_videos.append(os.path.join(self.cfg.DATA.PATH_PREFIX, path))
                    # self._labels.append(label)
                    self._labels.append(int(label))
                    self._spatial_temporal_idx.append(idx)
                    self._video_meta[clip_idx * self._num_clips + idx] = {}
        assert len(self._path_to_videos) > 0, "Failed to load Kinetics split {} from {}".format(
            self._split_idx, path_to_file
        )
        logger.info(
            "Constructing kinetics dataloader (size: {} skip_rows {}) from {} ".format(
                len(self._path_to_videos), self.skip_rows, path_to_file
            )
        )
        
        self.avg_read_time = 0
        self.avg_preprocessed_time = 0
        self.cnt_processed = 0
        

    def _set_epoch_num(self, epoch):
        self.epoch = epoch

    def _get_chunk(self, path_to_file, chunksize):
        try:
            for chunk in pandas.read_csv(
                path_to_file,
                chunksize=self.cfg.DATA.LOADER_CHUNK_SIZE,
                skiprows=self.skip_rows,
            ):
                break
        except Exception:
            self.skip_rows = 0
            return self._get_chunk(path_to_file, chunksize)
        else:
            return pandas.array(chunk.values.flatten(), dtype="string")

    # @nvtx.annotate()
    def __getitem__(self, index):
        """
        Given the video index, return the list of frames, label, and video
        index if the video can be fetched and decoded successfully, otherwise
        repeatly find a random video that can be decoded as a replacement.
        Args:
            index (int): the video index provided by the pytorch sampler.
        Returns:
            frames (tensor): the frames of sampled from the video. The dimension
                is `channel` x `num frames` x `height` x `width`.
            label (int): the label of the current video.
            index (int): if the video provided by pytorch sampler can be
                decoded, then return the index of the video. If not, return the
                index of the video replacement that can be decoded.
        """

        short_cycle_idx = None
        # When short cycle is used, input index is a tupple.
        if isinstance(index, tuple):
            index, self._num_yielded = index
            if self.cfg.MULTIGRID.SHORT_CYCLE:
                index, short_cycle_idx = index
        if self.dummy_output is not None:
            return self.dummy_output
        if self.mode in ["train", "val"]:
            # -1 indicates random sampling.
            temporal_sample_index = -1
            spatial_sample_index = -1
            min_scale = self.cfg.DATA.TRAIN_JITTER_SCALES[0]
            max_scale = self.cfg.DATA.TRAIN_JITTER_SCALES[1]
            crop_size = self.cfg.DATA.TRAIN_CROP_SIZE
            if short_cycle_idx in [0, 1]:
                crop_size = int(
                    round(self.cfg.MULTIGRID.SHORT_CYCLE_FACTORS[short_cycle_idx] * self.cfg.MULTIGRID.DEFAULT_S)
                )
            if self.cfg.MULTIGRID.DEFAULT_S > 0:
                # Decreasing the scale is equivalent to using a larger "span"
                # in a sampling grid.
                min_scale = int(round(float(min_scale) * crop_size / self.cfg.MULTIGRID.DEFAULT_S))
        elif self.mode in ["test"]:
            temporal_sample_index = self._spatial_temporal_idx[index] // self.cfg.TEST.NUM_SPATIAL_CROPS
            # spatial_sample_index is in [0, 1, 2]. Corresponding to left,
            # center, or right if width is larger than height, and top, middle,
            # or bottom if height is larger than width.
            spatial_sample_index = (
                (self._spatial_temporal_idx[index] % self.cfg.TEST.NUM_SPATIAL_CROPS)
                if self.cfg.TEST.NUM_SPATIAL_CROPS > 1
                else 1
            )
            min_scale, max_scale, crop_size = (
                [self.cfg.DATA.TEST_CROP_SIZE] * 3
                if self.cfg.TEST.NUM_SPATIAL_CROPS > 1
                else [self.cfg.DATA.TRAIN_JITTER_SCALES[0]] * 2 + [self.cfg.DATA.TEST_CROP_SIZE]
            )
            # The testing is deterministic and no jitter should be performed.
            # min_scale, max_scale, and crop_size are expect to be the same.
            assert len({min_scale, max_scale}) == 1
        else:
            raise NotImplementedError("Does not support {} mode".format(self.mode))
        num_decode = self.cfg.DATA.TRAIN_CROP_NUM_TEMPORAL if self.mode in ["train"] else 1
        min_scale, max_scale, crop_size = [min_scale], [max_scale], [crop_size]
        if len(min_scale) < num_decode:
            min_scale += [self.cfg.DATA.TRAIN_JITTER_SCALES[0]] * (num_decode - len(min_scale))
            max_scale += [self.cfg.DATA.TRAIN_JITTER_SCALES[1]] * (num_decode - len(max_scale))
            crop_size += (
                [self.cfg.MULTIGRID.DEFAULT_S] * (num_decode - len(crop_size))
                if self.cfg.MULTIGRID.LONG_CYCLE or self.cfg.MULTIGRID.SHORT_CYCLE
                else [self.cfg.DATA.TRAIN_CROP_SIZE] * (num_decode - len(crop_size))
            )
            assert self.mode in ["train", "val"]
        # Try to decode and sample a clip from a video. If the video can not be
        # decoded, repeatly find a random video replacement that can be decoded.

        for i_try in range(self._num_retries):


            frames_decoded, time_idx_decoded = (
                [None] * num_decode,
                [None] * num_decode,
            )
            if self.cfg.DATA.DUMMY_FRAMES and self.dummy_frame is not None:
                logger.debug("Loading DUMMY_FRAMES...")
                frames = self.dummy_frame
                time_idx = self.dummy_time_idx_decode
            else:
                i = int(self.epoch) % 31
                # get the video frames and information form SAND file system
                
                filename = self._path_to_videos[index]
                filename = os.path.basename(filename)
                filename = os.path.splitext(os.path.basename(filename))[0]
                
                
                # for train100.csv
                # root_path = "/data/hong/k400/reduced/server/test_0821"
                # root_path = "/home/hong/space-1/sand-dev/snfs/cmake/test_dir/client/test_0821"
                
                # for train998.csv
                root_path = "/data/hong/k400/reduced/server/savepoint_998_31"
                # root_path = "/home/hong/space-1/sand-dev/snfs/cmake/test_dir/client/savepoint_998_31"
                

                trgt_path = os.path.join(root_path, f'{filename}_{i}')
                
                decoded_data = [trgt_path + x for x in ["_a.png", "_b.png", "_st.pckl", "_tdiff.pckl"]]
                
                # time measure for read
                
                read_tic = TTT.time()
                # time information for training
                with open(decoded_data[2], 'rb') as f2:
                    ret_st = pickle.load(f2)
                with open(decoded_data[3], 'rb') as f3:
                    ret_tdiff = pickle.load(f3)

                # series of frames
                img_a, img_b = Image.open(decoded_data[0]), Image.open(decoded_data[1])
                total_w, total_h = img_a.size
                curr_frames_a, curr_frames_b = [], []

                
                for w in range(int(total_w/self.cfg.DATA.TRAIN_CROP_SIZE)):
                    for h in range(int(total_h/self.cfg.DATA.TRAIN_CROP_SIZE)):
                        position = (w*self.cfg.DATA.TRAIN_CROP_SIZE, h*self.cfg.DATA.TRAIN_CROP_SIZE, \
                            (w+1)*self.cfg.DATA.TRAIN_CROP_SIZE, (h+1)*self.cfg.DATA.TRAIN_CROP_SIZE)
                        
                        cropped_a, cropped_b = img_a.crop(position), img_b.crop(position)
                        np_cropped_a, np_cropped_b = np.array(cropped_a), np.array(cropped_b)
                        curr_frames_a.append(cropped_a)
                        curr_frames_b.append(cropped_b)
                
                img_a.close()
                img_b.close()
                
                read_toc = TTT.time()
                ret_frames = [torch.as_tensor(np.stack(curr_frames_a)), torch.as_tensor(np.stack(curr_frames_b))]
                
                self.cnt_processed += 1
                self.avg_read_time = ((read_toc-read_tic) + (self.cnt_processed-1)*self.avg_read_time) / self.cnt_processed

                # # remove storage data after loading is complete
                # for u_file in decoded_data:
                #     if os.path.exists(u_file):
                #         os.remove(u_file)
                #     else:
                #         logger.debug("error to remove" + u_file)
                    
            frames_decoded = ret_frames
            time_idx_decoded = ret_st


            # If decoding failed (wrong format, video is too short, and etc),
            # select another video.
            if frames_decoded is None or None in frames_decoded:
                logger.warning(
                    "Failed to decode video idx {} from {}; trial {}".format(index, self._path_to_videos[index], i_try)
                )
                logger.info(f"num_retries: {self._num_retries}")
                index = random.randint(0, len(self._path_to_videos) - 1)
                # if self.mode not in ["test"] and (i_try % (self._num_retries // 8)) == 0:
                #     # let's try another one
                #     index = random.randint(0, len(self._path_to_videos) - 1)
                continue

            if self.dummy_frame is None:
                self.dummy_frame = frames_decoded
                self.dummy_time_idx_decode = time_idx_decoded
            
            num_aug = self.cfg.DATA.TRAIN_CROP_NUM_SPATIAL * self.cfg.AUG.NUM_SAMPLE if self.mode in ["train"] else 1
            num_out = num_aug * num_decode
            f_out, time_idx_out = [None] * num_out, [None] * num_out
            idx = -1
            label = self._labels[index]

            ## hong added below, 더미 데이터가 있을 경우, 데이터 로딩, 전처리 과정을 생략한다
            # if self.dummy_output is not None:
            #     return self.dummy_output
            
            start_preprocess_t = TTT.time()
            for i in range(num_decode):
                for _ in range(num_aug):
                    idx += 1
                    f_out[idx] = frames_decoded[i].clone()
                    time_idx_out[idx] = time_idx_decoded[i, :]

                    f_out[idx] = f_out[idx].float()
                    f_out[idx] = f_out[idx] / 255.0
                    
                    # # T H W C -> C T H W.
                    # f_out[idx] = f_out[idx].permute(3, 0, 1, 2)
                    # f_out[idx], _ = transform.random_crop(f_out[idx], crop_size[i])
                    # f_out[idx] = f_out[idx].permute(1, 2, 3, 0)

                    # T H W C -> C T H W.
                    f_out[idx] = f_out[idx].permute(3, 0, 1, 2)
                    f_out[idx], _ = transform.random_crop(f_out[idx], crop_size[i])
                    f_out[idx] = f_out[idx].permute(1, 2, 3, 0)

                    if self.mode in ["train"] and self.cfg.DATA.SSL_COLOR_JITTER:
                        f_out[idx] = transform.color_jitter_video_ssl(
                            f_out[idx],
                            bri_con_sat=self.cfg.DATA.SSL_COLOR_BRI_CON_SAT,
                            hue=self.cfg.DATA.SSL_COLOR_HUE,
                            p_convert_gray=self.p_convert_gray,
                            moco_v2_aug=self.cfg.DATA.SSL_MOCOV2_AUG,
                            gaussan_sigma_min=self.cfg.DATA.SSL_BLUR_SIGMA_MIN,
                            gaussan_sigma_max=self.cfg.DATA.SSL_BLUR_SIGMA_MAX,
                        )

                    if self.aug and self.cfg.AUG.AA_TYPE:
                        aug_transform = create_random_augment(
                            input_size=(f_out[idx].size(1), f_out[idx].size(2)),
                            auto_augment=self.cfg.AUG.AA_TYPE,
                            interpolation=self.cfg.AUG.INTERPOLATION,
                        )
                        # T H W C -> T C H W.
                        f_out[idx] = f_out[idx].permute(0, 3, 1, 2)
                        list_img = self._frame_to_list_img(f_out[idx])
                        list_img = aug_transform(list_img)
                        f_out[idx] = self._list_img_to_frames(list_img)
                        f_out[idx] = f_out[idx].permute(0, 2, 3, 1)

                    # Perform color normalization.
                    f_out[idx] = utils.tensor_normalize(f_out[idx], self.cfg.DATA.MEAN, self.cfg.DATA.STD)

                    # T H W C -> C T H W.
                    f_out[idx] = f_out[idx].permute(3, 0, 1, 2)

                    scl, asp = (
                        self.cfg.DATA.TRAIN_JITTER_SCALES_RELATIVE,
                        self.cfg.DATA.TRAIN_JITTER_ASPECT_RELATIVE,
                    )
                    relative_scales = None if (self.mode not in ["train"] or len(scl) == 0) else scl
                    relative_aspect = None if (self.mode not in ["train"] or len(asp) == 0) else asp

                    f_out[idx] = utils.spatial_sampling(
                        f_out[idx],
                        spatial_idx=spatial_sample_index,
                        min_scale=min_scale[i],
                        max_scale=max_scale[i],
                        crop_size=crop_size[i],
                        random_horizontal_flip=self.cfg.DATA.RANDOM_FLIP,
                        inverse_uniform_sampling=self.cfg.DATA.INV_UNIFORM_SAMPLE,
                        aspect_ratio=relative_aspect,
                        scale=relative_scales,
                        motion_shift=self.cfg.DATA.TRAIN_JITTER_MOTION_SHIFT if self.mode in ["train"] else False,
                    )

                    if self.rand_erase:
                        erase_transform = RandomErasing(
                            self.cfg.AUG.RE_PROB,
                            mode=self.cfg.AUG.RE_MODE,
                            max_count=self.cfg.AUG.RE_COUNT,
                            num_splits=self.cfg.AUG.RE_COUNT,
                            device="cpu",
                        )
                        f_out[idx] = erase_transform(f_out[idx].permute(1, 0, 2, 3)).permute(1, 0, 2, 3)

                    f_out[idx] = utils.pack_pathway_output(self.cfg, f_out[idx])
                    if self.cfg.AUG.GEN_MASK_LOADER:
                        mask = self._gen_mask()
                        f_out[idx] = f_out[idx] + [torch.Tensor(), mask]

            frames = f_out[0] if num_out == 1 else f_out
            time_idx = np.array(time_idx_out)
            if num_aug * num_decode > 1 and not self.cfg.MODEL.MODEL_NAME == "ContrastiveModel":
                label = [label] * num_aug * num_decode
                index = [index] * num_aug * num_decode
            if self.cfg.DATA.DUMMY_LOAD:
                if self.dummy_output is None:
                    self.dummy_output = (frames, label, index, time_idx, {})
            
            # get the avg preprocessed time
            diff_preprocess_t = TTT.time() - start_preprocess_t
            self.avg_preprocessed_time = ( diff_preprocess_t + self.avg_preprocessed_time * (self.cnt_processed - 1)) / self.cnt_processed
            # self.avg_preprocessed_time = ( diff_preprocess_t + self.avg_preprocessed_time * (self.cnt_processed - 1)) / self.cnt_processed
            if self.num_videos / self.cfg.DATA_LOADER.NUM_WORKERS <= self.cnt_processed:
                logger.info(f"{os.getpid()}: read_cnt={self.cnt_processed}, avg_read_t={self.avg_read_time}, avg_prepr_t={self.avg_preprocessed_time}")
            
            return frames, label, index, time_idx, {}
        else:
            logger.warning("Failed to fetch video after {} retries.".format(self._num_retries))

    def _gen_mask(self):
        if self.cfg.AUG.MASK_TUBE:
            num_masking_patches = round(np.prod(self.cfg.AUG.MASK_WINDOW_SIZE) * self.cfg.AUG.MASK_RATIO)
            min_mask = num_masking_patches // 5
            masked_position_generator = MaskingGenerator(
                mask_window_size=self.cfg.AUG.MASK_WINDOW_SIZE,
                num_masking_patches=num_masking_patches,
                max_num_patches=None,
                min_num_patches=min_mask,
            )
            mask = masked_position_generator()
            mask = np.tile(mask, (8, 1, 1))
        elif self.cfg.AUG.MASK_FRAMES:
            mask = np.zeros(shape=self.cfg.AUG.MASK_WINDOW_SIZE, dtype=np.int)
            n_mask = round(self.cfg.AUG.MASK_WINDOW_SIZE[0] * self.cfg.AUG.MASK_RATIO)
            mask_t_ind = random.sample(range(0, self.cfg.AUG.MASK_WINDOW_SIZE[0]), n_mask)
            mask[mask_t_ind, :, :] += 1
        else:
            num_masking_patches = round(np.prod(self.cfg.AUG.MASK_WINDOW_SIZE) * self.cfg.AUG.MASK_RATIO)
            max_mask = np.prod(self.cfg.AUG.MASK_WINDOW_SIZE[1:])
            min_mask = max_mask // 5
            masked_position_generator = MaskingGenerator3D(
                mask_window_size=self.cfg.AUG.MASK_WINDOW_SIZE,
                num_masking_patches=num_masking_patches,
                max_num_patches=max_mask,
                min_num_patches=min_mask,
            )
            mask = masked_position_generator()
        return mask

    def _frame_to_list_img(self, frames):
        img_list = [transforms.ToPILImage()(frames[i]) for i in range(frames.size(0))]
        return img_list

    def _list_img_to_frames(self, img_list):
        img_list = [transforms.ToTensor()(img) for img in img_list]
        return torch.stack(img_list)

    def __len__(self):
        """
        Returns:
            (int): the number of videos in the dataset.
        """
        return self.num_videos

    @property
    def num_videos(self):
        """
        Returns:
            (int): the number of videos in the dataset.
        """
        return len(self._path_to_videos)
