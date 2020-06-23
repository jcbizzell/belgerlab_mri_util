#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys, os, csv
import lxml.etree as et

# More info here: https://bids-specification.readthedocs.io/en/latest/04-modality-specific-files/05-task-events.html
# And here: https://bids-specification.readthedocs.io/en/latest/04-modality-specific-files/07-behavioral-experiments.html

from belgerlab_utils import MyParser

def convert_to_seconds(text_value, units): 
    out_value = text_value
    if units == 'msec': 
        out_value = str(float(text_value)/1000)
    return out_value

# Setup and get the input arguments
parser = MyParser(description='Convert STF behavioral folder to BIDS format xxxx_events.tsv')
parser.add_argument("stf_dir", help="folder name of with the STF files to convert")
parser.add_argument("out_tsv", help="filename of the output xxxx_events.tsv file")
args = parser.parse_args()

# Initialize some variables
header_row = ['onset','duration','trial_type']

try: 
    allevents=[]
    # print(os.path.join(behavpath2,row[0],e[10]))
    for count_b, fname_b in enumerate(sorted(os.listdir(args.stf_dir)), start=1):
        if fname_b.endswith(".stf"):
            with open(os.path.join(args.stf_dir,fname_b)) as tsv: 
                for line in csv.reader(tsv, delimiter="\t"): 
                    if len(line) == 1:
                        line = line[0].split()
                    allevents.append([float(line[0]),float(line[1]),fname_b[:-4]])
    if len(allevents) > 0: 
        # print(outnamebids+"_events.tsv")
        # Open the events tsv file
        outputtsv = args.out_tsv
        outputtsv = open(outputtsv,'w+')
        # Write the header
        outputtsv.write('onset\tduration\ttrial_type\n')
        for i in sorted(allevents): 
            #print(i)
            outputtsv.write(str(i[0])+'\t'+str(i[1])+'\t'+i[2]+'\n')
        # Close the events tsv file
        outputtsv.close()
except OSError: 
    pass