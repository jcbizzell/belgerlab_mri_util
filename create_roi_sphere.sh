#!/bin/bash

# Example: 
# bash create_roi_sphere.sh 29 71 36 exp_blk_ctl_ins_R 5
# Coordinates need to be image coordintates, NOT MNI coordinates
# Can get that transform from FSLView

# Read in input variables
X=$1
Y=$2
Z=$3
ROI=$4
SPHRSZ=$5

# Set variable

OUTDIR=/mnt/BIAC/munin.dhe.duke.edu/Belger/ADOLSTRESS.01/Analysis/ROIs

#IMAGE, X Y Z coords outname, if your coordinate is 36,46,45, will create a one point mask 
fslmaths $FSLDIR/data/standard/MNI152_T1_2mm_brain -add 10000 -roi $X 1 $Y 1 $Z 1 0 1 $OUTDIR/${ROI}_point_mask

#now make indiv Xmm sj spheres 5mm or 8 mm
fslmaths $OUTDIR/${ROI}_point_mask -kernel sphere $SPHRSZ -fmean $OUTDIR/${ROI}_${SPHRSZ}MM_sphere

#binarize the data
fslmaths $OUTDIR/${ROI}_${SPHRSZ}MM_sphere -bin $OUTDIR/${ROI}_${SPHRSZ}MM_bin

#remove point mask
rm -f $OUTDIR/${ROI}_point_mask.*
