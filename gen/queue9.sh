#!/bin/bash
# waits for the eighth queue (new voice takes, dense mouth poses), then renders the smiling poses
while [ ! -f logs/log_q8.txt ]; do sleep 20; done
./venv2/bin/python lpx3.py paige cy dee sunny mel > logs/log_lpx3.txt 2>&1
echo finished > logs/log_q9.txt
