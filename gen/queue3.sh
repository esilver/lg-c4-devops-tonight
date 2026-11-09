#!/bin/bash
while pgrep -f queue2.sh > /dev/null; do sleep 5; done
./venv/bin/python prep.py cy 24 > log_prep_cy.txt 2>&1
