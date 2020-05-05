#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

import sys
import errno
import os
import subprocess
import csv
import calendar
from datetime import datetime
import re
import lxml.etree as ET
import json
import shutil

# ------------------
# Change items below
# ------------------

# What is the base directory where the scan list, demographics and output .csv template will be located
exppath = "/mnt/BIAC/munin.dhe.duke.edu/Belger/ADOLSTRESS.01"
# What is the full file name of the scan directory list; this also reads that file
scanlist = csv.reader(open(os.path.join(exppath,"Scripts","BIDS_conversion","scan_dir_list.csv"),"rb"),delimiter=",")
# Load and read the demographics file
demofile = open(os.path.join(exppath,"Notes","demographics.csv"),"rb")
demos = csv.reader(demofile, delimiter = ',')
# Where is the behavioral data stored?
behavpath=os.path.join(exppath,"Data","Behav")
# Load and read the experiments description file
expfile = open(os.path.join(exppath,"Scripts","NDAR_Upload","adolstress01_experiment_list.csv"),"rb")
exps = csv.reader(expfile, delimiter = ',')
# Where is the sessions description json file
sessjson=os.path.join(exppath,"Scripts","BIDS_conversion","sessions.json")
# What is the name of the output TSV
# outtsv = "series_order_note.tsv"
# Where should the BIDS data be saved?
bidspath=os.path.join(exppath,"Analysis","BIDS_Cognit","BIDS_Data")
# Where is the BIDS skeleton folder?
skeletonpath=os.path.join(exppath,"Analysis","BIDS_Cognit","Skeleton")
# Which image series BXH "descriptions" should be included
funclist = ['sensespiral fMRI','Sag 2sh-MB resting fMRI']
dtilist = ['Ax DTI']
#anatlist = ['SC:Ax FSPGR 3D','3 plane loc ssfse','Ax T2 / PD FRFSE','average dc','fractional aniso.','isotropic image','Ax FSPGR 3D']
anatlist = ['SC:Ax FSPGR 3D','Ax T2 / PD FRFSE']
firstscan = ['3 plane loc ssfse']

# ---------------------------
# Possibly change items below
# (Advanced settings)
# ---------------------------

# List of all of the element names in the output tsv file
series_order_elements=['image_file','experiment_description']

# Write just the skeleton files (0: no, 1: yes)
writeskeleton=0

# ------------------------------------
# Shouldn't need to change items below
# ------------------------------------

# Create a function to convert day number in a year to months in that year/round up if day in last half of month
def daynum_to_date(year, daynum):
	month = 1
	day = daynum
	while month < 13:
		month_days = calendar.monthrange(year, month)[1]
		if day <= month_days:
			if day <= month_days/2:
				return month
			else: 
				return (month+1)
		day -= month_days
		month += 1
	raise ValueError('{} does not have {} days'.format(year, daynum))
	
def copy_skeleton_dir(srcdir, destdir):
	thisprocstr = str("cp -R " + srcdir + " " + destdir)
	subprocess.Popen(thisprocstr,shell=True).wait()

# Initialize other variables
nspace={'b': 'http://www.biac.duke.edu/bxh'}
# Make all values in include lists lowercase
funclist = [x.lower() for x in funclist]
dtilist = [x.lower() for x in dtilist]
anatlist = [x.lower() for x in anatlist]
# Search the experiment file to find number of experiment groups
num_exp_grps=0
grp=0
expfile.seek(0)
for e in exps:
	try:
		grp=int(e[3])
		if grp > num_exp_grps:
			num_exp_grps = int(e[3])
	except ValueError:
		pass

