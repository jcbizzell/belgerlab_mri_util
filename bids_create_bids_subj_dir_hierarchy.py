#!/usr/bin/python

from belgerlab_utils import MyParser, create_bids_subj_directory_hierarchy

# Setup and get the input arguments
parser = MyParser(description='Create an empty BIDS subject directory hierarchy')
parser.add_argument("bids_dir", help="BIDS top level directory")
parser.add_argument("bids_subjid", help="BIDS subject ID")
parser.add_argument("visit", help="vist string; ex. ses-baseline")
args = parser.parse_args()

# Initialize some variables
bidssubdirs=["anat", "func", "fmap", "dwi", "beh", "notsupported"]

# Create the empty directory
create_bids_subj_directory_hierarchy(args.bids_subjid,args.visit,[args.bids_dir],bidssubdirs)
