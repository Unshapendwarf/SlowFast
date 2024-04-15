#!/bin/bash -e
# Copyright (c) Facebook, Inc. and its affiliates. All Rights Reserved.
# Run this script at project root by ".linter.sh" before you commit.

current_path=$(pwd)
echo "Current directory path:" "$current_path"

IFS='/' read -ra parts <<< "$current_path"

last_part="${parts[-1]}"

if [ "$last_part" = "run_scripts" ]; then
  echo "Change directory to working root..."
  cd ..
  echo $(pwd)

  echo "Running isort..."
  isort -y -sp .

  echo "Running black..."
  black -l 80 .

  echo "Running flake..."
  flake8 .

  command -v arc > /dev/null && {
    echo "Running arc lint ..."
    arc lint
  }


else
  echo "Please start in 'run_scripts' directory"
  exit 0
fi

