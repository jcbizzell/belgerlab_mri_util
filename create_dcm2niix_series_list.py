#!/usr/bin/python

import sys, argparse, os, csv, errno

from belgerlab_utils import MyParser

# Setup and get the input arguments
parser = MyParser(description='Create/append dcm2niix series info CSV file')
parser.add_argument("raw_dir", help="raw data directory")
parser.add_argument("list_file", help="series list CSV file")
parser.add_argument("subj_id", help="BIDS subject ID")
parser.add_argument("sess", help="BIDS session")
args = parser.parse_args()

# Check to see if the raw directory exists
if not os.path.isdir(args.raw_dir): 
    sys.exit('Error - could not find raw data directory: {}'.format(args.raw_dir))

# Loop through the NIFTI files in the raw data directory
for fname in sorted(os.listdir(args.raw_dir)):
    if fname.endswith('.nii.gz'):

        # Initialize the series list
        series_list = []
        # Open the series list CSV file
        try: 
            with open(args.list_file, newline='') as csvfile: 
                series = csv.reader(csvfile, delimiter=',')
                try: 
                    # Loop through the series list CSV file
                    for row in series:
                        series_list.append(row)
                except csv.Error as e:
                    sys.exit('Error - file {}, line {}: {}'.format(args.list_file, series.line_num, e))
                except Exception as e: 
                    sys.exit('Error - invalid convert_dcm2niix_to_bids options CSV file: {}, {}'.format(args.list_file, e))
        except FileNotFoundError as e:
            sys.exit('Error - cannot find series list CSV file: {}'.format(e))

        # Get the description from the file name
        fileparts=os.path.basename(fname).split('_')
        imdesc=fileparts[3]
        for s in fileparts[4:]: 
            imdesc=imdesc+"_"+s
        imdesc = imdesc.replace('.nii.gz','')

        # Look for the image description in the series list
        series_found = False
        for i in series_list:
            if i[0] == imdesc:
                series_found = True
                break
        
        # If image description not in list, add it to series list CSV
        if not series_found:
            print('Writing {} to {} for {} {}'.format(imdesc,args.list_file,args.subj_id,args.sess))
            with open(args.list_file, 'a', newline='') as csvfile:
                series = csv.writer(csvfile)
                series.writerow([imdesc])
                csvfile.close()
