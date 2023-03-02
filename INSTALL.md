# Installation

## Requirements
- Python >= 3.8
- Numpy
- PyTorch >= 1.3
- [fvcore](https://github.com/facebookresearch/fvcore/): `pip install 'git+https://github.com/facebookresearch/fvcore'`
- [torchvision](https://github.com/pytorch/vision/) that matches the PyTorch installation.
  You can install them together at [pytorch.org](https://pytorch.org) to make sure of this.
- simplejson: `pip install simplejson`
- GCC >= 4.9
- PyAV: `conda install av -c conda-forge`
- ffmpeg (4.0 is prefereed, will be installed along with PyAV)
- PyYaml: (will be installed along with fvcore)
- tqdm: (will be installed along with fvcore)
- iopath: `pip install -U iopath` or `conda install -c iopath iopath`
- psutil: `pip install psutil`
- OpenCV: `pip install opencv-python`
- torchvision: `pip install torchvision` or `conda install torchvision -c pytorch`
- tensorboard: `pip install tensorboard`
- moviepy: (optional, for visualizing video on tensorboard) `conda install -c conda-forge moviepy` or `pip install moviepy`
- PyTorchVideo: `pip install pytorchvideo`
- [Detectron2](https://github.com/facebookresearch/detectron2):
- FairScale: `pip install 'git+https://github.com/facebookresearch/fairscale'`
```
    pip install -U torch torchvision cython
    pip install -U 'git+https://github.com/facebookresearch/fvcore.git' 'git+https://github.com/cocodataset/cocoapi.git#subdirectory=PythonAPI'
    git clone https://github.com/facebookresearch/detectron2 detectron2_repo
    pip install -e detectron2_repo
    # You can find more details at https://github.com/facebookresearch/detectron2/blob/master/INSTALL.md
```

## Install with Conda
- `conda create -n $YOUR_ENV_NAME python=3.9`
- pytorch, torchvision: `conda install pytorch==1.10.0 torchvision==0.11.0 torchaudio==0.10.0 cudatoolkit=11.3 -c pytorch -c conda-forge`
- fvcore>=0.1.5, pyyaml: `conda install -c fvcore -c iopath -c conda-forge fvcore`
- simplejson: `conda install -c conda-forge simplejson`
- pyav: `conda install av -c conda-forge`
- tqdm: `conda install -c conda-forge tqdm`
- iopath: `conda install -c iopath iopath`
- psutil: `conda install -c conda-forge psutil`
- opencv: `pip install opencv-python`
- pandas: `conda install -c anaconda pandas`
- scikit-learn: `conda install -c anaconda scikit-learn`
- tensorboard: `conda install -c conda-forge tensorboard=2.12`
- moviepy: `conda install -c conda-forge moviepy`
- pytorchvideo:
```
  git clone https://github.com/facebookresearch/pytorchvideo.git
  cd pytorchvideo
  pip install -e .
```
- FairScale: `pip install 'git+https://github.com/facebookresearch/fairscale'`
- detectron: `python -m pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html`
- DALI(opional): `pip install --extra-index-url https://developer.download.nvidia.com/compute/redist --upgrade nvidia-dali-cuda110`

## Pytorch
Please follow PyTorch official instructions to install from source:
```
git clone --recursive https://github.com/pytorch/pytorch
```

## PySlowFast

Clone the PySlowFast Video Understanding repository.
```
git clone https://github.com/facebookresearch/slowfast
```

Add this repository to $PYTHONPATH.
```
export PYTHONPATH=/path/to/SlowFast/slowfast:$PYTHONPATH
```

### Build PySlowFast

After having the above dependencies, run:
```
git clone https://github.com/facebookresearch/slowfast
cd SlowFast
python setup.py build develop
```

Now the installation is finished, run the pipeline with:
```
python tools/run_net.py --cfg configs/Kinetics/C2D_8x8_R50.yaml NUM_GPUS 1 TRAIN.BATCH_SIZE 8 SOLVER.BASE_LR 0.0125 DATA.PATH_TO_DATA_DIR path_to_your_data_folder
```
