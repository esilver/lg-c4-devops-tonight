#!/bin/bash
./venv4/bin/python tts2.py 2 > logs/log_tts2.txt 2>&1
./venv2/bin/python lpx2.py paige cy dee sunny mel > logs/log_lpx2.txt 2>&1
echo finished > logs/log_q8.txt
