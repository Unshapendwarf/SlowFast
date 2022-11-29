#!/bin/bash

# python -m grpc_tools.protoc -I<protos folder> --python_out=<out_path> --grpc_python_out=<out_path> <path to proto file>
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. data_feed.proto
