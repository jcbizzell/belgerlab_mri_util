#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys
import os
import csv
from random import randint
    
# Input 1 is the EPrime text file to split into separate runs
txtfile = sys.argv[1]
fpath = os.path.dirname(txtfile)

# Open the EPrime text file and read through the lines
with open(txtfile, 'r', encoding='utf_16', newline='') as eprimefile:
    for line in eprimefile:
        # Remove unnecessary characters from the line
        line = line.strip()
        print(line)

