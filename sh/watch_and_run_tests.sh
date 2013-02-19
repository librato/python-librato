#!/bin/bash
#
script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source $script_dir/common.sh

check_requirements
export PYTHONPATH=$PYTHONPATH:$script_dir/../librato
cd $script_dir/..

test_files="tests/test_basic.py tests/test_queue.py tests/test_retry_logic.py"
filewatcher "tests/*.py librato/*.py" "nosetests --nocapture $test_files; echo"
cd ..
