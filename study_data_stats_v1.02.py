#!/usr/bin/python

import os, csv, collections, glob, subprocess
import numpy as np

# ------------------
# Change items below
# ------------------

# What is the base experiment directory 
exppath = "/proj/belgerlab/projects/Cognit_MRI"
# Load and read the demographics file
demofile = open(os.path.join(exppath,"Notes","demographics.csv"),"r")
demos = csv.reader(demofile, delimiter = ',')
# Which columns in the demographics file represents subject id, group id, 
# gender, age and visit number
bidsid_col=14
subjid2_col=1
scanid_col=2
group_col=5
gender_col=4
age_col=6
visit_col=12

# Tuple collection of strings that describe subject types (1,2,3,etc....)
subj_types=("control","mid-risk","high-risk")
# Tuple collection of strings that describe visit names
visit_desc=("ses-baseline","ses-followup01")
gender_types=('M','F')

# Load and read the study instructions file
instructfile = open(os.path.join(exppath,"Scripts","bin","study_instructions_longleaf.csv"),"r")
instructions = csv.reader(instructfile, delimiter = ',')

# ------------------------------------
# Shouldn't need to change items below
# ------------------------------------

def python_grep(search_path,file_type,search_str):
    # Initialize output list
    output_list = []
    
    # Append a directory separator if not already present
    if not (search_path.endswith("/") or search_path.endswith("\\") ): 
            search_path = search_path + "/"
                                                              
    # If path does not exist, set search path to current directory
    if not os.path.exists(search_path):
            search_path ="."

    # Repeat for each file in the directory  
    for fname in os.listdir(search_path):
       # Apply file type filter   
       if fname.endswith(file_type):
            # Run subprocess grep to find string in file
            try: 
                p=subprocess.check_output(['/bin/grep',search_str,search_path + fname])
                output_list.append(fname)
            except: 
                pass
            # Open file for reading
            # fo = open(search_path + fname)
            # Read the first line from the file
            # line = fo.readline()
            # Initialize counter for line number
            # line_no = 1
            # Loop until EOF
            # while line != '' :
                    # Search for string in line
                    # index = line.find(search_str)
                    # if ( index != -1) :
                        # print(fname, "[", line_no, ",", index, "] ", line, sep="")
                        # print(fname,line_no,index,line)
                        # output_list.append(fname)
                    # Read next line
                    # line = fo.readline()  
                    # Increment line counter
                    # line_no += 1
            # Close the files
            # fo.close()
    return output_list
    
def python_file_pattern(search_path,search_str):
    # Initialize output list
    output_list = []
    
    # Append a directory separator if not already present
    if not (search_path.endswith("/") or search_path.endswith("\\") ): 
            search_path = search_path + "/"
                                                              
    # If path does not exist, set search path to current directory
    if not os.path.exists(search_path):
            search_path ="."

    output_list += glob.glob(search_path + search_str)
    return output_list

all_subj=[]
unique_subj=[]
all_subjid2=[]
all_gender = []
all_group = []
all_ages=[]
all_visit=[]
all_scanid=[]

# Loop through demographics file initializing variables
for row in demos:
    # If not the first row in the demographics file
    if row[0] != "SUBJ_ID":
        all_subj.append(row[bidsid_col-1])
        # Add bidsid to unique_subj if not there
        if row[bidsid_col-1] not in unique_subj: 
            unique_subj.append(row[bidsid_col-1])
        all_subjid2.append(row[subjid2_col-1])
        all_gender.append(row[gender_col-1])
        all_group.append(row[group_col-1])
        all_ages.append(row[age_col-1])
        all_visit.append(row[visit_col-1])
        all_scanid.append(row[scanid_col-1])
    
# Sort the unique subject list alphabetically
unique_subj.sort()

# Print to the screen the macro demographic stats
print("OVERALL DEMOGRAPHICS")
print("  Number of unique subjects: "+str(len(unique_subj)))
for i, elem in enumerate(subj_types): 
    if i == 0: 
        outstr=elem
    else: 
        outstr=outstr+", "+elem
print("  Number of unique groups: "+str(len(subj_types))+" -- "+outstr)
print("  Number of total visits: "+str(len(all_subj)))
visit_counter=collections.Counter(all_visit)
for i, elem in enumerate(visit_desc): 
    print("  Number of visits "+elem+": "+str(visit_counter.get(str(i+1))))

print("\nGROUP DEMOGRAPHICS")
print("  VISIT: all sessions combined")
counter=collections.Counter(all_group)
for i, elem in enumerate(subj_types):
    if i == 0: 
        outstr="    Group counts (all visits) -- "+elem+": "+str(counter.get(str(i+1)))
    else: 
        outstr=outstr+", "+elem+": "+str(counter.get(str(i+1)))
print(outstr)
counter=collections.Counter(all_gender)
for i, elem in enumerate(gender_types):
    if i == 0: 
        outstr="    Gender counts (all visits) -- "+elem+": "+str(counter.get(elem))
    else: 
        outstr=outstr+", "+elem+": "+str(counter.get(elem))
print(outstr)
if np.array(all_ages).size != 0:
    all_ages_np=np.genfromtxt(np.array(all_ages))
    print("    Age statistics (all visits) -- "+"Mean: "+str(round(np.nanmean(all_ages_np),2))+" months, StdDev: "+ \
        str(round(np.nanstd(all_ages_np),2))+", Min: "+str(round(np.nanmin(all_ages_np)))+", Max: "+ \
        str(round(np.nanmax(all_ages_np))))
