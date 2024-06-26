# /bin/bash


# 1. Working directory setup
MACHINE_NAME=$(hostname)
WORK_SPACE=$HOME/slowfast/
cd $WORK_SPACE
echo "$MACHINE_NAME, $PWD"


# 2. Program Variable setup: default
# CUDA_VISIBLE_DEVICES=0
my_python_path="anaconda3/envs/torch10/bin/python"
config_path="configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml"


# 2-1. Machine specific setup: Select GPU and Python Environment
if [ $MACHINE_NAME = "mango2" ];then
    # CUDA_VISIBLE_DEVICES=1
    my_python_path="anaconda3/envs/torch10/bin/python"
    # config_path="configs/Kinetics/custom_MVIT.yaml"
    # config_path="configs/Kinetics/custom_MVIT.yaml"
    # config_path="configs/Kinetics/custom_mvit_32.yaml"
    # config_path="configs/masked_ssl/k400_VIT_B_16x4_MAE_PT.yaml"
    # config_path="configs/masked_ssl/k400_VIT_L_16x4_MAE_PT.yaml"
elif [ $MACHINE_NAME = "mango3" ];then
    # CUDA_VISIBLE_DEVICES=3
    my_python_path="miniconda3/envs/slow/bin/python"
fi


# 4. GPU log or not
echo "Record the GPU utilization? [y/n]"

GPU_LOG=0
read choice

if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    echo "nvidia-smi --id=$CUDA_VISIBLE_DEVICES --query-gpu=utilization.gpu --format=csv"
    GPU_LOG=1

    echo "Logfile name: [XXX].log"
    read log_name
    
elif [ "$choice" = "n" ] || [ "$choice" = "N" ]; then
    echo "GPU logging: skipped"
else
    echo "Invalid choice, Please enter y or n."
fi

# 3. Function to generate and log a timestamp
log_gpustamp() {
    while true; do
        gpu_log=$(nvidia-smi --query-gpu=gpu_name,timestamp,utilization.gpu,power.draw --format=csv)
        echo $gpu_log >> out/$log_name-gpu.log
        sleep 1
    done
}

log_ramstamp() {
    while true; do
        ram_log=$(free -m | awk 'NR==2 {printf "Total: %sMB Used: %sMB Free: %sMB\n", $2, $3, $4}')
        echo "$(date) / $ram_log" >> out/$log_name-ram.log
        sleep 1
    done
}

# log_cpustamp() {
#     mpstat -P ALL 1 | tail -n +4 >> out/$log_name-cpu.log
# }


# 5. RUN the python script

if [ $GPU_LOG = 1 ]; then
    log_gpustamp &
    log_pid_gpu=$!

    log_ramstamp &
    log_pid_ram=$!
    
    # log_cpustamp &
    mpstat -P 5-39 1 | tail -n +4 >> out/$log_name-cpu.log &
    log_pid_cpu=$!
fi


trap cleanup INT

cleanup() {
    echo "Cleaning up and exiting..."
    if [ $GPU_LOG = 1 ]; then
        echo "Logging process stopped: $log_pid_gpu, $log_pid_ram, $log_pid_cpu"
        kill $log_pid_gpu
        kill $log_pid_ram
        kill $log_pid_cpu
    fi
    exit 0
}


echo "Starting process..."

# sleep 10
# run the python process
if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    /home/hong/"$my_python_path" tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml >> out/$log_name-stdout.log   
else
    /home/hong/"$my_python_path" tools/run_net.py --cfg configs/contrastive_ssl/custom_BYOL_SlowR50_8x8.yaml 
fi

echo "Process finished."

if [ $GPU_LOG = 1 ]; then
    echo "Logging process stopped: $log_pid_gpu, $log_pid_ram, $log_pid_cpu"
    kill $log_pid_gpu
    kill $log_pid_ram
    kill $log_pid_cpu
fi

