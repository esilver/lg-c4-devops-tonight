#!/bin/bash
./venv2/bin/python lp_extra.py paige cy dee sunny mel > logs/log_lp_extra.txt 2>&1
./venv/bin/python gen_base.py dcext2,paged2,office2 51,52 > logs/log_broll2.txt 2>&1
echo finished > logs/log_q6.txt
