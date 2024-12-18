#!/bin/bash
# start.sh

python3 /home/vladymir/bi/batterindicator.py -k -p &
sleep 1
python3 /home/vladymir/bi/batterindicator.py -m -p &
