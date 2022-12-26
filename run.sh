# /bin/bash
WORK_SPACE=$HOME/slowfast/
cd $WORK_SPACE
echo $PWD

CUDA_VISIBLE_DEVICES=0 /home/hong/miniconda3/envs/slow/bin/python tools/run_net.py --cfg configs/contrastive_ssl/ourdesign0.yaml
# CUDA_VISIBLE_DEVICES=1 /home/hong/miniconda3/envs/slow/bin/python tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml