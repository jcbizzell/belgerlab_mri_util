#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys, argparse
import os
import csv
from random import randint

from belgerlab_utils import MyParser

# Sub-function to print a list to a file
def writelisttofile(writelines, outfile):
    for i, key in enumerate(writelines):
        outfile.write(key+'\r\n')

# Setup and get the input arguments
parser = MyParser(description='Split multi-run EPrime behavioral file into separate run files')
parser.add_argument("eprime_txt", help="eprime output behavioral file you want to split")
parser.add_argument("instruct_file", help="instructions file that describes the start of a run")
args = parser.parse_args()
    
# Input 1 is the EPrime text file to split into separate runs
txtfile = args.eprime_txt
fpath = os.path.dirname(txtfile)
# Input 2 is the instructions file that tells the first few lines of a new run
instructfile = args.instruct_file

# Add the instruction start lines to a list
splitinstructions=[]
startlines = []
diffinstructperrun = False
prevrun = "All"
firstrun = True
with open(instructfile, newline='') as csvfile: 
    instructions = csv.reader(csvfile, delimiter=',')
    for line in instructions:
        if line[0] != "EPRIME_LINE_TEXT": 
            # print(line)
            # print(splitinstructions)
            if line[1] != "All": 
                diffinstructperrun = True
            if line[1] != prevrun:
                if not firstrun: 
                    splitinstructions.append(startlines)
                    startlines = []
                    startlines.append(line)
                else: 
                    startlines.append(line)
                firstrun = False
            else: 
                startlines.append(line)
            prevrun=line[1]
    splitinstructions.append(startlines)

# Initialize some variables
rndsuff = randint(1000,9999)
f_hdr = open(os.path.join(fpath,"tmpeprimehdr_"+str(rndsuff)+".txt"),"w+")
runcnt = 0
writehdr = False
writefile = False
instart = False
startlines = splitinstructions[0]
startline = startlines[0][0]
startcnt = 0
writelines = []  # This list will temporarily store the lines read that look like run start lines

# Open the EPrime text file and read through the lines
with open(txtfile, 'r', encoding='utf_16', newline='') as eprimefile:
    for line in eprimefile:
        # Remove unnecessary characters from the line
        line = line.strip()
        if writehdr: 
            f_hdr.write(line+'\r\n')
        if line == "*** Header Start ***":
            writehdr = True
            f_hdr.write(line+'\r\n')
        if line == "*** Header End ***":
            writehdr = False
        if instart: 
            if line in startline: 
                # If you've reached the last of the run start lines defined in the instructions
                if startcnt == len(startlines)-1:
                    # print(writelines)
                    try: 
                        outfile.close()
                    except NameError: 
                        pass
                    outfile = open(os.path.join(fpath,"tmpeprimerun"+str(runcnt)+"_"+str(rndsuff)+".txt"),"w+")
                    # print(writelines)
                    # Start lines were not written to output file; write them all now
                    writelisttofile(writelines, outfile)
                    # Reset some variables; increment run count
                    runcnt += 1
                    startcnt = 0
                    if diffinstructperrun and runcnt < len(splitinstructions): 
                        startlines = splitinstructions[runcnt]
                    startline=startlines[startcnt][0]
                    instart = False
                    writelines=[]
                    writefile = True
                # Still in the run start lines defined in the instructions
                else: 
                    writelines.append(line)
                    startcnt += 1
                    startline=startlines[startcnt][0]
            # Didn't make it to the end of the run start lines defined in the instructions
            else: 
                # print(writelines)
                # Start lines were not written to output file; write them all now
                writelisttofile(writelines, outfile)
                # Reset some variables
                startcnt = 0
                startline=startlines[startcnt][0]
                instart = False
                writelines = []
                writefile = True
        # Found the first of the run start lines defined in the instructions
        if not instart:
            if line in startline: 
                writelines.append(line)
                instart = True
                startcnt += 1
                startline=startlines[startcnt][0]
                writefile = False
        if writefile: 
            # print(line)
            outfile.write(line+'\r\n')

# Close the open files
f_hdr.close()
outfile.close()


