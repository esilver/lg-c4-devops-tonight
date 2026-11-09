#!/bin/bash
while pgrep -f "queue2.sh|queue3.sh" > /dev/null; do sleep 5; done
./venv/bin/python stills.py studio=41 servers=41 dcext=41 office=41 paged=41 sat=41 > log_stills.txt 2>&1
./venv2/bin/python matte_onnx.py birefnet work/dee/frame.png work/dee/alpha.png work/sunny/frame.png work/sunny/alpha.png work/mel/frame.png work/mel/alpha.png work/cy/frame.png work/cy/alpha.png > log_matte.txt 2>&1
echo finished > log_q4.txt
