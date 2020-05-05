from __future__ import absolute_import
from __future__ import print_function
from __future__ import division

try:
    dummy = profile
except:
    profile = lambda x: x

import os, sys, errno
import argparse
import csv

# Define my own argument parser to change error handling
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def get_subj_demo_from_raw_dir(demo_file, raw_dir, raw_col=0): 
    # Initialize subject demographics
    subj_demo = []
    # Open the demographics CSV file
    try: 
        with open(demo_file, newline='') as csvfile: 
            demos = csv.reader(csvfile, delimiter=',')
            try: 
                # Loop through the demographics
                for row in demos:
                    if row[raw_col-1] in raw_dir or raw_dir in row[raw_col-1]: 
                        # If raw data directory found in demographics file
                        subj_demo = row
                        break
            except csv.Error as e:
                sys.exit('Error - file {}, line {}: {}'.format(demo_file, demos.line_num, e))
            except: 
                sys.exit('Error - invalid demographics CSV file, {}'.format(demo_file))
    except FileNotFoundError as e:
        sys.exit('Error - cannot find demographics file, {}'.format(e))
    if not subj_demo: 
        sys.exit('Error - could not find raw data directory in demographics CSV file: {}'.format(raw_dir))
    return subj_demo

def get_subj_demo_from_subjid_and_visit(demo_file, subjid, visit, subjid_col=0, visit_col=0): 
    # Initialize subject demographics
    subj_demo = []
    # Open the demographics CSV file
    try: 
        with open(demo_file, newline='') as csvfile: 
            demos = csv.reader(csvfile, delimiter=',')
            try: 
                # Loop through the demographics
                for row in demos:
                    if (row[subjid_col-1] == subjid) and (row[visit_col-1] == visit): 
                        # If raw data directory found in demographics file
                        subj_demo = row
                        break
            except csv.Error as e:
                sys.exit('Error - file {}, line {}: {}'.format(demo_file, demos.line_num, e))
            except: 
                sys.exit('Error - invalid demographics CSV file, {}'.format(demo_file))
    except FileNotFoundError as e:
        sys.exit('Error - cannot find demographics file, {}'.format(e))
    if not subj_demo: 
        sys.exit('Error - could not find {} visit {} in demographics CSV file'.format(subjid,visit))
    return subj_demo

def search_replace_in_string(in_string, keyword_dict): 
    out_string = in_string
    for k, v in keyword_dict.items():
        out_string = out_string.replace('{'+k+'}',v)
    return out_string

def create_bids_subj_directory_hierarchy(bidssubjid,visit,bids_roots,bidssubdirs): 
    for dirname in bids_roots:
        for dirname2 in bidssubdirs:
            # Build the directory name
            fulldirname=os.path.join(dirname,bidssubjid,visit,dirname2)
            # Create the directory
            try:  
                os.makedirs(fulldirname)
            except OSError as e: 
                if e.errno == errno.EEXIST and os.path.isdir(fulldirname):
                    pass
                else:
                    raise
