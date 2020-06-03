#!/usr/bin/python

import sys, argparse, os, csv, errno, subprocess
import lxml.etree as et

from belgerlab_utils import MyParser, get_subj_demo_from_raw_dir, create_bids_subj_directory_hierarchy

# Create recursive function to add "+" to any output that already exists
def check_if_already_converted(outname):
    if os.path.isfile(outname + ".nii.gz"): 
        outname = outname + "+"
        outname = check_if_already_converted(outname)
    return outname

# Setup and get the input arguments
parser = MyParser(description='Convert raw BXH/NII.GZ file to BIDS format')
parser.add_argument("raw_dir", help="raw data directory")
parser.add_argument("in_file", help="input BXH/NII.GZ filename")
parser.add_argument("bids_dir", 
    help="output directory; the root folder of a BIDS valid dataset (sub-XXXXX folders should be found at the top level in this folder)")
parser.add_argument("demo_file", help="demographics CSV file")
parser.add_argument("opts_file", help="convert_rawbxh_to_bids options CSV file")
# parser.add_argument("-d", "--add_date", help="add date and time to output filename", action="store_true")
args = parser.parse_args()

# Initialize some variables
bidssubdirs=["anat", "func", "fmap", "dwi", "beh", "notsupported"]
nspace={'b': 'http://www.biac.duke.edu/bxh'}

# Intialize the options dictionary
opts = {'demographics_rawdatadir_column': -1, 
    'demographics_subjid_column': -1,
    'demographics_bidssubjid_column': -1, 
    'demographics_rawdatadir_column': -1,
    'demographics_scandate_column': -1,
    'demographics_visit_column': -1,
    'demographics_group_column': -1,
    'demographics_gender_column': -1,
    'demographics_agemonths_column': -1,
    'write_skeleton_dir': "FALSE",
    'skeleton_dir_path': "N/A",
    'bxh_tools_path': None,
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
        except: 
            sys.exit('Error - invalid convert_rawbxh_to_bids options CSV file: {}'.format(args.opts_file))
except FileNotFoundError as e:
    sys.exit('Error - cannot find convert_rawbxh_to_bids options file: {}'.format(e))

# Get the subject's specific session demographics
try: 
    subj_demo = get_subj_demo_from_raw_dir(args.demo_file, args.raw_dir, int(opts['demographics_rawdatadir_column']))
except Exception as e: 
    sys.exit('Error - {}'.format(e))

# Initialize root directory(s) & create subject directories
bidssubjid = subj_demo[int(opts['demographics_bidssubjid_column'])-1]
visit = subj_demo[int(opts['demographics_visit_column'])-1]
bids_roots = [args.bids_dir]
if not opts['skeleton_dir_path'] == "N/A":
    bids_roots.append(opts['skeleton_dir_path'])
create_bids_subj_directory_hierarchy(bidssubjid,visit,bids_roots,bidssubdirs)

if args.in_file[-3:] == 'bxh': 
    # Read the BXH file using XML parser
    doc = et.parse(args.in_file)
    root = doc.getroot()
    datarec = root.find('b:datarec',namespaces=nspace)
    acqelem = root.find('b:acquisitiondata', namespaces=nspace)
    # Get the description from the acquisition elements
    imdesc=acqelem.findtext('b:description',namespaces=nspace)
    # TODO: if file has .nii.gz with is, change args.infile to name of NIFTI file
elif args.in_file[-6:] == 'nii.gz': 
    # Get the description from the file name
    fileparts=os.path.basename(args.in_file).split('---')
    imdesc=fileparts[3]
    for s in fileparts[4:]: 
        imdesc=imdesc+"_"+s
    imdesc = imdesc.replace('.nii.gz','')
else: 
    sys.exit('File format must be BXH or NIIGZ: {}'.format(args.in_file))

# Look for the image description in the options file converstion instructions
srs_desc = []
for i in conv_instruct: 
    if (imdesc in i[1] or i[1] in imdesc or imdesc in i[1].replace(' ','_') or i[1].replace(' ','_') in imdesc) and (visit in i[3] or i[3] in visit): 
        srs_desc = i
        break
if not srs_desc: 
    sys.exit('Error - could not find series_description vor vist {} in options file matching: {}'.format(visit,imdesc))

# Create the new output filename
for dirname in bids_roots:
    outname=os.path.join(dirname,bidssubjid,visit,srs_desc[4],srs_desc[2].replace('{SUBJ}',bidssubjid))
    outname=check_if_already_converted(outname)
    if dirname == opts['skeleton_dir_path']:
        print('Creating skeleton file {}'.format(outname+".nii.gz"))
        thisprocstr = str("touch " + outname + ".nii.gz")
        subprocess.Popen(thisprocstr,shell=True).wait()
    else: 
        if args.in_file[-3:] == 'bxh':
            # If the file is a BXH file, convert using BXH tools
            print('Converting {} to {}'.format(args.in_file,outname+".nii.gz"))
            bxh2analyzestr = "bxh2analyze"
            if not opts['bxh_tools_path'] == None: 
                bxh2analyzestr = os.path.join(opts['bxh_tools_path'],"bxh2analyze")
            try: 
                thisprocstr = str(bxh2analyzestr + " --niigz -s " + args.in_file + " " + outname)
                subprocess.Popen(thisprocstr,shell=True).wait()
            except Exception as e: 
                sys.exit('Error - could not convert BXH file to NIFTI: {}, {}'.format(args.in_file,e))
            try: 
                thisprocstr = str("bxh2json -i " + outname + ".bxh")
                subprocess.Popen(thisprocstr,shell=True).wait()
            except Exception as e:
                print('Warning - could not create JSON from: {}, {}'.format(args.in_file,e))
        elif args.in_file[-6:] == 'nii.gz':
            # If the file is NIFTI, rename and/or move file
            # TODO: If file has .bxh header already, move .bxh file as well
            print('Renaming and/or moving {} to {}'.format(args.in_file,outname+".nii.gz"))
            os.rename(args.in_file,outname+".nii.gz")
            # Create BXH file
            analyze2bxhstr = "analyze2bxh"
            if not opts['bxh_tools_path'] == None: 
                analyze2bxhstr = os.path.join(opts['bxh_tools_path'],"analyze2bxh")
            try: 
                thisprocstr = str(analyze2bxhstr + " " + outname + ".nii.gz " + outname + ".bxh")
                subprocess.Popen(thisprocstr,shell=True).wait()
            except Exception as e:
                print('Warning - could not create BXH from: {}, {}'.format(outname+".nii.gz",e))
            jsonname=args.in_file.replace('.nii.gz','.json')
            if os.path.isfile(jsonname):
                print('Renaming and/or moving {} to {}'.format(jsonname,outname+'.json'))
                os.rename(jsonname,outname+'.json')