# Loop through the list of scans
for scan in scanlist:
	# Reset the search to the beginning of demographics file
	demofile.seek(0)
	# Initialize some variables
	exp_orders = [1]*num_exp_grps
	# Loop through the demographics searching for subject scan ID
	foundscan = False
	foundfirst = False
	scandate = 'n/a'
	scantime = 'n/a'
	for row in demos:
		# If scan id found in demographics file
		if row[1] in scan[0]:
			print('Working on '+row[0]+' dir '+scan[0])
			foundscan = True
			# Set the BIDS subject ID
			bidsid = "sub-"+row[0][:-3].replace('_','')
			# Convert YYYYMMDD to MM/DD/YYYY
			#scandate=datetime.strptime(row[1][0:8], '%Y%m%d').strftime('%m/%d/%Y')
			# Convert age to number of months
			#try: 
			#   age=float(row[5])
			#  age_in_m = str((int(age)*12)+(daynum_to_date(int(row[1][0:4]), round((age-int(age))*365))))
			#except ValueError: 
			#  age_in_m = "N/A"
			# Find the group name
			if row[4] == '1': 
				group="control"
			elif row[4] == '2': 
				group="mid-risk"
			elif row[4] == '3': 
				group="high-risk"
			elif row[4] == '4':
				group="pilot"
			else:
				group="n/a"
			# Set the visit number
			visit = row[11]
			if visit == '1':
				bidsses="ses-baseline"
				behavpath2=behavpath
			else: 
				bidsses="ses-followup01"
				behavpath2=os.path.join(behavpath,"FollowUp")		
			# Create the output directories anat, func, dwi and notsupported
			outpath=os.path.join(skeletonpath,bidsid,bidsses,"anat")
			try:  
				os.makedirs(outpath)
			except OSError as exc: 
				if exc.errno == errno.EEXIST and os.path.isdir(outpath):
					pass
				else:
					raise
			if writeskeleton != 1:
				try:
					os.makedirs(os.path.join(bidspath,bidsid,bidsses,"anat"))
				except OSError as exc:
					if exc.errno == errno.EEXIST and os.path.isdir(outpath):
						pass
					else:
						raise
			outpath=os.path.join(skeletonpath,bidsid,bidsses,"func")
			try:  
				os.makedirs(outpath)
			except OSError as exc: 
				if exc.errno == errno.EEXIST and os.path.isdir(outpath):
					pass
				else:
					raise
			if writeskeleton != 1:
				try:
					os.makedirs(os.path.join(bidspath,bidsid,bidsses,"func"))
				except OSError as exc:
					if exc.errno == errno.EEXIST and os.path.isdir(outpath):
						pass
					else:
						raise					
			outpath=os.path.join(skeletonpath,bidsid,bidsses,"dwi")
			try:  
				os.makedirs(outpath)
			except OSError as exc: 
				if exc.errno == errno.EEXIST and os.path.isdir(outpath):
					pass
				else:
					raise
			if writeskeleton != 1:
				try:
					os.makedirs(os.path.join(bidspath,bidsid,bidsses,"dwi"))
				except OSError as exc:
					if exc.errno == errno.EEXIST and os.path.isdir(outpath):
						pass
					else:
						raise
			outpath=os.path.join(skeletonpath,bidsid,bidsses,"notsupported")
			try:  
				os.makedirs(outpath)
			except OSError as exc: 
				if exc.errno == errno.EEXIST and os.path.isdir(outpath):
					pass
				else:
					raise
			if writeskeleton != 1:
				try:
					os.makedirs(os.path.join(bidspath,bidsid,bidsses,"notsupported"))
				except OSError as exc:
					if exc.errno == errno.EEXIST and os.path.isdir(outpath):
						pass
					else:
						raise
			# Open the participants.tsv file and add subject if not included
			outtsv = os.path.join(skeletonpath,"participants.tsv")
			if os.path.isfile(outtsv):
				subjfound = False
				with open(outtsv) as csv_file:
					csv_reader = csv.reader(csv_file, delimiter='\t')
					for line in csv_reader:
						if line[0] == bidsid: 
							subjfound = True
							break
				if not subjfound:
					with open(outtsv, mode='a') as csv_file:
						csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
						csv_writer.writerow([bidsid, row[3], group]) 
			else: # If participants.tsv doesn't exist
				with open(outtsv, mode='w') as csv_file:
					csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
					csv_writer.writerow(['participant_id', 'sex', 'group'])
					csv_writer.writerow([bidsid, row[3], group])
			if writeskeleton != 1: 
				thisprocstr = str("cp " + outtsv + " " + os.path.join(bidspath,"participants.tsv"))
				subprocess.Popen(thisprocstr,shell=True).wait()

			# Loop through the files in the directories list looking for BXH files
			for count, fname in enumerate(sorted(os.listdir(scan[0])), start=1):
				if fname.endswith(".bxh"):
					# print('Loading '+os.path.join(scan[0],fname))
					# xmlh = bxh.load(os.path.join(scan[0],fname))
					doc = ET.parse(os.path.join(scan[0],fname))
					root = doc.getroot()
					datarec = root.find('b:datarec',namespaces=nspace)
					acqelem = root.find('b:acquisitiondata', namespaces=nspace)
					#print('finished loading')
					imdesc=acqelem.findtext('b:description',namespaces=nspace).lower()
					if imdesc in firstscan and not foundfirst: 
						foundfirst = True
						# Find the scan date
						scandate=acqelem.find('b:scandate',namespaces=nspace).text
						# Find the scan time
						scantime=acqelem.find('b:scantime',namespaces=nspace).text
						# Open the sessions tsv file and add subject if not included
						outtsv = os.path.join(skeletonpath,bidsid,bidsid + "_sessions.tsv")
						if os.path.isfile(outtsv):
							subjfound = False
							with open(outtsv) as csv_file:
								csv_reader = csv.reader(csv_file, delimiter='\t')
								for line in csv_reader:
									if line[0] == bidsses: 
										subjfound = True
										break
							if not subjfound:
								with open(outtsv, mode='a') as csv_file:
									csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
									try: 
										csv_writer.writerow([bidsses, scandate+"T"+scantime, int(float(row[5])/12)])
									except ValueError: 
										csv_writer.writerow([bidsses, scandate+"T"+scantime, 'n/a'])
						else: # If sessions tsv doesn't exist
							with open(outtsv, mode='w') as csv_file:
								csv_writer = csv.writer(csv_file, delimiter='\t', quotechar='|', quoting=csv.QUOTE_MINIMAL)
								csv_writer.writerow(['session_id', 'acq_time', 'age'])
								try: 
									csv_writer.writerow([bidsses, scandate+"T"+scantime,int(float(row[5])/12)])
								except ValueError: 
									csv_writer.writerow([bidsses, scandate+"T"+scantime, 'n/a'])
								shutil.copy(sessjson, os.path.join(skeletonpath,bidsid,bidsid + "_sessions.json"))
						if writeskeleton != 1: 
							thisprocstr = str("cp " + outtsv + " " + os.path.join(bidspath,bidsid,bidsid + "_sessions.tsv"))
							subprocess.Popen(thisprocstr,shell=True).wait()
							shutil.copy(sessjson, os.path.join(bidspath,bidsid,bidsid + "_sessions.json"))
					if imdesc in funclist+dtilist+anatlist:
						# Initialize variables
						isfunc=False
						isdti=False
						subdir="notsupported"
						# Initialize the output string
						outstr = ['']*len(series_order_elements)
						# Find the number of timepoints
						try: 
							numtp=datarec.findall('b:dimension',namespaces=nspace)[3].find('b:size',namespaces=nspace).text
						except IndexError: 
							numtp='1'
						if imdesc in funclist: 
							isfunc = True
							# Search the experiment file to find correct experiment
							expfile.seek(0)
							for e in exps:
								if imdesc == e[5].lower() and numtp in e[6] and visit == e[7]:
									if exp_orders[int(e[3])-1] == int(e[4]):
										outstr[series_order_elements.index('experiment_description')]=e[1].replace(' ','_')
										#outstr[series_order_elements.index('experiment_id')]=e[2]
										exp_orders[int(e[3])-1]+=1
										subdir=e[8]
										outpath=os.path.join(skeletonpath,bidsid,bidsses,e[8])
										outname=os.path.join(outpath,bidsid+"_"+bidsses+"_task-"+e[1].replace(' ',''))
										outpathbids=os.path.join(bidspath,bidsid,bidsses,e[8])
										outnamebids=os.path.join(outpathbids,bidsid+"_"+bidsses+"_task-"+e[1].replace(' ',''))
										if not os.path.isfile(outname + "_" + e[9] + ".nii.gz") and not os.path.isfile(outname + "_" + e[9] + ".bxh"):
											print('CONVERTING '+imdesc)
											thisprocstr = str("touch " + outname + "_" + e[9] + ".bxh")
											subprocess.Popen(thisprocstr,shell=True).wait()
											thisprocstr = str("touch " + outname + "_" + e[9] + ".nii.gz")
											subprocess.Popen(thisprocstr,shell=True).wait()
											if writeskeleton != 1: 
												thisprocstr = str("bxhselect " + os.path.join(scan[0],fname) + " " + outnamebids + "_" + e[9] + ".bxh")
												subprocess.Popen(thisprocstr,shell=True).wait()
										else: 
											print('ERROR: File exists, delete it and corresponding BXH to recreate: '+ outname + "_" + e[9] + ".nii.gz")
										if not os.path.isfile(outname + "_" + e[9] + ".json"): 
											thisprocstr = str("touch " + outname + "_" + e[9] + ".json")
											subprocess.Popen(thisprocstr,shell=True).wait()
											if writeskeleton != 1:										
												thisprocstr = str("python bxh2json_cognit -i " + outnamebids + "_" + e[9] + ".bxh")
												subprocess.Popen(thisprocstr,shell=True).wait()
												a_dict = {'TaskName': e[1]}
												with open(outnamebids + "_" + e[9] + '.json') as f:
													data = json.load(f)
												data.update(a_dict)
												with open(outnamebids + "_" + e[9] + '.json', 'w') as f:
													json.dump(data,f,sort_keys=True,indent=1)
										else: 
											print('ERROR: File exists, delete to recreate: '+ outname + "_" + e[9] + ".json")
										#print(thisprocstr)
										if not os.path.isfile(outname+"_events.tsv"):  
											thisprocstr = str("touch " + outname + "_events.tsv")
											subprocess.Popen(thisprocstr,shell=True).wait()
											if writeskeleton != 1: 
												try: 
													allevents=[]
													# print(os.path.join(behavpath2,row[0],e[10]))
													for count_b, fname_b in enumerate(sorted(os.listdir(os.path.join(behavpath2,row[0],e[10]))), start=1):
														if fname_b.endswith(".stf"):
															with open(os.path.join(behavpath2,row[0],e[10],fname_b)) as tsv: 
																for line in csv.reader(tsv, delimiter="\t"): 
																	if len(line) == 1:
																		line = line[0].split()
																	allevents.append([float(line[0]),float(line[1]),fname_b[:-4]])
													if len(allevents) > 0: 
														# print(outnamebids+"_events.tsv")
														# Open the events tsv file
														outputtsv = outnamebids+"_events.tsv"
														outputtsv = open(outputtsv,'w+')
														# Write the header
														outputtsv.write('onset\tduration\ttrial_type\n')
														for i in sorted(allevents): 
															#print(i)
															outputtsv.write(str(i[0])+'\t'+str(i[1])+'\t'+i[2]+'\n')
														# Close the events tsv file
														outputtsv.close()
												except OSError: 
													pass
												break
										else: 
											print('ERROR: File exists, delete to recreate: '+ outname+"_events.tsv")
										#print(thisprocstr)										
						else:
							# Search the experiment file to find correct experiment
							expfile.seek(0)
							for e in exps:
								#print(imdesc, numtp, visit)
								#print(e[5].lower(), e[6], e[7])
								if imdesc == e[5].lower() and numtp in e[6] and visit == e[7]:
									outstr[series_order_elements.index('experiment_description')]=e[1].replace(' ','_')
									#outstr[series_order_elements.index('experiment_id')]=e[2]
									outpath=os.path.join(skeletonpath,bidsid,bidsses,e[8])
									outname=os.path.join(outpath,bidsid+"_"+bidsses+"_"+e[9])
									outpathbids=os.path.join(bidspath,bidsid,bidsses,e[8])
									outnamebids=os.path.join(outpathbids,bidsid+"_"+bidsses+"_"+e[9])
									if not os.path.isfile(outname + ".nii.gz") and not os.path.isfile(outname + ".bxh"):
										print('CONVERTING '+imdesc)
										thisprocstr = str("touch " + outname + ".bxh")
										subprocess.Popen(thisprocstr,shell=True).wait()
										thisprocstr = str("touch " + outname + ".nii.gz")
										subprocess.Popen(thisprocstr,shell=True).wait()
										if writeskeleton != 1: 
											thisprocstr = str("bxhselect " + os.path.join(scan[0],fname) + " " + outnamebids + ".bxh")
											subprocess.Popen(thisprocstr,shell=True).wait()
									else: 
										print('ERROR: File exists, delete it and corresponding BXH to recreate: '+ outname + ".nii.gz")
									if not os.path.isfile(outname + ".json"): 
										thisprocstr = str("touch " + outname + ".json")
										subprocess.Popen(thisprocstr,shell=True).wait()
										if writeskeleton != 1: 
											thisprocstr = str("python bxh2json_cognit -i " + outnamebids + ".bxh")
											subprocess.Popen(thisprocstr,shell=True).wait()
									else: 
										print('ERROR: File exists, delete to recreate: '+ outname + ".json")
									#print(outname)
									if imdesc in dtilist:
										if not os.path.isfile(outname + ".bval") and not os.path.isfile(outname + ".bvec"): 
											thisprocstr = str("touch " + outname + ".bval")
											subprocess.Popen(thisprocstr,shell=True).wait()
											thisprocstr = str("touch " + outname + ".bvec")
											subprocess.Popen(thisprocstr,shell=True).wait()
											if writeskeleton != 1: 
												# Convert the bvals and bvecs to space delimited
												tsvfile = open(outnamebids+".bval","rb")
												temptsv = open(outnamebids+".bval.tmp","w")
												for i in tsvfile: 
													temptsv.write(i.replace('\t',' '))
												tsvfile.close()
												temptsv.close()
												os.remove(outname+".bval")
												os.rename(outnamebids+".bval.tmp",outnamebids+".bval")
												tsvfile = open(outnamebids+".bvec","rb")
												temptsv = open(outnamebids+".bvec.tmp","w")
												for i in tsvfile: 
													temptsv.write(i.replace('\t',' '))
												tsvfile.close()
												temptsv.close()
												os.remove(outnamebids+".bvec")
												os.rename(outnamebids+".bvec.tmp",outnamebids+".bvec")
										else: 
											print('ERROR: File exists, delete to recreate: '+ outname + ".bval/.bvec")
									break

					else:
						print('Not adding '+imdesc)
			
			# Break out of the loop through demographics file if found
			break
		
	if not(foundscan):
		print('Found no demographics data for '+scan[0])
