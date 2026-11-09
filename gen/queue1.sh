#!/bin/bash
./venv/bin/python prep.py paige 21 > log_prep_paige.txt 2>&1
./venv/bin/python gen_base.py cy2 31,32,33,34,35,36 > log_cy2.txt 2>&1
./venv/bin/python gen_base.py studio,servers,dcext,office,paged,sat 41,42 > log_broll.txt 2>&1
