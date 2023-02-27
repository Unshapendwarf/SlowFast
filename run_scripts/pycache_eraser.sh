#!/bin/sh
WORK_SPACE=$HOME/slowfast/
cd $WORK_SPACE
echo $PWD
find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf
