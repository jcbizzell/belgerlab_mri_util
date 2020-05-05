#!/usr/bin/python

import sys, os, argparse, csv
from shutil import copyfile
from subprocess import check_output

from belgerlab_utils import MyParser, get_subj_demo_from_subjid_and_visit, search_replace_in_string

# Setup and get the input arguments
parser = MyParser(description='Add and/or edit an imaging session in the sessions.tsv file')
parser.add_argument("bids_dir", help="BIDS top level directory")
parser.add_argument("demo_file", help="demographics CSV file")
parser.add_argument("template_file", help="BIDS sessions.tsv template CSV file; header row with column number matching that field from demographics CSV")
parser.add_argument("json_file", help="sessions.json file that will be copied with the sessions.tsv")
parser.add_argument("bids_subjid", help="BIDS subject ID")
parser.add_argument("subjid_col", help="BIDS subject ID column in demographics CSV file", nargs='?', type=int, const=0, default=0)
parser.add_argument("visit", help="vist string; ex. ses-baseline")
parser.add_argument("visit_col", help="BIDS visit column in demographics CSV file", nargs='?', type=int, const=0, default=0)
parser.add_argument("-c","--session_col_template", help="BIDS session column in sessions.tsv template CSV file; default 1 (first column)", nargs='?', type=int, const=1, default=1)
parser.add_argument("-s", "--skeleton_dir", help="location of BIDS skeleton directory if saving there as well", nargs='?', type=str)
args = parser.parse_args()

# Create the replacement keyword dict
keywords = {'SUBJ': args.bids_subjid, 'VISIT': args.visit}

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
# Open the sessions.tsv template CSV file
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
                        try: 
                            opts.update( {v : (int(row[k])-1)} )
                        except: 
                            opts.update( {v : row[k]} )
                in_header = False
        except csv.Error as e:
            sys.exit('Error - file {}, line {}: {}'.format(args.template_file, options.line_num, e))
        except Exception as e: 
            sys.exit('Error - invalid sessions.tsv template CSV file: {}, {}'.format(args.template_file, e))
except FileNotFoundError as e:
    sys.exit('Error - cannot find sessions.tsv template CSV file: {}'.format(e))

# Initialize the BIDS directories
bids_roots = [args.bids_dir]
if args.skeleton_dir:
    bids_roots.append(args.skeleton_dir)

# Loop through the BIDS directories
for dirname in bids_roots:
    outtsv = os.path.join(dirname,args.bids_subjid,"sessions.tsv")
    # Copy the session.json file
    try:
        copyfile(args.json_file, os.path.join(dirname,args.bids_subjid,"sessions.json"))
    except IOError as e:
        sys.exit('Error - unable to copy file: {}, {}'.format(args.json_file, e))
    except Exception as e:
        sys.exit('Error - unexpected error: {}'.format(e))
    if os.path.isfile(outtsv):
        # sessions.tsv exists; search for the session
        sessfound = False
        lines = []
        sessline = []
        with open(outtsv) as csv_file:
            csv_reader = csv.reader(csv_file, delimiter='\t')
            for line in csv_reader:
                lines.append(line)
                if line[args.session_col_template-1] == args.visit: 
                    sessfound = True
                    sessline = line
        if not sessfound:
            # If subject not found in sessions.tsv, add the subject
            with open(outtsv, mode='a') as csv_file:
                csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                row = []
                for i in header_row: 
                    try: 
                        row.append(subj_demo[opts.get(i)])
                    except TypeError: 
                        cmd_str = search_replace_in_string(opts.get(i), keywords)
                        try: 
                            row.append(check_output(cmd_str.split()).strip().decode("utf-8"))
                        except: 
                            row.append('N/A')
                csv_writer.writerow(row)
        else: 
            # Find out if the subject demographics are different than what is in sessions.tsv
            rewrite_sess = False
            for k, v in enumerate(header_row): 
                try: 
                    if not subj_demo[opts.get(v)] == sessline[k]: 
                        rewrite_sess = True
                        break
                except: 
                    pass
            if rewrite_sess: 
                # If subject demographics are different, change the sessions.tsv file
                with open(outtsv, mode='w') as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    for line in lines: 
                        if line == sessline: 
                            row = []
                            for i in header_row: 
                                try: 
                                    row.append(subj_demo[opts.get(i)])
                                except TypeError: 
                                    cmd_str = search_replace_in_string(opts.get(i), keywords)
                                    try: 
                                        row.append(check_output(cmd_str.split()).strip().decode("utf-8"))
                                    except: 
                                        row.append('N/A')
                            csv_writer.writerow(row)
                        else: 
                            csv_writer.writerow(line)
    else: 
        # Create new sessions.tsv file and add first subject
        with open(outtsv, mode='w') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(header_row)
            row = []
            for i in header_row: 
                try: 
                    row.append(subj_demo[opts.get(i)])
                except TypeError: 
                    cmd_str = search_replace_in_string(opts.get(i), keywords)
                    try: 
                        row.append(check_output(cmd_str.split()).strip().decode("utf-8"))
                    except: 
                        row.append('N/A')
            csv_writer.writerow(row)

