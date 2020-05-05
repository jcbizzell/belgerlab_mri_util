#!/usr/bin/python

import sys, os, argparse, json, subprocess
from datetime import datetime

from belgerlab_utils import MyParser

# Setup and get the input arguments
parser = MyParser(description='Find the acquistion time of an imaging series and write to file if it is the first series')
parser.add_argument("in_file", help="input file describing the imaging series; BXH or BIDS JSON")
parser.add_argument("time_file", help="file where the time of scan will be saved")
args = parser.parse_args()

# Check to see if input file exists
if not os.path.isfile(args.in_file): 
    sys.exit('Error - could not find input file: {}'.format(args.in_file))

# Find the previous "first" series time if the file exists
oldtime=''
if os.path.isfile(args.time_file):
    with open(args.time_file, 'r', newline='') as timefile:
        for line in timefile: 
            oldtime = line.strip()
    # NOTE: might need to change this; go here: https://strftime.org/
    oldtime=datetime.strptime(oldtime, '%H:%M:%S.%f')

# Find the acquisition time from JSON or BXH file
if args.in_file.endswith('.json'): 
    jsonFile = open(args.in_file, 'r')
    values = json.load(jsonFile)
    jsonFile.close()
    time_field = 'AcquisitionTime'
elif args.in_file.endswith('.bxh'):
    # Need to write this part
    pass
else: 
    sys.exit('Error - Must be BXH or JSON file. Do not know how to handle {}'.format(args.in_file))
srs_time = values.get(time_field)

if srs_time: 
    # Compare this series acquistion time to previously saved time and re-write if its older
    srs_time=datetime.strptime(srs_time, '%H:%M:%S.%f')
    if oldtime == '' or srs_time < oldtime:
        print('Writing first series time file {}'.format(args.time_file))
        thisprocstr = str("echo " + srs_time.strftime('%H:%M:%S.%f') + " > " + args.time_file)
        subprocess.Popen(thisprocstr,shell=True).wait()
else: 
    sys.exit('Error - Could not find acquistion time field in {}'.format(args.in_file))
