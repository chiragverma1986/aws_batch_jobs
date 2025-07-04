#!/bin/bash -x

python3 app.py

if [ $? -ne 0 ];then
  echo "process Failed.."
  exit 2
fi
