#!/bin/bash

# -t fd  True if file descriptor fd is open and refers to a terminal.
if [ -t 0 ]
then
  echo "No data in stdin." 2>&1
  exit 1
else
  cat - | python -mjson.tool
fi
