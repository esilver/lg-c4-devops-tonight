#!/bin/bash
while pgrep -f "queue2.sh|queue3.sh|queue4.sh" > /dev/null; do sleep 5; done
for a in "dee 22" "sunny 23" "mel 21" "cy 24"; do set -- $a; ./venv/bin/python prep.py $1 $2 > log_prep2_$1.txt 2>&1; done
echo finished > log_q5.txt
