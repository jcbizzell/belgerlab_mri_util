#!/usr/bin/python

import sys, argparse, os, csv, errno, subprocess

from belgerlab_utils import MyParser, create_bids_subj_directory_hierarchy

# Create recursive function to add "+" to any output that already exists
def check_if_already_converted(outname):
    if os.path.isfile(outname + ".nii.gz"):
        result = outname.find("run-") 
        outname=outname.replace('run-'+outname[result+4], 'run-'+str(int(outname[result+4])+1))
        outname = check_if_already_converted(outname)
    return outname

# Setup and get the input arguments
parser = MyParser(description='Convert raw NII.GZ file to BIDS format')
parser.add_argument("subj_id", help="subject ID in BIDS format (e.g. sub-MA001)")
parser.add_argument("visit", help="session ID in BIDS format (e.g. ses-baseline)")
parser.add_argument("raw_dir", help="raw data directory")
parser.add_argument("in_file", help="input NII.GZ filename")
parser.add_argument("bids_dir", 
    help="output directory; the root folder of a BIDS valid dataset (sub-XXXXX folders should be found at the top level in this folder)")
parser.add_argument("opts_file", help="convert_dcm2niix_to_bids options CSV file")
parser.add_argument("-s", "--series_num", help="add series to output filename; will be put in acq section", nargs='?', type=str, default="N/A")
args = parser.parse_args()

# Initialize some variables
bidssubdirs=["anat", "func", "fmap", "dwi", "beh", "notsupported"]

# Intialize the options dictionary
opts = {'write_skeleton_dir': "FALSE",
    'skeleton_dir_path': "N/A",
    }

# Check to see if the input file exists
# Get the file path and file name
fpath = os.path.dirname(args.in_file)
fname = os.path.basename(args.in_file)
if not fpath: 
    fpath = args.raw_dir
args.in_file = os.path.join(fpath,fname)
if not os.path.isfile(args.in_file): 
    sys.exit('Error - could not find input file: {}'.format(args.in_file))

# Check to see if root BIDS directory exists
if not os.path.isdir(args.bids_dir):
    sys.exit('Error - could not find root BIDS directory: {}'.format(args.bids_dir))

# Initialize the conversion instructions
conv_instruct = []
# Open the convert_rawbxh_to_bids options CSV file
try: 
    with open(args.opts_file, newline='') as csvfile: 
        options = csv.reader(csvfile, delimiter=',')
        try: 
            # Loop through the options file
            for row in options:
                # if len(row) == 5:
                if len(row) == 4:
                    if row[0] in 'series_description' or 'series_description' in row[0]: 
                        conv_instruct.append(row)
                    else: 
                        # See if this option is in opts dictionary defined above and change value if so
                        for k, v in opts.items():
                            if k == row[0]: 
                                opts[k] = row[1]
                                break
        except csv.Error as e:
            sys.exit('Error - file {}, line {}: {}'.format(args.opts_file, options.line_num, e))
        except Exception as e: 
            sys.exit('Error - invalid convert_dcm2niix_to_bids options CSV file: {}, {}'.format(args.opts_file, e))
except FileNotFoundError as e:
    sys.exit('Error - cannot find convert_dcm2niix_to_bids options file: {}'.format(e))

# Initialize root directory(s) & create subject directories
bidssubjid = args.subj_id
visit = args.visit
bids_roots = [args.bids_dir]
if not opts['skeleton_dir_path'] == "N/A":
    bids_roots.append(opts['skeleton_dir_path'])
create_bids_subj_directory_hierarchy(bidssubjid,visit,bids_roots,bidssubdirs)

if args.in_file[-6:] == 'nii.gz': 
    # Get the description from the file name
    fileparts=os.path.basename(args.in_file).split('_')
    imdesc=fileparts[3]
    for s in fileparts[4:]: 
        imdesc=imdesc+"_"+s
    # imdesc = imdesc.replace('.nii.gz','')
else: 
    sys.exit('File format must be NIIGZ: {}'.format(args.in_file))

# Look for the image description in the options file converstion instructions
srs_desc = []
print(imdesc)
for i in conv_instruct: 
    print("  "+i[1])
    # if (imdesc in i[1] or i[1] in imdesc or imdesc in i[1].replace(' ','_') or i[1].replace(' ','_') in imdesc) and (visit in i[3] or i[3] in visit): 
    if imdesc in i[1] or i[1] in imdesc or imdesc in i[1].replace(' ','_') or i[1].replace(' ','_') in imdesc:
        srs_desc = i
        break
if not srs_desc: 
    print('Error - could not find series_description in options file matching: {}, {} {}'.format(imdesc,bidssubjid,visit))
    sys.exit('Error - could not find series_description for visit {} in options file matching: {}'.format(visit,imdesc))

# Create the new output filename
for dirname in bids_roots:
    if args.series_num == "N/A":
        # outname=os.path.join(dirname,bidssubjid,visit,srs_desc[4],srs_desc[2].replace('{SUBJ}',bidssubjid)).replace('{SESS}',visit)
        outname=os.path.join(dirname,bidssubjid,visit,srs_desc[3],srs_desc[2].replace('{SUBJ}',bidssubjid)).replace('{SESS}',visit)
    else:
        # outname=os.path.join(dirname,bidssubjid,visit,srs_desc[4],srs_desc[2].replace('{SUBJ}',bidssubjid).replace('{SESS}',visit).replace('{SRS}',args.series_num))
        outname=os.path.join(dirname,bidssubjid,visit,srs_desc[3],srs_desc[2].replace('{SUBJ}',bidssubjid).replace('{SESS}',visit).replace('{SRS}',args.series_num))
    outname=check_if_already_converted(outname)
    if dirname == opts['skeleton_dir_path']:
        print('Creating skeleton file {}'.format(outname+".nii.gz"))
        thisprocstr = str("touch " + outname + ".nii.gz")
        subprocess.Popen(thisprocstr,shell=True).wait()
    else: 
        if args.in_file[-6:] == 'nii.gz':
            # If the file is NIFTI, rename and/or move file
            print('Renaming and/or moving {} to {}'.format(args.in_file,outname+".nii.gz"))
            os.rename(args.in_file,outname+".nii.gz")
            jsonname=args.in_file.replace('.nii.gz','.json')
            if os.path.isfile(jsonname):
                print('Renaming and/or moving {} to {}'.format(jsonname,outname+'.json'))
                os.rename(jsonname,outname+'.json')
            bvalname=args.in_file.replace('.nii.gz','.bval')
            if os.path.isfile(bvalname):
                print('Renaming and/or moving {} to {}'.format(bvalname,outname+'.bval'))
                os.rename(bvalname,outname+'.bval')
            bvecname=args.in_file.replace('.nii.gz','.bvec')
            if os.path.isfile(bvecname):
                print('Renaming and/or moving {} to {}'.format(bvecname,outname+'.bvec'))
                os.rename(bvecname,outname+'.bvec')



