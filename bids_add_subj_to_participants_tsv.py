#!/usr/bin/python

import sys, os, argparse, csv

from belgerlab_utils import MyParser, get_subj_demo_from_subjid_and_visit

# Setup and get the input arguments
parser = MyParser(description='Add and/or edit a BIDS subject in the participants.tsv file')
parser.add_argument("bids_dir", help="BIDS top level directory")
parser.add_argument("demo_file", help="demographics CSV file")
parser.add_argument("template_file", help="BIDS participants.tsv template CSV file; header row with column number matching that field from demographics CSV")
parser.add_argument("bids_subjid", help="BIDS subject ID")
parser.add_argument("subjid_col", help="BIDS subject ID column in demographics CSV file", nargs='?', type=int, const=0, default=0)
parser.add_argument("visit", help="vist string; ex. ses-baseline")
parser.add_argument("visit_col", help="BIDS visit column in demographics CSV file", nargs='?', type=int, const=0, default=0)
parser.add_argument("-c","--subjid_col_template", help="BIDS subject ID column in participants.tsv template CSV file; default 1 (first column)", nargs='?', type=int, const=1, default=1)
parser.add_argument("-s", "--skeleton_dir", help="location of BIDS skeleton directory if saving there as well", nargs='?', type=str)
args = parser.parse_args()

# Get the subject's specific session demographics
subj_demo = []
try: 
    subj_demo = get_subj_demo_from_subjid_and_visit(args.demo_file, args.bids_subjid, args.visit, args.subjid_col, args.visit_col)
except Exception as e: 
    sys.exit('Error - {}'.format(e))

# Initialize the template options
opts = {}
in_header = True
header_row = []
# Open the participants.tsv template CSV file
try: 
    with open(args.template_file, newline='') as csvfile: 
        options = csv.reader(csvfile, delimiter=',')
        try: 
            # Loop through the template file
            for row in options:
                if in_header: 
                    header_row = row
                else: 
                    for k, v in enumerate(header_row): 
                        opts.update( {v : (int(row[k])-1)} )
                in_header = False
        except csv.Error as e:
            sys.exit('Error - file {}, line {}: {}'.format(args.template_file, options.line_num, e))
        except Exception as e: 
            sys.exit('Error - invalid participants.tsv template CSV file: {}, {}'.format(args.template_file, e))
except FileNotFoundError as e:
    sys.exit('Error - cannot find participants.tsv template CSV file: {}'.format(e))

# Initialize the BIDS directories
bids_roots = [args.bids_dir]
if args.skeleton_dir:
    bids_roots.append(args.skeleton_dir)

# Loop through the BIDS directories
for dirname in bids_roots:
    outtsv = os.path.join(dirname,"participants.tsv")
    if os.path.isfile(outtsv):
        # participants.tsv exists; search for the subject
        subjfound = False
        lines = []
        subjline = []
        with open(outtsv) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            for line in csv_reader:
                lines.append(line)
                if line[args.subjid_col_template-1] == args.bids_subjid: 
                    subjfound = True
                    subjline = line
        if not subjfound:
            # If subject not found in participants.tsv, add the subject
            with open(outtsv, mode='a') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                row = []
                for i in header_row: 
                    row.append(subj_demo[opts.get(i)])
                csv_writer.writerow(row)
        else: 
            # Find out if the subject demographics are different than what is in participants.tsv
            rewrite_subj = False
            for k, v in enumerate(header_row): 
                if not subj_demo[opts.get(v)] == subjline[k]: 
                    rewrite_subj = True
                    break
            if rewrite_subj: 
                # If subject demographics are different, change the participants.tsv file
                with open(outtsv, mode='w') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    for line in lines: 
                        if line == subjline: 
                            row = []
                            for i in header_row: 
                                row.append(subj_demo[opts.get(i)])
                            csv_writer.writerow(row)
                        else: 
                            csv_writer.writerow(line)
    else: 
        # Create new participants.tsv file and add first subject
        with open(outtsv, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header_row)
            row = []
            for i in header_row: 
                row.append(subj_demo[opts.get(i)])
            csv_writer.writerow(row)

