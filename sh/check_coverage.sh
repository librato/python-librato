#!/bin/bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $script_dir/common.sh

check_requirements
export PYTHONPATH=$PYTHONPATH:$script_dir/../drio.py
cd $script_dir/..
rm -rf .coverage* htmlcov
for f in tests/test*.py; do
  coverage run -p $f
done
coverage combine
coverage report -m
coverage html
cd ..