else: 
    print("    Age statistics (all visits) -- None")
for i, elem in enumerate(visit_desc): 
    print("  VISIT: "+elem)
    grp_data=[[] for j in range(len(subj_types))]
    sex_data=[[] for j in range(len(subj_types))]
    age_data=[[] for j in range(len(subj_types))]
    for s, subj in enumerate(all_subj):
        if int(all_visit[s]) == (i+1): 
            try: 
                grp_idx=int(all_group[s])-1 
                grp_data[grp_idx].append(grp_idx+1)
                sex_data[grp_idx].append(all_gender[s])
                age_data[grp_idx].append(all_ages[s])
            except ValueError: 
                pass
    counter=collections.Counter([item for sublist in grp_data for item in sublist])
    for j, elem2 in enumerate(subj_types):
        if j == 0: 
            outstr="    Group counts -- "+elem2+": "+str(counter.get(j+1))
        else: 
            outstr=outstr+", "+elem2+": "+str(counter.get(j+1))
    print(outstr)
    counter=collections.Counter([item for sublist in sex_data for item in sublist])
    for j, elem2 in enumerate(gender_types):
        if j == 0: 
            outstr="    Gender counts -- "+elem2+": "+str(counter.get(elem2))
        else: 
            outstr=outstr+", "+elem2+": "+str(counter.get(elem2))
    print(outstr)
    if np.array(age_data[j]).size != 0:
        all_ages_np=np.genfromtxt(np.array([item for sublist in age_data for item in sublist]))
        print("    Age statistics -- "+"Mean: "+str(round(np.nanmean(all_ages_np),2))+" months, StdDev: "+ \
            str(round(np.nanstd(all_ages_np),2))+", Min: "+str(round(np.nanmin(all_ages_np)))+ ", Max: "+ \
            str(round(np.nanmax(all_ages_np))))
    else: 
        print("    Age statistics -- None")             
    for j, elem2 in enumerate(subj_types):
        counter=collections.Counter(sex_data[j])
        for k, elem3 in enumerate(gender_types):
            if k == 0: 
                outstr="    Gender counts ("+elem2+") -- "+elem3+": "+str(counter.get(elem3))
            else: 
                outstr=outstr+", "+elem3+": "+str(counter.get(elem3))
        print(outstr)
        if np.array(age_data[j]).size != 0: 
            all_ages_np=np.genfromtxt(np.array(age_data[j]))
            print("    Age statistics ("+elem2+") -- "+"Mean: "+str(round(np.nanmean(all_ages_np),2))+" months, StdDev: "+ \
                str(round(np.nanstd(all_ages_np),2))+", Min: "+str(np.nanmin(all_ages_np))+", Max: "+str(np.nanmax(all_ages_np)))
        else: 
            print("    Age statistics ("+elem2+") -- None")         

for row in instructions:
    # If not the first row in the demographics file
    if row[0] != "SCREEN PRINT STRING":
        # print(row)
        # print(visit_counter)
        if row[1] == "HEADING":
            print("\n"+" "*int(row[4])+row[0])
        elif row[1] == "PRINT":
            print("\n"+" "*int(row[4])+row[0])
        else:
            subj_count=0
            none_str=""
            missing_str=""
            multiple_str=""
            cmd_str=row[1]
            for i, elem in enumerate(unique_subj):
                for j, SUBJ in enumerate(all_subj): 
                    if elem == SUBJ and row[2] == all_visit[j]: 
                        # print("Found "+SUBJ+" visit "+all_visit[j])
                        new_cmd_str = cmd_str.replace("EXPERIMENT",exppath)
                        new_cmd_str = new_cmd_str.replace("SCANID",all_scanid[j])
                        new_cmd_str = new_cmd_str.replace("SUBJID2",all_subjid2[j])
                        new_cmd_str = new_cmd_str.replace("SUBJID",all_subj[j])
                        # print(new_cmd_str)
                        exec(new_cmd_str)
                        if row[5] == "SEARCH": 
                            # If no files found with grep string
                            if A == []: 
                                if none_str == "": 
                                    none_str = elem[-3:]
                                else: 
                                    none_str = none_str + ", " + elem[-3:]
                            else: 
                                # Files were found with grep string
                                subj_count += 1
                                if len(A) > int(row[3]):
                                    if multiple_str == "": 
                                        multiple_str = elem[-3:]
                                    else: 
                                        multiple_str = multiple_str + ", " + elem[-3:]
                                if len(A) < int(row[3]) and A != []:
                                    if missing_str == "": 
                                        missing_str = elem[-3:]
                                    else: 
                                        missing_str = missing_str + ", " + elem[-3:]
            if row[5] == "PRINT":
                print(" "*int(row[4])+row[0]+": "+str(A))
            if row[5] == "SEARCH": 
                if subj_count > 0: 
                    outstr=str(subj_count)
                    if none_str != "": 
                        outstr=outstr+"  -- Subjects with none: "+none_str
                    if missing_str != "":
                        outstr=outstr+" -- Subjects with one or more missing: "+missing_str                     
                    if multiple_str != "":
                        outstr=outstr+" -- Subjects with extra: "+multiple_str
                else: 
                    outstr="None"
                print(" "*int(row[4])+row[0]+": "+outstr)
        
        
        
        
