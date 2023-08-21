#!/bin/bash

pids=($(pgrep -u hong -a python | grep "BYOL" | awk '{print $1}'))
# pids=($(pgrep -u hong -a python | grep "python server.py" | awk '{print $1}'))

# Access the array elements

for pid in "${pids[@]}"; do
    echo "PID: $pid==>" $(ps -p $pid -o pcpu,pmem,cmd)
    # echo "PID: $pid==>" $(top -b -n1 -p $pid)
done
