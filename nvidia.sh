#!/bin/bash
while true
do
  # nvidia-smi --id=0 --query-gpu=utilization.gpu --format=csv >> gpu_utilization.csv
  nvidia-smi --id=2 --query-gpu=utilization.gpu --format=csv
  # echo hello
  sleep 1
done
