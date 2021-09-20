#!/usr/bin/python

import sys, os, argparse

from belgerlab_utils import MyParser

# Setup and get the input arguments
parser = MyParser(description='Zero-pad the series and acquisition numbers to make listing chronological')
parser.add_argument("infile", help="input filename to zero-pad")
parser.add_argument("-s", "--srspad", help="how many digits for series number; default 3", nargs='?', type=int, const=3, default=3)
parser.add_argument("-a", "--acqpad", help="how many digits for acquisition number; default 3", nargs='?', type=int, const=3, default=3)
args = parser.parse_args()

# Get the file path and file name
fpath = os.path.dirname(args.infile)
fname = os.path.basename(args.infile)
fileparts = fname.split('_')
# Add zeros in front of series and acquisition 
fileparts[0]=fileparts[0].zfill(args.srspad)
fileparts[1]=fileparts[1].zfill(args.acqpad)
newfile=fileparts[0]
for s in fileparts[1:]: 
    newfile=newfile+"_"+s
os.rename(args.infile,os.path.join(fpath,newfile))
