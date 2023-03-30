# /bin/bash
MACHINE_NAME=$(hostname)
WORK_SPACE=$HOME/slowfast/
cd $WORK_SPACE
echo "$MACHINE_NAME, $PWD"

if [ $MACHINE_NAME = "mango2" ];then
    CUDA_VISIBLE_DEVICES=1 /home/hong/anaconda3/envs/torch10/bin/python tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml
    # CUDA_VISIBLE_DEVICES=1 /home/hong/anaconda3/envs/torch10/bin/python tools/run_net.py --cfg configs/Kinetics/custom_MVIT.yaml
    # CUDA_VISIBLE_DEVICES=1 /home/hong/anaconda3/envs/torch10/bin/python tools/run_net.py --cfg configs/Kinetics/custom_MVIT.yaml
    # CUDA_VISIBLE_DEVICES=1 /home/hong/anaconda3/envs/torch10/bin/python tools/run_net.py --cfg configs/masked_ssl/k400_VIT_B_16x4_MAE_PT.yaml 
elif [ $MACHINE_NAME = "mango3" ];then
    CUDA_VISIBLE_DEVICES=0 /home/hong/miniconda3/envs/slow/bin/python tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml
fi