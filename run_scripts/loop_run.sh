# /bin/bash
MACHINE_NAME=$(hostname)
WORK_SPACE=$HOME/slowfast/
cd $WORK_SPACE
echo "$MACHINE_NAME, $PWD"

INDEX_FILE=$WORK_SPACE/configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml
if MACHINE_NAME=="mango2";then
    CUDA_VISIBLE_DEVICES=1
    # /home/hong/anaconda3/envs/torch10/bin/python tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml
elif MACHINE_NAME=="mango3";then
    CUDA_VISIBLE_DEVICES=0
    # /home/hong/miniconda3/envs/slow/bin/python tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml
fi

#=============================================================# 2022-08-18
last_var=0
for var in 1 4 8 16 20 32 
do
    sed -i "20,22s/NUM_WORKERS: ${last_var}/NUM_WORKERS: ${var}/g" $INDEX_FILE
    new=`sed -n "21p" $INDEX_FILE`
    echo "Current Config-> \"${new}\""
    sleep 1
    # run
    # python main.py --dali
    CUDA_VISIBLE_DEVICES=1 /home/hong/anaconda3/envs/torch10/bin/python tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml > ${var}.out

    sleep 2
    last_var=${var}
done


sed -i "20,22s/NUM_WORKERS: ${last_var}/NUM_WORKERS: 0/g" $INDEX_FILE
new=`sed -n "21p" $INDEX_FILE`
echo "FInal Config-> \"${new}\""
