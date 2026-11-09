#!/bin/bash
while pgrep -f queue1.sh > /dev/null; do sleep 5; done
for a in "dee 22" "sunny 23" "mel 21" "paige 21"; do set -- $a; ./venv/bin/python prep.py $1 $2 > log_prep_$1.txt 2>&1; done
